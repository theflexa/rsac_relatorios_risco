from __future__ import annotations

import json
import time
import urllib.parse
import uuid
from pathlib import Path

import pyautogui
import pyperclip

from rsac_relatorios_risco.windows.save_as_flow import WindowsSaveAsFlow


class BrowserWindowFlowError(RuntimeError):
    pass


class BrowserWindowPortalFlow:
    def __init__(
        self,
        browser_window,
        *,
        save_as_flow=None,
        sleep=time.sleep,
        screenshot_func=None,
        mouse_move=None,
        mouse_click=None,
    ) -> None:
        if browser_window is None:
            raise BrowserWindowFlowError("Janela do navegador RSA nao foi fornecida.")
        self.browser_window = browser_window
        self.save_as_flow = save_as_flow or WindowsSaveAsFlow()
        self.sleep = sleep
        self.screenshot_func = screenshot_func or pyautogui.screenshot
        self.mouse_move = mouse_move or pyautogui.moveTo
        self.mouse_click = mouse_click or pyautogui.click
        self._current_competencia: str | None = None
        self._current_cooperativa: str | None = None

    def executar_fluxo_exportacao(
        self,
        *,
        competencia: str,
        cooperativa: str,
        download_dir: Path,
        relatorio: str = "RELATORIO_RISCO_COOPERATIVA",
        situacao: str = "Processado com sucesso",
        tipo: str = "XLSX",
    ) -> Path:
        del situacao, tipo
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        self._current_competencia = competencia
        self._current_cooperativa = cooperativa

        self._focus_portal_tab()
        self._ensure_form_page()
        self._fill_form(competencia=competencia, cooperativa=cooperativa)
        self._open_export_modal()
        status = self._generate_report(relatorio=relatorio)
        if "alerta" in self._normalize_text(status):
            return self._capture_alert_snapshot(download_dir, status=status)
        self._click_print(relatorio=relatorio, status=status)
        return self.save_as_flow.save_file(self._build_download_path(download_dir))

    def _focus_portal_tab(self) -> None:
        self.browser_window.set_focus()
        for _ in range(20):
            current_url = self._current_url()
            if current_url.startswith("portal.sisbr.coop.br/rsa/"):
                return
            pyautogui.hotkey("ctrl", "tab")
            self.sleep(0.6)
        raise BrowserWindowFlowError(
            "Nao foi possivel focar a aba do portal RSA no Chrome.",
        )

    def _current_url(self) -> str:
        edits = [element for element in self.browser_window.descendants() if element.friendly_class_name() == "Edit"]
        if not edits:
            return ""
        try:
            return (edits[0].window_text() or "").strip()
        except Exception:
            return ""

    def _ensure_form_page(self) -> None:
        current_path = self._run_script("return location.pathname;", timeout_seconds=10)
        if "/rsa/risco" in current_path:
            return
        self._click_dom_target(
            r"""
const xp = (expr) => document.evaluate(expr, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
return xp("//div[contains(@class,'ss-toolbar-item')][.//span[contains(normalize-space(),'Relat')]]");
""",
            timeout_seconds=12,
        )
        self._click_dom_target(
            r"""
const xp = (expr) => document.evaluate(expr, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
const wait = async (fn, ms=12000, label='wait') => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('timeout:' + label);
};
return await wait(
  () => xp("//div[contains(@class, 'ss-toolbar-menu')]//a[contains(normalize-space(),'Riscos Social') and contains(normalize-space(),'Clim')]"),
  12000,
  'menu item'
);
""",
            timeout_seconds=15,
        )
        self._run_script(
            r"""
const xp = (expr) => document.evaluate(expr, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
const wait = async (fn, ms=15000, label='wait') => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('timeout:' + label);
};
await wait(
  () => xp("//div[contains(@class, 'cdk-overlay-container')]//h6[contains(normalize-space(),'Riscos Social') and contains(normalize-space(),'Clim')]"),
  15000,
  'form page'
);
return location.pathname;
""",
            timeout_seconds=20,
        )

    def _fill_form(self, *, competencia: str, cooperativa: str) -> None:
        self._click_dom_target(
            r"""
const select = document.getElementById('tipo-relatorio');
return select && (select.querySelector('.ng-select-container') || select);
""",
            timeout_seconds=12,
        )
        self._click_dom_target(
            f"""
return Array.from(document.querySelectorAll('.ng-dropdown-panel .ng-option, [role=option]'))
  .find(el => (el.textContent || '').includes({json.dumps("Relatório por Cooperativa")}));
""",
            timeout_seconds=12,
        )
        self.sleep(0.6)
        self._click_dom_target(
            r"""
const select = document.getElementById('combo-singular');
return select && (select.querySelector('.ng-select-container') || select);
""",
            timeout_seconds=12,
        )
        self._click_dom_target(
            f"""
return Array.from(document.querySelectorAll('.ng-dropdown-panel .ng-option, [role=option]'))
  .find(el => (el.textContent || '').includes({json.dumps(cooperativa + " -")}));
""",
            timeout_seconds=12,
        )
        self.sleep(0.6)
        self._click_dom_target(
            r"""
return document.getElementById('mes-ano');
""",
            timeout_seconds=12,
        )
        body = f"""
const setInputValue = (id, value) => {{
  const el = document.getElementById(id);
  if (!el) throw new Error('missing input ' + id);
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(el, value);
  el.dispatchEvent(new InputEvent('input', {{ bubbles: true, data: value, inputType: 'insertText' }}));
  el.dispatchEvent(new Event('change', {{ bubbles: true }}));
  el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
  return el.value;
}};
return setInputValue('mes-ano', {competencia!r});
"""
        payload = self._run_script(body, timeout_seconds=30)
        if payload != competencia:
            raise BrowserWindowFlowError(
                f"Competencia preenchida incorretamente no portal RSA: {payload!r}",
            )

    def _open_export_modal(self) -> None:
        self._click_dom_target(
            r"""
const xp = (expr) => document.evaluate(expr, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
return xp("//button[@type='button' and @value='Exportar']")
  || Array.from(document.querySelectorAll('button')).find(button => (button.textContent || '').includes('Exportar'));
""",
            timeout_seconds=12,
        )
        self._run_script(
            r"""
const wait = async (fn, ms=12000, label='wait') => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('timeout:' + label);
};
await wait(
  () => Array.from(document.querySelectorAll('button')).find(button => (button.textContent || '').includes('Gerar')),
  12000,
  'export modal'
);
return 'modal-open';
""",
            timeout_seconds=15,
        )

    def _generate_report(self, *, relatorio: str) -> str:
        self._click_dom_target(
            r"""
const select = document.getElementById('formato-impressao');
return select && (select.querySelector('.ng-select-container') || select);
""",
            timeout_seconds=12,
        )
        self._click_dom_target(
            f"""
return Array.from(document.querySelectorAll('.ng-dropdown-panel .ng-option, [role=option]'))
  .find(el => (el.textContent || '').includes({json.dumps("XLSX")}));
""",
            timeout_seconds=12,
        )
        self.sleep(0.6)
        self._click_dom_target(
            f"""
return Array.from(document.querySelectorAll('button'))
  .find(button => (button.textContent || '').includes({json.dumps("Gerar")}));
""",
            timeout_seconds=12,
        )
        body = """
const wait = async (fn, ms=25000, label='wait') => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('timeout:' + label);
};
const row = await wait(
  () => Array.from(document.querySelectorAll('table tr')).find(tr => (tr.textContent || '').includes(__RELATORIO__)),
  30000,
  'relatorios disponiveis',
);
const statusCell = row.querySelector('td');
return (statusCell && statusCell.textContent || '').trim() || 'Status desconhecido';
"""
        body = body.replace("__RELATORIO__", json.dumps(relatorio))
        return self._run_script(body, timeout_seconds=45)

    def _click_print(self, *, relatorio: str, status: str | None = None) -> None:
        self._click_dom_target(
            f"""
const rows = Array.from(document.querySelectorAll('table tr'));
const row = rows.find(tr => {{
  const text = tr.textContent || '';
  return text.includes({relatorio!r}) && ({status!r} ? text.includes({status!r}) : true);
}});
if (!row) throw new Error('report row missing');
return Array.from(row.querySelectorAll('[title], [aria-label], a, button, i, mat-icon, span'))
  .find(el => {{
    const title = (el.getAttribute && (el.getAttribute('title') || el.getAttribute('aria-label') || '')) || '';
    return title.toLowerCase().includes('imprim');
  }});
""",
            timeout_seconds=15,
        )
        self.sleep(2.5)

    def _run_script(self, body: str, *, timeout_seconds: int) -> str:
        marker = f"RSAFLOW{uuid.uuid4().hex[:8]}"
        wrapped = (
            "(() => { "
            f"const done=(status,payload)=>{{document.title='{marker}|'+status+'|'+encodeURIComponent(String(payload));}}; "
            f"Promise.resolve((async()=>{{ {body} }})()).then(result=>done('OK',result)).catch(error=>done('ERR', error && error.message || String(error))); "
            "})()"
        )
        self.browser_window.set_focus()
        pyperclip.copy(wrapped)
        pyautogui.hotkey("ctrl", "l")
        self.sleep(0.3)
        pyautogui.write("javascript:")
        self.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        self.sleep(0.2)
        pyautogui.press("enter")

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            title = self.browser_window.window_text()
            if marker in title:
                return self._parse_script_result(title, marker)
            self.sleep(0.5)
        raise BrowserWindowFlowError(
            f"Script RSA nao retornou resultado em {timeout_seconds}s.",
        )

    @staticmethod
    def _parse_script_result(window_title: str, marker: str) -> str:
        raw_title = window_title.split(" - Google Chrome", 1)[0]
        parts = raw_title.split("|", 2)
        if len(parts) < 3 or parts[0] != marker:
            raise BrowserWindowFlowError(f"Resultado inesperado do script RSA: {window_title}")
        status, payload = parts[1], urllib.parse.unquote(parts[2])
        if status == "ERR":
            raise BrowserWindowFlowError(payload)
        return payload

    def _capture_alert_snapshot(self, download_dir: Path, *, status: str) -> Path:
        destination = self._build_alert_path(download_dir, status=status)
        self.browser_window.set_focus()
        self.sleep(1.0)
        self.screenshot_func(str(destination))
        return destination

    def _click_dom_target(self, locator_script: str, *, timeout_seconds: int) -> None:
        target = self._locate_dom_target(locator_script, timeout_seconds=timeout_seconds)
        self.browser_window.set_focus()
        self.mouse_click(x=target["x"], y=target["y"])
        self.sleep(0.5)

    def _locate_dom_target(self, locator_script: str, *, timeout_seconds: int) -> dict[str, int]:
        body = """
const wait = async (fn, ms=12000, label='wait') => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('timeout:' + label);
};
const describe = (el) => {
  if (!el) throw new Error('target missing');
  el.scrollIntoView({ block: 'center', inline: 'center' });
  const rect = el.getBoundingClientRect();
  const viewport = window.visualViewport || { offsetLeft: 0, offsetTop: 0 };
  const chromeTop = window.outerHeight - window.innerHeight;
  return JSON.stringify({
    x: Math.round(window.screenX + viewport.offsetLeft + rect.left + (rect.width / 2)),
    y: Math.round(window.screenY + chromeTop + viewport.offsetTop + rect.top + (rect.height / 2))
  });
};
const target = await (async () => { __LOCATOR__ })();
return describe(target);
"""
        payload = self._run_script(body.replace("__LOCATOR__", locator_script), timeout_seconds=timeout_seconds)
        coords = json.loads(payload)
        return {"x": int(coords["x"]), "y": int(coords["y"])}

    def _build_alert_path(self, download_dir: Path, *, status: str) -> Path:
        del status
        cooperativa = self._current_cooperativa or "coop"
        competencia = (self._current_competencia or "000000").replace("/", "")
        return Path(download_dir) / f"alerta_{cooperativa}_{competencia}.png"

    def _build_download_path(self, download_dir: Path) -> Path:
        cooperativa = self._current_cooperativa or "coop"
        competencia = (self._current_competencia or "000000").replace("/", "")
        return Path(download_dir) / f"relatorio_{cooperativa}_{competencia}.xlsx"

    @staticmethod
    def _normalize_text(value: str) -> str:
        return (value or "").casefold()
