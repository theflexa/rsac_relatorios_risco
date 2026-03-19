from pywinauto.application import Application

# Conecta ao Sisbr 2.0 aberto
app = Application(backend="uia").connect(title_re="Sisbr 2.0")

# Pega a janela principal
win = app.window(title_re="Sisbr 2.0")

# Se estiver minimizada, restaura
if win.is_minimized():
    win.restore()

# Garante que a janela está em foco
win.set_focus()

# Mostra todos os elementos filhos identificáveis
win.print_control_identifiers()