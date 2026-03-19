# 📦 sisbr_desktop

Automatiza interações com o sistema Sisbr 2.0 (desktop) utilizando Python 3.11, Pywinauto, OCR e coordenadas. 

Projetado para ser uma **lib reutilizável** em múltiplos fluxos como Análise de Crédito, Conta Corrente, Liberação de Limite, entre outros.

---

## ✅ Funcionalidades

- Abertura segura do Sisbr 2.0 (`abrir_sisbr`)
- Login com validação (`login`)
- Acesso a módulos dinâmicos por nome (`acessar_modulo`)
- Detecção de janelas e validação de estado (`utils/window`, `utils/status`)
- Digitação segura com OCR opcional
- Coordenações controladas com tolerância mínima (sem cliques errados)

---

## 🛠 Requisitos

- Python 3.11+
- Windows 10 ou 11
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado (opcional, se usar OCR)

---

## 🚀 Instalação via Poetry

```bash
poetry install
```

---

## 🔧 Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
SISBR_EXE=C:/Sisbr 2.0/Sisbr 2.0.exe

USUARIO=username_aqui
SENHA=senha_aqui
COOP=coop_central
NPAC=0
```

---

## 📄 Exemplo de uso (main.py)

```python
from core.abrir_sisbr import abrir_sisbr
from core.login import login
from core.acessar_modulo import acessar_modulo
from utils.status import is_logado, is_modulo_aberto
from utils.window import get_window_by_title
from config import SISBR_EXE, USUARIO, SENHA, COOP, NPAC

app, win = abrir_sisbr(SISBR_EXE)

if not is_logado(win):
    login(win, USUARIO, SENHA, COOP, NPAC)

if not is_modulo_aberto("CONTA CORRENTE", app):
    win_modulo = acessar_modulo(win, "CONTA CORRENTE")
else:
    win_modulo = get_window_by_title("CONTA CORRENTE", app)
```

---

## 📁 Estrutura recomendada

```
sisbr_desktop/
├── pyproject.toml
├── .env
├── src/
│   └── sisbr_desktop/
│       ├── config.py
│       ├── core/
│       │   ├── abrir_sisbr.py
│       │   ├── login.py
│       │   ├── acessar_modulo.py
│       ├── gui/
│       │   ├── typer.py
│       │   ├── helpers.py
│       │   ├── mapeamento.py
│       ├── utils/
│       │   ├── window.py
|       |   ├── wait.py
│       │   ├── status.py
```

---

## 🧠 Padrões adotados

- Nenhum uso de `found_index` para cliques críticos
- Mapeamento baseado em `rectangle` com tolerância <= 2px
- Todos os comandos de digitação validados com leitura posterior
- Reuso total de módulos entre diferentes fluxos (projetos externos importam via Poetry)

---

## 🔐 Segurança

- `.env` **não deve ser versionado**
- Todos os fluxos validam janelas antes de interagir
- Fluxos toleram falhas com retry seguro

---

## ✍️ Autor

Lisandro Davi de Souza – RPA Architect