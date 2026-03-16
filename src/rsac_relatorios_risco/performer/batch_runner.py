from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PublishResult:
    sheet_saved: bool
    sharepoint_published: bool


class PerformerBatchRunner:
    def __init__(self, consolidado_service, sharepoint_client) -> None:
        self.consolidado_service = consolidado_service
        self.sharepoint_client = sharepoint_client

    def publish_one(self, *, report, workbook_path: Path, destination: str) -> PublishResult:
        self.consolidado_service.apply_report(workbook_path, report)
        sharepoint_published = self.sharepoint_client.upload_incremental(
            workbook_path,
            destination,
        )
        return PublishResult(
            sheet_saved=workbook_path.exists(),
            sharepoint_published=sharepoint_published,
        )
