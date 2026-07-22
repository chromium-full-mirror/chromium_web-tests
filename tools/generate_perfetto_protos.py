# Copyright 2026 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Generates Python protobuf bindings for Perfetto v2 metrics.

This is meant to be run via a gclient hook during `gclient sync`.
"""

import subprocess
import sys
from pathlib import Path


def main():
  script_dir = Path(__file__).resolve().parent
  web_tests_root = script_dir.parent

  perfetto_dir = web_tests_root / "third_party" / "perfetto"
  if not perfetto_dir.exists():
    print(f"Error: Perfetto directory not found at {perfetto_dir}")
    return 1

  out_dir = web_tests_root / "protoc" / "gen"
  out_dir.mkdir(parents=True, exist_ok=True)
  (out_dir / "__init__.py").touch(exist_ok=True)

  protos = [
      perfetto_dir / "protos/perfetto/trace_summary/file.proto",
      perfetto_dir / "protos/perfetto/trace_summary/v2_metric.proto",
      perfetto_dir / "protos/perfetto/perfetto_sql/structured_query.proto",
  ]

  try:
    subprocess.run([
        "protoc", f"--python_out={out_dir}", f"-I={perfetto_dir}",
        *(str(p) for p in protos)
    ],
                   check=True)
    print("Successfully compiled Perfetto protobuf bindings.")
  except FileNotFoundError:
    print("Error: The 'protoc' command was not found in PATH.")
    print("Please install the protobuf compiler "
          "(e.g. 'sudo apt install protobuf-compiler').")
    return 1
  except subprocess.CalledProcessError as e:
    print(f"Error: protoc failed with exit code {e.returncode}")
    return e.returncode

  return 0


if __name__ == "__main__":
  sys.exit(main())
