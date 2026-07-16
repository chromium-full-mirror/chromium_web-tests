-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE chrome.histograms;

INCLUDE PERFETTO MODULE sql_packages.queries.uma_histogram_constants;

DROP TABLE IF EXISTS uma_histogram_summaries;

CREATE PERFETTO TABLE uma_histogram_summaries AS
WITH summaries AS (
  SELECT
    hist.name AS "hist_name",
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
    hist_name
)
SELECT hist_name, enum_name, 'avg' AS agg_type, "avg" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'count' AS agg_type, "count" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'total' AS agg_type, "total" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'max' AS agg_type, "max" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'p95' AS agg_type, "p95" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'p90' AS agg_type, "p90" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'p75' AS agg_type, "p75" AS value FROM summaries
UNION ALL
SELECT hist_name, enum_name, 'p50' AS agg_type, "p50" AS value FROM summaries;
