SELECT
  (
    SELECT
      (dur / 1000000)
    FROM
      slice
    WHERE
      slice.name = 'scroll'
  ) AS 'duration_ms'