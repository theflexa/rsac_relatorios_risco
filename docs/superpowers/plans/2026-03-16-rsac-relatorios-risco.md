# RSAC Relatórios de Risco Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a fase 1 do projeto RSAC com `Dispatcher`, leitura do `Config.xlsx`, manipulação do consolidado mensal, reconciliação do `Performer`, upload incremental no SharePoint, e-mail final, limpeza local e entrada do worker Jarbis, mantendo a automação web RSA bloqueada até a entrega dos seletores.

**Architecture:** O projeto será um pacote Python em `src/rsac_relatorios_risco`, separado em `config`, `dispatcher`, `performer`, `services`, `integrations` e `web`. Nesta fase, a entrega útil é backend-first: `Config.xlsx`, Excel, Jarbis/banco, SharePoint e e-mail; a camada web fica em stub.

**Tech Stack:** Python 3.11, pytest, openpyxl, requests, msal, python-dotenv, loguru, jarbis_external_client

---

## Preflight

- O diretório atual não está em um repositório `git`
- Antes de executar os commits deste plano, inicialize ou conecte este diretório a um repositório real
- A camada web RSA está fora do escopo desta fase; qualquer código dela deve ficar em stub/contrato apenas

## File Map

- `pyproject.toml`
- `.env.example`
- `agent_jarbis.py`
- `src/rsac_relatorios_risco/__init__.py`
- `src/rsac_relatorios_risco/config/models.py`
- `src/rsac_relatorios_risco/config/placeholder_resolver.py`
- `src/rsac_relatorios_risco/config/workbook_loader.py`
- `src/rsac_relatorios_risco/dispatcher/service.py`
- `src/rsac_relatorios_risco/performer/reconciliation.py`
- `src/rsac_relatorios_risco/performer/batch_runner.py`
- `src/rsac_relatorios_risco/services/report_service.py`
- `src/rsac_relatorios_risco/services/consolidado_service.py`
- `src/rsac_relatorios_risco/services/email_service.py`
- `src/rsac_relatorios_risco/services/cleanup_service.py`
- `src/rsac_relatorios_risco/integrations/database_client.py`
- `src/rsac_relatorios_risco/integrations/jarbis_client.py`
- `src/rsac_relatorios_risco/integrations/sharepoint_client.py`
- `src/rsac_relatorios_risco/integrations/mail_client.py`
- `src/rsac_relatorios_risco/web/rsa_portal_stub.py`
- `tests/test_package_bootstrap.py`
- `tests/config/test_placeholder_resolver.py`
- `tests/config/test_workbook_loader.py`
- `tests/dispatcher/test_dispatcher_service.py`
- `tests/services/test_report_service.py`
- `tests/services/test_consolidado_service.py`
- `tests/performer/test_reconciliation.py`
- `tests/performer/test_batch_runner.py`
- `tests/services/test_email_service.py`
- `tests/services/test_cleanup_service.py`
- `tests/integrations/test_sharepoint_client.py`
- `tests/test_agent_jarbis_smoke.py`

## Chunk 1: Fundação, Config e Dispatcher

### Task 1: Bootstrap do pacote

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `src/rsac_relatorios_risco/__init__.py`
- Test: `tests/test_package_bootstrap.py`

- [ ] **Step 1: Write the failing test**
```python
import importlib
def test_package_bootstrap_imports():
    assert importlib.import_module("rsac_relatorios_risco") is not None
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_package_bootstrap.py::test_package_bootstrap_imports -v`
Expected: FAIL with `ModuleNotFoundError`
- [ ] **Step 3: Write minimal implementation**
```toml
[project]
name = "rsac-relatorios-risco"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["openpyxl","python-dotenv","loguru","requests","msal","jarbis_external_client"]
[tool.pytest.ini_options]
pythonpath = ["src"]
```
```env
DATABASE_URL=
DATABASE_API_KEY=
JARBIS_BASE_URL=
JARBIS_USERNAME=
JARBIS_PASSWORD=
SHAREPOINT_TENANT_ID=
SHAREPOINT_CLIENT_ID=
SHAREPOINT_CLIENT_SECRET=
MAIL_MODE=disabled
```
```python
__all__ = []
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_package_bootstrap.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add pyproject.toml .env.example src/rsac_relatorios_risco/__init__.py tests/test_package_bootstrap.py
git commit -m "chore: bootstrap rsac package"
```

