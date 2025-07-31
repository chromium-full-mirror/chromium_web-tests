-- Copyright 2025 The Chromium Authors
-- Use of this source code is governed by a BSD-style license that can be
-- found in the LICENSE file.

include PERFETTO MODULE sql_packages.web_tests_common.iterations;

drop view if exists tabs_alive;

create view tabs_alive
as
with
  page_loaded_events as (
    -- 1. Get all page-loaded events with their process info
    select
      cast(substr(s.name, instr(s.name, '~') + 1) as integer) as page_loaded_tab_index,
      s.ts as page_loaded_ts,
      p.pid as page_loaded_pid
    from slice s
    join thread_track tt
      on s.track_id = tt.id
    join thread t
      using (utid)
    join process p
      using (upid)
    where s.cat = 'blink.user_timing' and s.name glob 'page-loaded~*'
  ),
  process_lifetimes as (
    -- 2. Determine the start and end timestamps for all processes
    --    Note: process.end_ts might be NULL if process is alive at trace end.
    --    We'll use trace_end as a fallback for 'alive' processes.
    select
      ple.page_loaded_tab_index as tab_index,
      p.pid,
      p.name as process_name,
      p.start_ts,
      coalesce(p.end_ts, (select max(ts) from slice)) as end_ts_effective,
      ple.page_loaded_ts as page_loaded_ts
    from process p
    join page_loaded_events ple
      ON p.pid = ple.page_loaded_pid
    where ple.page_loaded_ts between p.start_ts and coalesce(p.end_ts, (select max(ts) from slice))
  )
select
  pl_outer.tab_index,
  pl_outer.page_loaded_ts,
  pl_outer.pid,
  pl_outer.process_name,
  (
    select count(*)
    from process_lifetimes pl_inner
    where
      -- Process must be emitted a 'page-loaded' event before the current tab's
      -- 'page-loaded' event and must still be alive
      pl_inner.page_loaded_ts <= pl_outer.page_loaded_ts
      and pl_inner.end_ts_effective >= pl_outer.page_loaded_ts
  ) as tabs_alive
from process_lifetimes pl_outer
order by pl_outer.tab_index;

drop view if exists tabs_alive_by_iteration;

create view tabs_alive_by_iteration
as
select
  iterations.id as it_id,
  tabs_alive.tab_index,
  tabs_alive.tabs_alive,
  tabs_alive.pid,
  tabs_alive.process_name
from iterations
join tabs_alive
  on tabs_alive.page_loaded_ts >= iterations.start and tabs_alive.page_loaded_ts <= iterations.end;

create table avg_tabs_alive_after_first_kill
as
with
  tabs_alive_with_prev_count as (
    select
      it_id,
      tab_index,
      tabs_alive,
      lag(tabs_alive, 1, -1) over (partition by it_id order by tab_index) as prev_tabs_alive
    from tabs_alive_by_iteration
  ),
  first_kill_point as (
    select it_id, min(tab_index) as first_kill_tab_index
    from tabs_alive_with_prev_count
    where
      tabs_alive <= prev_tabs_alive  -- condition for no increase (i.e., decrease or stay the same)
    group by it_id
  )
select fkp.it_id, fkp.first_kill_tab_index, avg(tai.tabs_alive) as average_tabs_alive_after_kill
from first_kill_point fkp
join tabs_alive_by_iteration tai
  on fkp.it_id = tai.it_id and tai.tab_index >= fkp.first_kill_tab_index
group by
  fkp.it_id, fkp.first_kill_tab_index  -- group by this to ensure it's in the output if needed
order by fkp.it_id;
