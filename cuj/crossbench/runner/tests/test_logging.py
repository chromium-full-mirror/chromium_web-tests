# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from unittest import mock

import pytest
from runner.logging import DirectLogCapture, LogCapture
from runner.runner import execute_crossbench


def test_log_capture_collapses_carriage_returns_and_keeps_colors() -> None:
  capture = LogCapture(max_lines=10)
  capture.write("\x1b[32mSETUP\x1b[39m\n")
  capture.write("   GET                           \r")
  assert capture.get_text() == (
      "\x1b[32mSETUP\x1b[39m\n   GET                           ")

  capture.write("   ClickAction                   \r")
  assert capture.get_text() == (
      "\x1b[32mSETUP\x1b[39m\n   ClickAction                   ")

  capture.write("\x1b[32mRUNNING STORY\x1b[39m\n")
  assert capture.get_text() == (
      "\x1b[32mSETUP\x1b[39m\n\x1b[32mRUNNING STORY\x1b[39m")


def test_log_capture_preserves_blank_line_after_transient_status() -> None:
  capture = LogCapture(max_lines=10)
  capture.write("Line 1\n")
  capture.write("   WaitAction                    \r")
  capture.write("\n")
  capture.write("Line 2\n")
  assert capture.get_text() == "Line 1\n\nLine 2"


def test_log_capture_shows_unterminated_prompt_immediately() -> None:
  capture = LogCapture(max_lines=10)
  capture.write("VALIDATE ENVIRONMENT: PROMPT\n")
  capture.write("\x1b[31mMissing dependencies.\x1b[39m Continue? [Yn]")
  assert capture.get_text() == (
      "VALIDATE ENVIRONMENT: PROMPT\n"
      "\x1b[31mMissing dependencies.\x1b[39m Continue? [Yn]")


@pytest.mark.parametrize("chunk_size", [1, 2, 5, 13, 31])
def test_log_capture_chunk_splitting_invariance(chunk_size: int) -> None:
  osc_link = "\x1b]8;;file:///tmp/errors.json\x1b\\errors.json\x1b]8;;\x1b\\"
  raw_stream = (
      "\x1b[32mBanner\x1b[39m\n"
      "   SplashScreen                  \r"
      "   ClickAction                   \r"
      "\n"
      f"\x1b[31mSee {osc_link}\x1b[39m\n"
      "Final active prompt [Yn]"
  )

  whole_capture = LogCapture(max_lines=20)
  whole_capture.write(raw_stream)

  chunked_capture = LogCapture(max_lines=20)
  for idx in range(0, len(raw_stream), chunk_size):
    chunked_capture.write(raw_stream[idx:idx + chunk_size])

  assert chunked_capture.get_text() == whole_capture.get_text()


def test_execute_crossbench_sets_force_color_and_handles_utf8(
    tmp_path: Path) -> None:
  cb_dir = tmp_path / "third_party" / "crossbench"
  cb_dir.mkdir(parents=True)
  (cb_dir / "cb.py").write_text(
      "import os, sys\n"
      "assert not sys.stdout.isatty(), 'expected pipe'\n"
      "assert os.environ.get('FORCE_COLOR') == '1'\n"
      "banner = '▞▀▖' * 1500\n"
      "sys.stdout.write(f'\\x1b[32m{banner}\\x1b[39m\\n')\n"
      "sys.stdout.write('   TransientAction               \\r')\n"
      "sys.stdout.flush()\n"
      "sys.stderr.write('\\x1b[33mWarning line\\x1b[39m\\n')\n",
      encoding="utf-8",
  )
  results_dir = tmp_path / "run_0"
  capture = LogCapture(max_lines=10)

  with (
      mock.patch("runner.runner.WEB_TESTS_ROOT", tmp_path),
      mock.patch.dict(os.environ, {}, clear=False),
  ):
    os.environ.pop("NO_COLOR", None)
    os.environ.pop("FORCE_COLOR", None)
    execute_crossbench(
        cb_benchmark_name="loading",
        probe_config_file=None,
        browser_config="{}",
        additional_crossbench_args="",
        debug=False,
        dry_run=False,
        no_symlinks=True,
        results_path=results_dir,
        log_buffer=capture,
    )

  expected_banner = "▞▀▖" * 1500
  assert "\ufffd" not in capture.get_text()
  assert f"\x1b[32m{expected_banner}\x1b[39m" in capture.get_text()
  assert "\x1b[33mWarning line\x1b[39m" in capture.get_text()
  assert "TransientAction" not in capture.get_text()

  saved_log = (results_dir / "raw_crossbench_logs.txt").read_text(
      encoding="utf-8")
  assert "\ufffd" not in saved_log
  assert "Warning line" in saved_log


def test_execute_crossbench_non_tty_omits_force_color(tmp_path: Path) -> None:
  cb_dir = tmp_path / "third_party" / "crossbench"
  cb_dir.mkdir(parents=True)
  (cb_dir / "cb.py").write_text(
      "import os, sys\n"
      "assert 'FORCE_COLOR' not in os.environ\n"
      "sys.stdout.write('   GET\\r')\n"
      "sys.stdout.write('Finished story\\n')\n",
      encoding="utf-8",
  )
  results_dir = tmp_path / "run_non_tty"
  direct_out = io.StringIO()

  with (
      mock.patch("runner.runner.WEB_TESTS_ROOT", tmp_path),
      mock.patch.object(sys, "stdout", direct_out),
      mock.patch.dict(os.environ, {}, clear=False),
  ):
    os.environ.pop("FORCE_COLOR", None)
    execute_crossbench(
        cb_benchmark_name="loading",
        probe_config_file=None,
        browser_config="{}",
        additional_crossbench_args="",
        debug=False,
        dry_run=False,
        no_symlinks=True,
        results_path=results_dir,
        log_buffer=DirectLogCapture(),
    )

  saved_log = (results_dir / "raw_crossbench_logs.txt").read_bytes().decode(
      "utf-8")
  assert saved_log == "   GET\rFinished story\n"


def test_execute_crossbench_writes_raw_log_on_failure(tmp_path: Path) -> None:
  cb_dir = tmp_path / "third_party" / "crossbench"
  cb_dir.mkdir(parents=True)
  (cb_dir / "cb.py").write_text(
      "import sys\n"
      "sys.stdout.write('   ClickAction\\r')\n"
      "sys.stderr.write('\\x1b[31mAction failed\\x1b[39m\\n')\n"
      "sys.exit(2)\n",
      encoding="utf-8",
  )
  results_dir = tmp_path / "run_fail"
  capture = LogCapture(max_lines=10)

  with mock.patch("runner.runner.WEB_TESTS_ROOT", tmp_path):
    with pytest.raises(RuntimeError, match="exit code 2"):
      execute_crossbench(
          cb_benchmark_name="loading",
          probe_config_file=None,
          browser_config="{}",
          additional_crossbench_args="",
          debug=False,
          dry_run=False,
          no_symlinks=True,
          results_path=results_dir,
          log_buffer=capture,
      )

  saved_log = (results_dir / "raw_crossbench_logs.txt").read_bytes().decode(
      "utf-8")
  assert "Action failed" in saved_log
  assert "\x1b[31mAction failed\x1b[39m" in capture.get_text()