### Task 2: Implementar placeholders e loader do `Config.xlsx`

**Files:**
- Create: `src/rsac_relatorios_risco/config/models.py`
- Create: `src/rsac_relatorios_risco/config/placeholder_resolver.py`
- Create: `src/rsac_relatorios_risco/config/workbook_loader.py`
- Test: `tests/config/test_placeholder_resolver.py`
- Test: `tests/config/test_workbook_loader.py`

- [ ] **Step 1: Write the failing tests**
```python
from rsac_relatorios_risco.config.placeholder_resolver import resolve_value
def test_resolve_supported_placeholders_in_literal_and_formula_string():
    ctx = {"Data": "032026", "YYYY-MM": "2026-03"}
    assert resolve_value("{Data}", ctx) == "032026"
    assert resolve_value("saida/{YYYY-MM}", ctx) == "saida/2026-03"
    assert resolve_value('=D2 & "_RSAC_RISCO_{Data}"', ctx) == '=D2 & "_RSAC_RISCO_032026"'
```
```python
# test_workbook_loader.py
# cobrir 4 cenários:
# 1. Items vence quando Items e QueueItems coexistem
# 2. fallback para QueueItems
# 3. valor vazio em Items herda default de Settings
# 4. Reference vazia após resolução gera ValueError
```
- [ ] **Step 2: Run tests to verify they fail**
Run: `pytest tests/config/test_placeholder_resolver.py tests/config/test_workbook_loader.py -v`
Expected: FAIL because resolver e loader não existem
- [ ] **Step 3: Write minimal implementation**
```python
def resolve_value(raw: str, context: dict[str, str]) -> str:
    result = raw
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", value)
    return result

def load_config_workbook(path: Path, mes: str, ano: str) -> ConfigWorkbook:
    context = {"Data": f"{mes}{ano}", "YYYY-MM": f"{ano}-{mes}"}
    settings = _load_settings(path)
    rows = _load_rows(path, preferred_sheet="Items", fallback_sheet="QueueItems")
    items = []
    for row in rows:
        merged = _merge_row_with_settings_defaults(row, settings)
        resolved = _resolve_placeholders_in_row(merged, context)
        if not resolved["Reference"]:
            raise ValueError("Reference vazia após resolução")
        items.append(_build_item_config(resolved))
    return ConfigWorkbook(settings=settings, items=items)
```
- [ ] **Step 4: Run tests to verify it passes**
Run: `pytest tests/config/test_placeholder_resolver.py tests/config/test_workbook_loader.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/config/models.py src/rsac_relatorios_risco/config/placeholder_resolver.py src/rsac_relatorios_risco/config/workbook_loader.py tests/config/test_placeholder_resolver.py tests/config/test_workbook_loader.py
git commit -m "feat: add config workbook contract and placeholders"
```

### Task 3: Implementar contratos de integração com banco e Jarbis

**Files:**
- Create: `src/rsac_relatorios_risco/integrations/database_client.py`
- Create: `src/rsac_relatorios_risco/integrations/jarbis_client.py`
- Test: `tests/dispatcher/test_dispatcher_service.py`

- [ ] **Step 1: Write the failing tests**
```python
from rsac_relatorios_risco.integrations.database_client import build_item_payload
from rsac_relatorios_risco.integrations.jarbis_client import build_process_variables
def test_build_item_payload_preserves_sheet_reference():
    payload = build_item_payload(1, 2, "3333_RSAC_RISCO_032026", {"cooperativa": "3333"})
    assert payload["reference"] == "3333_RSAC_RISCO_032026"
    assert payload["status"] == "aguardando"
def test_build_process_variables_uses_inserted_item_reference():
    variables = build_process_variables({"reference": "3333_RSAC_RISCO_032026"})
    assert variables["reference"]["value"] == "3333_RSAC_RISCO_032026"
```
- [ ] **Step 2: Run tests to verify they fail**
Run: `pytest tests/dispatcher/test_dispatcher_service.py::test_build_item_payload_preserves_sheet_reference tests/dispatcher/test_dispatcher_service.py::test_build_process_variables_uses_inserted_item_reference -v`
Expected: FAIL because helpers não existem
- [ ] **Step 3: Write minimal implementation**
```python
def build_item_payload(project_id: int, job_id: int, reference: str, json_data: dict) -> dict:
    return {"project_id": project_id, "job_id": job_id, "data": json_data, "status": "aguardando", "reference": reference}
def build_process_variables(item_payload: dict) -> dict:
    return {"reference": {"value": item_payload["reference"], "type": "String"}}
```
- [ ] **Step 4: Run tests to verify they pass**
Run: `pytest tests/dispatcher/test_dispatcher_service.py::test_build_item_payload_preserves_sheet_reference tests/dispatcher/test_dispatcher_service.py::test_build_process_variables_uses_inserted_item_reference -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/integrations/database_client.py src/rsac_relatorios_risco/integrations/jarbis_client.py tests/dispatcher/test_dispatcher_service.py
git commit -m "feat: add dispatcher integration contracts"
```

