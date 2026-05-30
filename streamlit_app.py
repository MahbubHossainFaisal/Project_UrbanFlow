import os
from datetime import date, timedelta

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

APP_TITLE = "UrbanFlow Executive Dashboard"
GOLD_SCHEMA = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "GOLD")


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def qualified_table(table_name: str) -> str:
    database = get_required_env("SNOWFLAKE_DATABASE")
    return f"{database}.{GOLD_SCHEMA}.{table_name}".upper()


@st.cache_resource(show_spinner=False)
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=get_required_env("SNOWFLAKE_USER"),
        account=get_required_env("SNOWFLAKE_ACCOUNT"),
        password=get_required_env("SNOWFLAKE_PASSWORD"),
        warehouse=get_required_env("SNOWFLAKE_WAREHOUSE"),
        database=get_required_env("SNOWFLAKE_DATABASE"),
        schema=GOLD_SCHEMA,
        role=get_required_env("SNOWFLAKE_ROLE"),
    )


@st.cache_data(ttl=600, show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    conn = get_snowflake_connection()
    with conn.cursor() as cursor:
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
    df.columns = [column.lower() for column in df.columns]
    return df


def sql_date(value: date) -> str:
    return value.isoformat()


def get_date_bounds() -> tuple[date, date]:
    query = f"""
        WITH daily_volume AS (
            SELECT
                pickup_datetime::DATE AS pickup_date,
                COUNT(*) AS trip_count
            FROM {qualified_table("gold_fact_trips")}
            WHERE is_distance_anomaly = FALSE
              AND is_fare_anomaly = FALSE
            GROUP BY pickup_date
            HAVING COUNT(*) >= 1000
        )
        SELECT
            MIN(pickup_date) AS min_date,
            MAX(pickup_date) AS max_date
        FROM daily_volume
    """
    df = run_query(query)
    min_date = df.loc[0, "min_date"]
    max_date = df.loc[0, "max_date"]
    return pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date()


def get_boroughs() -> list[str]:
    query = f"""
        SELECT DISTINCT pickup_borough
        FROM {qualified_table("gold_fact_trips")}
        WHERE pickup_borough IS NOT NULL
        ORDER BY pickup_borough
    """
    df = run_query(query)
    return df["pickup_borough"].dropna().tolist()


def make_filters(min_date: date, max_date: date, boroughs: list[str]) -> tuple[date, date, list[str]]:
    default_start = max(min_date, max_date - timedelta(days=30))

    st.sidebar.header("Filters")
    selected_dates = st.sidebar.date_input(
        "Pickup date range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = default_start, max_date

    selected_boroughs = st.sidebar.multiselect(
        "Pickup borough",
        options=boroughs,
        default=boroughs,
    )

    return start_date, end_date, selected_boroughs


def borough_filter(selected_boroughs: list[str]) -> str:
    if not selected_boroughs:
        return "AND 1 = 0"
    values = ", ".join("'" + borough.replace("'", "''") + "'" for borough in selected_boroughs)
    return f"AND pickup_borough IN ({values})"


def load_overview(start_date: date, end_date: date, selected_boroughs: list[str]) -> dict[str, pd.DataFrame]:
    date_clause = f"""
        pickup_datetime::DATE BETWEEN '{sql_date(start_date)}' AND '{sql_date(end_date)}'
        {borough_filter(selected_boroughs)}
    """

    trips_table = qualified_table("gold_fact_trips")
    financials_table = qualified_table("gold_fact_financials")
    sustainability_table = qualified_table("gold_fact_sustainability")
    demand_table = qualified_table("gold_agg_demand_weather")

    metrics = run_query(
        f"""
        WITH trips AS (
            SELECT *
            FROM {trips_table}
            WHERE {date_clause}
              AND is_distance_anomaly = FALSE
              AND is_fare_anomaly = FALSE
        ),
        financials AS (
            SELECT f.*
            FROM {financials_table} f
            INNER JOIN trips t USING (trip_id)
        ),
        sustainability AS (
            SELECT s.*
            FROM {sustainability_table} s
            INNER JOIN trips t USING (trip_id)
        )
        SELECT
            COUNT(DISTINCT trips.trip_id) AS total_trips,
            SUM(trips.fare_amount) AS total_revenue,
            AVG(trips.fare_amount) AS avg_fare,
            AVG(trips.trip_distance) AS avg_trip_distance,
            AVG(trips.trip_duration_minutes) AS avg_trip_duration,
            SUM(IFF(trips.is_precipitation, 1, 0)) / NULLIF(COUNT(*), 0) AS precipitation_trip_share,
            SUM(IFF(financials.is_price_anomaly, 1, 0)) AS price_anomaly_count,
            SUM(sustainability.co2_emission_kg) AS total_co2_kg,
            AVG(sustainability.co2_per_passenger_mile) AS avg_co2_per_passenger_mile,
            SUM(IFF(sustainability.is_short_efficiency_risk, 1, 0)) AS short_efficiency_risk_count
        FROM trips
        LEFT JOIN financials USING (trip_id)
        LEFT JOIN sustainability USING (trip_id)
        """
    )

    borough_summary = run_query(
        f"""
        SELECT
            pickup_borough,
            COUNT(*) AS total_trips,
            SUM(fare_amount) AS total_revenue,
            AVG(trip_distance) AS avg_trip_distance
        FROM {trips_table}
        WHERE {date_clause}
          AND is_distance_anomaly = FALSE
          AND is_fare_anomaly = FALSE
        GROUP BY pickup_borough
        ORDER BY total_trips DESC
        """
    )

    weather_summary = run_query(
        f"""
        SELECT
            weather_category,
            SUM(total_trips) AS total_trips,
            SUM(total_revenue) AS total_revenue,
            AVG(avg_fare_amount) AS avg_fare
        FROM {demand_table}
        WHERE pickup_hour_truncated::DATE BETWEEN '{sql_date(start_date)}' AND '{sql_date(end_date)}'
          {borough_filter(selected_boroughs)}
        GROUP BY weather_category
        ORDER BY total_trips DESC
        """
    )

    hourly_demand = run_query(
        f"""
        SELECT
            EXTRACT(HOUR FROM pickup_hour_truncated) AS pickup_hour,
            SUM(total_trips) AS total_trips
        FROM {demand_table}
        WHERE pickup_hour_truncated::DATE BETWEEN '{sql_date(start_date)}' AND '{sql_date(end_date)}'
          {borough_filter(selected_boroughs)}
        GROUP BY pickup_hour
        ORDER BY pickup_hour
        """
    )

    finance_watchlist = run_query(
        f"""
        SELECT
            t.pickup_borough,
            COUNT(*) AS airport_trips,
            SUM(IFF(f.is_price_anomaly, 1, 0)) AS price_anomalies,
            AVG(ABS(f.fare_variance)) AS avg_abs_fare_variance
        FROM {financials_table} f
        INNER JOIN {trips_table} t USING (trip_id)
        WHERE {date_clause}
          AND f.is_airport_trip = TRUE
        GROUP BY t.pickup_borough
        ORDER BY price_anomalies DESC, airport_trips DESC
        """
    )

    return {
        "metrics": metrics,
        "borough_summary": borough_summary,
        "weather_summary": weather_summary,
        "hourly_demand": hourly_demand,
        "finance_watchlist": finance_watchlist,
    }


def format_number(value, suffix: str = "") -> str:
    if pd.isna(value):
        return "0"
    return f"{value:,.0f}{suffix}"


def format_money(value) -> str:
    if pd.isna(value):
        return "$0"
    return f"${value:,.0f}"


def format_decimal(value, digits: int = 2) -> str:
    if pd.isna(value):
        return "0"
    return f"{value:,.{digits}f}"


def add_page_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        [data-testid="stMetric"] {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 14px 16px;
            background: #ffffff;
        }
        [data-testid="stMetricLabel"] {
            color: #334155;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #111827;
            font-size: 1.65rem;
        }
        div[data-testid="stSidebar"] {
            border-right: 1px solid #e5e7eb;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=None,
        layout="wide",
    )
    add_page_style()

    st.title(APP_TITLE)

    try:
        min_date, max_date = get_date_bounds()
        boroughs = get_boroughs()
        start_date, end_date, selected_boroughs = make_filters(min_date, max_date, boroughs)
        data = load_overview(start_date, end_date, selected_boroughs)
    except Exception as exc:
        st.error(f"Unable to load dashboard data: {exc}")
        st.stop()

    metrics = data["metrics"].iloc[0]

    st.caption(f"{start_date:%b %d, %Y} to {end_date:%b %d, %Y}")

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Trips", format_number(metrics["total_trips"]))
    kpi_cols[1].metric("Revenue", format_money(metrics["total_revenue"]))
    kpi_cols[2].metric("Avg fare", format_money(metrics["avg_fare"]))
    kpi_cols[3].metric("CO2 kg", format_number(metrics["total_co2_kg"]))
    kpi_cols[4].metric("Price anomalies", format_number(metrics["price_anomaly_count"]))

    second_cols = st.columns(4)
    second_cols[0].metric("Avg distance", f"{format_decimal(metrics['avg_trip_distance'])} mi")
    second_cols[1].metric("Avg duration", f"{format_decimal(metrics['avg_trip_duration'])} min")
    second_cols[2].metric(
        "Weather share",
        f"{format_decimal(metrics['precipitation_trip_share'] * 100, 1)}%",
    )
    second_cols[3].metric("Short-risk trips", format_number(metrics["short_efficiency_risk_count"]))

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Demand by Borough")
        borough_chart = data["borough_summary"].set_index("pickup_borough")[["total_trips"]]
        st.bar_chart(borough_chart, height=320)

    with right:
        st.subheader("Hourly Demand")
        hourly_chart = data["hourly_demand"].set_index("pickup_hour")[["total_trips"]]
        st.line_chart(hourly_chart, height=320)

    st.divider()

    weather_col, finance_col = st.columns(2)

    with weather_col:
        st.subheader("Weather Demand Mix")
        weather_df = data["weather_summary"].copy()
        st.dataframe(
            weather_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "weather_category": "Weather",
                "total_trips": st.column_config.NumberColumn("Trips", format="%d"),
                "total_revenue": st.column_config.NumberColumn("Revenue", format="$%d"),
                "avg_fare": st.column_config.NumberColumn("Avg fare", format="$%.2f"),
            },
        )

    with finance_col:
        st.subheader("Airport Fare Watchlist")
        finance_df = data["finance_watchlist"].copy()
        st.dataframe(
            finance_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "pickup_borough": "Pickup borough",
                "airport_trips": st.column_config.NumberColumn("Airport trips", format="%d"),
                "price_anomalies": st.column_config.NumberColumn("Anomalies", format="%d"),
                "avg_abs_fare_variance": st.column_config.NumberColumn("Avg variance", format="$%.2f"),
            },
        )


if __name__ == "__main__":
    render_dashboard()
