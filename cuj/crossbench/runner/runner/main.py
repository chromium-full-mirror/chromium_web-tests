import argparse
import os
import sys

from pathlib import Path
from runner import run_benchmark, run_cuj


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
        default=None,
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
    parser.add_argument(
        "--playback",
        help="Directly passed to crossbench as the --playback flag for the loading benchmark.",
        type=str,
        default="1x",
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--variants", type=str, default="*")
    args = parser.parse_args()

    device_id = args.device_id
    browser_config_file = args.browser_config_file.resolve()
    secrets_config_file = None
    if args.secrets_config_file:
        secrets_config_file = args.secrets_config_file.resolve()
    crossbench = args.crossbench.resolve()
    web_tests = args.web_tests.resolve()
    do_upload = args.upload
    tests_glob = args.tests
    variants_glob = args.variants
    playback_value = args.playback
    verbose = args.verbose

    for benchmark_dir in (web_tests / "cuj/crossbench/benchmarks").glob(tests_glob):

        if not benchmark_dir.is_dir():
            continue

        benchmark = os.path.basename(benchmark_dir)

        try:
            run_benchmark(
                device_id,
                benchmark,
                crossbench,
                web_tests,
                benchmark_dir,
                browser_config_file,
                verbose,
                do_upload,
            )
        except Exception as e:
            print(f"Failed to run crossbench benchmark {benchmark}: {e}")

    for test_dir in (web_tests / "cuj/crossbench/cujs").glob(tests_glob):

        if not test_dir.is_dir():
            continue

        test_name = os.path.basename(test_dir)

        try:
            run_cuj(
                device_id,
                test_name,
                crossbench,
                web_tests,
                test_dir,
                browser_config_file,
                secrets_config_file,
                verbose,
                do_upload,
                playback_value,
                variants_glob,
            )
        except Exception as e:
            print(f"Failed to run crossbench for test {test_name}: {e}")
            pass


if __name__ == "__main__":
    argv = sys.argv
    run_and_upload(argv)
