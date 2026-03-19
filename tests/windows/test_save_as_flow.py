from pathlib import Path

from rsac_relatorios_risco.windows.save_as_flow import WindowsSaveAsFlow


class FakeDialog:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def wait(self, condition: str, timeout: int):
        self.calls.append(("wait", condition, timeout))
        return self

    def set_focus(self):
        self.calls.append(("set_focus",))


class FakeDesktop:
    def __init__(self, dialog: FakeDialog) -> None:
        self.dialog = dialog
        self.last_title_re = None

    def window(self, title_re: str):
        self.last_title_re = title_re
        return self.dialog


def test_save_as_flow_uses_dialog_and_keyboard_sequence(tmp_path: Path):
    dialog = FakeDialog()
    desktop = FakeDesktop(dialog)
    keys: list[str] = []
    destination = tmp_path / "relatorio.xlsx"
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: desktop,
        keyboard_send=lambda text, **kwargs: keys.append(text),
        path_exists=lambda path: path == destination,
        sleep=lambda seconds: None,
    )

    result = flow.save_file(destination)

    assert result == destination
    assert desktop.last_title_re == ".*(Salvar como|Save As).*"
    assert dialog.calls == [
        ("wait", "visible", 20),
        ("set_focus",),
    ]
    assert keys == [
        "%n",
        "^a{BACKSPACE}",
        str(destination),
        "%s",
    ]
