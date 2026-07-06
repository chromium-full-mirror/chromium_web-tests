-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS browser_info;

CREATE PERFETTO TABLE browser_info AS
SELECT
  1 AS dummy_value,
  (SELECT str_value FROM metadata WHERE name LIKE '%os-name%' LIMIT 1) AS cr_os_name,
  (SELECT str_value FROM metadata WHERE name LIKE '%os-version%' LIMIT 1) AS cr_os_version,
  (SELECT str_value FROM metadata WHERE name LIKE '%product-version%' LIMIT 1) AS cr_version,
  (SELECT str_value FROM metadata WHERE name LIKE '%revision%' LIMIT 1) AS cr_revision;
