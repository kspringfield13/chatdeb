SELECT
  id,
  name,
  latitude,
  longitude
FROM {{ ref('raw_distribution_centers') }}