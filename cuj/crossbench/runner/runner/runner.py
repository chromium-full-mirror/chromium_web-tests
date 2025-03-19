import re
import subprocess
import tempfile

from pathlib import Path
from uploader import upload_results


RESUTLS_PATH_RE = re.compile(
    r"RESULTS( \(maybe incomplete\/broken\))?: (.+\/crossbench\/results\/.+)"
)


def execute_crossbench(
    crossbench_path,
    page_config,
    probe_config,
    browser_config,
    secrets_config,
    additional_crossbench_args,
    verbose,
    playback_flag
):
    with tempfile.NamedTemporaryFile() as browser_config_file:
        browser_config_file.write(browser_config.encode("utf-8"))
        browser_config_file.seek(0)

        debug = ""

        if verbose:
            debug = "--debug"

        command = (
            f"poetry run cb loading --page-config {page_config}"
            f" --probe-config {probe_config} --browser-config {browser_config_file.name}"
            f" --secrets {secrets_config} --playback {playback_flag} {additional_crossbench_args} {debug}"
        )
        print(f"Invoking crossbench: '{command}'")
        proc = subprocess.run(
            command, shell=True, cwd=crossbench_path, capture_output=True
        )

        print("Crossbench stdout:")
        print(proc.stdout.decode("utf-8"))
        print("Crossbench stderr:")
        print(proc.stderr.decode("utf-8"))

        results_path = re.search(RESUTLS_PATH_RE, proc.stderr.decode("utf-8"))

        if results_path:
            results_path = results_path.group(2)

        if proc.returncode:
            return False, results_path

    return True, results_path


def is_page_config(filename):
    return filename.endswith("page-config.hjson")


def get_test_variant(page_config_file):
    name_sections = page_config_file.split(".")

    if len(name_sections) <= 2:
        return ""

    return name_sections[0]


def get_full_browser_config(browser_config_file, browser_flags_file):
    with open(browser_config_file, "r") as file:
        browser_config = file.read()

    # TODO Currently crossbench doesn't support templates for
    # browser config. When it does, replace this logic with a template.
    return browser_config.replace("$[FLAGS_DEFINITION]", str(browser_flags_file))


def run_test(
    device_id,
    test_name,
    crossbench_path,
    web_tests_path,
    runnable_config_dir,
    browser_config_file,
    secrets_config,
    verbose,
    do_upload,
    playback_flag
):
    for config_file in runnable_config_dir.glob("*"):
        filename = config_file.name

        if is_page_config(filename):

            test_variant = get_test_variant(filename)

            page_config = config_file

            probe_config = Path.joinpath(
                runnable_config_dir, f"{test_variant}.probe-config.hjson"
            )

            if not probe_config.is_file():
                probe_config = Path.joinpath(runnable_config_dir, "probe-config.hjson")

            browser_flags_file = Path.joinpath(
                runnable_config_dir, f"{test_variant}.browser-flags.hjson"
            )

            if not browser_flags_file.is_file():
                browser_flags_file = Path.joinpath(
                    runnable_config_dir, "browser-flags.hjson"
                )

            additional_crossbench_args_file = Path.joinpath(
                runnable_config_dir, f"{test_variant}.cb-args"
            )

            if not additional_crossbench_args_file.is_file():
                additional_crossbench_args_file = Path.joinpath(
                    runnable_config_dir, "cb-args"
                )

            try:
                additional_crossbench_args = additional_crossbench_args_file.read_text()
            except Exception:
                additional_crossbench_args = ""

            additional_crossbench_args = additional_crossbench_args.replace(
                "$[WEB_TESTS]", str(web_tests_path)
            )

            success, results_path = execute_crossbench(
                crossbench_path=crossbench_path,
                page_config=page_config,
                probe_config=probe_config,
                browser_config=get_full_browser_config(
                    browser_config_file, browser_flags_file
                ),
                secrets_config=secrets_config,
                additional_crossbench_args=additional_crossbench_args,
                verbose=verbose,
                playback_flag=playback_flag
            )

            full_test_name = test_name

            if test_variant:
                full_test_name = f"{test_name}_{test_variant}"

            if do_upload:
                try:
                    upload_results(results_path, device_id, full_test_name, success)
                except Exception as e:
                    print(f"Failed to upload results for test {full_test_name}: {e}")
