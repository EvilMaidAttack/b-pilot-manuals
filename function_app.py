from core.graph_api import GraphAPI
from core.manual_api import ManualsAPI, Manual
import azure.functions as func
import logging
import os

app = func.FunctionApp()

@app.timer_trigger(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=False)
def FetchFromAPIUploadToSharepoint(myTimer: func.TimerRequest) -> None:

    logging.info('Started function "FetchFromAPIUploadToSharepoint"...')

    manuals_api = ManualsAPI(base_url=os.getenv("MANUALS_API_BASE_URL"), api_key=os.getenv("MANUALS_API_KEY"))
    manuals = manuals_api.load_manuals()

    graph = GraphAPI()

    site_id = os.getenv("SHAREPOINT_SITE_ID")
    drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
    folder_path = "Manuals"

    # sharepoint_items = graph.list_folder_items(site_id, drive_id, folder_path)
    # TODO: Use the hash to check if the file already exists and is up to date
    # TODO: Store the hashes of uploaded files in tinydb or similar lightweight DB
    for manual in manuals:
        download_url = manual.download_url
        file_name = manual.file_name
        file_content = manuals_api.download_file(download_url)
        graph.upload_file(site_id, drive_id, folder_path, file_name, file_content)
        logging.info(f'Uploaded {file_name} to SharePoint')
