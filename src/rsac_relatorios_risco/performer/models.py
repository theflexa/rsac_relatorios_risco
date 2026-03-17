from dataclasses import dataclass, field


@dataclass(slots=True)
class PerformerItem:
    item_id: int
    reference: str
    status: str
    attempts: list[dict] = field(default_factory=list)
    data: dict = field(default_factory=dict)
