import csv
import json
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_MAP_ID = "1GcNTMRuPRvy5mbEY51Ew4rhJmyvOQKHn_YYCjs-J6hs"
SPREADSHEET_MAP_RANGE = "sheet_map!A1:B"
RESULTS_CLIENT_SECRET = Path.joinpath(Path.home(), "results_client_secret.json")
TOKEN_PATH = Path.joinpath(Path.home(), "token.json")


def create_new_sheet(sheet_api, title):
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = sheet_api.create(body=spreadsheet, fields="spreadsheetId").execute()
    return spreadsheet.get("spreadsheetId")


def get_sheet_id_for_test(sheet_api, test_name):
    result = (
        sheet_api.values()
        .get(spreadsheetId=SPREADSHEET_MAP_ID, range=SPREADSHEET_MAP_RANGE)
        .execute()
    )

    rows = result.get("values", [])

    for row in rows:
        if row[0] == test_name:
            return row[1]

    new_sheet_id = create_new_sheet(sheet_api, f"{test_name}_metrics")

    new_row = [test_name, new_sheet_id]

    sheet_api.values().append(
        spreadsheetId=SPREADSHEET_MAP_ID,
        range=SPREADSHEET_MAP_RANGE,
        body={"values": [new_row]},
        valueInputOption="USER_ENTERED",
    ).execute()

    return new_sheet_id


def get_sheet_api():
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                RESULTS_CLIENT_SECRET, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    sheet_api = None

    try:
        service = build("sheets", "v4", credentials=creds)
        sheet_api = service.spreadsheets()
    except HttpError as err:
        print(err)

    if not sheet_api:
        print("Failed to connect to sheets.")
        exit()

    return sheet_api


def get_device_info(results_path):
    with open(Path(results_path) / "first_run/cb.system.details.json") as f:
        system_details = json.load(f)

    sys_info_columns = []

    sys_info_columns.append(system_details["os"]["release"])
    sys_info_columns.append(system_details["CPU"]["info"])

    if system_details.get("ChromeOS"):
        sys_info_columns.append(
            system_details["ChromeOS"]["CHROMEOS_RELEASE_DESCRIPTION"]
        )
    if system_details.get("Android"):
        sys_info_columns.append(
            system_details["Android"]["ro.vendor.build.fingerprint"]
        )
        sys_info_columns.append(system_details["Android"]["ro.vendor.build.id"])
    return sys_info_columns


def upload_rows(metric_name, sheet_api, test_name, rows):
    spreasheet_id = get_sheet_id_for_test(sheet_api, test_name)

    full_metric_name = f"{test_name}_{metric_name}"

    print(f"Processing metric: {full_metric_name}")

    body = {"requests": [{"addSheet": {"properties": {"title": full_metric_name}}}]}

    new_sheet = True

    try:
        sheet_api.batchUpdate(spreadsheetId=spreasheet_id, body=body).execute()
    except HttpError as e:
        if "A sheet with the name" in str(e):
            new_sheet = False
        else:
            raise

    data_range = f"{full_metric_name}!A1:E"

    # Only add the column headers if it is a new sheet
    if not new_sheet:
        rows.pop(0)

    body = {"values": rows}

    sheet_api.values().append(
        spreadsheetId=spreasheet_id,
        range=data_range,
        body=body,
        valueInputOption="USER_ENTERED",
    ).execute()


def upload_csv(metric_name, metric_csv, sheet_api, test_name, run_info_columns):
    metric_data = []

    with open(metric_csv, "r") as csv_file:
        reader = csv.reader(csv_file)

        for row in reader:
            row.extend(run_info_columns)
            metric_data.append(row)

    upload_rows(metric_name, sheet_api, test_name, metric_data)


def upload_success(sheet_api, test_name, success, run_info):
    upload_rows("success", sheet_api, test_name, [["SUCCESS"], [success] + run_info])


def upload_benchmark_results(results_path, device_id, test_name, success):
    run_info_columns = [device_id]
    run_info_columns.extend(get_device_info(results_path))
    run_info_columns.append(os.path.basename(results_path))

    sheet_api = get_sheet_api()

    upload_success(sheet_api, test_name, success, run_info_columns)

    results_json = {}

    if results_path:
        results_json_path = Path(results_path) / f"{test_name}.json"

        with results_json_path.open() as f:
            results_json = json.load(f)

    for _, run in results_json.items():
        column_headers = []
        row = []

        for datapoint_name, datapoint in run["data"].items():
            column_headers.append(datapoint_name)
            # No support for multiple values yet
            row.append(datapoint["values"][0])

        row.extend(run_info_columns)

        upload_rows("scores", sheet_api, test_name, [column_headers, row])


def upload_cuj_results(results_path, device_id, test_name, success):
    run_info_columns = [device_id]
    run_info_columns.extend(get_device_info(results_path))
    run_info_columns.append(os.path.basename(results_path))

    sheet_api = get_sheet_api()

    upload_success(sheet_api, test_name, success, run_info_columns)

    if results_path:
        trace_processor_path = Path.joinpath(Path(results_path), "trace_processor")

        for metric_file in trace_processor_path.glob("*.csv"):
            upload_csv(
                metric_file.stem,
                Path.joinpath(trace_processor_path, metric_file),
                sheet_api,
                test_name,
                run_info_columns,
            )
