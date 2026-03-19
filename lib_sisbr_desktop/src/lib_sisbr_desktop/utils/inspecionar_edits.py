from pywinauto.application import Application

app = Application(backend="uia").connect(title_re="Sisbr 2.0")
win = app.window(title_re="Sisbr 2.0")
win.set_focus()

edits = win.descendants(control_type="Edit")

print(f"\n {len(edits)} campos Edit encontrados:\n")

for i, edit in enumerate(edits):
    try:
        r = edit.rectangle()
        text = edit.window_text()
        print(f"[{i}] ({r.left}, {r.top}, {r.right}, {r.bottom}) — texto: '{text}'")
    except Exception as e:
        print(f"[{i}] [INFO] Erro ao acessar campo: {e}")
