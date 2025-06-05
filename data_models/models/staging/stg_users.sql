SELECT
  id,
  first_name,
  last_name,
  email,
  age,
  gender,
  state,
  street_address,
  postal_code,
  city,
  country,
  latitude,
  longitude,
  traffic_source,
  created_at
FROM {{ source('main', 'raw_users') }}