import argparse
import os
import sys

from pathlib import Path
from runner import run_test


def run_and_upload(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device-id",
        help="The id of the device on which tests are run (i.e. asset tag).",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--browser-config-file",
        help="The browser config for the target.",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--secrets-config-file",
        help="The secrets config for the tests.",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--crossbench", help="The path to crossbench.", type=Path, required=True
    )
    parser.add_argument(
        "--web-tests", help="The path to web tests.", type=Path, required=True
    )
    parser.add_argument(
        "--upload",
        help="Upload results.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--tests", help="Glob to match tests to run.", type=str, default="*"
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    device_id = args.device_id
    browser_config_file = args.browser_config_file.resolve()
    secrets_config_file = args.secrets_config_file.resolve()
    crossbench = args.crossbench.resolve()
    web_tests = args.web_tests.resolve()
    do_upload = args.upload
    tests_glob = args.tests
    verbose = args.verbose

    for test in (web_tests / "cuj/crossbench/runnable-configs").glob(tests_glob):

        if not test.is_dir():
            continue

        test_name = os.path.basename(test)

        try:
            run_test(
                device_id,
                test_name,
                crossbench,
                web_tests,
                test,
                browser_config_file,
                secrets_config_file,
                verbose,
                do_upload,
            )
        except Exception as e:
            print(f"Failed to run crossbench for test {test_name}: {e}")
            pass


if __name__ == "__main__":
    argv = sys.argv
    run_and_upload(argv)
