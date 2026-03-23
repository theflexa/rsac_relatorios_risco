from __future__ import annotations


RSAC_MODULE_NAME = "RISCOS SOCIAL, AMBIENTAL E CLIMÁTICO"


class SisbrDependencyNotConfiguredError(RuntimeError):
    pass


class _MissingBackend:
    def acessar_modulo(self, win_principal, nome_modulo: str, max_retentativas: int = 3):
        raise SisbrDependencyNotConfiguredError(
            "Backend do Sisbr Desktop nao configurado. Injete a funcao acessar_modulo da lib_sisbr_desktop.",
        )


class SisbrModuleAccessor:
    def __init__(
        self,
        *,
        win_principal,
        backend=None,
        module_name: str = RSAC_MODULE_NAME,
        max_retentativas: int = 3,
    ) -> None:
        self.win_principal = win_principal
        self.backend = backend or _MissingBackend()
        self.module_name = module_name
        self.max_retentativas = max_retentativas

    def acessar_modulo_rsa(self):
        return self.backend.acessar_modulo(
            self.win_principal,
            self.module_name,
            max_retentativas=self.max_retentativas,
        )
