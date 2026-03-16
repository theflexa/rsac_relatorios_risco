def build_item_payload(
    project_id: int,
    job_id: int,
    reference: str,
    json_data: dict,
) -> dict:
    return {
        "project_id": project_id,
        "job_id": job_id,
        "data": json_data,
        "status": "aguardando",
        "reference": reference,
    }
