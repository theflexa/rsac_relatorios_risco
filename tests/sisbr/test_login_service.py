from rsac_relatorios_risco.sisbr.login_service import SisbrLoginService


class FakeBackend:
    def __init__(self, result=True) -> None:
        self.result = result
        self.calls = 0

    def login(self):
        self.calls += 1
        return self.result


def test_login_service_delegates_to_backend():
    backend = FakeBackend(result=True)
    service = SisbrLoginService(backend=backend)

    result = service.ensure_logged_in()

    assert result is True
    assert backend.calls == 1
