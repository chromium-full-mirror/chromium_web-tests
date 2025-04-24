import argparse
from datetime import datetime as dt
import logging
import re
import sys

from pathlib import Path
from runner import run_benchmark, run_cuj

from typing import List


def run(argv: List[str]) -> None:
  logging.getLogger().setLevel(logging.INFO)

  # TODO this will break if main.py is ever moved within web-tests
  web_tests_root: Path = Path(
      argv[0]).resolve().parent.parent.parent.parent.parent

  if not (web_tests_root / "cuj" / "crossbench").is_dir():
    logging.error(
        "web-tests does not have the expected layout. Did this file move?")
    return

  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--target",
      help="The IP or adb ID of the device to run against. For adb devices, use the format abd:<ID listed by 'adb devices'>",
      type=str,
      required=True,
  )
  parser.add_argument(
      "--secrets-config-file",
      help="The secrets config for the tests.",
      type=Path,
      default=None,
  )
  parser.add_argument(
      "--tests", help="Regex to match tests to run.", type=str, default=".*")
  parser.add_argument(
      "--playback",
      help="Directly passed to crossbench as the --playback flag for the loading benchmark.",
      type=str,
      default="1x",
  )
  parser.add_argument("--debug", action="store_true", default=False)
  parser.add_argument(
      "--variants",
      help="Regex to match test variants to run.",
      type=str,
      default=".*")
  args = parser.parse_args()

  target = args.target

  secrets_config_file = None
  if args.secrets_config_file:
    secrets_config_file: Path = args.secrets_config_file.resolve()

  tests_regex: re.Pattern = re.compile(args.tests)
  variants_regex: re.Pattern = re.compile(args.variants)

  playback_value: str = args.playback
  debug: bool = args.debug

  results_root: Path = web_tests_root / "cuj/crossbench/runner/results/"
  run_results_path: Path = results_root / dt.now().strftime("%Y-%m-%d_%H%M%S")
  run_results_path.mkdir(parents=True)

  latest_results: Path = results_root / "latest"
  latest_results.unlink(missing_ok=True)
  latest_results.symlink_to(run_results_path, target_is_directory=True)

  for benchmark_path in (web_tests_root /
                         "cuj/crossbench/benchmarks").iterdir():

    if not benchmark_path.is_dir() or not tests_regex.match(
        benchmark_path.name):
      continue

    try:
      run_benchmark(
          benchmark_path=benchmark_path,
          results_path=run_results_path,
          web_tests_path=web_tests_root,
          target=target,
          debug=debug,
      )
    except Exception as e:
      logging.error(f"Failed to run crossbench benchmark {benchmark_path}: {e}")

  for cuj_path in (web_tests_root / "cuj/crossbench/cujs").iterdir():

    if not cuj_path.is_dir() or not tests_regex.match(cuj_path.name):
      continue

    try:
      run_cuj(
          cuj_path=cuj_path,
          variants_regex=variants_regex,
          results_path=run_results_path,
          target=target,
          secrets_config_file=secrets_config_file,
          web_tests_path=web_tests_root,
          debug=debug,
          playback_value=playback_value,
      )
    except Exception as e:
      logging.error(f"Failed to run crossbench for test {cuj_path}: {e}")
      pass


if __name__ == "__main__":
  argv = sys.argv
  run(argv)
