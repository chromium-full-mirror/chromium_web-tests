#!/bin/bash

# Copyright 2025 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

dir=$(dirname "$(readlink -f "$0")")
cd "$dir"

GS_PATH="gs://chrome-partner-telemetry/cros/cuj/crossbench/page-click-scroll-20250623.wprgo"
LOCAL_PATH="page-click-scroll.wprgo"

if ! command -v gcloud &> /dev/null; then
  echo "Error: gcloud command not found."
  exit 1
fi

# Get remote MD5 hash
REMOTE_MD5=$(gcloud storage hash "$GS_PATH" --hex --skip-crc32c | grep "^md5_hash:" | awk '{print $2}')

if [ -z "$REMOTE_MD5" ]; then
  echo "Error: Failed to get remote MD5 hash for $GS_PATH."
  echo "Please check your permissions (e.g., run 'gcloud auth login')."
  exit 1
fi

# Check if local file exists and get its MD5 hash
LOCAL_MD5=""
if [ -f "$LOCAL_PATH" ]; then
  echo "Getting local MD5 hash for $LOCAL_PATH..."
  LOCAL_MD5=$(gcloud storage hash "$LOCAL_PATH" --hex --skip-crc32c | grep "^md5_hash:" | awk '{print $2}')
fi

echo "Local MD5: $LOCAL_MD5, Remote MD5: $REMOTE_MD5"

# Compare hashes and download if necessary
if [ "$REMOTE_MD5" == "$LOCAL_MD5" ]; then
  echo "Local file $LOCAL_PATH is up-to-date (MD5 matches)."
else
  gcloud storage cp "$GS_PATH" "$LOCAL_PATH"
  echo "Download complete."
fi
