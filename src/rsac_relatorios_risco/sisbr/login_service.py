from __future__ import annotations


class SisbrLoginDependencyNotConfiguredError(RuntimeError):
    pass


class _MissingLoginBackend:
    def login(self) -> bool:
        raise SisbrLoginDependencyNotConfiguredError(
            "Backend de login do Sisbr nao configurado. Injete a funcao login da lib_sisbr_desktop.",
        )


class SisbrLoginService:
    def __init__(self, *, backend=None) -> None:
        self.backend = backend or _MissingLoginBackend()

    def ensure_logged_in(self) -> bool:
        return bool(self.backend.login())
