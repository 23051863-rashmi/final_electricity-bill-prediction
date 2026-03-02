import streamlit as st


def get_user_input(prefix=""):

    # -------------------------
    # Basic Household Info
    # -------------------------
    house_size = st.number_input(
        "House Size (sqft)", 500, 5000, 1200,
        key=f"{prefix}_house_size"
    )

    residents = st.number_input(
        "Residents", 1, 10, 4,
        key=f"{prefix}_residents"
    )

    rate = st.number_input(
        "Electricity Rate (₹ per kWh)", 1.0, 20.0, 8.0,
        key=f"{prefix}_rate"
    )

    avg_temp = st.number_input(
        "Average Temperature (°C)", 0, 50, 30,
        key=f"{prefix}_avg_temp"
    )

    prev_bill = st.number_input(
        "Previous Month Bill (₹)", 0.0, 20000.0, 3200.0,
        key=f"{prefix}_prev_bill"
    )

    month = st.selectbox(
        "Current Month", list(range(1, 13)),
        key=f"{prefix}_month"
    )

    year = st.number_input(
        "Year", 2020, 2035, 2024,
        key=f"{prefix}_year"
    )

    city = st.selectbox(
        "City", ["Delhi", "Mumbai", "Kolkata"],
        key=f"{prefix}_city"
    )

    season = st.selectbox(
        "Season", ["Summer", "Winter"],
        key=f"{prefix}_season"
    )

    # -------------------------
    # Appliance Usage Section
    # -------------------------
    st.subheader("⚡ Appliance Usage (kWh per month)")

    ac_kwh = st.number_input("AC", 0.0, 500.0, 150.0, key=f"{prefix}_ac")
    geyser_kwh = st.number_input("Geyser", 0.0, 300.0, 60.0, key=f"{prefix}_geyser")
    fridge_kwh = st.number_input("Fridge", 0.0, 200.0, 40.0, key=f"{prefix}_fridge")
    wm_kwh = st.number_input("Washing Machine", 0.0, 200.0, 30.0, key=f"{prefix}_wm")
    tv_kwh = st.number_input("TV", 0.0, 200.0, 35.0, key=f"{prefix}_tv")
    fan_kwh = st.number_input("Fan", 0.0, 200.0, 50.0, key=f"{prefix}_fan")
    lighting_kwh = st.number_input("Lighting", 0.0, 200.0, 45.0, key=f"{prefix}_lighting")

    # -------------------------
    # Return Input Dictionary
    # -------------------------
    return {
        "house_size": house_size,
        "residents": residents,
        "rate": rate,
        "avg_temp": avg_temp,
        "ac_kwh": ac_kwh,
        "geyser_kwh": geyser_kwh,
        "fridge_kwh": fridge_kwh,
        "wm_kwh": wm_kwh,
        "tv_kwh": tv_kwh,
        "fan_kwh": fan_kwh,
        "lighting_kwh": lighting_kwh,
        "prev_bill": prev_bill,
        "month": month,
        "year": year,
        "city": city,
        "season": season
    }