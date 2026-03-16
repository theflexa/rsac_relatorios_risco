import importlib


def test_package_bootstrap_imports():
    assert importlib.import_module("rsac_relatorios_risco") is not None
