from __future__ import annotations

import json
import time
import urllib.parse
import uuid
import unicodedata
from pathlib import Path

import pyautogui
import pyperclip

from rsac_relatorios_risco.windows.save_as_flow import WindowsSaveAsFlow


class BrowserWindowFlowError(RuntimeError):
    pass


class BrowserWindowPortalFlow:
    _ADDRESS_BAR_HINTS = (
        "address and search bar",
        "address bar",
        "barra de endereco e pesquisa",
        "barra de enderecos e pesquisa",
        "barra de endereco",
        "barra de enderecos",
        "search google or type a url",
        "search or enter web address",
        "pesquise no google ou digite um url",
        "pesquisar no google ou digitar um url",
        "digite um url",
        "omnibox",
    )
    _URL_HINTS = (
        "http://",
        "https://",
        "portal.sisbr.coop.br",
        "sisbr.coop.br",
        "/rsa/",
        "chrome://",
        "edge://",
        "about:",
    )

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
            if self._is_rsa_url(current_url):
                return
            pyautogui.hotkey("ctrl", "tab")
            self.sleep(0.6)
        raise BrowserWindowFlowError(
            "Nao foi possivel focar a aba do portal RSA no Chrome.",
        )

    def _current_url(self) -> str:
        address_bar = self._find_address_bar()
        if address_bar is None:
            return ""
        try:
            return (address_bar.window_text() or "").strip()
        except Exception:
            return ""

    def _ensure_form_page(self) -> None:
        current_path = self._run_script("return location.pathname;", timeout_seconds=10)
        self._dismiss_reports_overlay_if_present()
        form_state = self._run_script(
            r"""
const isVisible = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};
const heading = Array.from(document.querySelectorAll('h6, h5, h4, h3, h2, h1'))
  .find(el => /Riscos Social/i.test(el.textContent || '') && /Clim/i.test(el.textContent || ''));
const hasForm = Boolean(
  isVisible(heading)
  && isVisible(document.getElementById('tipo-relatorio'))
  && isVisible(document.getElementById('combo-singular'))
  && isVisible(document.getElementById('mes-ano'))
);
return hasForm ? 'form-ready' : 'not-form';
""",
            timeout_seconds=10,
        )
        if "/rsa/risco" in current_path and form_state == "form-ready":
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
        self._dismiss_reports_overlay_if_present()

    def _dismiss_reports_overlay_if_present(self) -> bool:
        overlay_state = self._run_script(
            r"""
const normalize = (value = '') => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const isVisible = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};
const heading = Array.from(document.querySelectorAll('h6, h5, h4, h3, h2, h1, [role=heading], strong'))
  .find(el => isVisible(el) && normalize(el.textContent || '').includes('relatorios disponiveis'));
return heading ? 'overlay-open' : 'overlay-closed';
""",
            timeout_seconds=10,
        )
        if overlay_state != "overlay-open":
            return False
        self._click_dom_target(
            r"""
const normalize = (value = '') => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const isVisible = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};
const heading = Array.from(document.querySelectorAll('h6, h5, h4, h3, h2, h1, [role=heading], strong'))
  .find(el => isVisible(el) && normalize(el.textContent || '').includes('relatorios disponiveis'));
if (!heading) return null;
const headingRect = heading.getBoundingClientRect();
const containers = [
  heading.closest('.cdk-overlay-pane'),
  heading.closest('.mat-dialog-container'),
  heading.closest('.modal-dialog'),
  heading.closest('.modal-content'),
  heading.closest('[role=dialog]'),
  heading.parentElement,
  heading.parentElement && heading.parentElement.parentElement,
  document.body,
].filter(Boolean);
for (const container of containers) {
  const candidates = Array.from(container.querySelectorAll('button, [role=button], a, [title], [aria-label], mat-icon, i, span'))
    .filter(el => isVisible(el));
  const labelled = candidates.find(el => {
    const attrs = `${el.getAttribute && (el.getAttribute('title') || '')} ${el.getAttribute && (el.getAttribute('aria-label') || '')} ${el.textContent || ''}`;
    const text = normalize(attrs);
    return text.includes('fechar') || text.includes('close');
  });
  if (labelled) return labelled.closest('button, [role=button], a') || labelled;
  const rightSide = candidates
    .map(el => ({ el, rect: el.getBoundingClientRect() }))
    .filter(({ rect }) => rect.top <= headingRect.bottom + 20 && rect.bottom >= headingRect.top - 10 && rect.left >= headingRect.left)
    .sort((left, right) => (right.rect.left + right.rect.width) - (left.rect.left + left.rect.width));
  if (rightSide.length) return rightSide[0].el;
}
return null;
""",
            timeout_seconds=12,
        )
        self._run_script(
            r"""
const normalize = (value = '') => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const isVisible = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};
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
  () => !Array.from(document.querySelectorAll('h6, h5, h4, h3, h2, h1, [role=heading], strong'))
    .some(el => isVisible(el) && normalize(el.textContent || '').includes('relatorios disponiveis')),
  12000,
  'overlay close'
);
return 'overlay-closed';
""",
            timeout_seconds=15,
        )
        return True

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
const wait = async (fn, ms=12000, label='wait') => {{
  const end = Date.now() + ms;
  while (Date.now() < end) {{
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }}
  throw new Error('timeout:' + label);
}};
return await wait(
  () => Array.from(document.querySelectorAll('.ng-dropdown-panel .ng-option, [role=option]'))
    .find(el => (el.textContent || '').includes({json.dumps("Relatório por Cooperativa")})),
  12000,
  'tipo relatorio option'
);
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
const wait = async (fn, ms=12000, label='wait') => {{
  const end = Date.now() + ms;
  while (Date.now() < end) {{
    const value = fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 250));
  }}
  throw new Error('timeout:' + label);
}};
return await wait(
  () => Array.from(document.querySelectorAll('.ng-dropdown-panel .ng-option, [role=option]'))
    .find(el => (el.textContent || '').includes({json.dumps(cooperativa + " -")})),
  12000,
  'singular option'
);
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
  'relatorios disponiveis'
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
            f"const __rsaflowMarker={marker!r}; "
            "const done=(status,payload)=>{ "
            "const base=location.pathname + location.search; "
            "history.replaceState(history.state, document.title, base + '#' + __rsaflowMarker + '|' + status + '|' + encodeURIComponent(String(payload)));"
            "}; "
            f"Promise.resolve((async()=>{{ {body} }})()).then(result=>done('OK',result)).catch(error=>done('ERR', error && error.message || String(error))); "
            "})()"
        )
        self._activate_address_bar()
        pyperclip.copy(wrapped)
        pyautogui.hotkey("ctrl", "a")
        self.sleep(0.2)
        pyautogui.write("javascript:")
        self.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        self.sleep(0.2)
        pyautogui.press("enter")

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            current_url = self._current_url()
            if marker in current_url:
                return self._parse_script_result(current_url, marker)
            self.sleep(0.5)
        raise BrowserWindowFlowError(
            f"Script RSA nao retornou resultado em {timeout_seconds}s.",
        )

    @staticmethod
    def _parse_script_result(current_url: str, marker: str) -> str:
        fragment = (current_url or "").rsplit("#", 1)[-1]
        parts = fragment.split("|", 2)
        if len(parts) < 3 or parts[0] != marker:
            raise BrowserWindowFlowError(f"Resultado inesperado do script RSA: {current_url}")
        status, payload = urllib.parse.unquote(parts[1]), urllib.parse.unquote(parts[2])
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

    def _activate_address_bar(self) -> None:
        self.browser_window.set_focus()
        address_bar = self._find_address_bar()
        if address_bar is not None:
            try:
                address_bar.click_input()
                self.sleep(0.2)
            except Exception:
                try:
                    address_bar.set_focus()
                    self.sleep(0.2)
                except Exception:
                    pass
        pyautogui.hotkey("ctrl", "l")
        self.sleep(0.3)
        if self._find_address_bar() is None:
            raise BrowserWindowFlowError(
                "Nao foi possivel localizar a barra de endereco do navegador para executar o script RSA.",
            )

    def _find_address_bar(self):
        candidates = self._edit_controls()
        scored = sorted(
            ((self._score_address_bar_candidate(control), control) for control in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        for score, control in scored:
            if score > 0:
                return control
        return None

    def _edit_controls(self) -> list:
        try:
            descendants = list(self.browser_window.descendants(control_type="Edit"))
            if descendants:
                return descendants
        except TypeError:
            descendants = []
        except Exception:
            descendants = []

        if descendants:
            return descendants

        try:
            return [
                element
                for element in self.browser_window.descendants()
                if self._normalize_text(self._safe_call(element, "friendly_class_name")) == "edit"
            ]
        except Exception:
            return []

    def _score_address_bar_candidate(self, control) -> int:
        text_candidates = [
            self._normalize_text(self._safe_call(control, "window_text")),
            self._normalize_text(getattr(getattr(control, "element_info", None), "name", "")),
            self._normalize_text(getattr(getattr(control, "element_info", None), "automation_id", "")),
        ]

        score = 0
        if any(hint in candidate for hint in self._ADDRESS_BAR_HINTS for candidate in text_candidates):
            score += 10
        value = next((candidate for candidate in text_candidates if candidate), "")
        if any(hint in value for hint in self._URL_HINTS):
            score += 8
        return score

    @staticmethod
    def _safe_call(control, method_name: str) -> str:
        try:
            method = getattr(control, method_name)
        except Exception:
            return ""
        try:
            return method() or ""
        except Exception:
            return ""

    @classmethod
    def _is_rsa_url(cls, value: str) -> bool:
        normalized = cls._normalize_text(value)
        return "portal.sisbr.coop.br/rsa" in normalized or "/rsa/" in normalized

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_only.casefold()
