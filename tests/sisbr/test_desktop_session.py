import pytest

from rsac_relatorios_risco.sisbr.desktop_session import (
    LibSisbrDesktopSession,
    RSAC_MODULE_NAME,
    SisbrInitializationError,
)
from rsac_relatorios_risco.sisbr.login_service import SisbrLoginFailedError


class FakeBootstrapper:
    def __init__(self) -> None:
        self.calls = []

    def __call__(self):
        self.calls.append("bootstrap")


class FakeOpenBackend:
    def __init__(self) -> None:
        self.calls = []

    def abrir_sisbr(self, caminho_exe=None):
        self.calls.append(caminho_exe)
        return "app", "janela-principal"


class FakeLoginService:
    def __init__(self) -> None:
        self.calls = 0

    def ensure_logged_in(self, win_principal=None):
        self.calls += 1
        return True


class FakeStatusBackend:
    def __init__(
        self,
        *,
        is_logado=False,
        is_updating=False,
        has_connectivity_error=False,
        has_io_error=False,
        has_restart_prompt=False,
        wait_until_ready_result=True,
    ) -> None:
        self.is_logado_value = is_logado
        self.is_updating_value = is_updating
        self.has_connectivity_error_value = has_connectivity_error
        self.has_io_error_value = has_io_error
        self.has_restart_prompt_value = has_restart_prompt
        self.wait_until_ready_result = wait_until_ready_result
        self.calls = []

    def is_logado(self, win_principal):
        self.calls.append(win_principal)
        return self.is_logado_value

    def is_updating(self, win_principal):
        return self.is_updating_value

    def has_connectivity_error(self, win_principal):
        return self.has_connectivity_error_value

    def has_io_error(self, win_principal):
        return self.has_io_error_value

    def has_restart_prompt(self, win_principal):
        return self.has_restart_prompt_value

    def click_restart_button(self, win_principal):
        return True

    def wait_until_ready(self, win_principal, timeout=120.0):
        return self.wait_until_ready_result


class FakeAccessorBackend:
    def __init__(self) -> None:
        self.calls = []

    def acessar_modulo(self, win_principal, nome_modulo, max_retentativas=3):
        self.calls.append((win_principal, nome_modulo, max_retentativas))
        return "janela-rsa"


def test_session_opens_logs_in_and_accesses_rsa():
    bootstrap = FakeBootstrapper()
    open_backend = FakeOpenBackend()
    login_service = FakeLoginService()
    accessor_backend = FakeAccessorBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=bootstrap,
        open_backend=open_backend,
        login_service=login_service,
        accessor_backend=accessor_backend,
        status_backend=FakeStatusBackend(is_logado=False),
        max_retentativas=5,
    )

    result = session.ensure_rsa_open()

    assert result == "janela-rsa"
    assert bootstrap.calls == ["bootstrap"]
    assert open_backend.calls == [None]
    assert login_service.calls == 1
    assert accessor_backend.calls == [("janela-principal", RSAC_MODULE_NAME, 5)]


def test_session_passes_custom_sisbr_executable():
    open_backend = FakeOpenBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        sisbr_exe="C:/Sisbr 2.0/Sisbr 2.0.exe",
        open_backend=open_backend,
        login_service=FakeLoginService(),
        accessor_backend=FakeAccessorBackend(),
        status_backend=FakeStatusBackend(is_logado=False),
        bootstrap_sys_path=lambda: None,
    )

    session.ensure_rsa_open()

    assert open_backend.calls == ["C:/Sisbr 2.0/Sisbr 2.0.exe"]


class FakeFailedLoginService:
    def __init__(self) -> None:
        self.calls = 0

    def ensure_logged_in(self, win_principal=None):
        self.calls += 1
        raise SisbrLoginFailedError("login falhou")


