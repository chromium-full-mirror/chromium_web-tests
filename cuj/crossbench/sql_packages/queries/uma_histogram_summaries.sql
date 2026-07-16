-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE chrome.histograms;

INCLUDE PERFETTO MODULE sql_packages.queries.uma_histogram_constants;

DROP TABLE IF EXISTS uma_histogram_summaries;

CREATE PERFETTO TABLE uma_histogram_summaries AS
SELECT
  hist.name AS hist_name,
  enum_table.enum_name AS "enum_name",
  avg(hist.value) AS "avg",
  count(*) AS "count",
  sum(hist.value) AS "total",
  max(hist.value) AS "max",
  percentile(hist.value, 95) AS "p95",
  percentile(hist.value, 90) AS "p90",
  percentile(hist.value, 75) AS "p75",
  percentile(hist.value, 50) AS "p50"
FROM chrome_histograms AS hist
LEFT JOIN enum_table
  ON hist.name = enum_table.histogram_name AND hist.value = enum_table.enum_value
GROUP BY
  hist_name;

