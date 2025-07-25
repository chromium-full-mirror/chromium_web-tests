# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import argparse
import dataclasses
import enum
from pathlib import Path
from typing import Any, Self

from crossbench.config import ConfigEnum, ConfigObject, ConfigParser
from crossbench.parse import NumberParser, ObjectParser
from typing_extensions import override


@enum.unique
class TargetPlatform(ConfigEnum):
  ANDROID = ("adb", "Android via adb")
  CHROME_OS = ("cros", "ChromeOS via ssh")
  LOCAL = ("local", "local browser")


@dataclasses.dataclass(frozen=True, kw_only=True)
class Test:
  name: str
  path: Path
  probe_config: Path
  browser_flags: Path
  extensions: Path | None
  crossbench_args: str
  page_config: Path | None = None

  @property
  def full_name(self) -> str:
    return self.name

  @property
  def crossbench_command(self) -> str:
    return self.name


@dataclasses.dataclass(frozen=True, kw_only=True)
class Benchmark(Test):
  pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class Cuj(Test):
  variant: str
  page_config: Path

  @property
  @override
  def full_name(self) -> str:
    if self.variant:
      return f"{self.name}_{self.variant}"

    return super().full_name

  @property
  @override
  def crossbench_command(self) -> str:
    return "loading"


@dataclasses.dataclass(frozen=True, kw_only=True)
class TestInvocation(Test):
  min_successes: int | None = None
  max_consecutive_failures: int | None = None
  playback: str | None = None


@dataclasses.dataclass(frozen=True, kw_only=True)
class BenchmarkInvocation(TestInvocation, Benchmark):

  @classmethod
  def from_benchmark(
      cls, benchmark: Benchmark, min_successes: int | None,
      max_consecutive_failures: int | None) -> BenchmarkInvocation:
    benchmark_fields: dict[str, Any] = {
        field.name: getattr(benchmark, field.name)
        for field in dataclasses.fields(Benchmark)
    }
    return BenchmarkInvocation(
        **benchmark_fields,
        min_successes=min_successes,
        max_consecutive_failures=max_consecutive_failures)


@dataclasses.dataclass(frozen=True, kw_only=True)
class CujInvocation(TestInvocation, Cuj):

  @classmethod
  def from_cuj(cls, cuj: Cuj, min_successes: int | None,
               max_consecutive_failures: int | None,
               playback: str | None) -> CujInvocation:
    cuj_fields: dict[str, Any] = {
        # pylint: disable=line-too-long
        field.name: getattr(cuj, field.name) for field in dataclasses.fields(Cuj)
    }
    return CujInvocation(
        **cuj_fields,
        min_successes=min_successes,
        max_consecutive_failures=max_consecutive_failures,
        playback=playback)


@dataclasses.dataclass(frozen=True)
class Tests:
  cujs: list[Cuj]
  benchmarks: list[Benchmark]


@dataclasses.dataclass(frozen=True)
class TestGroup(ConfigObject):
  filter_regex: str = ".*"
  min_successes: int | None = None
  max_consecutive_failures: int | None = None

  @classmethod
  @override
  def config_parser(cls) -> ConfigParser[Self]:
    parser = ConfigParser(cls)
    parser.add_argument(
        "filter_regex", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument(
        "min_successes", type=NumberParser.positive_int, required=False)
    parser.add_argument(
        "max_consecutive_failures",
        type=NumberParser.positive_int,
        required=False)
    return parser

  @classmethod
  @override
  def parse_str(cls, value: str) -> Self:
    raise ValueError("Cannot parse TestGroup from string")


@dataclasses.dataclass(frozen=True)
class BenchmarkGroup(TestGroup):
  pass


@dataclasses.dataclass(frozen=True)
class CujGroup(TestGroup):
  variants_filter_regex: str = ".*"
  playback: str | None = None

  @classmethod
  @override
  def config_parser(cls) -> ConfigParser[Self]:
    parser = super().config_parser()
    parser.add_argument(
        "variants_filter_regex", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument(
        "playback", type=ObjectParser.non_empty_str, required=False)
    return parser


@dataclasses.dataclass(frozen=True)
class TestGroupConfig(ConfigObject):
  cuj_groups: list[CujGroup]
  benchmark_groups: list[BenchmarkGroup]

  @classmethod
  @override
  def config_parser(cls) -> ConfigParser[Self]:
    parser = ConfigParser(cls)
    parser.add_argument("cuj_groups", type=CujGroup, is_list=True, default=[])
    parser.add_argument(
        "benchmark_groups", type=BenchmarkGroup, is_list=True, default=[])
    return parser

  @classmethod
  @override
  def parse_str(cls, value: str) -> Self:
    raise ValueError("Cannot parse TestGroupConfig from string")

  @classmethod
  def from_cmdline_flags(cls, tests: str, variants: str,
                         playback: str | None) -> TestGroupConfig:
    return TestGroupConfig(
        benchmark_groups=[BenchmarkGroup(filter_regex=tests)],
        cuj_groups=[
            CujGroup(
                filter_regex=tests,
                variants_filter_regex=variants,
                playback=playback)
        ])


@dataclasses.dataclass(frozen=True)
class CliConfig:
  platform: TargetPlatform
  device: str | None
  browser: str | None
  tests: str
  variants: str
  secrets: Path | None
  results_prefix: str | None
  debug: bool
  dry_run: bool
  playback: str | None
  wait_for_debugger: bool

  @classmethod
  def from_cmdline(cls, argv: list[str]) -> CliConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", type=TargetPlatform.parse, required=True)
    parser.add_argument(
        "--device", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--browser", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--playback", type=ObjectParser.non_empty_str, required=False)
    parser.add_argument(
        "--tests", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument(
        "--variants", type=ObjectParser.non_empty_str, default=".*")
    parser.add_argument("--secrets", type=Path, required=False)
    parser.add_argument(
        "--results-prefix", type=ObjectParser.any_str, default="")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--wait-for-debugger", action="store_true", default=False)

    parsed = parser.parse_args(argv)

    secrets_file: Path | None = parsed.secrets.resolve(
    ) if parsed.secrets else None

    return CliConfig(
        platform=parsed.platform,
        device=parsed.device,
        browser=parsed.browser,
        tests=parsed.tests,
        variants=parsed.variants,
        playback=parsed.playback,
        secrets=secrets_file,
        results_prefix=parsed.results_prefix,
        debug=parsed.debug,
        dry_run=parsed.dry_run,
        wait_for_debugger=parsed.wait_for_debugger)


@dataclasses.dataclass(frozen=True)
class RunConfig:
  platform: TargetPlatform
  device: str | None
  browser: str | None
  secrets: Path | None
  results_root: Path
  debug: bool
  dry_run: bool
  tests: tuple[TestInvocation, ...]
