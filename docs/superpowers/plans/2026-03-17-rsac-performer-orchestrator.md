# RSAC Performer Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um `Performer` offline-orquestrador que coleta itens elegíveis no banco, respeita `attempts` e `MaxAttempts`, processa uma cooperativa por vez e atualiza o consolidado mensal com save e publicação incremental.

**Architecture:** O `Performer` será decomposto em unidades pequenas: seleção de fila, atualização de tentativas/status, resolução do consolidado mensal, runner do item e orquestrador principal. As integrações externas continuarão injetáveis, para preservar a regra de negócio e permitir conexão posterior com banco real, SharePoint, e-mail e fluxo RSA sem reescrever o núcleo.

**Tech Stack:** Python 3.13, pytest, openpyxl, dataclasses, pathlib

---

## File Map

- Modify: `src/rsac_relatorios_risco/config/models.py`
  - acrescentar modelos utilitários para dados operacionais se necessário
- Modify: `src/rsac_relatorios_risco/config/workbook_loader.py`
  - expor acesso previsível a `Settings`, incluindo `MaxAttempts`
- Create: `src/rsac_relatorios_risco/performer/models.py`
  - dataclasses do domínio do `Performer`
- Create: `src/rsac_relatorios_risco/performer/queue_selector.py`
  - elegibilidade de itens por status e `MaxAttempts`
- Create: `src/rsac_relatorios_risco/performer/item_updater.py`
  - espelho da lógica de `UpdateItem` da lib UiPath
- Create: `src/rsac_relatorios_risco/performer/consolidado_resolver.py`
  - localizar ou criar consolidado mensal a partir da competência
- Create: `src/rsac_relatorios_risco/performer/item_runner.py`
  - fluxo completo de um item já coletado
- Create: `src/rsac_relatorios_risco/performer/orchestrator.py`
  - loop principal do `Performer`
- Modify: `src/rsac_relatorios_risco/performer/__init__.py`
  - exportar componentes principais se fizer sentido
- Modify: `agent_jarbis.py`
  - expor uma entrada mínima do `Performer` offline
- Test: `tests/performer/test_queue_selector.py`
- Test: `tests/performer/test_item_updater.py`
- Test: `tests/performer/test_consolidado_resolver.py`
- Test: `tests/performer/test_item_runner.py`
- Test: `tests/performer/test_orchestrator.py`
- Modify: `tests/test_agent_jarbis_smoke.py`

## Chunk 1: Fila e Attempts

### Task 1: Seleção de itens elegíveis

**Files:**
- Create: `src/rsac_relatorios_risco/performer/models.py`
- Create: `src/rsac_relatorios_risco/performer/queue_selector.py`
- Test: `tests/performer/test_queue_selector.py`

- [ ] **Step 1: Write the failing tests**

```python
from rsac_relatorios_risco.performer.models import PerformerItem
from rsac_relatorios_risco.performer.queue_selector import (
    filter_eligible_items,
    is_item_eligible,
)


def test_is_item_eligible_accepts_pending_and_retryable_error_statuses():
    assert is_item_eligible("pendente", 0, 3) is True
    assert is_item_eligible("erro sistêmico", 1, 3) is True
    assert is_item_eligible("exceção negocial", 2, 3) is True


def test_is_item_eligible_rejects_success_and_processing_or_max_attempts_reached():
    assert is_item_eligible("sucesso", 0, 3) is False
    assert is_item_eligible("processando", 1, 3) is False
    assert is_item_eligible("erro sistêmico", 3, 3) is False


def test_filter_eligible_items_returns_only_processable_items():
    items = [
        PerformerItem(item_id=1, reference="A", status="pendente", attempts=[]),
        PerformerItem(item_id=2, reference="B", status="sucesso", attempts=[]),
        PerformerItem(item_id=3, reference="C", status="erro sistêmico", attempts=[{}, {}]),
    ]

    eligible = filter_eligible_items(items, max_attempts=3)

    assert [item.item_id for item in eligible] == [1, 3]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/performer/test_queue_selector.py -v`

Expected: FAIL because `models.py` and `queue_selector.py` do not exist

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class PerformerItem:
    item_id: int
    reference: str
    status: str
    attempts: list[dict] = field(default_factory=list)


ELIGIBLE_STATUSES = {"pendente", "erro sistêmico", "exceção negocial"}


def is_item_eligible(status: str, attempt_count: int, max_attempts: int) -> bool:
    return status in ELIGIBLE_STATUSES and attempt_count < max_attempts


