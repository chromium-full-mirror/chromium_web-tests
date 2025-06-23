#!/bin/bash

# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

dir=$(dirname "$(readlink -f "$0")")
cd "$dir"

gsutil cp gs://chrome-partner-telemetry/cros/cuj/crossbench/page-click-scroll-20250623.wprgo \
 page-click-scroll.wprgo
