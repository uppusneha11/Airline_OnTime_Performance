CREATE TABLE fact_flights (

    fl_date DATE,
    op_unique_carrier VARCHAR(10),
    op_carrier_fl_num INTEGER,
    origin_airport_id INTEGER,
    origin_city_name VARCHAR(100),
    origin_state_abr VARCHAR(10),
    dest_airport_id INTEGER,
    dest_city_name VARCHAR(100),
    dest_state_abr VARCHAR(10),
    crs_dep_time INTEGER,
	dep_time DOUBLE PRECISION,
	dep_delay_new DOUBLE PRECISION,
	dep_del15 DOUBLE PRECISION,
    crs_arr_time INTEGER,
	arr_time DOUBLE PRECISION,
	arr_delay_new DOUBLE PRECISION,
    arr_del15 DOUBLE PRECISION,
    cancelled INTEGER,
    cancellation_code VARCHAR(5),
    diverted INTEGER,
    distance DOUBLE PRECISION,
    distance_group INTEGER,
    carrier_delay DOUBLE PRECISION,
    weather_delay DOUBLE PRECISION,
    nas_delay DOUBLE PRECISION,
    security_delay DOUBLE PRECISION,
    late_aircraft_delay DOUBLE PRECISION,
	div_airport_landings DOUBLE PRECISION,
	div_reached_dest DOUBLE PRECISION,
	div_arr_delay DOUBLE PRECISION,
	div_distance DOUBLE PRECISION,
	div1_airport VARCHAR(50),
	div2_airport VARCHAR(50),
	year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
	sch_dep_hour INTEGER,
    sch_arr_hour INTEGER,
    dep_hour INTEGER,
    arr_hour INTEGER,
	time_bucket VARCHAR(50)
);

SELECT column_name
FROM information_schema.columns
WHERE table_name = 'fact_flights'
ORDER BY ordinal_position;

SELECT COUNT(*) FROM fact_flights;

TRUNCATE TABLE fact_flights;

ALTER TABLE

CREATE INDEX idx_carrier
ON fact_flights(op_unique_carrier);

CREATE INDEX idx_route
ON fact_flights(origin_airport_id, dest_airport_id);

CREATE INDEX idx_day_of_week
ON fact_flights(day_of_week);

CREATE INDEX idx_time_bucket
ON fact_flights(time_bucket);