def filter_eligible_items(items: list[PerformerItem], max_attempts: int) -> list[PerformerItem]:
    return [
        item
        for item in items
        if is_item_eligible(item.status, len(item.attempts), max_attempts)
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/performer/test_queue_selector.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rsac_relatorios_risco/performer/models.py src/rsac_relatorios_risco/performer/queue_selector.py tests/performer/test_queue_selector.py
git commit -m "feat: add performer queue eligibility rules"
```

### Task 2: Espelhar a lógica de `UpdateItem` para attempts

**Files:**
- Modify: `src/rsac_relatorios_risco/performer/models.py`
- Create: `src/rsac_relatorios_risco/performer/item_updater.py`
- Test: `tests/performer/test_item_updater.py`

- [ ] **Step 1: Write the failing tests**

```python
from rsac_relatorios_risco.performer.item_updater import (
    close_attempt,
    open_processing_attempt,
)


def test_open_processing_attempt_appends_new_processing_attempt():
    attempts = []

    updated = open_processing_attempt(attempts)

    assert updated[-1]["status"] == "processando"
    assert updated[-1]["attempt_number"] == 1
    assert updated[-1]["finished_at"] == ""


def test_open_processing_attempt_rejects_duplicate_open_processing_attempt():
    attempts = [{"status": "processando", "attempt_number": 1, "started_at": "x", "finished_at": ""}]

    with pytest.raises(ValueError, match="processando já existe"):
        open_processing_attempt(attempts)


def test_close_attempt_finishes_last_processing_attempt_with_final_status():
    attempts = [{"status": "processando", "attempt_number": 1, "started_at": "x", "finished_at": ""}]

    updated = close_attempt(attempts, "sucesso")

    assert updated[-1]["status"] == "sucesso"
    assert updated[-1]["finished_at"] != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/performer/test_item_updater.py -v`

Expected: FAIL because `item_updater.py` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
from copy import deepcopy
from datetime import datetime, timezone


FINAL_STATUSES = {"sucesso", "erro sistêmico", "exceção negocial"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def open_processing_attempt(attempts: list[dict]) -> list[dict]:
    updated = deepcopy(attempts)
    if updated and updated[-1]["status"] == "processando":
        raise ValueError("Operação inválida. Status processando já existe.")
    updated.append(
        {
            "status": "processando",
            "started_at": _utc_now(),
            "finished_at": "",
            "attempt_number": len(updated) + 1,
        }
    )
    return updated


def close_attempt(attempts: list[dict], final_status: str) -> list[dict]:
    if final_status not in FINAL_STATUSES:
        raise ValueError("Status final inválido")
    updated = deepcopy(attempts)
    if not updated or updated[-1]["status"] != "processando":
        raise ValueError("Operação inválida. Status atual diferente de processando.")
    updated[-1]["status"] = final_status
    updated[-1]["finished_at"] = _utc_now()
    return updated
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/performer/test_item_updater.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rsac_relatorios_risco/performer/models.py src/rsac_relatorios_risco/performer/item_updater.py tests/performer/test_item_updater.py
git commit -m "feat: mirror attempt lifecycle from update item logic"
```

## Chunk 2: Consolidado e Runner do Item

### Task 3: Resolver o consolidado mensal

**Files:**
- Create: `src/rsac_relatorios_risco/performer/consolidado_resolver.py`
- Test: `tests/performer/test_consolidado_resolver.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from openpyxl import Workbook, load_workbook

from rsac_relatorios_risco.performer.consolidado_resolver import resolve_monthly_workbook


def test_resolve_monthly_workbook_creates_copy_from_template_when_missing(tmp_path: Path):
    template = tmp_path / "modelo.xlsx"
    wb = Workbook()
    wb.save(template)

    workbook_path = resolve_monthly_workbook(
        template_path=template,
        output_dir=tmp_path,
        competencia="03/2026",
        file_name="RSAC_032026.xlsx",
    )

    assert workbook_path.exists()
    assert workbook_path.name == "RSAC_032026.xlsx"


def test_resolve_monthly_workbook_reuses_existing_file_when_already_created(tmp_path: Path):
    template = tmp_path / "modelo.xlsx"
    Workbook().save(template)
    existing = tmp_path / "RSAC_032026.xlsx"
    Workbook().save(existing)

    workbook_path = resolve_monthly_workbook(
        template_path=template,
        output_dir=tmp_path,
        competencia="03/2026",
        file_name="RSAC_032026.xlsx",
    )

    assert workbook_path == existing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/performer/test_consolidado_resolver.py -v`

Expected: FAIL because `consolidado_resolver.py` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path
import shutil


def resolve_monthly_workbook(
    *,
    template_path: Path,
    output_dir: Path,
    competencia: str,
    file_name: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook_path = output_dir / file_name
    if workbook_path.exists():
        return workbook_path
    shutil.copy2(template_path, workbook_path)
    return workbook_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/performer/test_consolidado_resolver.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rsac_relatorios_risco/performer/consolidado_resolver.py tests/performer/test_consolidado_resolver.py
git commit -m "feat: add monthly consolidated workbook resolver"
```

### Task 4: Executar um item completo

**Files:**
- Create: `src/rsac_relatorios_risco/performer/item_runner.py`
- Modify: `src/rsac_relatorios_risco/performer/models.py`
- Test: `tests/performer/test_item_runner.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from rsac_relatorios_risco.performer.item_runner import PerformerItemRunner
from rsac_relatorios_risco.performer.models import PerformerItem


class FakeFlow:
    def __init__(self):
        self.calls = []
    def abrir_modulo_rsa(self): self.calls.append("abrir")
    def preencher_filtros(self, *, competencia, tipo_relatorio): self.calls.append(("filtros", competencia, tipo_relatorio))
    def selecionar_cooperativas(self, cooperativas): self.calls.append(("coops", cooperativas))
    def exportar_relatorio(self, download_dir): self.calls.append(("exportar", download_dir)); return download_dir / "relatorio.xlsx"


class FakeReportService:
    def read_report(self, path): return "REPORT"


class FakeBatchRunner:
    def publish_one(self, *, report, workbook_path, destination):
        return type("Result", (), {"sheet_saved": True, "sharepoint_published": True})()


def test_item_runner_executes_flow_for_single_item(tmp_path: Path):
    item = PerformerItem(
        item_id=1,
        reference="3333_RSAC_RISCO_032026",
        status="processando",
        attempts=[{"status": "processando", "attempt_number": 1, "started_at": "x", "finished_at": ""}],
        data={"cooperativa": "3333", "competencia": "03/2026", "tipo_relatorio": "RSAC", "sharepoint": "destino"},
    )
    runner = PerformerItemRunner(
        rsa_flow=FakeFlow(),
        report_service=FakeReportService(),
        batch_runner=FakeBatchRunner(),
    )

    result = runner.run(item=item, workbook_path=tmp_path / "consolidado.xlsx", download_dir=tmp_path)

    assert result.final_status == "sucesso"
    assert result.report_path.name == "relatorio.xlsx"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/performer/test_item_runner.py -v`

Expected: FAIL because `item_runner.py` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ItemRunResult:
    final_status: str
    report_path: Path


class PerformerItemRunner:
    def __init__(self, rsa_flow, report_service, batch_runner) -> None:
        self.rsa_flow = rsa_flow
        self.report_service = report_service
        self.batch_runner = batch_runner

    def run(self, *, item, workbook_path: Path, download_dir: Path) -> ItemRunResult:
        data = item.data
        self.rsa_flow.abrir_modulo_rsa()
        self.rsa_flow.preencher_filtros(
            competencia=data["competencia"],
            tipo_relatorio=data["tipo_relatorio"],
        )
        self.rsa_flow.selecionar_cooperativas([data["cooperativa"]])
        report_path = self.rsa_flow.exportar_relatorio(download_dir)
        report = self.report_service.read_report(report_path)
        publish_result = self.batch_runner.publish_one(
            report=report,
            workbook_path=workbook_path,
            destination=data["sharepoint"],
        )
        final_status = "sucesso" if publish_result.sheet_saved and publish_result.sharepoint_published else "erro sistêmico"
        return ItemRunResult(final_status=final_status, report_path=report_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/performer/test_item_runner.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rsac_relatorios_risco/performer/models.py src/rsac_relatorios_risco/performer/item_runner.py tests/performer/test_item_runner.py
git commit -m "feat: add single-item performer runner"
```

## Chunk 3: Orquestrador e Entrada do Worker

### Task 5: Orquestrar o loop do Performer

**Files:**
- Create: `src/rsac_relatorios_risco/performer/orchestrator.py`
- Modify: `src/rsac_relatorios_risco/config/workbook_loader.py`
- Test: `tests/performer/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from rsac_relatorios_risco.performer.models import PerformerItem
from rsac_relatorios_risco.performer.orchestrator import PerformerOrchestrator


class FakeQueueRepository:
    def __init__(self, items):
        self.items = items
    def list_items(self):
        return self.items


class FakeItemUpdater:
    def __init__(self):
        self.transitions = []
    def mark_processing(self, item):
        self.transitions.append(("processando", item.item_id))
        return item
    def mark_finished(self, item, final_status):
        self.transitions.append((final_status, item.item_id))


class FakeResolver:
    def resolve(self, item):
        return Path("temp/RSAC_032026.xlsx")


class FakeRunner:
    def run(self, *, item, workbook_path, download_dir):
        return type("Result", (), {"final_status": "sucesso", "report_path": download_dir / "r.xlsx"})()


class FakeEmailService:
    def __init__(self):
        self.sent = None
    def send_summary(self, summary):
        self.sent = summary


def test_orchestrator_processes_only_eligible_items_until_queue_is_exhausted(tmp_path: Path):
    items = [
        PerformerItem(item_id=1, reference="A", status="pendente", attempts=[], data={"competencia": "03/2026"}),
        PerformerItem(item_id=2, reference="B", status="sucesso", attempts=[], data={"competencia": "03/2026"}),
    ]
    orchestrator = PerformerOrchestrator(
        queue_repository=FakeQueueRepository(items),
        item_updater=FakeItemUpdater(),
        consolidado_resolver=FakeResolver(),
        item_runner=FakeRunner(),
        email_service=FakeEmailService(),
        max_attempts=3,
        download_dir=tmp_path,
    )

    summary = orchestrator.run()

    assert summary["concluidos"] == ["A"]
    assert summary["ignorados_por_max_attempts"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/performer/test_orchestrator.py -v`

Expected: FAIL because `orchestrator.py` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
from rsac_relatorios_risco.performer.queue_selector import filter_eligible_items


class PerformerOrchestrator:
    def __init__(
        self,
        *,
        queue_repository,
        item_updater,
        consolidado_resolver,
        item_runner,
        email_service,
        max_attempts: int,
        download_dir,
    ) -> None:
        self.queue_repository = queue_repository
        self.item_updater = item_updater
        self.consolidado_resolver = consolidado_resolver
        self.item_runner = item_runner
        self.email_service = email_service
        self.max_attempts = max_attempts
        self.download_dir = download_dir

    def run(self) -> dict:
        items = self.queue_repository.list_items()
        eligible = filter_eligible_items(items, self.max_attempts)
        summary = {
            "concluidos": [],
            "erros_sistemicos": [],
            "excecoes_negociais": [],
            "ignorados_por_max_attempts": [],
        }
        for item in eligible:
            self.item_updater.mark_processing(item)
            workbook_path = self.consolidado_resolver.resolve(item)
            result = self.item_runner.run(
                item=item,
                workbook_path=workbook_path,
                download_dir=self.download_dir,
            )
            self.item_updater.mark_finished(item, result.final_status)
            if result.final_status == "sucesso":
                summary["concluidos"].append(item.reference)
            elif result.final_status == "erro sistêmico":
                summary["erros_sistemicos"].append(item.reference)
            else:
                summary["excecoes_negociais"].append(item.reference)
        self.email_service.send_summary(summary)
        return summary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/performer/test_orchestrator.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rsac_relatorios_risco/performer/orchestrator.py tests/performer/test_orchestrator.py
git commit -m "feat: add performer offline orchestrator"
```

### Task 6: Expor entrada mínima do Performer

**Files:**
- Modify: `agent_jarbis.py`
- Modify: `tests/test_agent_jarbis_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
import agent_jarbis


def test_agent_jarbis_exposes_performer_entrypoint():
    assert hasattr(agent_jarbis, "run_performer")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agent_jarbis_smoke.py::test_agent_jarbis_exposes_performer_entrypoint -v`

Expected: FAIL because `run_performer` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
REGISTERED_TOPICS = ["DISPATCHER_RSAC", "PERFORMER_RSAC"]


def run_performer(orchestrator):
    return orchestrator.run()


def main():
    return REGISTERED_TOPICS
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agent_jarbis_smoke.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent_jarbis.py tests/test_agent_jarbis_smoke.py
git commit -m "feat: expose performer entrypoint"
```

## Chunk 4: Verificação da Fase do Performer

### Task 7: Rodar verificação completa do slice

**Files:**
- Verify only: arquivos do `performer`, `utils/rpa_actions.py`, `agent_jarbis.py`, testes relacionados

- [ ] **Step 1: Run the full performer slice**

Run: `python -m pytest tests/performer tests/web tests/test_agent_jarbis_smoke.py -v`

Expected: PASS

- [ ] **Step 2: Run the full project test suite**

Run: `python -m pytest tests -q`

Expected: `30+ passed` com possível warning conhecido do `openpyxl`

- [ ] **Step 3: Verify clean orchestration entrypoint**

Run: `python -c "import agent_jarbis; print(hasattr(agent_jarbis, 'run_performer'))"`

Expected: `True`

- [ ] **Step 4: Commit final verification slice**

```bash
git add agent_jarbis.py src/rsac_relatorios_risco/performer tests/performer tests/test_agent_jarbis_smoke.py
git commit -m "chore: verify performer orchestrator slice"
```

- [ ] **Step 5: Stop before real integrations**

Expected:
- `Performer` offline-orquestrador pronto
- política de `attempts` espelhada
- coleta elegível por `MaxAttempts`
- execução item a item pronta
- integrações reais ainda plugáveis