### Task 4: Entregar um slice executável do `Dispatcher`

**Files:**
- Create: `src/rsac_relatorios_risco/dispatcher/service.py`
- Modify: `tests/dispatcher/test_dispatcher_service.py`

- [ ] **Step 1: Write the failing test**
```python
# testar que:
# 1. load_config_workbook lê as refs da planilha
# 2. refs já existentes são reaproveitadas
# 3. apenas itens novos entram no insert
# 4. cada item inserido gera start_process_instance
# 5. resultado retorna inserted_count, skipped_count, reused_references e log_messages em pt-BR
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/dispatcher/test_dispatcher_service.py -v`
Expected: FAIL because `DispatcherService` não existe
- [ ] **Step 3: Write minimal implementation**
```python
@dataclass
class DispatchResult:
    inserted_count: int
    skipped_count: int
    reused_references: list[str]
    log_messages: list[str]

class DispatcherService:
    def dispatch(self, workbook_path: Path, mes: str, ano: str) -> DispatchResult:
        config = load_config_workbook(workbook_path, mes=mes, ano=ano)
        existing = self.database_client.get_existing_references(project_id=1)
        project_id, job_id = self.database_client.ensure_project_and_job()
        reused = [item.reference for item in config.items if item.reference in existing]
        log_messages = [f"Item {reference} reaproveitado" for reference in reused]
        payloads = [build_item_payload(project_id, job_id, item.reference, item.to_json()) for item in config.items if item.reference not in existing]
        inserted = self.database_client.insert_items(payloads)
        for item_payload in inserted:
            self.jarbis_client.start_process_instance(item_payload)
        return DispatchResult(len(inserted), len(reused), reused, log_messages)
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/dispatcher/test_dispatcher_service.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/dispatcher/service.py tests/dispatcher/test_dispatcher_service.py
git commit -m "feat: implement executable dispatcher slice"
```

## Chunk 2: Excel, Performer e Saídas Incrementais

### Task 5: Ler metadados e linhas do relatório exportado

**Files:**
- Create: `src/rsac_relatorios_risco/services/report_service.py`
- Test: `tests/services/test_report_service.py`

- [ ] **Step 1: Write the failing test**
```python
from pathlib import Path
from rsac_relatorios_risco.services.report_service import read_report
def test_read_report_extracts_metadata_and_rows():
    report = read_report(Path("Models/rpas1004_00_RELATORIO_RISCO_COOPERATIVA_20260313_182416_0644.XLSX.XLSX.XLSX"))
    assert report.cooperativa == "3042"
    assert report.competencia == "03/2026"
    assert len(report.rows) > 0
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/services/test_report_service.py::test_read_report_extracts_metadata_and_rows -v`
Expected: FAIL because service não existe
- [ ] **Step 3: Write minimal implementation**
```python
def read_report(path: Path) -> ReportData:
    raise NotImplementedError
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/services/test_report_service.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/services/report_service.py tests/services/test_report_service.py
git commit -m "feat: parse rsac exported report"
```

### Task 6: Criar e atualizar o consolidado mensal

**Files:**
- Create: `src/rsac_relatorios_risco/services/consolidado_service.py`
- Test: `tests/services/test_consolidado_service.py`

