from dataclasses import dataclass


@dataclass(slots=True)
class ConfigItem:
    reference: str
    tipo_relatorio: str | None
    timeout: int | None
    cooperativa: str | None
    pa: str | None
    nome_cooperativa_1: str | None
    nome_cooperativa_2: str | None
    destinatarios: str | None
    sharepoint: str | None
    nome_arquivo: str | None
    extensao: str | None


@dataclass(slots=True)
class ConfigWorkbook:
    settings: dict[str, str]
    items: list[ConfigItem]
