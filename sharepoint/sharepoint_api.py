import os
import logging
import requests
from urllib.parse import unquote
from msal import ConfidentialClientApplication
logger = logging.getLogger(__name__)

class SharePointClient:
    def __init__(self, tenant: str, client_id: str, client_secret: str, site_id: str, drive_id: str):
        self.tenant = tenant
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_id = site_id
        self.drive_id = drive_id

        if not self.tenant or not self.client_id or not self.client_secret:
            raise ValueError(
                "Environment variables TENANT_ID, CLIENT_ID, CLIENT_SECRET are required."
            )
        
        if not self.site_id or not self.drive_id:
            raise ValueError(
                "Site ID and Drive ID are required for SharePoint operations."
            )

        self._app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant}",
            client_credential=self.client_secret
        )

        self._token = None
    
    def file_exists(self, path, filename) -> bool:
        logger.debug(f"Checking if file exists", extra={"path": path, "file_name": filename})
        url = (
            f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}"
            f"/root:/{path}/{filename}"
        )

        response = requests.get(url, headers=self._headers())

        if response.status_code == 200:
            logger.info(f"File exists in SharePoint", extra={"path": path, "file_name": filename})
            return True
        if response.status_code == 404:
            logger.info(f"File does not exist in SharePoint", extra={"path": path, "file_name": filename})
            return False
        
        logger.error(f"Error checking file existence", extra={"status_code": response.status_code, "response": response.text})
        
        response.raise_for_status()
        return False
    

    def file_exists_with_same_hash(self, path: str, filename: str, expected_hash: str) -> bool:
        logger.debug(
            "Checking if file exists with matching hash",
            extra={"path": path, "file_name": filename},
        )


        item_id = self._get_item_id_by_path(path, filename)

        if not item_id:
            logger.info("File does not exist in SharePoint")
            return False

        
        fields = self._get_item_fields(item_id)

        stored_hash = fields.get("manualHash")
        logger.info(f"Comparing: expected = {expected_hash}, stored = {stored_hash}")

        if stored_hash == expected_hash:
            logger.info(
                "File exists and hash matches, skipping upload",
                extra={"file_name": filename},
            )
            return True

        logger.info(
            "File exists but hash differs, will re-upload",
            extra={
                "file_name": filename,
                "stored_hash": stored_hash,
                "expected_hash": expected_hash,
            },
        )
        return False



    def upload_file(self, path: str, filename: str, content: bytes, metadata: dict | None = None):
        self._ensure_folder(path)

        upload_url = (
            f"https://graph.microsoft.com/v1.0/"
            f"drives/{self.drive_id}/root:/{path}/{filename}:/content"
        )

        response = requests.put(
            upload_url,
            headers=self._headers(content_type="application/octet-stream"),
            data=content,
        )
        response.raise_for_status()

        if metadata:
            item_id = response.json().get("id")
            if item_id:
                self._set_metadata(item_id, metadata)


    def _obtain_token(self):
        """Obtains an access token using client credentials flow."""
        if self._token:
            return self._token

        try:
            result = self._app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
        except Exception as e:
            logging.error(f"Error acquiring Graph token: {e}")
            return None

        if "access_token" not in result:
            logging.error(f"Failed to acquire access token: {result}")
            return None

        self._token = result["access_token"]
        return self._token
    

    def _headers(self, content_type: str = "application/json") -> dict:
        return {
            "Authorization": f"Bearer {self._obtain_token()}",
            "Content-Type": content_type,
        }
    
    def _set_metadata(self, item_id: str, metadata: dict):
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{item_id}/listItem/fields"

        response = requests.patch(
            url,
            headers=self._headers(),
            json=metadata,
        )
        logger.debug(f"Set metadata response: {response.status_code} - {response.text}")
    

    def _ensure_folder(self, path: str):
        logger.info(f"Ensuring folder structure", extra={"path": path})
        parts = path.strip("/").split("/")
        current = ""

        for part in parts:
            current = f"{current}/{part}" if current else part
            url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{current}"

            response = requests.get(url, headers=self._headers())
            if response.status_code == 404:
                logger.info(f"Creating folder", extra={"folder": current})
                parent = "/".join(current.split("/")[:-1])
                create_url = (
                    f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{parent}:/children"
                    if parent
                    else f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root/children"
                )

                create_response = requests.post(
                    create_url,
                    headers=self._headers(),
                    json={
                        "name": part,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "fail",
                    },
                )
                create_response.raise_for_status()

    def _normalize_path(self, path: str, filename: str) -> tuple[str, str]:
        return unquote(path), unquote(filename)
    

    def _get_item_id_by_path(self, path: str, filename: str) -> str | None:
        raw_path, raw_filename = self._normalize_path(path, filename)

        url = (
            f"https://graph.microsoft.com/v1.0/"
            f"drives/{self.drive_id}/root:/{raw_path}/{raw_filename}"
        )

        response = requests.get(url, headers=self._headers())
        logger.debug(f"Get item by path response: {response.status_code} - {response.text}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json().get("id")
    
    def _get_item_fields(self, item_id: str) -> dict:
        url = (
            f"https://graph.microsoft.com/v1.0/"
            f"drives/{self.drive_id}/items/{item_id}/listItem/fields"
        )

        response = requests.get(url, headers=self._headers())
        logger.debug(f"Get item fields response: {response.status_code} - {response.text}")

        if response.status_code == 404:
            return {}

        response.raise_for_status()
        return response.json()



