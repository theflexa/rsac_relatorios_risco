from __future__ import annotations

import sys
from pathlib import Path

from rsac_relatorios_risco.sisbr.login_service import SisbrLoginService
from rsac_relatorios_risco.sisbr.module_accessor import SisbrModuleAccessor


class SisbrConnectivityError(RuntimeError):
    pass


RSAC_MODULE_NAME = "RISCOS SOCIAL, AMBIENTAL E CLIMÁTICO"


class _LibSisbrOpenBackend:
    def abrir_sisbr(self, caminho_exe=None):
        from lib_sisbr_desktop.src.lib_sisbr_desktop.core.abrir_sisbr import abrir_sisbr  # type: ignore

        if caminho_exe:
            return abrir_sisbr(caminho_exe=caminho_exe)
        return abrir_sisbr()


class _LibSisbrLoginBackend:
    def login(self, win_principal=None) -> bool:
        from lib_sisbr_desktop.src.lib_sisbr_desktop.core.login import login  # type: ignore

        return bool(login(win_principal))


class _LibSisbrStatusBackend:
    def is_logado(self, win_principal) -> bool:
        from lib_sisbr_desktop.src.lib_sisbr_desktop.utils.status import is_logado  # type: ignore

        return bool(is_logado(win_principal))

    def is_updating(self, win_principal) -> bool:
        from lib_sisbr_desktop.src.lib_sisbr_desktop.utils.status import is_updating  # type: ignore

        return bool(is_updating(win_principal))

    def wait_until_ready(self, win_principal, timeout: float = 120.0) -> bool:
        from lib_sisbr_desktop.src.lib_sisbr_desktop.utils.status import wait_until_ready  # type: ignore

        return bool(wait_until_ready(win_principal, timeout=timeout))

    def has_connectivity_error(self, win_principal) -> bool:
        from lib_sisbr_desktop.src.lib_sisbr_desktop.utils.status import has_connectivity_error  # type: ignore

        return bool(has_connectivity_error(win_principal))


class _LibSisbrAccessorBackend:
    def acessar_modulo(self, win_principal, nome_modulo: str, max_retentativas: int = 3):
        from lib_sisbr_desktop.src.lib_sisbr_desktop.core.acessar_modulo import acessar_modulo  # type: ignore

        return acessar_modulo(
            win_principal,
            nome_modulo,
            max_retentativas=max_retentativas,
        )


class LibSisbrDesktopSession:
    def __init__(
        self,
        *,
        lib_path,
        sisbr_exe: str | None = None,
        module_name: str = RSAC_MODULE_NAME,
        max_retentativas: int = 3,
        bootstrap_sys_path=None,
        open_backend=None,
        login_service=None,
        accessor_backend=None,
        status_backend=None,
    ) -> None:
        self.lib_path = Path(lib_path)
        self.sisbr_exe = sisbr_exe
        self.module_name = module_name
        self.max_retentativas = max_retentativas
        self.bootstrap_sys_path = bootstrap_sys_path or self._default_bootstrap_sys_path
        self.open_backend = open_backend or _LibSisbrOpenBackend()
        self.login_service = login_service or SisbrLoginService(
            backend=_LibSisbrLoginBackend(),
        )
        self.accessor_backend = accessor_backend or _LibSisbrAccessorBackend()
        self.status_backend = status_backend or _LibSisbrStatusBackend()

    def ensure_rsa_open(self):
        self.bootstrap_sys_path()
        app, win_principal = self._open_sisbr()
        del app
        if self.status_backend.has_connectivity_error(win_principal):
            raise SisbrConnectivityError(
                "Sisbr exibiu a tela de erro de conectividade com o Sicoob Confederacao antes do login.",
            )
        if self.status_backend.is_logado(win_principal):
            pass
        elif self.status_backend.is_updating(win_principal):
            if not self.status_backend.wait_until_ready(win_principal, timeout=180.0):
                if self.status_backend.has_connectivity_error(win_principal):
                    raise SisbrConnectivityError(
                        "Sisbr exibiu a tela de erro de conectividade com o Sicoob Confederacao durante a inicializacao.",
                    )
                raise RuntimeError(
                    "Sisbr permaneceu na tela de atualização e não chegou à tela principal em tempo hábil.",
                )
        else:
            self.login_service.ensure_logged_in(win_principal)
            if not self.status_backend.wait_until_ready(win_principal, timeout=180.0):
                if self.status_backend.has_connectivity_error(win_principal):
                    raise SisbrConnectivityError(
                        "Sisbr exibiu a tela de erro de conectividade com o Sicoob Confederacao apos o login.",
                    )
                raise RuntimeError(
                    "Login executado, mas o Sisbr não chegou à tela principal em tempo hábil.",
                )
        accessor = SisbrModuleAccessor(
            win_principal=win_principal,
            backend=self.accessor_backend,
            module_name=self.module_name,
            max_retentativas=self.max_retentativas,
        )
        return accessor.acessar_modulo_rsa()

    def _open_sisbr(self):
        return self.open_backend.abrir_sisbr(caminho_exe=self.sisbr_exe)

    def _default_bootstrap_sys_path(self) -> None:
        repo_parent = self.lib_path.parent
        if str(repo_parent) not in sys.path:
            sys.path.insert(0, str(repo_parent))
