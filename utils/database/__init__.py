"""Camada de acesso ao banco via PostgREST (estilo Supabase)."""
from utils.database.client import (  # noqa: F401
    has_database_config,
    ensure_project,
    insert_job,
    update_job,
    insert_item,
    get_item_by_id,
    get_items,
    reference_exists,
    update_item,
    update_item_merge,
)