- [ ] **Step 1: Write the failing tests**
```python
# cobrir:
# 1. um único match de cabeçalho retorna row index
# 2. nenhum match levanta TableMatchError
# 3. mais de um match levanta TableMatchError
# 4. apply_report limpa apenas dados abaixo do cabeçalho e reescreve a tabela
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/services/test_consolidado_service.py -v`
Expected: FAIL because service não existe
- [ ] **Step 3: Write minimal implementation**
```python
class ConsolidadoService:
    def find_header_row(self, cooperativa: str) -> int:
        raise NotImplementedError
    def _validate_header_matches(self, matches: list[int]) -> int:
        raise NotImplementedError
    def apply_report(self, workbook_path: Path, report: ReportData) -> None:
        raise NotImplementedError
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/services/test_consolidado_service.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/services/consolidado_service.py tests/services/test_consolidado_service.py
git commit -m "feat: add consolidated workbook service"
```

### Task 7: Implementar reconciliação e lote do Performer

**Files:**
- Create: `src/rsac_relatorios_risco/performer/reconciliation.py`
- Create: `src/rsac_relatorios_risco/performer/batch_runner.py`
- Test: `tests/performer/test_reconciliation.py`
- Test: `tests/performer/test_batch_runner.py`

- [ ] **Step 1: Write the failing tests**
```python
# cobrir:
# 1. finalize = sheet_saved and sharepoint_published
# 2. retry = status in aguardando/em andamento and not sheet_complete
# 3. reconcile_item_state usa SharePoint para finalização e consolidado local para retry
# 4. batch runner publica incrementalmente por cooperativa
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/performer/test_reconciliation.py tests/performer/test_batch_runner.py -v`
Expected: FAIL because services não existem
- [ ] **Step 3: Write minimal implementation**
```python
def should_finalize_item(sheet_saved: bool, sharepoint_published: bool) -> bool:
    return sheet_saved and sharepoint_published
def should_retry_item(status: str, sheet_complete: bool) -> bool:
    return status in {"aguardando", "em andamento"} and not sheet_complete
def reconcile_item_state(item_status: str, sheet_complete: bool, local_report_available: bool, sharepoint_published: bool):
    finalized = should_finalize_item(sheet_complete, sharepoint_published)
    should_retry = should_retry_item(item_status, sheet_complete) and local_report_available
    return SimpleNamespace(finalized=finalized, should_retry=should_retry)
class PerformerBatchRunner:
    def publish_one(self, report, workbook_path: Path, destination: str):
        sharepoint_published = self.sharepoint_client.upload_incremental(workbook_path, destination)
        return PublishResult(sheet_saved=workbook_path.exists(), sharepoint_published=sharepoint_published)
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/performer/test_reconciliation.py tests/performer/test_batch_runner.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/performer/reconciliation.py src/rsac_relatorios_risco/performer/batch_runner.py tests/performer/test_reconciliation.py tests/performer/test_batch_runner.py
git commit -m "feat: add performer reconciliation and batch runner"
```

### Task 8: Implementar integrações de saída e serviços operacionais

**Files:**
- Create: `src/rsac_relatorios_risco/integrations/sharepoint_client.py`
- Create: `src/rsac_relatorios_risco/integrations/mail_client.py`
- Create: `src/rsac_relatorios_risco/services/email_service.py`
- Create: `src/rsac_relatorios_risco/services/cleanup_service.py`
- Test: `tests/integrations/test_sharepoint_client.py`
- Test: `tests/services/test_email_service.py`
- Test: `tests/services/test_cleanup_service.py`

