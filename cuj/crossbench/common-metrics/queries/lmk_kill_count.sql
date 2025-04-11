include PERFETTO MODULE web_tests_common.iterations;

drop view if exists lmk_kill_ts;

create view
  lmk_kill_ts as
select
  ts
from
  slice
where
  name = 'lmk_kill_occurred';

select
  iterations.id as it_id,
  count(lmk_kill_ts.ts) as kill_count
from
  iterations
  left join lmk_kill_ts on lmk_kill_ts.ts >= iterations.start
  and lmk_kill_ts.ts <= iterations.end