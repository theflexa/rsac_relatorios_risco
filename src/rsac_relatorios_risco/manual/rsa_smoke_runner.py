from __future__ import annotations

import os
import re
import socket
import subprocess
import time
import zipfile
from pathlib import Path

from rsac_relatorios_risco.sisbr.desktop_session import LibSisbrDesktopSession
from rsac_relatorios_risco.web.browser_window_flow import BrowserWindowPortalFlow
from rsac_relatorios_risco.web.rsa_portal_flow import RsaPortalFlow

try:
    from selenium.webdriver import Chrome, Edge  # type: ignore
    from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
    from selenium.webdriver.edge.options import Options as EdgeOptions  # type: ignore
    from selenium.webdriver.chrome.service import Service as ChromeService  # type: ignore
    from selenium.webdriver.edge.service import Service as EdgeService  # type: ignore
except ImportError:  # pragma: no cover
    Chrome = None
    Edge = None
    ChromeOptions = None
    EdgeOptions = None
    ChromeService = None
    EdgeService = None

import requests


class ManualRunnerDependencyError(RuntimeError):
    pass


class _FallbackLogger:
    def info(self, message: str) -> None:
        print(message)


class BrowserWindowSession:
    def __init__(
        self,
        *,
        browser: str = "chrome",
        desktop_factory=None,
    ) -> None:
        self.browser = browser.lower()
        self.desktop_factory = desktop_factory or self._default_desktop_factory

    def close_preexisting_tabs(self) -> None:
        process_name = _browser_process_name(self.browser)
        if process_name and _is_process_running(process_name):
            _kill_process(process_name)
            time.sleep(2)

    def attach(self, browser_window=None):
        if browser_window is not None:
            return browser_window
        return self._find_rsac_window()

    def _find_rsac_window(self):
        desktop = self.desktop_factory(backend="uia")
        title_pattern = _browser_title_pattern(self.browser)
        window = desktop.window(title_re=title_pattern)
        try:
            window.wait("exists ready visible", timeout=20)
        except Exception as exc:  # pragma: no cover
            raise ManualRunnerDependencyError(
                "Janela do portal RSAC nao foi encontrada no navegador apos a abertura pelo Sisbr.",
            ) from exc
        return window

    @staticmethod
    def _default_desktop_factory(*, backend: str):
        from pywinauto import Desktop  # type: ignore

        return Desktop(backend=backend)


