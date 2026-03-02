import joblib
import pandas as pd

# Default appliance power ratings (kW)
DEFAULT_POWER = {
    "ac_kwh": 1.5,
    "geyser_kwh": 2.0,
    "fridge_kwh": 0.3,
    "wm_kwh": 0.5,
    "tv_kwh": 0.1,
    "fan_kwh": 0.07,
    "lighting_kwh": 0.05
}

# Load model
best_xgb = joblib.load("best_xgb.pkl")
features = best_xgb.get_booster().feature_names


# ------------------------------------------------
# Helper function: Only Prediction (No recursion)
# ------------------------------------------------
def predict_bill(input_dict):

    user_df = pd.DataFrame([input_dict])

    user_df["household_id"] = 0

    user_df["total_kwh"] = (
        user_df["ac_kwh"] +
        user_df["geyser_kwh"] +
        user_df["fridge_kwh"] +
        user_df["wm_kwh"] +
        user_df["tv_kwh"] +
        user_df["fan_kwh"] +
        user_df["lighting_kwh"]
    )

    user_df["city_Delhi"] = 1 if input_dict.get("city") == "Delhi" else 0
    user_df["city_Kolkata"] = 1 if input_dict.get("city") == "Kolkata" else 0
    user_df["city_Mumbai"] = 1 if input_dict.get("city") == "Mumbai" else 0
    user_df["season_Summer"] = 1 if input_dict.get("season") == "Summer" else 0
    user_df["season_Winter"] = 1 if input_dict.get("season") == "Winter" else 0

    user_df = user_df[features]

    return best_xgb.predict(user_df)[0]


# ------------------------------------------------
# Main Smart Assistant
# ------------------------------------------------
def smart_energy_assistant(input_dict, threshold=25, appliance_power=None):

    if appliance_power is None:
        appliance_power = DEFAULT_POWER

    # Automatic month handling
    current_month = input_dict["month"]
    current_year = input_dict["year"]

    if current_month == 12:
        prediction_month = 1
        prediction_year = current_year + 1
    else:
        prediction_month = current_month + 1
        prediction_year = current_year

    input_dict["month"] = prediction_month
    input_dict["year"] = prediction_year

    predicted_bill = predict_bill(input_dict)

    # Appliance cost breakdown
    rate = input_dict["rate"]

    appliance_cols = list(DEFAULT_POWER.keys())

    costs = {
        col.replace("_kwh", ""): input_dict[col] * rate
        for col in appliance_cols
    }

    total_cost = sum(costs.values())

    recommendations = []

    for appliance_col in appliance_cols:

        cost = input_dict[appliance_col] * rate
        percent = (cost / total_cost) * 100

        if percent > threshold:

            T = threshold / 100
            O = total_cost - cost
            new_cost = (T * O) / (1 - T)
            new_kwh = new_cost / rate

            # ---- ML saving ----
            modified_input = input_dict.copy()
            modified_input[appliance_col] = new_kwh

            new_bill = predict_bill(modified_input)
            ml_saving = predicted_bill - new_bill

            # ---- Time conversion ----
            reduction_kwh = input_dict[appliance_col] - new_kwh
            power_kw = appliance_power.get(appliance_col, 1)

            monthly_hours = reduction_kwh / power_kw
            daily_minutes = round((monthly_hours / 30) * 60)

            if daily_minutes >= 60:
                hours = daily_minutes // 60
                minutes = daily_minutes % 60
                if minutes == 0:
                    time_text = f"{hours} hour(s)"
                else:
                    time_text = f"{hours} hour(s) {minutes} minute(s)"
            else:
                time_text = f"{daily_minutes} minute(s)"

            appliance_name = appliance_col.replace("_kwh", "").upper()

            recommendations.append(
                f"{appliance_name} contributes {percent:.1f}% of your bill.\n"
                f"To reach {threshold}% share:\n"
                f"• Reduce approx {time_text} per day\n"
                f"• Estimated ML saving: ₹{ml_saving:.2f}"
            )

    if not recommendations:
        recommendations.append("Your appliance usage is well balanced.")

    return {
        "Prediction Month": prediction_month,
        "Prediction Year": prediction_year,
        "Predicted Bill": round(predicted_bill, 2),
        "Appliance Costs": costs,
        "Recommendations": recommendations
    }