def test_session_stops_before_accessing_module_when_login_fails():
    open_backend = FakeOpenBackend()
    login_service = FakeFailedLoginService()
    accessor_backend = FakeAccessorBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=login_service,
        accessor_backend=accessor_backend,
        status_backend=FakeStatusBackend(is_logado=False),
    )

    with pytest.raises(SisbrLoginFailedError):
        session.ensure_rsa_open()

    assert open_backend.calls == [None]
    assert login_service.calls == 1
    assert accessor_backend.calls == []


def test_session_skips_login_when_sisbr_is_already_logged_in():
    open_backend = FakeOpenBackend()
    login_service = FakeLoginService()
    accessor_backend = FakeAccessorBackend()
    status_backend = FakeStatusBackend(is_logado=True)
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=login_service,
        accessor_backend=accessor_backend,
        status_backend=status_backend,
    )

    result = session.ensure_rsa_open()

    assert result == "janela-rsa"
    assert open_backend.calls == [None]
    assert status_backend.calls == ["janela-principal"]
    assert login_service.calls == 0
    assert accessor_backend.calls == [("janela-principal", RSAC_MODULE_NAME, 3)]


def test_session_raises_initialization_error_on_io_error_after_retries(monkeypatch):
    monkeypatch.setattr("rsac_relatorios_risco.sisbr.desktop_session.kill_process", lambda *a, **kw: True)
    open_backend = FakeOpenBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=FakeLoginService(),
        accessor_backend=FakeAccessorBackend(),
        status_backend=FakeStatusBackend(has_io_error=True),
        max_retentativas=3,
    )

    with pytest.raises(SisbrInitializationError, match="Tentativas realizadas: 3"):
        session.ensure_rsa_open()

    # Deve ter tentado abrir 3 vezes
    assert len(open_backend.calls) == 3


def test_session_clicks_restart_and_reopens_sisbr():
    open_backend = FakeOpenBackend()
    status_backend = FakeStatusBackend(has_restart_prompt=True, is_logado=False)
    login_service = FakeLoginService()
    accessor_backend = FakeAccessorBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=login_service,
        accessor_backend=accessor_backend,
        status_backend=status_backend,
    )

    result = session.ensure_rsa_open()

    assert result == "janela-rsa"
    # Sisbr opened twice: initial + after restart
    assert len(open_backend.calls) == 2


def test_session_raises_initialization_error_on_connectivity_error_after_retries(monkeypatch):
    monkeypatch.setattr("rsac_relatorios_risco.sisbr.desktop_session.kill_process", lambda *a, **kw: True)
    open_backend = FakeOpenBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=FakeLoginService(),
        accessor_backend=FakeAccessorBackend(),
        status_backend=FakeStatusBackend(has_connectivity_error=True),
        max_retentativas=3,
    )

    with pytest.raises(SisbrInitializationError, match="Tentativas realizadas: 3"):
        session.ensure_rsa_open()

    assert len(open_backend.calls) == 3


def test_session_retries_when_connectivity_fails_during_update(monkeypatch):
    monkeypatch.setattr("rsac_relatorios_risco.sisbr.desktop_session.kill_process", lambda *a, **kw: True)
    open_backend = FakeOpenBackend()
    status = FakeStatusBackend(
        is_updating=True,
        has_connectivity_error=False,
        wait_until_ready_result=False,
    )
    # Simula connectivity error aparecendo após wait_until_ready falhar
    original_wait = status.wait_until_ready

    def wait_then_set_error(win, timeout=120.0):
        result = original_wait(win, timeout)
        status.has_connectivity_error_value = True
        return result

    status.wait_until_ready = wait_then_set_error

    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        bootstrap_sys_path=lambda: None,
        open_backend=open_backend,
        login_service=FakeLoginService(),
        accessor_backend=FakeAccessorBackend(),
        status_backend=status,
        max_retentativas=3,
    )

    with pytest.raises(SisbrInitializationError, match="Tentativas realizadas: 3"):
        session.ensure_rsa_open()

    # Deve ter tentado abrir 3 vezes
    assert len(open_backend.calls) == 3
