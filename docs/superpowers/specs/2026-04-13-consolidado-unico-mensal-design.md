# Design: Consolidado unico mensal + insumos por cooperativa

## Contexto

Hoje a automacao gera um arquivo consolidado por cooperativa (ex: `RSAC_3042_042026.xlsx`).
O correto e ter um unico consolidado por mes (`RSAC_042026.xlsx`) que acumula todas as cooperativas,
e os insumos (relatorios exportados do portal) ficam em subpastas por cooperativa.

## Estrutura de pastas

### Local (temp)

```
temp/downloads/04-2026/3042/relatorio_3042_042026.xlsx   <- insumo
temp/downloads/04-2026/3056/relatorio_3056_042026.xlsx   <- insumo
temp/consolidado/RSAC_042026.xlsx                        <- consolidado unico
```

### SharePoint

```
{base}/2026 - Acoes RSAC/04-2026/RSAC_042026.xlsx                <- consolidado (atualizado a cada coop)
{base}/2026 - Acoes RSAC/04-2026/3042/relatorio_3042_042026.xlsx <- insumo
{base}/2026 - Acoes RSAC/04-2026/3056/relatorio_3056_042026.xlsx <- insumo
```

## Fluxo por cooperativa

1. Exportar relatorio do portal -> salvar em `temp/downloads/{MM-YYYY}/{coop}/`
2. Ler relatorio (insumo)
3. Upload do **insumo** para SharePoint em `{base}/.../04-2026/{coop}/`
4. Preencher aba da cooperativa no **consolidado** unico (`RSAC_042026.xlsx`)
5. Upload do **consolidado** atualizado para SharePoint em `{base}/.../04-2026/`

## Mudancas no codigo

### `consolidado_resolver.py`
- `file_name` passa a nao conter codigo da cooperativa
- Formato: `RSAC_{MMYYYY}.xlsx`

### `utils/sharepoint/client.py`
- Novo helper `build_rsac_month_folder_path` para path sem cooperativa (pasta do mes)
- `build_rsac_folder_path` continua existindo para path com cooperativa (insumos)

### `_build_download_path` (browser_window_flow.py e rsa_portal_flow.py)
- Download vai para subpasta da cooperativa: `{download_dir}/{MM-YYYY}/{coop}/`

### `task_performer.py`
- Dois uploads por cooperativa:
  1. Insumo (pasta da cooperativa)
  2. Consolidado atualizado (pasta do mes)

### `scripts/teste_manual_rsa.py`
- Mesmo ajuste de paths e dois uploads

## O que nao muda
- `report_service.py` — leitura do relatorio exportado
- `consolidado_service.py` — preenchimento da aba
- Template `Modelo_PlanilhaPrincipal.xlsx`
- Email
