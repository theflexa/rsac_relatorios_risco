from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "Prints_telas" / "Prints_telas"
DEFAULT_OUTPUT_DIR = ROOT / "Prints_telas" / "Recortes_Seletores"


def _find_single(base_dir: Path, prefix: str, contains: str | None = None) -> Path:
    matches = []
    for file_path in sorted(base_dir.glob("*.png")):
        if not file_path.name.startswith(prefix):
            continue
        if contains and contains.lower() not in file_path.name.lower():
            continue
        matches.append(file_path)

    if len(matches) != 1:
        raise RuntimeError(f"Nao foi possivel resolver a imagem para prefixo={prefix!r}, contains={contains!r}: {matches}")
    return matches[0]


def _resolve_sources(base_dir: Path) -> dict[str, Path]:
    screen_5_all = sorted(base_dir.glob("5*.png"))
    screen_5_form = [
        path
        for path in screen_5_all
        if "combobox" not in path.name.lower() and "exemplo preenchido" not in path.name.lower()
    ]
    if len(screen_5_form) != 1:
        raise RuntimeError(f"Nao foi possivel resolver a tela base do formulario: {screen_5_form}")

    return {
        "screen_3_home": _find_single(base_dir, "3."),
        "screen_4_menu": _find_single(base_dir, "4."),
        "screen_5_form": screen_5_form[0],
        "screen_5_combo": _find_single(base_dir, "5.", contains="combobox"),
        "screen_5_filled": _find_single(base_dir, "5.", contains="exemplo preenchido"),
        "screen_6_modal": _find_single(base_dir, "6."),
        "screen_7_reports": _find_single(base_dir, "7."),
    }


SELECTOR_CROPS = [
    {
        "selector_name": "VALIDACAO_HOME",
        "source_key": "screen_3_home",
        "box": (118, 174, 188, 211),
    },
    {
        "selector_name": "BTN_MENU_RELATORIOS",
        "source_key": "screen_3_home",
        "box": (0, 175, 82, 232),
    },
    {
        "selector_name": "ITEM_RELATORIOS_RSAC",
        "source_key": "screen_4_menu",
        "box": (78, 257, 471, 345),
    },
    {
        "selector_name": "VALIDACAO_TELA_FORMULARIO",
        "source_key": "screen_5_form",
        "box": (1360, 112, 1897, 153),
    },
    {
        "selector_name": "SELECT_TIPO_RELATORIO",
        "source_key": "screen_5_form",
        "box": (1362, 276, 1908, 317),
    },
    {
        "selector_name": "OPCAO_TIPO_RELATORIO_RELATORIO_POR_COOPERATIVA",
        "source_key": "screen_5_filled",
        "box": (1362, 276, 1890, 317),
    },
    {
        "selector_name": "SELECT_SINGULAR",
        "source_key": "screen_5_form",
        "box": (1362, 443, 1908, 486),
    },
    {
        "selector_name": "OPCAO_SINGULAR_TEMPLATE",
        "source_key": "screen_5_combo",
        "box": (1363, 518, 1908, 560),
    },
    {
        "selector_name": "INPUT_MES_ANO",
        "source_key": "screen_5_filled",
        "box": (1362, 519, 1639, 564),
    },
    {
        "selector_name": "BTN_EXPORTAR",
        "source_key": "screen_5_form",
        "box": (1638, 701, 1912, 744),
    },
    {
        "selector_name": "MODAL_OPCOES_IMPRESSAO",
        "source_key": "screen_6_modal",
        "box": (670, 398, 1200, 760),
    },
    {
        "selector_name": "SELECT_FORMATO",
        "source_key": "screen_6_modal",
        "box": (692, 562, 1204, 605),
    },
    {
        "selector_name": "OPCAO_FORMATO_XLSX",
        "source_key": "screen_6_modal",
        "box": (694, 562, 782, 605),
    },
    {
        "selector_name": "BTN_GERAR_RELATORIO",
        "source_key": "screen_6_modal",
        "box": (1043, 684, 1201, 728),
    },
    {
        "selector_name": "VALIDACAO_RELATORIOS_DISPONIVEIS",
        "source_key": "screen_7_reports",
        "box": (149, 95, 378, 132),
    },
    {
        "selector_name": "TABELA_RELATORIOS",
        "source_key": "screen_7_reports",
        "box": (88, 249, 1906, 438),
    },
    {
        "selector_name": "LINHA_RELATORIO_TEMPLATE",
        "source_key": "screen_7_reports",
        "box": (89, 288, 1906, 322),
    },
    {
        "selector_name": "BTN_IMPRIMIR_TEMPLATE",
        "source_key": "screen_7_reports",
        "box": (1822, 396, 1852, 421),
    },
]


def build_jobs(base_dir: Path, output_dir: Path) -> list[dict]:
    sources = _resolve_sources(base_dir)
    jobs = []
    for spec in SELECTOR_CROPS:
        jobs.append(
            {
                "selector_name": spec["selector_name"],
                "source_path": sources[spec["source_key"]],
                "output_path": output_dir / f"{spec['selector_name']}.png",
                "box": spec["box"],
            },
        )
    return jobs


def _clamp_box(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    left, top, right, bottom = box
    left = max(0, min(left, width))
    top = max(0, min(top, height))
    right = max(left + 1, min(right, width))
    bottom = max(top + 1, min(bottom, height))
    return (left, top, right, bottom)


def crop_all(base_dir: Path = DEFAULT_INPUT_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    for job in build_jobs(base_dir, output_dir):
        with Image.open(job["source_path"]) as image:
            crop_box = _clamp_box(job["box"], image.size)
            cropped = image.crop(crop_box)
            cropped.save(job["output_path"])
        saved_paths.append(job["output_path"])
    return saved_paths


def main() -> None:
    saved_paths = crop_all()
    print(f"Recortes gerados: {len(saved_paths)}")
    for path in saved_paths:
        print(path)


if __name__ == "__main__":
    main()
