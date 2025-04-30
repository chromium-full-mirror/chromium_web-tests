-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
INCLUDE PERFETTO MODULE sql_packages.web_tests_common.histograms;

CREATE PERFETTO TABLE enum_table AS
SELECT
    column1 AS name,
    column2 AS value
FROM
    (
        VALUES
            TABLE_NAME
    );

SELECT
    enum_table.name AS name,
    COUNT(*) AS count
FROM
    chrome_histograms hist
    JOIN enum_table
WHERE
    hist.value = enum_table.value
    AND hist.name = 'METRIC_NAME'