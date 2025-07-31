-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.
include PERFETTO MODULE sql_packages.web_tests_common.iterations;

drop view if exists open_latency;

create view open_latency
as
with
  page_load_end_events as (
    select substr(name, instr(name, '~') + 1) AS id, ts as page_load_end_ts
    from slice
    where category = 'blink.user_timing' and name glob 'page-loaded~*'
  ),
  page_load_start_events as (
    select substr(name, instr(name, '~') + 1) AS id, ts as page_load_start_ts
    from slice
    where category = 'blink.user_timing' and name glob 'page-load~*'
  )
select
  ple.id,
  (ple.page_load_end_ts - pls.page_load_start_ts) / 1000000 as page_load_duration_ms,
  pls.page_load_start_ts
from page_load_end_events ple
join page_load_start_events pls
  on ple.id = pls.id
order by ple.id;

drop view if exists allocation_latency;

create view allocation_latency
as
with
  allocation_done_events as (
    select substr(name, instr(name, '~') + 1) AS id, ts as page_load_end_ts
    from slice
    where category = 'blink.user_timing' and name glob 'allocation-done~*'
  ),
  allocation_start_events as (
    select substr(name, instr(name, '~') + 1) AS id, ts as page_load_start_ts
    from slice
    where category = 'blink.user_timing' and name glob 'allocation-start~*'
  )
select
  alloc_done.id,
  (alloc_done.page_load_end_ts - alloc_start.page_load_start_ts) / 1000000 as allocation_duration_ms
from allocation_done_events alloc_done
join allocation_start_events alloc_start
  on alloc_done.id = alloc_start.id
order by alloc_done.id;

drop view if exists tab_timing;

create view tab_timing
as
select ol.id, ol.page_load_duration_ms, al.allocation_duration_ms, ol.page_load_start_ts
from open_latency ol
join allocation_latency al
  on ol.id = al.id
order by ol.id;

drop view if exists tab_timing_by_iteration;

create view tab_timing_by_iteration
as
select
  iterations.id as it_id,
  tab_timing.id as tab_index,
  tab_timing.page_load_duration_ms as page_load_duration_ms,
  tab_timing.allocation_duration_ms as allocation_duration_ms
from iterations
join tab_timing
  on
    tab_timing.page_load_start_ts >= iterations.start
    and tab_timing.page_load_start_ts <= iterations.end;
