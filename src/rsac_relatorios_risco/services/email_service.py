def build_summary_subject(status: str, competencia: str) -> str:
    return f"RSAC {competencia} - {status}"


def build_summary_body(
    *,
    competencia: str,
    concluidos: list[str],
    pendentes: list[str],
    erros: list[str],
) -> str:
    concluidos_texto = ", ".join(concluidos) if concluidos else "nenhum"
    pendentes_texto = ", ".join(pendentes) if pendentes else "nenhum"
    erros_texto = " | ".join(erros) if erros else "nenhum"
    return (
        f"Competência: {competencia}\n"
        f"Concluídos: {concluidos_texto}\n"
        f"Pendentes: {pendentes_texto}\n"
        f"Erros: {erros_texto}"
    )
