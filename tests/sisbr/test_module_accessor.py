from rsac_relatorios_risco.sisbr.module_accessor import SisbrModuleAccessor


class FakeBackend:
    def __init__(self) -> None:
        self.calls = []

    def acessar_modulo(self, win_principal, nome_modulo, max_retentativas=3):
        self.calls.append((win_principal, nome_modulo, max_retentativas))
        return "janela-rsa"


def test_accessor_calls_backend_with_rsa_module_name() -> None:
    backend = FakeBackend()
    accessor = SisbrModuleAccessor(
        win_principal="janela-principal",
        backend=backend,
        module_name="RSA",
        max_retentativas=5,
    )

    result = accessor.acessar_modulo_rsa()

    assert result == "janela-rsa"
    assert backend.calls == [("janela-principal", "RSA", 5)]
