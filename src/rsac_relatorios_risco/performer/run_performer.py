from rsac_relatorios_risco.performer.queue_selector import filter_eligible_items


class _FallbackLogger:
    def info(self, message: str) -> None:
        return None


class StepByStepPerformer:
    def __init__(
        self,
        *,
        queue_repository,
        item_updater,
        consolidado_resolver,
        sisbr_flow,
        rsa_flow,
        report_service,
        batch_runner,
        email_service,
        cleanup_service,
        max_attempts: int,
        download_dir,
        cleanup_days: int,
        logger=None,
    ) -> None:
        self.queue_repository = queue_repository
        self.item_updater = item_updater
        self.consolidado_resolver = consolidado_resolver
        self.sisbr_flow = sisbr_flow
        self.rsa_flow = rsa_flow
        self.report_service = report_service
        self.batch_runner = batch_runner
        self.email_service = email_service
        self.cleanup_service = cleanup_service
        self.max_attempts = max_attempts
        self.download_dir = download_dir
        self.cleanup_days = cleanup_days
        self.logger = logger or _FallbackLogger()

    def run(self) -> dict:
        self.logger.info("Iniciando execução do Performer")
        self.logger.info("Coletando itens elegíveis")
        items = self.queue_repository.list_items()
        eligible = filter_eligible_items(items, self.max_attempts)
        summary = {
            "concluidos": [],
            "erros_sistemicos": [],
            "excecoes_negociais": [],
            "ignorados_por_max_attempts": [],
            "consolidado_path": None,
        }

        workbook_path = None
        for item in eligible:
            if workbook_path is None:
                self.logger.info("Localizando ou criando consolidado mensal")
                workbook_path = self.consolidado_resolver.resolve(item)
                summary["consolidado_path"] = str(workbook_path)

            self.logger.info(f"Coletando item {item.item_id} - {item.reference}")
            self.logger.info(f"Marcando item {item.item_id} como processando")
            item = self.item_updater.mark_processing(item)

            self.logger.info("Acessando módulo RSA via Sisbr Desktop")
            self.sisbr_flow.acessar_modulo_rsa()

            self.logger.info("Validando home RSA no navegador")
            self.rsa_flow.validar_home()

            self.logger.info(
                f"Preenchendo filtros da competência {item.data['competencia']}",
            )
            self.rsa_flow.preencher_filtros(
                competencia=item.data["competencia"],
                tipo_relatorio=item.data["tipo_relatorio"],
            )

            self.logger.info(f"Selecionando cooperativa {item.data['cooperativa']}")
            self.rsa_flow.selecionar_cooperativas([item.data["cooperativa"]])

            self.logger.info(
                f"Exportando relatório da cooperativa {item.data['cooperativa']}",
            )
            report_path = self.rsa_flow.exportar_relatorio(self.download_dir)

            self.logger.info("Lendo relatório exportado")
            report = self.report_service.read_report(report_path)

            self.logger.info(
                f"Atualizando aba da cooperativa {item.data['cooperativa']} e publicando consolidado",
            )
            publish_result = self.batch_runner.publish_one(
                report=report,
                workbook_path=workbook_path,
                destination=item.data["sharepoint"],
            )

            final_status = (
                "sucesso"
                if publish_result.sheet_saved and publish_result.sharepoint_published
                else "erro sistêmico"
            )
            if final_status == "sucesso":
                summary["concluidos"].append(item.reference)
                self.logger.info(f"Marcando item {item.item_id} como sucesso")
            elif final_status == "erro sistêmico":
                summary["erros_sistemicos"].append(item.reference)
                self.logger.info(f"Marcando item {item.item_id} como erro sistêmico")
            else:
                summary["excecoes_negociais"].append(item.reference)
                self.logger.info(f"Marcando item {item.item_id} como exceção negocial")

            self.item_updater.mark_finished(item, final_status)

        self.logger.info("Executando limpeza de temporários antigos")
        self.cleanup_service.delete_files_older_than(
            self.download_dir,
            self.cleanup_days,
        )
        self.logger.info("Enviando e-mail final")
        self.email_service.send_summary(summary)
        return summary
