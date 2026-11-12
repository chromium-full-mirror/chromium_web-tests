# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import argparse
import dataclasses
import enum
import logging
from concurrent.futures import Future
from pathlib import Path
from typing import Any, Self

from crossbench.config import ConfigEnum, ConfigObject, ConfigParser
from crossbench.parse import NumberParser, ObjectParser
from rich.spinner import Spinner
from typing_extensions import override


def parse_inline_page_config(value: object) -> dict[str, Any]:
  if isinstance(value, str):
    value = ObjectParser.inline_hjson(value)
  return dict(ObjectParser.non_empty_dict(value, "page_config"))


class TestVariantAction(argparse.Action):

  def __call__(self, parser, namespace, values, option_string=None):
    if "ordered_tests_variants" not in vars(namespace):
      namespace.ordered_tests_variants = []
    namespace.ordered_tests_variants.append((option_string, values))


@enum.unique
class TargetPlatform(ConfigEnum):
  ANDROID = ("adb", "Android via adb")
  CHROME_OS = ("cros", "ChromeOS via ssh")
  LOCAL = ("local", "local browser")
  MAC = ("mac", "macOS")


@dataclasses.dataclass(frozen=True)
class Test:
  name: str
  variant: str
  path: Path
  probe_config: Path | None
  browser_flags: Path
  extensions: Path | None
  crossbench_args: str
  page_config: Path | None = None

  @property
  def full_name(self) -> str:
    if self.variant:
      return f"{self.name}_{self.variant}"

    return self.name

  @property
  def crossbench_command(self) -> str:
    return self.name


@dataclasses.dataclass(frozen=True)
class Benchmark(Test):
  pass


@dataclasses.dataclass(frozen=True)
class Cuj(Test):
  page_config: Path | None = None

  @property
  @override
  def crossbench_command(self) -> str:
    return "loading"


@dataclasses.dataclass(frozen=True)
class TestInvocationConfig:
  test: Test
  min_successes: int | None = None
  max_consecutive_failures: int | None = None
  playback: str | None = None
  setup_delay: str | None = None
  startup_delay: str | None = None
  stories: str | None = None
  page_config: dict[str, Any] | None = None
  record_video: bool = False
  bypass_oobe: bool = True
  clear_browser_cache: bool = True


@dataclasses.dataclass
class TestInvocationState:
  config: TestInvocationConfig

  # Runtime state for UI tracking
  successes: int = 0
  failures: int = 0
  total_failures: int = 0
  spinner: Spinner = dataclasses.field(default_factory=lambda: Spinner("dots"))
  invocation_result: Future[bool] = dataclasses.field(default_factory=Future)

  def to_json(self) -> dict[str, Any]:
    return {
        "test": self.config.test.full_name,
        "passes": self.successes,
        "failures": self.total_failures
    }


