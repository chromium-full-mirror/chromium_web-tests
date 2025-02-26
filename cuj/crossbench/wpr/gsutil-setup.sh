#!/bin/bash

dir=$(dirname "$(readlink -f "$0")")
cd "$dir"

gsutil cp gs://chrome-partner-telemetry/cros/cuj/crossbench/archive-wbp-2.wprgo page-click.wprgo
gsutil cp gs://chrome-partner-telemetry/cros/cuj/crossbench/archive-wbp-1.wprgo page-scroll.wprgo