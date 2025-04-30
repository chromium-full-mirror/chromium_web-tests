-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE web_tests_common.histograms;

SELECT
  AVG(hist.value / UNITS_IN_MS) AS 'avg_ms',
  COUNT(*) AS 'count',
  SUM(hist.value / UNITS_IN_MS) AS 'sum_ms',
  MAX(hist.value / UNITS_IN_MS) AS 'max_ms',
  PERCENTILE (hist.value / UNITS_IN_MS, 90) AS 'p90_ms',
  PERCENTILE (hist.value / UNITS_IN_MS, 50) AS 'p50_ms'
FROM
  chrome_histograms hist
WHERE
  hist.name = 'METRIC_NAME'