SELECT
  id,
  product_id,
  created_at,
  sold_at,
  cost,
  product_category,
  product_name,
  product_brand,
  product_retail_price,
  product_department,
  product_sku,
  product_distribution_center_id
FROM {{ source('main', 'raw_inventory_items') }}