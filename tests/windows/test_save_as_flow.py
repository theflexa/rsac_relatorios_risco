from pathlib import Path

import pytest

from rsac_relatorios_risco.windows.save_as_flow import (
    WindowsSaveAsControlError,
    WindowsSaveAsFlow,
    WindowsSaveAsTimeoutError,
)


class FakeControl:
    def __init__(self, *, title: str = "") -> None:
        self.calls: list[tuple] = []
        self.children: dict[tuple, FakeControl] = {}
        self.title = title

    def wait(self, condition: str, timeout: int):
        self.calls.append(("wait", condition, timeout))
        return self

    def set_focus(self):
        self.calls.append(("set_focus",))

    def set_edit_text(self, value: str):
        self.calls.append(("set_edit_text", value))

    def click(self):
        self.calls.append(("click",))

    def click_input(self):
        self.calls.append(("click_input",))

    def invoke(self):
        self.calls.append(("invoke",))

    def child_window(self, **kwargs):
        self.calls.append(("child_window", kwargs))
        key = tuple(sorted(kwargs.items()))
        if key not in self.children:
            raise RuntimeError("control not found")
        return self.children[key]

    def window_text(self):
        return self.title


class FakeDesktop:
    def __init__(self, windows: dict[str, FakeControl]) -> None:
        self._windows = windows
        self.calls: list[tuple] = []

    def window(self, title: str, class_name: str | None = None):
        self.calls.append(("window", title, class_name))
        if title not in self._windows:
            failing = FakeControl()

            def fail_wait(condition: str, timeout: int):
                raise TimeoutError("window not found")

            failing.wait = fail_wait  # type: ignore
            return failing
        return self._windows[title]

    def windows(self, class_name: str, visible_only: bool):
        self.calls.append(("windows", class_name, visible_only))
        return list(self._windows.values())


def test_save_as_flow_fills_filename_clicks_save_and_handles_overwrite(tmp_path: Path):
    save_dialog = FakeControl(title="Salvar como")
    file_edit = FakeControl()
    save_button = FakeControl()
    overwrite_dialog = FakeControl(title="Confirmar Salvar como")
    yes_button = FakeControl()

    save_dialog.children[(("class_name", "Edit"), ("control_id", 1001))] = file_edit
    save_dialog.children[(("class_name", "Button"), ("control_id", 1))] = save_button
    save_dialog.children[(("auto_id", "1"), ("control_type", "Button"), ("title", "Salvar"))] = save_button
    overwrite_dialog.children[(("control_type", "Button"), ("title", "Sim"))] = yes_button

    destination = tmp_path / "relatorio.xlsx"
    state = {"exists": False}

    def path_exists(path: Path) -> bool:
        return path == destination and state["exists"]

    yes_button.invoke = lambda: (yes_button.calls.append(("invoke",)), state.__setitem__("exists", True))

    desktop = FakeDesktop(
        {
            "Salvar como": save_dialog,
            "Confirmar Salvar como": overwrite_dialog,
        }
    )
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: desktop,
        path_exists=path_exists,
        sleep=lambda seconds: None,
    )

    result = flow.save_file(destination)

    assert result == destination
    assert desktop.calls[:2] == [
        ("window", "Salvar como", "#32770"),
        ("window", "Confirmar Salvar como", "#32770"),
    ]
    assert save_dialog.calls[:3] == [
        ("wait", "visible", 1),
        ("set_focus",),
        ("child_window", {"control_id": 1001, "class_name": "Edit"}),
    ]
    assert file_edit.calls == [
        ("wait", "visible enabled ready", 1),
        ("set_edit_text", str(destination)),
    ]
    assert save_button.calls == [
        ("wait", "visible enabled ready", 1),
        ("invoke",),
    ]
    assert yes_button.calls == [
        ("wait", "visible enabled ready", 1),
        ("invoke",),
    ]


