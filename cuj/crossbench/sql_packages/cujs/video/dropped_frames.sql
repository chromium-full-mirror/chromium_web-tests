-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE chrome.histograms;

DROP TABLE IF EXISTS dropped_frames_output;

CREATE PERFETTO TABLE dropped_frames_output AS
SELECT
  avg(value) AS "avg_percent_dropped"
FROM chrome_histograms
WHERE
  name = 'Graphics.Smoothness.PercentDroppedFrames3.AllSequences';
