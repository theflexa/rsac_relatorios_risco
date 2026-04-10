"""
Template de e-mail HTML com identidade visual Sicoob.

Modulo reutilizavel — nao depende de nenhum codigo de projeto especifico.
Qualquer automacao pode importar e gerar o HTML padronizado.

Exemplo de uso::

    from utils.mail import build_status_email

    html = build_status_email(
        project_name="RSAC - Exportação Relatório de Risco",
        intro="Segue abaixo o resultado do processamento da automação.",
        items=[("3042", True), ("5555", False)],
        competencia="04/2026",
    )
"""
from __future__ import annotations

from pathlib import Path
import base64


def _load_logo_b64() -> str:
    """Carrega o logo Sicoob de um arquivo .b64 ao lado deste modulo."""
    b64_path = Path(__file__).parent / "sicoob_logo.b64"
    if b64_path.exists():
        return b64_path.read_text(encoding="utf-8").strip()
    return ""


_LOGO_B64_CACHE: str | None = None


def _get_logo_b64() -> str:
    global _LOGO_B64_CACHE
    if _LOGO_B64_CACHE is None:
        _LOGO_B64_CACHE = _load_logo_b64()
    return _LOGO_B64_CACHE


def _status_badge(is_success: bool) -> str:
    if is_success:
        return (
            '<span style="display:inline-block;background-color:#7DB61C;color:#fff;'
            'padding:3px 12px;border-radius:12px;font-size:13px;font-weight:600;">'
            "&#10003; Sucesso</span>"
        )
    return (
        '<span style="display:inline-block;background-color:#D32F2F;color:#fff;'
        'padding:3px 12px;border-radius:12px;font-size:13px;font-weight:600;">'
        "&#10007; Erro</span>"
    )


def build_status_email(
    *,
    project_name: str = "",
    intro: str = "",
    items: list[tuple[str, bool]] | None = None,
    competencia: str = "",
    col_label: str = "Item",
    extra_html_top: str = "",
    extra_html_bottom: str = "",
) -> str:
    """Gera HTML de e-mail padronizado Sicoob com tabela de status.

    Args:
        project_name: Nome da automacao (exibido ao lado do logo).
        intro: Mensagem introdutoria (ex: "Segue abaixo o resultado...").
        items: Lista de tuplas ``(referencia, sucesso)``.
        competencia: Competencia/periodo (ex: "04/2026"). Opcional.
        col_label: Rotulo da primeira coluna da tabela (default "Item").
        extra_html_top: HTML extra inserido acima da tabela.
        extra_html_bottom: HTML extra inserido abaixo da tabela.

    Returns:
        String HTML completa pronta para envio.
    """
    items = items or []
    logo_b64 = _get_logo_b64()

    # --- Header: logo + project name ---
    logo_img = ""
    if logo_b64:
        logo_img = (
            f'<img src="data:image/jpeg;base64,{logo_b64}" '
            f'alt="Sicoob" width="80" style="display:block;border-radius:4px;" />'
        )

    # --- Intro ---
    intro_html = ""
    if intro:
        intro_html = f'<p style="color:#333;font-size:14px;margin:0 0 16px;line-height:1.5;">{intro}</p>'

    # --- Competencia ---
    comp_html = ""
    if competencia:
        comp_html = (
            f'<p style="color:#555;font-size:14px;margin:0 0 4px;">'
            f'Compet&ecirc;ncia: <strong>{competencia}</strong></p>'
        )

    # --- Table rows ---
    total = len(items)
    rows = ""
    for i, (ref, success) in enumerate(items):
        bg = "#f9f9f9" if i % 2 else "#ffffff"
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="padding:10px 16px;border-bottom:1px solid #e0e0e0;">{ref}</td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #e0e0e0;text-align:center;">'
            f'{_status_badge(success)}</td></tr>\n'
        )

    count_html = ""
    if total:
        count_html = (
            f'<p style="color:#555;font-size:14px;margin:0 0 20px;">'
            f'Itens processados: <strong>{total}</strong></p>'
        )

    empty_row = (
        '<tr><td colspan="2" style="padding:16px;text-align:center;color:#999;">'
        'Nenhum item processado</td></tr>'
    )

    return f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Segoe UI,Roboto,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

<!-- HEADER -->
<tr><td style="background-color:#003641;padding:20px 32px;">
  <table cellpadding="0" cellspacing="0" border="0"><tr>
    <td style="vertical-align:middle;">{logo_img}</td>
    <td style="vertical-align:middle;padding-left:16px;">
      <span style="color:#ffffff;font-size:16px;font-weight:700;letter-spacing:0.3px;">{project_name or 'Automa&ccedil;&atilde;o'}</span>
    </td>
  </tr></table>
</td></tr>

<!-- TITLE BAR -->
<tr><td style="background:linear-gradient(90deg,#00AE9D,#7DB61C);padding:12px 32px;">
  <span style="color:#ffffff;font-size:15px;font-weight:600;">Resultado do Processamento</span>
</td></tr>

<!-- BODY -->
<tr><td style="padding:28px 32px;">
  {intro_html}
  {f'<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">' if intro else ''}
  {comp_html}
  {count_html}

  {f'<div style="margin-bottom:16px;">{extra_html_top}</div>' if extra_html_top else ''}

  <!-- TABLE -->
  <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e0e0e0;border-radius:6px;border-collapse:separate;overflow:hidden;">
  <tr style="background-color:#003641;">
    <th style="padding:12px 16px;color:#ffffff;font-size:14px;text-align:left;font-weight:600;">{col_label}</th>
    <th style="padding:12px 16px;color:#ffffff;font-size:14px;text-align:center;font-weight:600;width:140px;">Status</th>
  </tr>
  {rows if rows else empty_row}
  </table>

  {f'<div style="margin-top:16px;">{extra_html_bottom}</div>' if extra_html_bottom else ''}
</td></tr>

<!-- FOOTER -->
<tr><td style="background-color:#003641;padding:20px 32px;text-align:center;">
  <p style="color:#00AE9D;font-size:13px;margin:0 0 4px;font-weight:600;">SICOOB NOVA CENTRAL</p>
  <p style="color:rgba(255,255,255,0.6);font-size:11px;margin:0;">Tecnologia da Informa&ccedil;&atilde;o &bull; Automa&ccedil;&atilde;o de Processos</p>
</td></tr>

</table>
</td></tr></table>
</body>
</html>"""
