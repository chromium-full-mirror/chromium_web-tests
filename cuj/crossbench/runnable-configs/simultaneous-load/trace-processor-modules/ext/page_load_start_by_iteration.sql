include PERFETTO MODULE ext.iterations;

include PERFETTO MODULE ext.page_load_start;

-- Add the iteration id to the page load start table.
drop view if exists page_load_start_by_iteration;

create view
  page_load_start_by_iteration as
select
  page_load_start.id,
  iterations.id as it_id,
  page_load_start.page_load_start,
  page_load_start.detail
from
  iterations
  -- Join for all page loads that started during this iteration
  join page_load_start on page_load_start.page_load_start >= iterations.start
  and page_load_start.page_load_start <= iterations.end;