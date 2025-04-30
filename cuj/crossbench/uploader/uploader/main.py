# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import csv
import json
import logging
import os
import re
import sys

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_MAP_ID = "1GcNTMRuPRvy5mbEY51Ew4rhJmyvOQKHn_YYCjs-J6hs"
SPREADSHEET_MAP_RANGE = "sheet_map!A1:B"
RESULTS_CLIENT_SECRET = Path.home() / "results_client_secret.json"
TOKEN_PATH = Path.home() / "token.json"


def create_new_sheet(sheet_api, title: str):
  spreadsheet = {"properties": {"title": title}}
  spreadsheet = sheet_api.create(
      body=spreadsheet, fields="spreadsheetId").execute()
  return spreadsheet.get("spreadsheetId")


def get_sheet_id_for_test(sheet_api, test_name: str):
  result = (
      sheet_api.values().get(
          spreadsheetId=SPREADSHEET_MAP_ID,
          range=SPREADSHEET_MAP_RANGE).execute())

  rows = result.get("values", [])

  for row in rows:
    if row[0] == test_name:
      return row[1]

  new_sheet_id = create_new_sheet(sheet_api, f"{test_name}_metrics")

  new_row = [test_name, new_sheet_id]

  sheet_api.values().append(
      spreadsheetId=SPREADSHEET_MAP_ID,
      range=SPREADSHEET_MAP_RANGE,
      body={
          "values": [new_row]
      },
      valueInputOption="USER_ENTERED",
  ).execute()

  return new_sheet_id


def get_sheet_api():

  creds = None

  if TOKEN_PATH.is_file():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(RESULTS_CLIENT_SECRET,
                                                       SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    TOKEN_PATH.write_text(creds.to_json())

  sheet_api = None

  try:
    service = build("sheets", "v4", credentials=creds)
    sheet_api = service.spreadsheets()
  except HttpError as err:
    logging.error("Failed to initialize sheets api: %s", err)

  if not sheet_api:
    logging.error("Failed to connect to sheets.")
    sys.exit()

  return sheet_api


def get_device_info(results_path):
  with open(
      results_path / "first_run/cb.system.details.json", encoding="utf-8") as f:
    system_details = json.load(f)

  sys_info_columns = []

  sys_info_columns.append(system_details["os"]["release"])
  sys_info_columns.append(system_details["CPU"]["info"])

  if system_details.get("ChromeOS"):
    sys_info_columns.append(
        system_details["ChromeOS"]["CHROMEOS_RELEASE_DESCRIPTION"])
  if system_details.get("Android"):
    sys_info_columns.append(
        system_details["Android"]["ro.vendor.build.fingerprint"])
    sys_info_columns.append(system_details["Android"]["ro.vendor.build.id"])
  return sys_info_columns


def upload_rows(metric_name, sheet_api, test_name, rows):
  spreasheet_id = get_sheet_id_for_test(sheet_api, test_name)

  full_metric_name = f"{test_name}_{metric_name}"

  logging.info("Processing metric: %s", full_metric_name)

  body = {
      "requests": [{
          "addSheet": {
              "properties": {
                  "title": full_metric_name
              }
          }
      }]
  }

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

  with open(metric_csv, "r", encoding="utf-8") as csv_file:
    reader = csv.reader(csv_file)

    for row in reader:
      row.extend(run_info_columns)
      metric_data.append(row)

  upload_rows(metric_name, sheet_api, test_name, metric_data)


def upload_success(sheet_api, test_name, success, run_info):
  upload_rows("success", sheet_api, test_name,
              [["SUCCESS"], [success] + run_info])


def has_error(test_path):
  cb_results_json = test_path / "first_run" / "cb.results.json"

  try:
    with cb_results_json.open() as f:
      cb_results = json.load(f)

    return bool(cb_results["errors"])
  except FileNotFoundError:
    return True


def are_benchmark_results(test_path, test_name):
  benchmark_results = test_path / f"{test_name}.json"
  return benchmark_results.is_file()


def upload_benchmark_results(test_path, test_name, sheet_api, run_info_columns):
  results_json = {}

  results_json_path = test_path / f"{test_name}.json"

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


def upload_cuj_results(test_path, test_name, sheet_api, run_info_columns):
  trace_processor_path = test_path / "trace_processor"

  for metric_file in trace_processor_path.glob("*.csv"):
    upload_csv(
        metric_file.stem,
        trace_processor_path / metric_file,
        sheet_api,
        test_name,
        run_info_columns,
    )


def upload(args):
  logging.getLogger().setLevel(logging.INFO)

  if os.getlogin() != "crossbench-lab":
    logging.error(
        "This script should only be run on the crossbench lab in TOK. "
        "By running this you agree to fix anything that gets messed up "
        "in the google sheets dashboard.")
    bypass_input = input("To continue, type: CONTINUE\n")
    if bypass_input != "CONTINUE":
      sys.exit()

  if len(args) != 2:
    logging.error("Usage: main.py <path to results from runner>")
    return

  # resolve() is necessary incase a symlink
  # (such as results/latest) and/or a relative path is passed.
  # After resolve() the results_dir will be used as a test run ID
  # for uploading.
  results_dir = Path(args[1]).resolve()

  if not re.match(r"\d{4}-\d{2}-\d{2}_\d{6}", results_dir.name):
    logging.error(
        "Results dir name is not the expected format. Must be YYYY-MM-DD_HHMMSS"
    )
    return

  sheet_api = get_sheet_api()

  for test_path in results_dir.iterdir():
    test_name = test_path.name

    run_info_columns = get_device_info(test_path)
    run_info_columns.append(f"{test_path.parent.name}_{test_path.name}")

    if has_error(test_path):
      upload_success(sheet_api, test_name, False, run_info_columns)
      continue

    upload_success(sheet_api, test_name, True, run_info_columns)

    if are_benchmark_results(test_path, test_name):
      upload_benchmark_results(test_path, test_name, sheet_api,
                               run_info_columns)
    else:
      upload_cuj_results(test_path, test_name, sheet_api, run_info_columns)


if __name__ == "__main__":
  argv = sys.argv
  upload(argv)
