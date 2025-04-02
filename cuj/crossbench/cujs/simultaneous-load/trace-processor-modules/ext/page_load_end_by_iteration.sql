include PERFETTO MODULE ext.iterations;

include PERFETTO MODULE ext.page_load_end;

-- Add the iteration id to the page load end table.
drop view if exists page_load_end_by_iteration;

create view
  page_load_end_by_iteration as
select
  page_load_end.id,
  iterations.id as it_id,
  page_load_end.page_load_end,
  page_load_end.detail
from
  iterations
  -- Join for all page loads that ended during this iteration
  join page_load_end on page_load_end.page_load_end >= iterations.start
  and page_load_end.page_load_end <= iterations.end;