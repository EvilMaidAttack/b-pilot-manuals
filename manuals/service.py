from .models import ManualDocument, ManualFile
from .manual_api import ManualsAPI
from sharepoint.sharepoint_api import SharePointClient
import logging
import requests

logger = logging.getLogger(__name__)


class ManualsService:
    def __init__(self, manuals_api: ManualsAPI, sharepoint_api: SharePointClient):
        self.manuals_api = manuals_api
        self.sharepoint = sharepoint_api

    def sync_manuals(self, max_files: int | None = None):
        logger.info("Starting manuals synchronization...")
        response = self.manuals_api.fetch_manuals()
        processed = 0

        for doc in response.documents:
            logger.info("Processing document", extra={"document_type": doc.type})
            for file in doc.files:
                try:
                    self._process_file(doc, file)
                    processed += 1
                    if max_files and processed >= max_files:
                        return
                except Exception:
                    logger.exception(
                    "Failed to process manual file",
                    extra={
                        "document_type": doc.type,
                        "file_name": file.filename,
                    },
                )
                    
        logger.info("Manuals synchronization completed.")


    def _process_file(self, doc: ManualDocument, file: ManualFile):
        path = f"Manuals/{doc.type}/{file.type}/{file.language}"
        filename = file.filename
        logger.info("Processing file", extra={"document_type": doc.type, "language": file.language,"file_name": filename,})   

        if self.sharepoint.file_exists_with_same_hash(path, filename, file.hash):
            logger.info(
            "File already exists in SharePoint, skipping",
            extra={"file_name": filename, "path": path},
            )
            return  # already uploaded

        logger.info("Downloading file", extra={"download_url": file.download_url})
        content = self._download_file(file.download_url)

        logger.info("Uploading file to SharePoint", extra={"file_name": filename, "path": path})
        self.sharepoint.upload_file(
            path=path,
            filename=filename,
            content=content,
            metadata={
                "manualHash": file.hash,
                "source": "ManualsAPI",
            },
        )
        logger.info("File uploaded successfully", extra={"file_name": filename, "path": path})
    
    def _download_file(self, url: str) -> bytes:
        logger.info("Downloading manual content", extra={"download_url": url})
        url = self._normalize_url(url)

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        return response.content


    def _normalize_url(self, url: str) -> str:
        # Fix double scheme like "https://https://example.com"
        if url.startswith("https://https://"):
            return url.replace("https://https://", "https://", 1)

        if url.startswith("http://http://"):
            return url.replace("http://http://", "http://", 1)

        return url

