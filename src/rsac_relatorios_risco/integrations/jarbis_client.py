def build_process_variables(item_payload: dict) -> dict:
    return {
        "reference": {
            "value": item_payload["reference"],
            "type": "String",
        }
    }
