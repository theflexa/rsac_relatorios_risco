from time import time
from pathlib import Path
from time import sleep as _sleep

try:
    from pywinauto import Desktop  # type: ignore
    from pywinauto.timings import TimeoutError as PywinautoTimeoutError  # type: ignore
except ImportError:  # pragma: no cover
    Desktop = None
    PywinautoTimeoutError = TimeoutError


class WindowsSaveAsDependencyError(RuntimeError):
    pass


class WindowsSaveAsTimeoutError(TimeoutError):
    pass


class WindowsSaveAsControlError(RuntimeError):
    pass


class WindowsSaveAsFlow:
    def __init__(
        self,
        *,
        timeout_seconds: int = 20,
        wait_file_seconds: int = 20,
        desktop_factory=None,
        path_exists=None,
        sleep=None,
        logger=None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.wait_file_seconds = wait_file_seconds
        self.desktop_factory = desktop_factory or self._default_desktop_factory
        self.path_exists = path_exists or (lambda path: path.exists())
        self.sleep = sleep or _sleep
        self.logger = logger or (lambda message: None)

    def save_file(self, destination_path: Path) -> Path:
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        dialog = self._wait_dialog("Salvar como", timeout_seconds=self.timeout_seconds)
        dialog.set_focus()
        self._fill_filename(dialog, destination_path)
        self._click_button(
            dialog,
            title="Salvar",
            auto_id="1",
            error_message="Botao 'Salvar' nao foi encontrado na janela 'Salvar como'.",
        )
        self._handle_overwrite_confirmation()

        total_wait = 0
        while total_wait < self.wait_file_seconds:
            if self.path_exists(destination_path):
                return destination_path
            self.sleep(1)
            total_wait += 1

        raise WindowsSaveAsTimeoutError(
            f"Arquivo nao apareceu apos salvar: {destination_path}",
        )

    def _wait_dialog(self, title: str, *, timeout_seconds: int):
        deadline = time() + timeout_seconds
        while time() < deadline:
            for backend in ("win32", "uia"):
                desktop = self.desktop_factory(backend=backend)
                for candidate_title in self._dialog_title_candidates(title):
                    dialog = desktop.window(title=candidate_title, class_name="#32770")
                    try:
                        dialog.wait("visible", timeout=1)
                        self.logger(
                            f"[save_as] Janela localizada por titulo exato: {candidate_title} ({backend})"
                        )
                        return dialog
                    except Exception:
                        pass

                dialog = self._find_dialog_by_enumeration(
                    desktop,
                    expected_titles=self._dialog_title_candidates(title),
                )
                if dialog is not None:
                    self.logger(f"[save_as] Janela localizada por enumeracao ({backend})")
                    return dialog

            self.sleep(0.5)

        raise WindowsSaveAsTimeoutError(
            f"Janela '{title}' nao apareceu no tempo limite.",
        )

    def _find_dialog_by_enumeration(self, desktop, *, expected_titles: tuple[str, ...]):
        try:
            windows = desktop.windows(class_name="#32770", visible_only=True)
        except Exception:
            return None

        expected = {title.casefold() for title in expected_titles}
        for dialog in windows:
            try:
                title = (dialog.window_text() or "").strip()
            except Exception:
                continue
            if title.casefold() in expected:
                return dialog
        return None

    def _fill_filename(self, dialog, destination_path: Path) -> None:
        field = self._find_filename_field(dialog)
        try:
            field.set_edit_text(str(destination_path))
        except Exception:
            try:
                field.click_input()
                field.type_keys("^a{BACKSPACE}", set_foreground=True)
                field.type_keys(str(destination_path), with_spaces=True, set_foreground=True)
            except Exception as exc:
                raise WindowsSaveAsControlError(
                    "Campo de nome do arquivo nao respondeu ao preenchimento no dialogo 'Salvar como'.",
                ) from exc

    def _find_filename_field(self, dialog):
        candidates = (
            {"control_id": 1001, "class_name": "Edit"},
            {"title_re": "(?i)nome do arquivo", "control_type": "Edit"},
            {"auto_id": "1001", "control_type": "Edit"},
            {"control_type": "ComboBox"},
            {"control_type": "Edit"},
        )
        for selector in candidates:
            try:
                control = dialog.child_window(**selector)
                control.wait("visible enabled ready", timeout=1)
                if selector.get("control_type") == "ComboBox":
                    edit = control.child_window(control_type="Edit")
                    edit.wait("visible enabled ready", timeout=1)
                    return edit
                return control
            except Exception:
                continue
        raise WindowsSaveAsControlError(
            "Campo de nome do arquivo nao foi encontrado na janela 'Salvar como'.",
        )

    def _click_button(self, dialog, *, title: str, auto_id: str | None, error_message: str) -> None:
        selectors = []
        if title == "Salvar":
            selectors.append({"control_id": 1, "class_name": "Button"})
        if auto_id is not None:
            selectors.append({"title": title, "auto_id": auto_id, "control_type": "Button"})
        selectors.extend(
            [
                {"title": title, "control_type": "Button"},
                {"title": "Sa&lvar", "class_name": "Button"},
                {"title_re": f"(?i)^{title}$", "control_type": "Button"},
                {"title_re": r"(?i)^sa&?lvar$", "class_name": "Button"},
            ]
        )
        for selector in selectors:
            try:
                button = dialog.child_window(**selector)
                button.wait("visible enabled ready", timeout=1)
                self._press(button)
                self.logger(f"[save_as] Clique no botao: {title} via {selector}")
                return
            except Exception:
                continue

        normalized_title = self._normalize_caption(title)
        try:
            buttons = dialog.descendants(class_name="Button")
        except Exception:
            buttons = []
        for button in buttons:
            try:
                caption = button.window_text() or ""
            except Exception:
                continue
            if self._normalize_caption(caption) != normalized_title:
                continue
            try:
                self._press(button)
                self.logger(f"[save_as] Clique no botao: {title} via enumeracao ({caption!r})")
                return
            except Exception:
                continue
        raise WindowsSaveAsControlError(error_message)

    def _handle_overwrite_confirmation(self) -> None:
        try:
            dialog = self._wait_dialog("Confirmar Salvar como", timeout_seconds=2)
        except WindowsSaveAsTimeoutError:
            return
        self._click_button(
            dialog,
            title="Sim",
            auto_id=None,
            error_message="Botao 'Sim' nao foi encontrado na confirmacao de sobrescrita.",
        )

    @staticmethod
    def _press(control) -> None:
        for method_name in ("invoke", "click", "click_input"):
            method = getattr(control, method_name, None)
            if method is None:
                continue
            try:
                method()
                return
            except Exception:
                continue
        iface = getattr(control, "iface_invoke", None)
        if iface is not None:
            iface.Invoke()
            return
        raise WindowsSaveAsControlError("Controle localizado, mas nao respondeu a invoke/click.")

    @staticmethod
    def _default_desktop_factory(*, backend: str):
        if Desktop is None:
            raise WindowsSaveAsDependencyError(
                "pywinauto nao esta instalado para usar WindowsSaveAsFlow.",
            )
        return Desktop(backend=backend)

    @staticmethod
    def _dialog_title_candidates(title: str) -> tuple[str, ...]:
        if title == "Salvar como":
            return ("Salvar como", "Save As")
        if title == "Confirmar Salvar como":
            return ("Confirmar Salvar como", "Confirm Save As")
        return (title,)

    @staticmethod
    def _normalize_caption(value: str) -> str:
        return (value or "").replace("&", "").strip().casefold()
