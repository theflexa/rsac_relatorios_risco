from rsac_relatorios_risco.performer.queue_selector import filter_eligible_items


class PerformerOrchestrator:
    def __init__(
        self,
        *,
        queue_repository,
        item_updater,
        consolidado_resolver,
        item_runner,
        email_service,
        max_attempts: int,
        download_dir,
    ) -> None:
        self.queue_repository = queue_repository
        self.item_updater = item_updater
        self.consolidado_resolver = consolidado_resolver
        self.item_runner = item_runner
        self.email_service = email_service
        self.max_attempts = max_attempts
        self.download_dir = download_dir

    def run(self) -> dict:
        items = self.queue_repository.list_items()
        eligible = filter_eligible_items(items, self.max_attempts)
        summary = {
            "concluidos": [],
            "erros_sistemicos": [],
            "excecoes_negociais": [],
            "ignorados_por_max_attempts": [],
        }

        for item in eligible:
            self.item_updater.mark_processing(item)
            workbook_path = self.consolidado_resolver.resolve(item)
            result = self.item_runner.run(
                item=item,
                workbook_path=workbook_path,
                download_dir=self.download_dir,
            )
            self.item_updater.mark_finished(item, result.final_status)
            if result.final_status == "sucesso":
                summary["concluidos"].append(item.reference)
            elif result.final_status == "erro sistêmico":
                summary["erros_sistemicos"].append(item.reference)
            else:
                summary["excecoes_negociais"].append(item.reference)

        self.email_service.send_summary(summary)
        return summary
