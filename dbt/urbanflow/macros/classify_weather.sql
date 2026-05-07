{% macro classify_weather(weather_code_column) %}
    case 
        -- 0-3: Clear, Mainly Clear, Partly Cloudy, Overcast
        when {{ weather_code_column }} in (0, 1, 2, 3) then 'Clear'

        -- 45, 48: Fog and depositing rime fog
        when {{ weather_code_column }} in (45, 48) then 'Fog'

        -- 51-67: Drizzle, Rain, Freezing Rain
        when {{ weather_code_column }} between 51 and 67 then 'Rain'

        -- 71-77: Snow fall: Slight, moderate, and heavy intensity
        when {{ weather_code_column }} between 71 and 77 then 'Snow'

        -- 80-82: Rain showers: Slight, moderate, and violent
        when {{ weather_code_column }} between 80 and 82 then 'Showers'

        -- 85-86: Snow showers slight and heavy
        when {{ weather_code_column }} in (85, 86) then 'Snow Showers'

        -- 95-99: Thunderstorm: Slight or moderate
        when {{ weather_code_column }} >= 95 then 'Thunderstorm'

        else 'Unknown'
    end


{% endmacro %}