from collections.abc import Mapping


def resolve_value(raw: object | None, context: Mapping[str, str]) -> str:
    if raw is None:
        return ""

    result = str(raw)
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", value)
    return result
