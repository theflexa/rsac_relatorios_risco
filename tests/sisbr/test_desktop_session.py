from rsac_relatorios_risco.sisbr.desktop_session import LibSisbrDesktopSession


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

    def ensure_logged_in(self):
        self.calls += 1
        return True


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
        max_retentativas=5,
    )

    result = session.ensure_rsa_open()

    assert result == "janela-rsa"
    assert bootstrap.calls == ["bootstrap"]
    assert open_backend.calls == [None]
    assert login_service.calls == 1
    assert accessor_backend.calls == [("janela-principal", "RSA", 5)]


def test_session_passes_custom_sisbr_executable():
    open_backend = FakeOpenBackend()
    session = LibSisbrDesktopSession(
        lib_path="C:/lib_sisbr_desktop",
        sisbr_exe="C:/Sisbr 2.0/Sisbr 2.0.exe",
        open_backend=open_backend,
        login_service=FakeLoginService(),
        accessor_backend=FakeAccessorBackend(),
        bootstrap_sys_path=lambda: None,
    )

    session.ensure_rsa_open()

    assert open_backend.calls == ["C:/Sisbr 2.0/Sisbr 2.0.exe"]
