{{
  config(
    materialized = "table",
    description = "Inventory and sales summary for each distribution center"
  )
}}

WITH inventory AS (
    SELECT
        product_distribution_center_id AS distribution_center_id,
        COUNT(*) AS total_items,
        COUNT(sold_at) AS items_sold,
        SUM(cost) AS total_cost
    FROM {{ ref('stg_inventory_items') }}
    GROUP BY 1
),
product_sales AS (
    SELECT
        p.distribution_center_id,
        SUM(oi.sale_price) AS total_sales
    FROM {{ ref('stg_order_items') }} oi
    LEFT JOIN {{ ref('stg_products') }} p
        ON oi.product_id = p.id
    GROUP BY 1
)
SELECT
    dc.id AS distribution_center_id,
    dc.name AS distribution_center_name,
    COALESCE(i.total_items, 0) AS total_items,
    COALESCE(i.items_sold, 0) AS items_sold,
    COALESCE(i.total_items, 0) - COALESCE(i.items_sold, 0) AS items_in_stock,
    {{ coalesce_and_round('ps.total_sales', 2) }} AS total_sales,
    {{ coalesce_and_round('i.total_cost', 2) }} AS total_inventory_cost
FROM {{ ref('stg_distribution_centers') }} dc
LEFT JOIN inventory i ON dc.id = i.distribution_center_id
LEFT JOIN product_sales ps ON dc.id = ps.distribution_center_id
