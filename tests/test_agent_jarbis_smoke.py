import importlib

from agent_jarbis import REGISTERED_TOPICS
from rsac_relatorios_risco.web.rsa_portal_stub import RsaPortalNotReadyError


def test_rsa_portal_not_ready_error_exists():
    assert issubclass(RsaPortalNotReadyError, RuntimeError)


def test_registered_topics_contains_dispatcher_and_performer():
    assert "DISPATCHER_RSAC" in REGISTERED_TOPICS
    assert "PERFORMER_RSAC" in REGISTERED_TOPICS


def test_agent_jarbis_imports():
    assert importlib.import_module("agent_jarbis") is not None


def test_agent_jarbis_exposes_performer_entrypoint():
    module = importlib.import_module("agent_jarbis")

    assert hasattr(module, "run_performer")
