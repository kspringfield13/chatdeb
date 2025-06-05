{% snapshot orders_snapshot %}

{{
    config(
      target_schema='main',
      unique_key='order_id',
      strategy='timestamp',
      updated_at='created_at' 
    )
}}

SELECT * 
FROM {{ source('main', 'raw_orders') }}

{% endsnapshot %}