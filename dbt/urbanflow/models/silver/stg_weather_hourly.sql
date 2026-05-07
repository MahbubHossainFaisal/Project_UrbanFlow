{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('bronze', 'raw_weather_hourly') }}
),

renamed as (
    select
        cast(time as timestamp_ntz) as weather_time,
        cast(temperature_2m as float) as temperature_2m,
        cast(precipitation as float) as precipitation,
        cast(snowfall as float) as snowfall,
        cast(windspeed_10m as float) as windspeed_10m,
        cast(weathercode as integer) as weather_code,
        source_url,
        loaded_at
    from source
),

final as (
    select
        *,
        {{ classify_weather('weather_code') }} as weather_category,
        -- Logic to flag any hour with falling precipitation (Rain or Snow)
        case 
            when precipitation > 0 or snowfall > 0 then true 
            else false 
        end as is_precipitation
    from renamed
)

select * from final
