import os
import logging
import requests
from msal import ConfidentialClientApplication


class GraphAPI:
    """
    Wrapper-Klasse für den Zugriff auf die Microsoft Graph API.
    Kapselt Token Handling und SharePoint-spezifische Requests.
    """

    def __init__(self):
        self.tenant = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")

        if not self.tenant or not self.client_id or not self.client_secret:
            raise ValueError(
                "Environment variables TENANT_ID, CLIENT_ID, CLIENT_SECRET are required."
            )

        self._app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant}",
            client_credential=self.client_secret
        )

        self._token = None


    # -----------------------------------------------
    # TOKEN HANDLING
    # -----------------------------------------------
    def get_token(self):
        """Fordert einen Access Token an (Client Credentials Flow)."""
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


    # -----------------------------------------------
    # GENERIC GRAPH GET REQUEST
    # -----------------------------------------------
    def _get(self, url):
        """Führt einen GET Request an die Graph API aus."""
        token = self.get_token()
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logging.error(
                f"Graph API GET failed ({response.status_code}): {response.text}"
            )
            return None

        return response.json()


    # -----------------------------------------------
    # SHAREPOINT SPECIFIC METHODS
    # -----------------------------------------------
    def list_folder_items(self, site_id, drive_id, folder_path):
        """
        Listet alle Elemente in einem SharePoint Ordner auf.
        Beispiel folder_path: 'Manuals'
        """
        url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}"
            f"/root:/{folder_path}:/children"
        )

        logging.info(f"Fetching SharePoint folder: {folder_path}")
        return self._get(url)
    
    def upload_file(self, site_id, drive_id, folder_path, file_content, filename):
        """
        Lädt eine Datei in einen SharePoint-Ordner hoch.

        Parameter:
            site_id: ID der SharePoint Site
            drive_id: ID der Dokumentenbibliothek
            folder_path: Ordner in SharePoint, z.B. 'Manuals'
            file_content: Bytes der Datei (file.read())
            filename: Name der Datei inklusive Endung
        """

        url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}"
            f"/root:/{folder_path}/{filename}:/content"
        )

        token = self.get_token()
        if not token:
            logging.error("No Graph API token available.")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }

        logging.info(f"Uploading file '{filename}' to SharePoint folder '{folder_path}'")

        response = requests.put(url, headers=headers, data=file_content)

        if response.status_code not in (200, 201):
            logging.error(
                f"File upload failed ({response.status_code}): {response.text}"
            )
            return None

        logging.info(f"Upload succeeded: {filename}")
        return response.json()
