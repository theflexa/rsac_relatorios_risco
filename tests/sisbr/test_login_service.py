import pytest

from rsac_relatorios_risco.sisbr.login_service import SisbrLoginService, SisbrLoginFailedError


class FakeBackend:
    def __init__(self, result=True) -> None:
        self.result = result
        self.calls = 0

    def login(self, win_principal=None):
        self.calls += 1
        return self.result


class FakeBackendFailThenSucceed:
    def __init__(self, fail_count: int = 2) -> None:
        self.fail_count = fail_count
        self.calls = 0

    def login(self, win_principal=None):
        self.calls += 1
        if self.calls <= self.fail_count:
            return False
        return True


def test_login_service_delegates_to_backend():
    backend = FakeBackend(result=True)
    service = SisbrLoginService(backend=backend)

    result = service.ensure_logged_in()

    assert result is True
    assert backend.calls == 1


def test_login_service_retries_on_failure():
    backend = FakeBackendFailThenSucceed(fail_count=2)
    service = SisbrLoginService(backend=backend, max_attempts=3)

    result = service.ensure_logged_in()

    assert result is True
    assert backend.calls == 3


def test_login_service_raises_after_max_attempts():
    backend = FakeBackend(result=False)
    service = SisbrLoginService(backend=backend, max_attempts=3)

    with pytest.raises(SisbrLoginFailedError, match="3 tentativas"):
        service.ensure_logged_in()

    assert backend.calls == 3