class DebugBrowserSession:
    def __init__(
        self,
        *,
        browser: str = "chrome",
        debug_port: int = 9222,
        restart_existing_browser: bool = True,
        driver_factory=None,
        options_factory=None,
    ) -> None:
        self.browser = browser.lower()
        self.debug_port = debug_port
        self.restart_existing_browser = restart_existing_browser
        self.driver_factory = driver_factory or self._default_driver_factory
        self.options_factory = options_factory or self._default_options_factory

    def close_preexisting_tabs(self) -> None:
        process_name = _browser_process_name(self.browser)
        if process_name and _is_process_running(process_name):
            _kill_process(process_name)
            time.sleep(2)

    def prepare_for_external_navigation(self) -> None:
        self._ensure_debug_browser()

    def attach(self, browser_window=None):
        del browser_window
        self._ensure_debug_browser()
        options = self.options_factory(self.browser)
        options.debugger_address = f"127.0.0.1:{self.debug_port}"
        return self.driver_factory(self.browser, options)

    def _ensure_debug_browser(self) -> None:
        if _is_debug_port_open(self.debug_port):
            return
        if self.browser != "chrome":
            raise ManualRunnerDependencyError(
                f"Porta de depuracao {self.debug_port} indisponivel para o navegador '{self.browser}'.",
            )

        chrome_path = _find_chrome_binary()
        if chrome_path is None:
            raise ManualRunnerDependencyError(
                "Chrome nao encontrado para iniciar a sessao com porta de depuracao.",
            )

        launch_args = [
            str(chrome_path),
            f"--remote-debugging-port={self.debug_port}",
            "about:blank",
        ]

        self._launch_chrome(launch_args)
        if self._wait_for_debug_port():
            return

        if self.restart_existing_browser and _is_process_running("chrome.exe"):
            _kill_process("chrome.exe")
            time.sleep(2)
            self._launch_chrome(launch_args)
            if self._wait_for_debug_port():
                return

        raise ManualRunnerDependencyError(
            f"Chrome abriu sem expor a porta de depuracao {self.debug_port}. "
            "Feche instancias normais do Chrome e tente novamente.",
        )

    @staticmethod
    def _launch_chrome(launch_args: list[str]) -> None:
        subprocess.Popen(
            launch_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _wait_for_debug_port(self) -> bool:
        deadline = time.time() + 20
        while time.time() < deadline:
            if _is_debug_port_open(self.debug_port):
                return True
            time.sleep(0.5)
        return False

    @staticmethod
    def _default_options_factory(browser: str):
        if browser == "chrome":
            if ChromeOptions is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Chrome.")
            return ChromeOptions()
        if browser == "edge":
            if EdgeOptions is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Edge.")
            return EdgeOptions()
        raise ValueError(f"Navegador nao suportado: {browser}")

    @staticmethod
    def _default_driver_factory(browser: str, options):
        if browser == "chrome":
            if Chrome is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Chrome.")
            service = _build_local_service(
                env_var="CHROMEDRIVER_PATH",
                search_root=Path.home() / ".wdm" / "drivers" / "chromedriver",
                service_type=ChromeService,
            )
            if service is not None:
                return Chrome(options=options, service=service)
            return Chrome(options=options)
        if browser == "edge":
            if Edge is None:
                raise ManualRunnerDependencyError("selenium nao esta instalado para anexar ao Edge.")
            service = _build_local_service(
                env_var="EDGEDRIVER_PATH",
                search_root=Path.home() / ".wdm" / "drivers" / "edgedriver",
                service_type=EdgeService,
            )
            if service is not None:
                return Edge(options=options, service=service)
            return Edge(options=options)
        raise ValueError(f"Navegador nao suportado: {browser}")


class ManualRsaSmokeRunner:
    def __init__(
        self,
        *,
        browser_session,
        logger=None,
        sisbr_session=None,
        rsa_flow_factory=None,
    ) -> None:
        self.browser_session = browser_session
        self.logger = logger or _FallbackLogger()
        self.sisbr_session = sisbr_session
        self.rsa_flow_factory = rsa_flow_factory or (
            lambda browser_window: BrowserWindowPortalFlow(browser_window=browser_window)
        )

    def run(
        self,
        *,
        competencia: str,
        cooperativa: str,
        download_dir: Path,
        skip_sisbr: bool = False,
    ) -> Path:
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        if not skip_sisbr and self.sisbr_session is not None:
            if hasattr(self.browser_session, "close_preexisting_tabs"):
                self.logger.info("Fechando abas preexistentes do navegador")
                self.browser_session.close_preexisting_tabs()
            if hasattr(self.browser_session, "prepare_for_external_navigation"):
                self.logger.info("Preparando navegador para receber o portal do Sisbr")
                self.browser_session.prepare_for_external_navigation()
            self.logger.info("Abrindo Sisbr, garantindo login e acessando modulo RSA")
            browser_window = self.sisbr_session.ensure_rsa_open()
        else:
            browser_window = None

        self.logger.info("Conectando a janela do navegador aberta pelo Sisbr")
        attached_window = self.browser_session.attach(browser_window=browser_window)
        self.logger.info("Executando jornada RSA completa")
        flow = self.rsa_flow_factory(attached_window)
        output_path = flow.executar_fluxo_exportacao(
            competencia=competencia,
            cooperativa=cooperativa,
            download_dir=download_dir,
        )
        self.logger.info(f"Arquivo gerado em {output_path}")
        return output_path


def default_lib_sisbr_path() -> Path:
    return Path(
        os.getenv(
            "LIB_SISBR_DESKTOP_PATH",
            str(Path(__file__).resolve().parent.parent.parent.parent / "lib_sisbr_desktop"),
        )
    )


def _build_local_service(*, env_var: str, search_root: Path, service_type):
    if service_type is None:
        return None

    required_major = _get_browser_major_version(env_var)

    explicit_path = os.getenv(env_var)
    if explicit_path and Path(explicit_path).exists():
        explicit_driver = Path(explicit_path)
        if _is_matching_driver(explicit_driver, required_major):
            return service_type(executable_path=str(explicit_driver))

    if not search_root.exists():
        return None

    candidates = sorted(
        search_root.rglob("*driver.exe"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        if _is_matching_driver(candidate, required_major):
            return service_type(executable_path=str(candidate))

    downloaded_driver = _download_matching_driver(env_var, search_root)
    if downloaded_driver is not None:
        return service_type(executable_path=str(downloaded_driver))

    return None


def _is_debug_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _find_chrome_binary() -> Path | None:
    candidates = [
        os.getenv("CHROME_BINARY"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


def _browser_process_name(browser: str) -> str | None:
    process_names = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
    }
    return process_names.get((browser or "").lower())


def _browser_title_pattern(browser: str) -> str:
    suffix_map = {
        "chrome": "Google Chrome",
        "edge": "Microsoft Edge",
    }
    suffix = suffix_map.get((browser or "").lower())
    if suffix:
        return rf".*RSAC.*- {re.escape(suffix)}$"
    return r".*RSAC.*"


def _is_process_running(image_name: str) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {image_name}", "/NH"],
        capture_output=True,
        text=True,
        encoding="cp850",
        errors="ignore",
        check=False,
    )
    return image_name.lower() in (result.stdout or "").lower()


def _kill_process(image_name: str) -> None:
    subprocess.run(
        ["taskkill", "/F", "/IM", image_name],
        capture_output=True,
        text=True,
        encoding="cp850",
        errors="ignore",
        check=False,
    )


def _get_browser_major_version(env_var: str) -> int | None:
    browser_version = _get_browser_version(env_var)
    if browser_version is None:
        return None
    match = re.match(r"(\d+)\.", browser_version)
    if not match:
        return None
    return int(match.group(1))


def _get_browser_version(env_var: str) -> str | None:
    browser_binary = _find_browser_binary_for_driver_env(env_var)
    if browser_binary is None:
        return None
    try:
        info = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Item '{browser_binary}').VersionInfo.FileVersion",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    return info or None


def _find_browser_binary_for_driver_env(env_var: str) -> Path | None:
    if env_var == "CHROMEDRIVER_PATH":
        return _find_chrome_binary()
    return None


def _is_matching_driver(driver_path: Path, required_major: int | None) -> bool:
    if required_major is None:
        return True
    driver_major = _get_driver_major_version(driver_path)
    if driver_major is None:
        return False
    return driver_major == required_major


def _get_driver_major_version(driver_path: Path) -> int | None:
    try:
        output = subprocess.check_output(
            [str(driver_path), "--version"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    match = re.search(r"(\d+)\.", output)
    if not match:
        return None
    return int(match.group(1))


def _download_matching_driver(env_var: str, search_root: Path) -> Path | None:
    if env_var != "CHROMEDRIVER_PATH":
        return None

    browser_version = _get_browser_version(env_var)
    if not browser_version:
        return None

    driver_dir = search_root / "win64" / browser_version / "chromedriver-win64"
    driver_path = driver_dir / "chromedriver.exe"
    if driver_path.exists():
        return driver_path

    driver_dir.mkdir(parents=True, exist_ok=True)
    zip_path = driver_dir.parent / "chromedriver-win64.zip"
    download_url = (
        f"https://storage.googleapis.com/chrome-for-testing-public/"
        f"{browser_version}/win64/chromedriver-win64.zip"
    )
    try:
        _download_file(download_url, zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(driver_dir.parent)
    except Exception:
        return None
    return driver_path if driver_path.exists() else None


def _download_file(url: str, destination: Path) -> None:
    try:
        response = requests.get(url, timeout=90, stream=True)
        response.raise_for_status()
    except requests.exceptions.SSLError:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, timeout=90, stream=True, verify=False)
        response.raise_for_status()

    with destination.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                file.write(chunk)
