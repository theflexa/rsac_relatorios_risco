from __future__ import annotations


class SisbrLoginDependencyNotConfiguredError(RuntimeError):
    pass


class SisbrLoginFailedError(RuntimeError):
    pass


class _MissingLoginBackend:
    def login(self, win_principal=None) -> bool:
        raise SisbrLoginDependencyNotConfiguredError(
            "Backend de login do Sisbr nao configurado. Injete a funcao login da lib_sisbr_desktop.",
        )


class SisbrLoginService:
    def __init__(self, *, backend=None) -> None:
        self.backend = backend or _MissingLoginBackend()

    def ensure_logged_in(self, win_principal=None) -> bool:
        success = bool(self.backend.login(win_principal))
        if not success:
            raise SisbrLoginFailedError(
                "Falha no login do Sisbr. Verifique LOGIN_USER e LOGIN_PASSWORD no .env antes de acessar o modulo.",
            )
        return True
