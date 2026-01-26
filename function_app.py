from sharepoint.sharepoint_api import SharePointClient
from manuals.manual_api import ManualsAPI
from manuals.service import ManualsService
import azure.functions as func
import logging
import os
logger = logging.getLogger(__name__)

app = func.FunctionApp()

@app.timer_trigger(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=False)
def FetchFromAPIUploadToSharepoint(myTimer: func.TimerRequest) -> None:

    logger.info('Started function "FetchFromAPIUploadToSharepoint"...')

    # VARIABLES
    manual_base_url = os.getenv("MANUALS_API_BASE_URL")
    manual_api_key = os.getenv("MANUALS_API_KEY")
    sharepoint_site_id = os.getenv("SHAREPOINT_SITE_ID")
    sharepoint_drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    # SETUP SERVICES
    manuals_api = ManualsAPI(base_url = manual_base_url, api_key = manual_api_key)
    sharepoint_api = SharePointClient(tenant_id, client_id, client_secret, sharepoint_site_id, sharepoint_drive_id)
    service = ManualsService(manuals_api, sharepoint_api)

    # RUN SYNC
    service.sync_manuals(max_files=3)
        
    logger.info('Finished function "FetchFromAPIUploadToSharepoint".')