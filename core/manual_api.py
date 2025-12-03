import logging
import requests
from dataclasses import dataclass
from typing import List, Optional


# ------------------------------------------------------------
# DATA MODEL
# ------------------------------------------------------------
@dataclass
class Manual:
    id: str
    name: str
    download_url: str
    created_at: str
    last_modified: str
    hash: str


# ------------------------------------------------------------
# API WRAPPER
# ------------------------------------------------------------
class ManualsAPI:
    """
    API-Klasse für den Zugriff auf das Manuals-Backend.
    Stellt Methoden bereit, um Manuals abzurufen und als
    Manual-Objekte zu modelieren.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Parameter:
            base_url: URL des Backend-Endpunkts
            api_key (optional): Falls Authentifizierung benötigt wird
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

        # Liste der geladenen Manuals wird hier gespeichert
        self.manuals: List[Manual] = []

    # --------------------------------------------------------
    # PRIVATE METHOD: BUILD HEADERS
    # --------------------------------------------------------
    def _headers(self):
        headers = {
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # --------------------------------------------------------
    # PUBLIC METHOD: LOAD MANUALS
    # --------------------------------------------------------
    def load_manuals(self) -> List[Manual]:
        """
        Sendet einen GET Request an den API-Endpunkt,
        parsed die JSON Antwort und modelliert die Manuals.
        """

        url = f"{self.base_url}/manuals"

        logging.info(f"Fetching manuals from: {url}")
        response = requests.get(url, headers=self._headers())

        if response.status_code != 200:
            logging.error(
                f"Failed to fetch manuals ({response.status_code}): {response.text}"
            )
            return []

        try:
            data = response.json()
        except Exception as e:
            logging.error(f"Error decoding JSON from manuals API: {e}")
            return []

        manuals_raw = data.get("manuals", [])  # z.B. { "manuals": [ ... ] }

        loaded_manuals = []
        for entry in manuals_raw:
            try:
                manual = Manual(
                    id=entry["id"],
                    name=entry["name"],
                    download_url=entry["download_url"],
                    created_at=entry["created_at"],
                    last_modified=entry["last_modified"],
                    hash=entry["hash"]
                )
                loaded_manuals.append(manual)
            except KeyError as e:
                logging.error(f"Missing key in manual entry: {e} – {entry}")

        self.manuals = loaded_manuals
        logging.info(f"Loaded {len(self.manuals)} manuals.")

        return self.manuals
    
    def download_file(self, download_url: str) -> Optional[bytes]:
        """
        Lädt die Datei von der gegebenen Download-URL herunter.

        Parameter:
            download_url: URL zum Herunterladen der Datei

        Rückgabe:
            Der Inhalt der Datei als Bytes, oder None bei Fehlern.
        """
        logging.info(f"Downloading file from: {download_url}")
        response = requests.get(download_url, headers=self._headers())

        if response.status_code != 200:
            logging.error(
                f"Failed to download file ({response.status_code}): {response.text}"
            )
            return None

        return response.content
