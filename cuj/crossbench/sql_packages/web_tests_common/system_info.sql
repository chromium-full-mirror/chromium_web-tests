-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
DROP TABLE IF EXISTS system_info;

CREATE PERFETTO TABLE system_info AS
SELECT
  1 AS dummy_value,
  max(CASE WHEN name = 'system_name' THEN str_value END) AS system_name,
  max(CASE WHEN name = 'system_release' THEN str_value END) AS system_release,
  max(CASE WHEN name = 'system_version' THEN str_value END) AS system_version,
  max(CASE WHEN name = 'system_machine' THEN str_value END) AS system_machine,
  max(CASE WHEN name = 'android_build_fingerprint' THEN str_value END) AS android_build_fingerprint
FROM metadata;
