# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import annotations

import logging
import sys
import threading
from collections import deque

from rich.logging import RichHandler


def setup_logging() -> None:
  logging.basicConfig(
      level=logging.INFO,
      format="%(message)s",
      datefmt="[%X]",
      handlers=[RichHandler(show_time=False, show_path=False)],
      force=True)


class LogCapture:
  """Captures standard log output into a rolling buffer.

  This is primarily used to buffer Crossbench execution logs internally so they
  can be explicitly rendered inside a rich.panel.Panel without disrupting the
  live terminal table layout.
  """

  def __init__(self, max_lines: int = 20) -> None:
    self.lines: deque[str] = deque(maxlen=max_lines)
    self.buffer = ""
    self.lock = threading.Lock()

  def write(self, text: str) -> None:
    with self.lock:
      self.buffer += text
      while "\n" in self.buffer:
        line, self.buffer = self.buffer.split("\n", 1)
        self.lines.append(line)

  def flush(self) -> None:
    pass

  def get_text(self) -> str:
    with self.lock:
      return "\n".join(
          list(self.lines) + ([self.buffer] if self.buffer else []))


class DirectLogCapture:
  """Bypasses internal buffering and pipes log output directly to sys.stdout.

  This is used as a fallback for non-TTY environments (like the AL Lab Java
  wrappers) where stdout is piped directly to a parser and the rich UI elements
  would otherwise corrupt the expected output format.
  """

  def write(self, text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()

  def flush(self) -> None:
    sys.stdout.flush()

  def get_text(self) -> str:
    return ""


class NullLogCapture:
  """Silences all log output.
  
  Used during parallel dry-runs (like presubmit) where concurrent logs
  would otherwise become hopelessly jumbled.
  """

  def write(self, text: str) -> None:
    pass

  def flush(self) -> None:
    pass

  def get_text(self) -> str:
    return ""
