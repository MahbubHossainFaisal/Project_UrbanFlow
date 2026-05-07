/*
 When dealing with hourly API data, we don't just worry about "bad values" (like negative fares). We worry about Gaps and Grain.
   - If a single hour is missing from January 15th, our LEFT JOIN in the Gold layer will produce NULL weather for thousands of taxi trips.
   - If we have duplicate hours, our join will fan-out, multiplying the number of taxi trips and corrupting our financial metrics.
*/
select * from BRONZE.RAW_WEATHER_HOURLY

select count(*) from BRONZE.RAW_WEATHER_HOURLY
group by TIME
having count(*)>1;


SELECT WEATHERCODE, COUNT(*) FROM BRONZE.RAW_WEATHER_HOURLY
GROUP BY WEATHERCODE; -- output 13 distinct weather code

SELECT * FROM BRONZE.RAW_WEATHER_HOURLY
WHERE TEMPERATURE_2M IS NULL OR PRECIPITATION IS NULL OR WEATHERCODE IS NULL; -- output: No results

-- dbt model creation done and ran

SELECT * FROM SILVER.STG_WEATHER_HOURLY;