def test_save_as_flow_returns_without_overwrite_dialog(tmp_path: Path):
    save_dialog = FakeControl(title="Salvar como")
    file_edit = FakeControl()
    save_button = FakeControl()
    save_dialog.children[(("class_name", "Edit"), ("control_id", 1001))] = file_edit
    save_dialog.children[(("class_name", "Button"), ("control_id", 1))] = save_button

    destination = tmp_path / "relatorio.xlsx"
    state = {"exists": False}

    def path_exists(path: Path) -> bool:
        return path == destination and state["exists"]

    save_button.invoke = lambda: (save_button.calls.append(("invoke",)), state.__setitem__("exists", True))
    desktop = FakeDesktop({"Salvar como": save_dialog})
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: desktop,
        path_exists=path_exists,
        sleep=lambda seconds: None,
    )

    result = flow.save_file(destination)

    assert result == destination
    assert desktop.calls[:2] == [
        ("window", "Salvar como", "#32770"),
        ("window", "Confirmar Salvar como", "#32770"),
    ]


def test_save_as_flow_raises_when_save_dialog_does_not_appear(tmp_path: Path):
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: FakeDesktop({}),
        path_exists=lambda path: False,
        sleep=lambda seconds: None,
    )

    with pytest.raises(WindowsSaveAsTimeoutError, match="Janela 'Salvar como' nao apareceu"):
        flow.save_file(tmp_path / "relatorio.xlsx")


def test_save_as_flow_raises_when_save_button_is_not_found(tmp_path: Path):
    save_dialog = FakeControl(title="Salvar como")
    file_edit = FakeControl()
    save_dialog.children[(("class_name", "Edit"), ("control_id", 1001))] = file_edit
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: FakeDesktop({"Salvar como": save_dialog}),
        path_exists=lambda path: False,
        sleep=lambda seconds: None,
    )

    with pytest.raises(WindowsSaveAsControlError, match="Botao 'Salvar' nao foi encontrado"):
        flow.save_file(tmp_path / "relatorio.xlsx")


def test_save_as_flow_can_find_dialog_by_enumeration(tmp_path: Path):
    save_dialog = FakeControl(title="Salvar como")
    file_edit = FakeControl()
    save_button = FakeControl()
    save_dialog.children[(("class_name", "Edit"), ("control_id", 1001))] = file_edit
    save_dialog.children[(("class_name", "Button"), ("control_id", 1))] = save_button

    destination = tmp_path / "relatorio.xlsx"
    state = {"exists": False}

    def path_exists(path: Path) -> bool:
        return path == destination and state["exists"]

    save_button.invoke = lambda: (save_button.calls.append(("invoke",)), state.__setitem__("exists", True))
    desktop = FakeDesktop({"enum": save_dialog})
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: desktop,
        path_exists=path_exists,
        sleep=lambda seconds: None,
    )

    result = flow.save_file(destination)

    assert result == destination
    assert ("windows", "#32770", True) in desktop.calls


def test_save_as_flow_can_match_button_with_accelerator_caption(tmp_path: Path):
    save_dialog = FakeControl(title="Salvar como")
    file_edit = FakeControl()
    save_button = FakeControl()
    save_dialog.children[(("class_name", "Edit"), ("control_id", 1001))] = file_edit
    save_dialog.children[(("class_name", "Button"), ("title", "Sa&lvar"))] = save_button

    destination = tmp_path / "relatorio.xlsx"
    state = {"exists": False}

    def path_exists(path: Path) -> bool:
        return path == destination and state["exists"]

    save_button.invoke = lambda: (save_button.calls.append(("invoke",)), state.__setitem__("exists", True))
    flow = WindowsSaveAsFlow(
        desktop_factory=lambda backend: FakeDesktop({"Salvar como": save_dialog}),
        path_exists=path_exists,
        sleep=lambda seconds: None,
    )

    result = flow.save_file(destination)

    assert result == destination
