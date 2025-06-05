{{
  config(
    materialized = "table",
    description = "Monthly sales and order metrics"
  )
}}

WITH orders AS (
    SELECT
        DATE_TRUNC('month', CAST(created_at AS TIMESTAMP)) AS month,
        COUNT(*) AS num_orders,
        SUM(num_of_item) AS items_ordered
    FROM {{ ref('stg_orders') }}
    GROUP BY 1
),
revenue AS (
    SELECT
        DATE_TRUNC('month', CAST(created_at AS TIMESTAMP)) AS month,
        SUM(sale_price) AS revenue
    FROM {{ ref('stg_order_items') }}
    GROUP BY 1
)
SELECT
    o.month,
    o.num_orders,
    o.items_ordered,
    {{ coalesce_and_round('r.revenue', 2) }} AS revenue
FROM orders o
LEFT JOIN revenue r ON o.month = r.month
