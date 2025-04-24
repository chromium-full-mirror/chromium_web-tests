import logging
import re
import shlex
import tempfile

from pathlib import Path
from typing import List, Optional

from crossbench.cli.cli import CrossBenchCLI


def execute_crossbench(
    test_name: str,
    probe_config_file: Path,
    browser_config: str,
    additional_crossbench_args: str,
    debug: bool,
    results_path: Path,
    playback_value: Optional[str] = None,
    page_config_file: Optional[Path] = None,
    secrets_config_file: Optional[Path] = None,
) -> None:
  with tempfile.NamedTemporaryFile() as browser_config_file:
    browser_config_file.write(browser_config.encode("utf-8"))
    browser_config_file.seek(0)

    crossbench_args: List[str] = []

    crossbench_args.append(test_name)

    crossbench_args.append("--out-dir")
    crossbench_args.append(str(results_path))

    if page_config_file:
      crossbench_args.append("--page-config")
      crossbench_args.append(str(page_config_file))

    crossbench_args.append("--probe-config")
    crossbench_args.append(str(probe_config_file))

    crossbench_args.append("--browser-config")
    crossbench_args.append(str(browser_config_file.name))

    if secrets_config_file:
      crossbench_args.append("--secrets")
      crossbench_args.append(str(secrets_config_file))

    if playback_value:
      crossbench_args.append("--playback")
      crossbench_args.append(playback_value)

    if debug:
      crossbench_args.append("--debug")

    for arg in shlex.split(additional_crossbench_args):
      crossbench_args.append(arg)

    logging.info(f"Running crossbench with args: {crossbench_args}")

    CrossBenchCLI().run(crossbench_args)


def is_page_config(filename: str) -> bool:
  return filename.endswith("page-config.hjson")


def get_test_variant(page_config_filename: str) -> str:
  name_sections: List[str] = page_config_filename.split(".")

  if len(name_sections) <= 2:
    return ""

  return name_sections[0]


def get_full_browser_config(browser_config_file: Path,
                            browser_flags_file: Path) -> str:
  # TODO Currently crossbench doesn't support templates for
  # browser config. When it does, replace this logic with a template.
  return browser_config_file.read_text().replace("$[FLAGS_DEFINITION]",
                                                 str(browser_flags_file))


def get_additional_crossbench_args(test_path: Path,
                                   web_tests_path: Path,
                                   test_variant: str = "") -> str:
  additional_crossbench_args_file: Path = test_path / f"{test_variant}.cb-args"

  if not additional_crossbench_args_file.is_file():
    additional_crossbench_args_file = test_path / "cb-args"

  additional_crossbench_args: str = ""
  if additional_crossbench_args_file.is_file():
    additional_crossbench_args = additional_crossbench_args_file.read_text()

  return additional_crossbench_args.replace("$[WEB_TESTS]", str(web_tests_path))


def run_benchmark(
    benchmark_path: Path,
    results_path: Path,
    web_tests_path: Path,
    browser_config_file: Path,
    debug: bool,
) -> None:
  benchmark_name: str = benchmark_path.name
  benchmark_results_path: Path = results_path / benchmark_name
  probe_config_file: Path = benchmark_path / "probe-config.hjson"
  browser_flags_file: Path = benchmark_path / "browser-flags.hjson"

  logging.info(f"Executing crossbench for CUJ: {benchmark_name}")

  execute_crossbench(
      test_name=benchmark_name,
      probe_config_file=probe_config_file,
      browser_config=get_full_browser_config(browser_config_file,
                                             browser_flags_file),
      additional_crossbench_args=get_additional_crossbench_args(
          benchmark_path, web_tests_path),
      debug=debug,
      results_path=benchmark_results_path,
  )


def run_cuj(
    cuj_path: Path,
    variants_regex: re.Pattern,
    results_path: Path,
    browser_config_file: Path,
    secrets_config_file: Path,
    web_tests_path: Path,
    debug: bool,
    playback_value: str,
) -> None:
  cuj_name: str = cuj_path.name

  for config_file in cuj_path.iterdir():
    filename: str = config_file.name

    if is_page_config(filename):

      cuj_variant: str = get_test_variant(filename)

      if not variants_regex.match(cuj_variant):
        continue

      full_cuj_name = cuj_name

      if cuj_variant:
        full_cuj_name = full_cuj_name + f"_{cuj_variant}"

      variant_results_path: Path = results_path / full_cuj_name

      page_config_file: Path = config_file

      probe_config_file: Path = cuj_path / f"{cuj_variant}.probe-config.hjson"

      if not probe_config_file.is_file():
        probe_config_file = cuj_path / "probe-config.hjson"

      browser_flags_file: Path = cuj_path / f"{cuj_variant}.browser-flags.hjson"

      if not browser_flags_file.is_file():
        browser_flags_file = cuj_path / "browser-flags.hjson"

      logging.info(f"Executing crossbench for CUJ: {full_cuj_name}")

      execute_crossbench(
          test_name="loading",
          probe_config_file=probe_config_file,
          browser_config=get_full_browser_config(browser_config_file,
                                                 browser_flags_file),
          additional_crossbench_args=get_additional_crossbench_args(
              cuj_path, web_tests_path, cuj_variant),
          debug=debug,
          results_path=variant_results_path,
          playback_value=playback_value,
          page_config_file=page_config_file,
          secrets_config_file=secrets_config_file,
      )