- [ ] **Step 1: Write the failing tests**
```python
# cobrir:
# 1. subject/body de e-mail com concluídos, pendentes e erros
# 2. destino incremental do SharePoint
# 3. build_mail_message
# 4. limpeza de arquivos > 15 dias
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/integrations/test_sharepoint_client.py tests/services/test_email_service.py tests/services/test_cleanup_service.py -v`
Expected: FAIL because services não existem
- [ ] **Step 3: Write minimal implementation**
```python
def build_summary_subject(status: str, competencia: str) -> str:
    return f"RSAC {competencia} - {status}"
def build_summary_body(competencia: str, concluidos: list[str], pendentes: list[str], erros: list[str]) -> str:
    return f"Competência: {competencia}\nConcluídos: {concluidos}\nPendentes: {pendentes}\nErros: {erros}"
def delete_files_older_than(base_dir: Path, days: int) -> list[str]:
    ...
def should_publish_incrementally(workbook_exists: bool) -> bool:
    return workbook_exists
def build_incremental_destination(base_path: str, workbook_name: str) -> str:
    return f"{base_path.rstrip('/')}/{workbook_name}"
def build_mail_message(to: str, subject: str, body: str) -> dict:
    return {"to": to, "subject": subject, "body": body}
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/integrations/test_sharepoint_client.py tests/services/test_email_service.py tests/services/test_cleanup_service.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add src/rsac_relatorios_risco/integrations/sharepoint_client.py src/rsac_relatorios_risco/integrations/mail_client.py src/rsac_relatorios_risco/services/email_service.py src/rsac_relatorios_risco/services/cleanup_service.py tests/integrations/test_sharepoint_client.py tests/services/test_email_service.py tests/services/test_cleanup_service.py
git commit -m "feat: add output integrations and operational services"
```

### Task 9: Registrar a entrada do worker e o stub da fase web

**Files:**
- Create: `agent_jarbis.py`
- Create: `src/rsac_relatorios_risco/web/rsa_portal_stub.py`
- Test: `tests/test_agent_jarbis_smoke.py`

- [ ] **Step 1: Write the failing tests**
```python
# validar:
# 1. RsaPortalNotReadyError existe
# 2. REGISTERED_TOPICS contém DISPATCHER_RSAC e PERFORMER_RSAC
# 3. import de agent_jarbis funciona
```
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_agent_jarbis_smoke.py -v`
Expected: FAIL because files não existem
- [ ] **Step 3: Write minimal implementation**
```python
class RsaPortalNotReadyError(RuntimeError):
    pass
REGISTERED_TOPICS = ["DISPATCHER_RSAC", "PERFORMER_RSAC"]
def main():
    return REGISTERED_TOPICS
```
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_agent_jarbis_smoke.py -v`
Expected: PASS
- [ ] **Step 5: Commit**
```bash
git add agent_jarbis.py src/rsac_relatorios_risco/web/rsa_portal_stub.py tests/test_agent_jarbis_smoke.py
git commit -m "feat: add worker entrypoint and blocked web stub"
```

### Task 10: Rodar a verificação da fase 1

**Files:**
- Verify only: current chunk files

- [ ] **Step 1: Run the full test slice for this chunk**
Run: `pytest tests/services tests/performer tests/integrations tests/test_agent_jarbis_smoke.py -v`
Expected: PASS
- [ ] **Step 2: Run smoke import of the package and worker**
Run: `python -c "import agent_jarbis; import rsac_relatorios_risco; print('ok')"`
Expected: `ok`
- [ ] **Step 3: Verify blocked web phase remains isolated**
Run: `rg -n "RsaPortalNotReadyError|seletores pendentes" src/rsac_relatorios_risco/web/rsa_portal_stub.py`
Expected: matching line(s)
- [ ] **Step 4: Commit the verification slice**
```bash
git add agent_jarbis.py src/rsac_relatorios_risco/performer/reconciliation.py src/rsac_relatorios_risco/performer/batch_runner.py src/rsac_relatorios_risco/services/report_service.py src/rsac_relatorios_risco/services/consolidado_service.py src/rsac_relatorios_risco/services/email_service.py src/rsac_relatorios_risco/services/cleanup_service.py src/rsac_relatorios_risco/integrations/sharepoint_client.py src/rsac_relatorios_risco/integrations/mail_client.py src/rsac_relatorios_risco/web/rsa_portal_stub.py tests/services/test_report_service.py tests/services/test_consolidado_service.py tests/services/test_email_service.py tests/services/test_cleanup_service.py tests/performer/test_reconciliation.py tests/performer/test_batch_runner.py tests/integrations/test_sharepoint_client.py tests/test_agent_jarbis_smoke.py
git commit -m "chore: verify rsac phase one slice"
```
- [ ] **Step 5: Stop before phase 2**
Expected: `Dispatcher`, Excel/consolidado, reconciliação, SharePoint incremental, e-mail e limpeza prontos; automação web RSA ainda aguardando seletores
