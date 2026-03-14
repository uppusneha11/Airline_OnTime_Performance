AIRLINE_PERFORMANCE = """
SELECT
    op_unique_carrier AS carrier,
    COUNT(*) AS total_flights,
    AVG(arr_del15)*100 AS delay_rate,
    (1 - AVG(arr_del15))*100 AS on_time_rate,
    AVG(arr_delay_new) AS avg_arrival_delay,
    AVG(dep_delay_new) AS avg_departure_delay,
    AVG(cancelled)*100 AS cancellation_rate
FROM fact_flights
GROUP BY op_unique_carrier
"""


AIRPORT_DEPARTURE_DELAYS = """
SELECT
    origin_airport_id,
    COUNT(*) AS total_flights,
    AVG(dep_delay_new) AS avg_departure_delay,
    AVG(dep_del15)*100 AS delay_rate
FROM fact_flights
GROUP BY origin_airport_id
"""


AIRPORT_ARRIVAL_DELAYS = """
SELECT
    dest_airport_id,
    COUNT(*) AS total_flights,
    AVG(arr_delay_new) AS avg_arrival_delay,
    AVG(arr_del15)*100 AS delay_rate
FROM fact_flights
GROUP BY dest_airport_id
"""


DELAY_BY_DAY = """
SELECT
    day_of_week,
    COUNT(*) AS total_flights,
    AVG(arr_del15)*100 AS delay_rate,
    AVG(arr_delay_new) AS avg_delay
FROM fact_flights
GROUP BY day_of_week
"""


DELAY_BY_TIME_BUCKET = """
SELECT
    time_bucket,
    COUNT(*) AS total_flights,
    AVG(arr_del15)*100 AS delay_rate,
    AVG(arr_delay_new) AS avg_delay
FROM fact_flights
GROUP BY time_bucket
"""


ROUTE_PERFORMANCE = """
SELECT
    origin_airport_id,
    dest_airport_id,
    op_unique_carrier,
    COUNT(*) AS total_flights,
    AVG(arr_del15)*100 AS delay_rate,
    AVG(cancelled)*100 AS cancellation_rate,
    AVG(arr_delay_new) AS avg_arrival_delay
FROM fact_flights
GROUP BY origin_airport_id, dest_airport_id, op_unique_carrier
"""


ROUTE_TIME_DAY = """
SELECT
    origin_airport_id,
    dest_airport_id,
    op_unique_carrier,
    day_of_week,
    time_bucket,
    COUNT(*) AS total_flights,
    AVG(arr_del15)*100 AS delay_rate,
    AVG(cancelled)*100 AS cancellation_rate
FROM fact_flights
GROUP BY
origin_airport_id,
dest_airport_id,
op_unique_carrier,
day_of_week,
time_bucket
"""