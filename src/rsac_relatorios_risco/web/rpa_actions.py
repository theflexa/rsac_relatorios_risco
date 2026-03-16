from rsac_relatorios_risco.web.rsa_portal_stub import RsaPortalNotReadyError


def click(*args, **kwargs):
    raise RsaPortalNotReadyError(
        "click() ainda não foi conectado ao Selenium real em web/rpa_actions.py",
    )


def type_into(*args, **kwargs):
    raise RsaPortalNotReadyError(
        "type_into() ainda não foi conectado ao Selenium real em web/rpa_actions.py",
    )


def wait_element(*args, **kwargs):
    raise RsaPortalNotReadyError(
        "wait_element() ainda não foi conectado ao Selenium real em web/rpa_actions.py",
    )
