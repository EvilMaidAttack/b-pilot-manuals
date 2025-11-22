from core.graph_api import GraphAPI
import azure.functions as func
import logging
import os

app = func.FunctionApp()

@app.timer_trigger(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=False)
def FetchFromAPIUploadToSharepoint(myTimer: func.TimerRequest) -> None:

    logging.info('Started function "FetchFromAPIUploadToSharepoint"...')

    graph = GraphAPI()

    site_id = os.getenv("SHAREPOINT_SITE_ID")
    drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
    folder_path = "Manuals"

    data = graph.list_folder_items(
        site_id=site_id,
        drive_id=drive_id,
        folder_path=folder_path
    )

    if not data:
        logging.error("No data received from Graph API.")
        return

    logging.info(f"Files found in '{folder_path}' folder:")
    for item in data.get("value", []):
        logging.info(f"File Name: {item['name']}, File ID: {item['id']}")
