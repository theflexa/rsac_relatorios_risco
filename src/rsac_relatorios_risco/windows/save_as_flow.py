from pathlib import Path
from time import sleep as _sleep

try:
    from pywinauto import Desktop  # type: ignore
    from pywinauto.keyboard import send_keys  # type: ignore
except ImportError:  # pragma: no cover
    Desktop = None
    send_keys = None


class WindowsSaveAsDependencyError(RuntimeError):
    pass


class WindowsSaveAsTimeoutError(TimeoutError):
    pass


class WindowsSaveAsFlow:
    def __init__(
        self,
        *,
        timeout_seconds: int = 20,
        wait_file_seconds: int = 20,
        desktop_factory=None,
        keyboard_send=None,
        path_exists=None,
        sleep=None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.wait_file_seconds = wait_file_seconds
        self.desktop_factory = desktop_factory or self._default_desktop_factory
        self.keyboard_send = keyboard_send or self._default_keyboard_send
        self.path_exists = path_exists or (lambda path: path.exists())
        self.sleep = sleep or _sleep

    def save_file(self, destination_path: Path) -> Path:
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        dialog = self.desktop_factory(backend="uia").window(
            title_re=".*(Salvar como|Save As).*",
        )
        dialog.wait("visible", timeout=self.timeout_seconds)
        dialog.set_focus()

        self.keyboard_send("%n")
        self.keyboard_send("^a{BACKSPACE}")
        self.keyboard_send(str(destination_path), with_spaces=True)
        self.keyboard_send("%s")

        total_wait = 0
        while total_wait < self.wait_file_seconds:
            if self.path_exists(destination_path):
                return destination_path
            self.sleep(1)
            total_wait += 1

        raise WindowsSaveAsTimeoutError(
            f"Arquivo nao apareceu apos salvar: {destination_path}",
        )

    @staticmethod
    def _default_desktop_factory(*, backend: str):
        if Desktop is None:
            raise WindowsSaveAsDependencyError(
                "pywinauto nao esta instalado para usar WindowsSaveAsFlow.",
            )
        return Desktop(backend=backend)

    @staticmethod
    def _default_keyboard_send(text: str, **kwargs) -> None:
        if send_keys is None:
            raise WindowsSaveAsDependencyError(
                "pywinauto nao esta instalado para usar WindowsSaveAsFlow.",
            )
        send_keys(text, **kwargs)
