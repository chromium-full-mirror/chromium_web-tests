-- Get the ts for the start of each page load.
-- row_number() will be the tab open index.
drop view if exists page_load_start;

create view
  page_load_start as
select
  *
from
  (
    select
      row_number() over (
        order by
          ts
      ) as id,
      ts as page_load_start,
      extract_arg (arg_set_id, 'debug.data.detail') as detail
    from
      slice
    where
      category = 'blink.user_timing'
      and name = 'page-load'
  )
order by
  id;