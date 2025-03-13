-- The test may have been run multiple times in the same trace.
-- Grab the start and end ts for each iteration.
drop view if exists iterations;

create view
  iterations as
select
  *
from
  (
    select
      row_number() over (
        order by
          ts
      ) as id,
      ts as start
    from
      slice
    where
      category = 'blink.user_timing'
      and name = 'iteration-start'
  )
  join (
    select
      row_number() over (
        order by
          ts
      ) as id,
      ts as end
    from
      slice
    where
      category = 'blink.user_timing'
      and name = 'iteration-end'
  ) using (id)
order by
  id;