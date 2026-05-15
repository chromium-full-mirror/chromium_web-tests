-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE chrome.histograms;

DROP TABLE IF EXISTS meet_jank_output;

CREATE PERFETTO TABLE meet_jank_output AS
SELECT
  hist.name AS hist_name,
  avg(hist.value) AS "avg",
  count(*) AS "count",
  sum(hist.value) AS "total",
  max(hist.value) AS "max",
  percentile(hist.value, 95) AS "p95",
  percentile(hist.value, 90) AS "p90",
  percentile(hist.value, 75) AS "p75",
  percentile(hist.value, 50) AS "p50"
FROM chrome_histograms AS hist
WHERE
  hist.name IN (
    'Graphics.Smoothness.PercentDroppedFrames3.AllSequences',
    'Graphics.Smoothness.Jank3.AllSequences'
  )
  AND hist.ts
  > (
    SELECT min(ts)
    FROM slice
    WHERE
      category = 'blink.user_timing'
      AND name = 'meet-joined'
  )
GROUP BY
  hist_name;
