#!/usr/bin/env vpython3

import sys

from runner.cli import runner_cli

if __name__ == "__main__":
  argv = sys.argv
  runner_cli(argv)
