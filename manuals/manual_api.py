import logging
from .models import ManualsResponse
import httpx

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# API WRAPPER
# ------------------------------------------------------------
class ManualsAPI:
    """
    Wrapper for the Manuals backend API.
    Responsible only for:
    - HTTP communication
    - Parsing responses into Pydantic models
    """

    def __init__(self, base_url: str, api_key: str = None, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    # --------------------------------------------------------
    # PRIVATE METHODS
    # --------------------------------------------------------
    def _headers(self):
        headers = {
            "Accept": "application/json"
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    # --------------------------------------------------------
    # PUBLIC METHODS
    # --------------------------------------------------------
    def fetch_manuals(self) -> ManualsResponse:
        """
        Fetch manuals from the backend and return a validated Pydantic model.
        """
        logger.info(f"Fetching manuals from backend", extra={"url": self.base_url})
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                self.base_url,
                headers=self._headers(),
            )
            response.raise_for_status()
        
        manuals = ManualsResponse.model_validate(response.json())
        
        logger.info(
            "Manuals fetched successfully",
            extra={
                "documents_count": len(manuals.documents),
                "generated_at": manuals.last_generated_at.isoformat(),
            },
        )

        return manuals
    
 