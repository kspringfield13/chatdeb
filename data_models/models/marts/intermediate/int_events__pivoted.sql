{% set traffic_source_values = ['Adwords', 'Email', 'Facebook', 'Organic', 'YouTube'] %}
{% set browser_values = ['Chrome', 'Firefox', 'Safari', 'IE', 'Other'] %}

SELECT 
    user_id,
    COUNT(DISTINCT session_id) AS num_web_sessions,
    {%- for traffic_source_value in traffic_source_values %}
    COUNT(DISTINCT CASE WHEN traffic_source = '{{ traffic_source_value }}' THEN user_id END) AS num_traffic_source_{{ traffic_source_value }},
    {%- endfor %}
      
	{%- for browser_value in browser_values %}
    COUNT(DISTINCT CASE WHEN browser = '{{ browser_value }}' THEN user_id END) AS num_browser_{{ browser_value }}
    {%- if not loop.last -%}
        ,
    {%- endif -%}
    {%- endfor %}

FROM {{ ref('stg_events') }}
GROUP BY 1