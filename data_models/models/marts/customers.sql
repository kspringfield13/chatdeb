{% set order_items_status = 'Complete' %}
{% set country = 'Australia' %}

{{ 
  config(
    materialized = "table",
    description = "A table of customers for downstream analysis"
  ) 
}}

WITH customer_base AS (
    SELECT 
        id AS user_id,
        first_name AS customer_first_name,
        last_name AS customer_last_name,
        country AS customer_country,
        traffic_source AS customer_acquisition_channel
    FROM {{ ref('stg_users')}}
    WHERE country = '{{ country }}'
)
, order_items AS (
    SELECT 
        user_id,
        SUM(sale_price) AS total_amount_spent,
        COUNT(DISTINCT id) AS total_items_purchased,
        MIN(created_at) AS first_order_completed_at,
        MAX(created_at) AS last_order_completed_at,
    FROM {{ ref('stg_order_items') }}
    WHERE status = '{{ order_items_status }}'
    GROUP BY 1
)
, orders AS (
    SELECT * 
    FROM {{ ref('int_orders__pivoted') }}
)
, web_traffic AS (
    SELECT * 
    FROM {{ ref('int_events__pivoted') }}
)
SELECT
    cb.user_id,
    cb.customer_first_name,
    cb.customer_last_name,
    cb.customer_country,
    cb.customer_acquisition_channel,
    oi.total_amount_spent,
    oi.total_items_purchased,
    oi.first_order_completed_at,
    oi.last_order_completed_at,
    o.num_orders,
    o.num_orders_shipped,
    o.num_orders_complete,
    o.num_orders_processing,
    o.num_orders_cancelled,
    o.num_orders_returned,
    wt.num_web_sessions,
FROM customer_base cb
LEFT JOIN order_items oi 
    on cb.user_id = oi.user_id
LEFT JOIN orders o
    ON cb.user_id = o.user_id 
LEFT JOIN web_traffic wt 
    ON cb.user_id = wt.user_id