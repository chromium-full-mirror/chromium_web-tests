-- Copyright 2026 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.

DROP TABLE IF EXISTS shrinker_and_psi_output;

CREATE PERFETTO TABLE shrinker_and_psi_output AS

WITH all_mem as (

    WITH cxbx_mem as (

        SELECT fe.ts AS timestamp, t.name AS thread_name, t.tid AS thread_id, p.name AS process_name, p.pid AS process_id,
        EXTRACT_ARG(fe.arg_set_id, 'buf') AS message_json
        FROM ftrace_event fe
        LEFT JOIN thread t ON fe.utid = t.utid LEFT JOIN process p ON t.upid = p.upid
        WHERE fe.name = 'print' AND EXTRACT_ARG(fe.arg_set_id, 'buf') LIKE '{"cxbx.mem":%'
    ) select timestamp,
    CAST(JSON_EXTRACT(message_json, '$.off_buffers') AS INTEGER) AS off_buffers,
    CAST(JSON_EXTRACT(message_json, '$.off_bytes') AS INTEGER) AS off_bytes
    from cxbx_mem

),

all_frames as (

    SELECT
        s.ts AS timestamp,
        SUBSTR(s.name, 13) AS instance,
        CAST(json_extract(a.string_value, '$.fps') AS INT) AS fps,
        CAST(json_extract(a.string_value, '$.stored') AS INT) AS stored
    FROM slice s
    JOIN args a ON s.arg_set_id = a.arg_set_id AND a.key = 'debug.data.detail'
    WHERE s.name LIKE 'cxbx.frames.%'
    ORDER BY s.ts ASC

),
all_psi as (

    WITH psi_tracks AS (
        SELECT id, name
        FROM counter_track
        WHERE LOWER(name) IN ('psi.mem.some', 'psi.mem.full')
    ),
    psi_samples AS (
        SELECT
            c.ts,
            t.name AS track_name,
            c.value,
            LAG(c.value) OVER (PARTITION BY c.track_id ORDER BY c.ts) AS prev_value,
            LAG(c.ts) OVER (PARTITION BY c.track_id ORDER BY c.ts) AS prev_ts
        FROM counter c
        JOIN psi_tracks t ON c.track_id = t.id
    )
    SELECT
        ts AS timestamp,
        STR_SPLIT(track_name,'.',2) as track,
        CASE
            WHEN prev_ts IS NOT NULL AND ts > prev_ts THEN
                MAX(0.0, MIN(100.0, (CAST((value - prev_value) AS DOUBLE) / (ts - prev_ts)) * 100.0))
            ELSE 0.0
        END AS stall_percentage
    FROM psi_samples
    ORDER BY ts ASC

),
all_timestamps AS (

    SELECT timestamp FROM all_frames
    UNION ALL
    SELECT timestamp FROM all_mem
    UNION ALL
    SELECT timestamp FROM all_psi
)
select
    t.timestamp - FIRST_VALUE(t.timestamp) OVER(ORDER BY t.timestamp ASC)  as rel_ts,
    all_mem.off_buffers,
    all_mem.off_bytes,
    IIF(all_psi.track='some', all_psi.stall_percentage, NULL) as psi_some,
    IIF(all_psi.track='full', all_psi.stall_percentage, NULL) as psi_full,
    IIF(all_frames.instance='back', all_frames.stored, NULL) as back_stored,
    IIF(all_frames.instance='main', all_frames.stored, NULL) as main_stored,
    IIF(all_frames.instance='back', all_frames.fps, NULL) as back_fps,
    IIF(all_frames.instance='main', all_frames.fps, NULL) as main_fps

FROM all_timestamps t
FULL OUTER JOIN all_frames USING (timestamp)
FULL OUTER JOIN all_mem USING (timestamp)
FULL OUTER JOIN all_psi USING (timestamp)
ORDER BY t.timestamp ASC;
