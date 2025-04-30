-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE web_tests_common.histograms;

SELECT
  AVG(hist.value) AS 'avg',
  COUNT(*) AS 'count',
  SUM(hist.value) AS 'total',
  MAX(hist.value) AS 'max',
  PERCENTILE (hist.value, 90) AS 'p90',
  PERCENTILE (hist.value, 50) AS 'p50'
FROM
  chrome_histograms hist
WHERE
  hist.name = 'METRIC_NAME'