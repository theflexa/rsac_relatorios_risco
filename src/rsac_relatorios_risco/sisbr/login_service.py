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
    def __init__(self, *, backend=None, max_attempts: int = 3) -> None:
        self.backend = backend or _MissingLoginBackend()
        self.max_attempts = max_attempts

    def ensure_logged_in(self, win_principal=None) -> bool:
        last_error = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                success = bool(self.backend.login(win_principal))
                if success:
                    return True
            except Exception as exc:
                last_error = exc
            if attempt < self.max_attempts:
                import time
                time.sleep(2)
        raise SisbrLoginFailedError(
            f"Falha no login do Sisbr apos {self.max_attempts} tentativas. "
            "Verifique LOGIN_USER e LOGIN_PASSWORD no .env antes de acessar o modulo."
            + (f" Ultimo erro: {last_error}" if last_error else ""),
        )