@dataclasses.dataclass(frozen=True)
class TestGroup(ConfigObject):
  filter_regex: str = ".*"
  variants_filter_regex: str = ".*"
  min_successes: int | None = None
  max_consecutive_failures: int | None = None
  playback: str | None = None
  setup_delay: str | None = None
  startup_delay: str | None = None
  stories: str | None = None
  page_config: dict[str, Any] | None = None
  record_video: bool = False
  bypass_oobe: bool = True
  clear_browser_cache: bool = True

  @classmethod
  @override
  def config_parser(cls) -> ConfigParser[Self]:
    parser = ConfigParser(cls)
    parser.add_argument(
        "filter_regex", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument(
        "variants_filter_regex", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument(
        "min_successes", type=NumberParser.positive_int, required=False)
    parser.add_argument(
        "max_consecutive_failures",
        type=NumberParser.positive_int,
        required=False,
        default=5)
    parser.add_argument(
        "playback", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "setup_delay", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "startup_delay", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "stories", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "page_config", type=parse_inline_page_config, required=False)
    parser.add_argument(
        "record_video",
        aliases=("screen_recording",),
        type=ObjectParser.bool,
        required=False,
        default=False)
    parser.add_argument(
        "bypass_oobe", type=ObjectParser.bool, required=False, default=True)
    parser.add_argument(
        "clear_browser_cache",
        aliases=("clear_cache",),
        type=ObjectParser.bool,
        required=False,
        default=True)
    return parser

  @classmethod
  @override
  def parse_str(cls, value: str) -> Self:
    raise ValueError("Cannot parse TestGroup from string")


@dataclasses.dataclass(frozen=True)
class TestGroupConfig(ConfigObject):
  groups: list[TestGroup]

  @classmethod
  @override
  def config_parser(cls) -> ConfigParser[Self]:
    parser = ConfigParser(cls)
    parser.add_argument("groups", type=TestGroup, is_list=True, default=[])
    return parser

  @classmethod
  @override
  def parse_str(cls, value: str) -> Self:
    raise ValueError("Cannot parse TestGroupConfig from string")

  @classmethod
  def from_cmdline_flags(
      cls,
      tests: str,
      variants: str,
      playback: str | None,
      setup_delay: str | None,
      startup_delay: str | None,
      stories: str | None = None,
      page_config: dict[str, Any] | None = None,
      record_video: bool | None = None,
      bypass_oobe: bool | None = None,
      clear_browser_cache: bool | None = None,
  ) -> TestGroupConfig:
    return TestGroupConfig(groups=[
        TestGroup(
            filter_regex=tests,
            variants_filter_regex=variants,
            playback=playback,
            setup_delay=setup_delay,
            startup_delay=startup_delay,
            stories=stories,
            page_config=page_config,
            record_video=bool(record_video),
            bypass_oobe=(True if bypass_oobe is None else bypass_oobe),
            clear_browser_cache=(
                True if clear_browser_cache is None else clear_browser_cache))
    ])


@dataclasses.dataclass(frozen=True)
class CliConfig:
  platform: TargetPlatform
  device: str | None
  adb_bin: Path | None
  browser: str | None
  tests: list[tuple[str, str]]
  secrets: Path | None
  upload: bool
  out_dir: Path | None
  results_prefix: str | None
  tag: str | None
  debug: bool
  dry_run: bool
  playback: str | None
  setup_delay: str | None
  startup_delay: str | None
  stories: str | None
  page_config: dict[str, Any] | None
  wpr: str | None
  wait_for_debugger: bool
  no_symlinks: bool
  list_tests: bool
  record_video: bool | None = None
  bypass_oobe: bool | None = None
  clear_browser_cache: bool | None = None

  @classmethod
  def from_cmdline(cls, argv: list[str]) -> CliConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--platform", type=TargetPlatform.parse, default=TargetPlatform.LOCAL)
    parser.add_argument(
        "--device", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--adb-bin", type=Path, required=False)
    parser.add_argument(
        "--browser", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--playback", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--startup-delay", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--setup-delay", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--stories", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--page-config", type=parse_inline_page_config, required=False)
    parser.add_argument(
        "--tests", type=ObjectParser.non_empty_str, action=TestVariantAction)
    parser.add_argument(
        "--variants", type=ObjectParser.non_empty_str, action=TestVariantAction)
    parser.add_argument("--secrets", type=Path, required=False)
    parser.add_argument(
        "--wpr", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument("--upload", action="store_true", default=False)
    parser.add_argument("--out-dir", type=Path, required=False)
    parser.add_argument(
        "--results-prefix", type=ObjectParser.any_str, default="")
    parser.add_argument("--tag", type=ObjectParser.safe_filename, default=None)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--wait-for-debugger", action="store_true", default=False)
    parser.add_argument(
        "--no-symlinks", action="store_true", default=False)
    parser.add_argument(
        "--record-video",
        "--screen-recording",
        dest="record_video",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=("Enable full-screen video recording via Crossbench VideoProbe "
              "(default: False)."))
    parser.add_argument(
        "--bypass-oobe",
        dest="bypass_oobe",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=("Dismiss Android SetupWizard OOBE automatically before tests "
              "(default: True)."))
    parser.add_argument(
        "--clear-browser-cache",
        dest="clear_browser_cache",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=("Clear browser cache and app data before each session "
              "(default: True)."))
    parser.add_argument("--list", action="store_true", default=False)

    parsed = parser.parse_args(argv)

    if parsed.platform == TargetPlatform.LOCAL:
      logging.warning(
          "The 'local' platform is not officially supported by this script. "
          "You may need to tweak the probe config manually for some tests "
          "to pass.")

    ordered = vars(parsed).get("ordered_tests_variants", [])
    tests_variants: list[tuple[str, str]] = []
    current_test = None
    for opt, val in ordered:
      if opt == "--tests":
        if current_test is not None:
          tests_variants.append((current_test, ".*"))
        current_test = val
      elif opt == "--variants":
        if current_test is None:
          parser.error("--variants must follow a --tests flag")
        if Path(current_test).is_file():
          parser.error(
              f"--variants cannot be used with config file {current_test}")
        tests_variants.append((current_test, val))
        current_test = None
    if current_test is not None:
      tests_variants.append((current_test, ".*"))

    if parsed.list and not tests_variants:
      tests_variants.append((".*", ".*"))

    secrets_file: Path | None = parsed.secrets.resolve(
    ) if parsed.secrets else None

    wpr: str | None = None
    if parsed.wpr:
      if parsed.wpr.startswith("gs://"):
        wpr = parsed.wpr
      else:
        wpr_file = Path(parsed.wpr).expanduser().resolve()
        if not wpr_file.is_file():
          parser.error(f"--wpr archive not found: {wpr_file}")
        wpr = str(wpr_file)

    out_dir_path: Path | None = parsed.out_dir.resolve(
    ) if parsed.out_dir else None

    adb_bin_path: Path | None = parsed.adb_bin.resolve(
    ) if parsed.adb_bin else None

    return CliConfig(
        platform=parsed.platform,
        device=parsed.device,
        adb_bin=adb_bin_path,
        browser=parsed.browser,
        tests=tests_variants,
        playback=parsed.playback,
        setup_delay=parsed.setup_delay,
        startup_delay=parsed.startup_delay,
        stories=parsed.stories,
        page_config=parsed.page_config,
        secrets=secrets_file,
        wpr=wpr,
        upload=parsed.upload,
        out_dir=out_dir_path,
        results_prefix=parsed.results_prefix,
        tag=parsed.tag,
        debug=parsed.debug,
        dry_run=parsed.dry_run,
        wait_for_debugger=parsed.wait_for_debugger,
        no_symlinks=parsed.no_symlinks,
        list_tests=parsed.list,
        record_video=parsed.record_video,
        bypass_oobe=parsed.bypass_oobe,
        clear_browser_cache=parsed.clear_browser_cache,
    )


@dataclasses.dataclass(frozen=True)
class RunConfig:
  platform: TargetPlatform
  device: str | None
  adb_bin: Path | None
  browser: str | None
  secrets: Path | None
  wpr: str | None
  upload: bool
  results_root: Path
  tag: str | None
  debug: bool
  dry_run: bool
  no_symlinks: bool
  list_tests: bool
  tests: list[TestInvocationConfig]
