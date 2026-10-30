def render_task(description: str, target_name: str | None) -> str:
    """Fill {target}; if there is no target (e.g. a lone player), say 'someone'."""
    return description.replace("{target}", target_name or "someone")
