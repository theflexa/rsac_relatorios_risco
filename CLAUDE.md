# RSAC - Relatorios de Risco

Automacao RPA que exporta relatorios de Riscos Social, Ambiental e Climatico (RSAC) do portal Sisbr 3.0, preenche uma planilha consolidada e publica no SharePoint.

## Visao geral do fluxo

```
Dispatcher (le Config.xlsx, cria 1 item por cooperativa no banco)
    |
    v
Performer (para cada cooperativa):
  1. Abre Sisbr Desktop (login automatico)
  2. Acessa modulo RSAC no Sisbr (abre Chrome com sessao autenticada)
  3. Navega no portal web RSA: preenche filtros, exporta relatorio XLSX
  4. Salva arquivo via dialogo "Salvar como" do Windows
  5. Le o relatorio exportado (insumo)
  6. Copia todo o conteudo do insumo para a aba da cooperativa no consolidado mensal
  7. Upload do insumo no SharePoint (pasta da cooperativa)
  8. Upload do consolidado atualizado no SharePoint (pasta do mes)
  9. Ao final de todos os itens, envia e-mail de resumo
```

## Por que nao usa Selenium

O portal RSA exige sessao autenticada no Sisbr com certificado digital. Selenium cria uma sandbox limpa sem cookies/sessao. A automacao usa `pyautogui` + `pywinauto` para interagir com o Chrome ja aberto pelo Sisbr, injetando JavaScript via barra de endereco para localizar elementos e obter coordenadas de tela.

## Estrutura de pastas

```
rsac_relatorios_risco/
  agent_jarbis.py              # Worker Jarbis (Camunda external tasks)
  config/
    settings.py                # Variaveis do .env
    processes_to_kill.json     # Processos para encerrar (cleanup)
  tasks/
    task_dispatcher.py         # Handler: le Config.xlsx, insere itens no banco
    task_performer.py          # Handler: processa 1 cooperativa (Sisbr -> RSA -> download -> consolidado -> SharePoint)
  src/rsac_relatorios_risco/
    config/                    # Leitura do Config.xlsx (Settings + Items)
    dispatcher/                # Servico de dispatch
    performer/                 # Orquestradores, batch runner, item runner
    services/
      report_service.py        # Le o relatorio exportado do portal (insumo)
      consolidado_service.py   # Preenche aba da cooperativa no consolidado
      email_service.py         # Monta e envia e-mail de resultado (usa utils/mail)
      cleanup_service.py       # Limpa arquivos temporarios antigos
    web/
      browser_window_flow.py   # Fluxo via pyautogui (JS injetado na barra de endereco)
      rsa_portal_flow.py       # Fluxo via Selenium (alternativo, requer driver)
      selectors_config.py      # Seletores do portal RSA
    windows/
      save_as_flow.py          # Dialogo "Salvar como" via pywinauto
    sisbr/                     # Login e acesso a modulos do Sisbr Desktop
    manual/
      rsa_smoke_runner.py      # Runner para teste manual (Sisbr -> RSA -> download)
  scripts/
    teste_manual_rsa.py        # Teste manual end-to-end (1-click)
    teste_email.py             # Teste isolado de envio de e-mail
    teste_sharepoint_upload.py # Teste isolado de upload SharePoint
  utils/                       # Pacotes REUTILIZAVEIS entre projetos
    mail/                      # Envio de e-mail via Graph API + template HTML Sicoob
    sharepoint/                # Upload via Graph API
    database/                  # PostgREST/Supabase (projects, jobs, items)
    jarbis/                    # Cliente REST Camunda
    project_config.py          # Le constantes do .env (PROJECT_NAME, etc.)
    rpa_actions.py             # Acoes RPA estilo UiPath (click, type_into, wait, kill)
  Models/
    Config.xlsx                # Settings (destinatarios, subject) + Items (cooperativas)
    Modelo_PlanilhaPrincipal.xlsx  # Template do consolidado (136 abas, 1 por cooperativa)
  lib_sisbr_desktop/           # Lib vendored para interacao com Sisbr Desktop (OCR, pywinauto)
  rsac_dispatcher.bpmn         # BPMN do Dispatcher (publicar no Jarbis)
  rsac_performer.bpmn          # BPMN do Performer (publicar no Jarbis)
```

## Configuracao

### .env (credenciais e constantes)

Toda configuracao sensivel e constantes do projeto ficam no `.env`. Ver `.env.example` para referencia.

Variaveis importantes:
- `LOGIN_USER`, `LOGIN_PASSWORD` — credenciais Sisbr
- `SHAREPOINT_TENANT_ID`, `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET` — Graph API
- `SHAREPOINT_SITE_URL`, `SHAREPOINT_BIBLIOTECA`, `SHAREPOINT_FOLDER_PATH` — destino
- `EMAIL_TENANT_ID`, `EMAIL_CLIENT_ID`, `EMAIL_CLIENT_SECRET`, `FROM_EMAIL` — e-mail
- `PROJECT_NAME` — nome exibido no e-mail (ex: "RSAC - Exportacao Relatorio de Risco")
- `REPORT_FILENAME_PATTERN` — padrao do nome do insumo (ex: `RELATORIO_RISCO_{cooperativa}_{competencia}.xlsx`)
- `DATABASE_PROFILE` — `PRD` ou `HML`

### Config.xlsx (destinatarios e itens)

- Aba **Settings**: `MailDestinatarioResultado`, `MailDestinatarioCC`, `MailSubject`
- Aba **Items**: 1 linha por cooperativa com Reference, Tipo Relatorio, Cooperativa, PA, nomes, destinatarios, sharepoint path, nome arquivo, extensao

### Estrutura de pastas no SharePoint

```
{SHAREPOINT_FOLDER_PATH}/
  {ano} - Acoes RSAC/
    {MM-ano}/
      RSAC_{MMYYYY}.xlsx                              <- consolidado (atualizado a cada cooperativa)
      {cooperativa}/
        RELATORIO_RISCO_{cooperativa}_{MMYYYY}.xlsx   <- insumo (relatorio exportado)
```

## Consolidado mensal

- Um unico arquivo por mes: `RSAC_{MMYYYY}.xlsx`
- Copiado do template `Models/Modelo_PlanilhaPrincipal.xlsx` na primeira cooperativa
- Cada cooperativa preenche sua aba (ex: aba "3042") copiando todo o conteudo do insumo
- Upload incremental: a cada cooperativa concluida, o consolidado atualizado e enviado ao SharePoint
- Template tem 136 abas (4 por cooperativa: A{coop}, {coop}, Setor_S {coop}, For_{coop}) + 8 abas gerais

## Pacotes reutilizaveis (utils/)

Estes pacotes sao genericos e podem ser copiados para outros projetos RPA Sicoob:

### utils/mail/
- `client.py` — `send_mail()` via Microsoft Graph API `/sendMail`
- `graph_auth.py` — `get_access_token()` OAuth2 client credentials
- `template.py` — `build_status_email()` HTML com identidade visual Sicoob (logo, cores, badges)
- `sicoob_logo.b64` — logo Sicoob Nova Central em base64

Para usar em outro projeto:
```python
from utils.mail import send_mail, build_status_email

html = build_status_email(
    project_name="Nome do Projeto",
    intro="Segue abaixo o resultado do processamento.",
    items=[("item1", True), ("item2", False)],
    competencia="04/2026",
    col_label="Cooperativa",
)
send_mail(from_email="rpa@empresa.com.br", to="dest@empresa.com.br",
          subject="Resultado", body=html,
          tenant_id="...", client_id="...", client_secret="...")
```

### utils/sharepoint/
- `client.py` — `upload_file()`, `build_rsac_folder_path()`, `build_rsac_month_folder_path()`

### utils/database/
- `client.py` — `ensure_project()`, `insert_job()`, `insert_item()`, `update_item()`, etc.

### utils/jarbis/
- `api.py` — `start_process_instance()`, `format_camunda_variables()`

### utils/project_config.py
- `load_project_config()` — le PROJECT_NAME, PROJECT_STATUS, etc. do .env
- `build_report_filename()` — monta nome do insumo usando `REPORT_FILENAME_PATTERN` do .env

### utils/rpa_actions.py
- `click()`, `type_into()`, `select_item()`, `wait_element()` — acoes Selenium estilo UiPath
- `kill_process()`, `kill_all_processes()` — encerra processos (Chrome, Sisbr)

## Orquestracao Jarbis

O projeto usa o padrao Dispatcher/Performer do Jarbis (Camunda):

- **Dispatcher** (`tasks/task_dispatcher.py`): le Config.xlsx, cria 1 item no banco por cooperativa
- **Performer** (`tasks/task_performer.py`): recebe `item_id`, processa a cooperativa completa

Topics:
- `RSAC_RELATORIOS_RISCO_DISPATCHER`
- `RSAC_RELATORIOS_RISCO_PERFORMER`

Worker: `agent_jarbis.py` escuta ambos os topics.

BPMNs: `rsac_dispatcher.bpmn` e `rsac_performer.bpmn` — publicar no Jarbis via Camunda Modeler.

## Testes

```bash
# Rodar todos os testes (exceto smoke do Jarbis que requer a lib)
python -m pytest tests/ --ignore=tests/test_agent_jarbis_smoke.py -v

# Teste manual end-to-end (requer Sisbr + Chrome na sessao Windows)
python scripts/teste_manual_rsa.py
```

O teste manual (`scripts/teste_manual_rsa.py`) executa o fluxo completo: Sisbr -> portal RSA -> download -> consolidado -> SharePoint -> e-mail. Flags de controle no topo do arquivo: `SKIP_SISBR`, `SKIP_CONSOLIDADO`, `SKIP_SHAREPOINT`, `SKIP_EMAIL`.

## Regras de desenvolvimento

- Nunca gerar arquivos temporarios na raiz do projeto — tudo em `temp/`
- Preferir .env para configuracoes que mudam por ambiente
- Config.xlsx para dados que precisam ser alterados sem deploy (destinatarios, cooperativas)
- Pacotes em `utils/` devem ser genericos e reutilizaveis entre projetos
- O browser_window_flow.py usa pyautogui porque Selenium nao acessa sessao autenticada do Sisbr
