import streamlit as st
import pandas as pd
import shap
import matplotlib.pyplot as plt
from model import smart_energy_assistant, best_xgb, features
from scenario_schedular import get_user_input

# ----------------------------------

# PAGE CONFIG

# ----------------------------------

st.set_page_config(page_title="Smart Energy Optimizer", layout="wide")

# ----------------------------------

# ENERGY THEME UI

# ----------------------------------

st.markdown("""

<style>

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

/* Content card */
.block-container {
    background-color: rgba(255,255,255,0.05);
    padding: 2rem;
    border-radius: 15px;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    background-color: rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px;
    margin-right: 5px;
    color: white;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #00c6ff, #00ff9d);
    color: black;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #00ff9d);
    color: black;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}

.stButton>button:hover {
    background: linear-gradient(90deg, #00ff9d, #00c6ff);
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 12px;
}

</style>

""", unsafe_allow_html=True)

# ----------------------------------

# TITLE

# ----------------------------------

st.title("⚡ Smart Energy Consumption Optimizer")

tabs = st.tabs(["🔮 Prediction", "🔁 Scenario Simulator", "🧠 Explainability"])

# ==================================

# 🔮 Prediction Tab

# ==================================

with tabs[0]:

```
st.header("🔮 Bill Prediction")

user_input = get_user_input("pred")

threshold = st.slider(
    "Appliance Share Alert Threshold (%)",
    10, 50, 25,
    key="pred_threshold"
)

if st.button("Predict", key="pred_button"):

    result = smart_energy_assistant(user_input, threshold=threshold)

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Predicted Bill", f"₹{result['Predicted Bill']}")
    col2.metric(
        "Prediction Month",
        f"{result['Prediction Month']}/{result['Prediction Year']}"
    )

    # Appliance Breakdown
    st.subheader("📊 Appliance Cost Breakdown")

    costs_df = pd.DataFrame(
        result["Appliance Costs"].items(),
        columns=["Appliance", "Cost"]
    )

    colA, colB = st.columns([1,1])

    with colA:
        st.bar_chart(costs_df.set_index("Appliance"))

    with colB:
        fig, ax = plt.subplots(figsize=(4,4))
        ax.pie(
            costs_df["Cost"],
            labels=costs_df["Appliance"],
            autopct='%1.1f%%',
            textprops={'fontsize':9}
        )
        ax.set_title("Cost Distribution")
        st.pyplot(fig, use_container_width=True)

    # Recommendations
    st.subheader("💡 Usage Recommendations")

    for rec in result["Recommendations"]:
        if "reduce" in rec.lower():
            st.warning(rec)
        else:
            st.success(rec)
```

# ==================================

# 🔁 Scenario Simulator Tab

# ==================================

with tabs[1]:

```
st.header("🔁 Smart Scenario Builder")

user_input = get_user_input("sim")

st.subheader("⚙ Optimization Strategy")

threshold = st.slider(
    "Maximum Allowed Appliance Share (%)",
    10, 50, 25,
    key="sim_threshold"
)

strategy = st.selectbox(
    "Reduction Strategy",
    ["Proportional (Auto to Threshold)",
     "Fixed Percentage Reduction"],
    key="sim_strategy"
)

custom_reduction = st.slider(
    "Fixed Reduction %",
    5, 50, 10,
    key="sim_fixed",
    disabled=(strategy != "Fixed Percentage Reduction")
)

if st.button("Run Simulation", key="sim_button"):

    original_result = smart_energy_assistant(user_input)
    original_bill = original_result["Predicted Bill"]

    appliance_cols = [
        "ac_kwh","geyser_kwh","fridge_kwh",
        "wm_kwh","tv_kwh","fan_kwh","lighting_kwh"
    ]

    rate = user_input["rate"]

    costs = {col: user_input[col]*rate for col in appliance_cols}
    total_cost = sum(costs.values())

    individual_savings = {}

    for col, cost in costs.items():

        percent = (cost/total_cost)*100

        if percent > threshold:

            modified_input = user_input.copy()

            T = threshold/100
            O = total_cost - cost
            new_cost = (T*O)/(1-T)
            new_kwh = new_cost/rate

            modified_input[col] = new_kwh

            new_bill = smart_energy_assistant(modified_input)["Predicted Bill"]
            individual_savings[col] = original_bill - new_bill

    linear_expected_saving = sum(individual_savings.values())

    modified_input = user_input.copy()

    for col, cost in costs.items():

        percent = (cost/total_cost)*100

        if percent > threshold:

            T = threshold/100
            O = total_cost - cost
            new_cost = (T*O)/(1-T)
            new_kwh = new_cost/rate

            modified_input[col] = new_kwh

    optimized_bill = smart_energy_assistant(modified_input)["Predicted Bill"]

    ml_actual_saving = original_bill - optimized_bill
    interaction_effect = linear_expected_saving - ml_actual_saving

    col1, col2, col3 = st.columns(3)
    col1.metric("Original Bill", f"₹{round(original_bill,2)}")
    col2.metric("Optimized Bill", f"₹{round(optimized_bill,2)}")
    col3.metric("Actual ML Saving", f"₹{round(ml_actual_saving,2)}")

    st.subheader("📊 Optimization Analysis")
    st.write(f"🔹 Linear Expected Saving: ₹{round(linear_expected_saving,2)}")
    st.write(f"🔹 ML Actual Saving: ₹{round(ml_actual_saving,2)}")
    st.write(f"🔹 Interaction Effect: ₹{round(interaction_effect,2)}")

    if interaction_effect > 0:
        st.info("⚠ Some savings overlap due to feature interaction.")
    else:
        st.success("Features behave almost independently.")
```

# ==================================

# 🧠 Explainability Tab

# ==================================

with tabs[2]:

```
st.header("🧠 Bill Comparison & Explainability")

user_input = get_user_input("shap")

if st.button("Explain Prediction", key="shap_button"):

    result = smart_energy_assistant(user_input)

    predicted_bill = result["Predicted Bill"]
    previous_bill = user_input["prev_bill"]

    change = predicted_bill - previous_bill
    percent_change = (change/previous_bill)*100 if previous_bill != 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Previous Bill", f"₹{previous_bill}")
    col2.metric("Predicted Bill", f"₹{predicted_bill}")
    col3.metric("Change", f"₹{round(change,2)}", f"{round(percent_change,2)}%")

    if change > 0:
        st.warning("📈 Your bill is expected to increase.")
    elif change < 0:
        st.success("📉 Your bill is expected to decrease.")
    else:
        st.info("Bill expected to remain stable.")

    user_df = pd.DataFrame([user_input])
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

    user_df["city_Delhi"] = 1 if user_input["city"]=="Delhi" else 0
    user_df["city_Kolkata"] = 1 if user_input["city"]=="Kolkata" else 0
    user_df["city_Mumbai"] = 1 if user_input["city"]=="Mumbai" else 0
    user_df["season_Summer"] = 1 if user_input["season"]=="Summer" else 0
    user_df["season_Winter"] = 1 if user_input["season"]=="Winter" else 0

    user_df = user_df[features]

    explainer = shap.TreeExplainer(best_xgb)
    shap_values = explainer.shap_values(user_df)

    base_value = explainer.expected_value
    st.write(f"🔎 Model Base Value: ₹{round(base_value,2)}")

    shap_df = pd.DataFrame({
        "Feature": features,
        "Impact": shap_values[0]
    }).sort_values(by="Impact", key=abs, ascending=False)

    st.subheader("📊 Top Influencing Features")
    st.bar_chart(shap_df.set_index("Feature").head(8))
    st.dataframe(shap_df.head(8).style.format({"Impact":"{:.2f}"}))

    top_positive = shap_df[shap_df["Impact"]>0].head(3)
    top_negative = shap_df[shap_df["Impact"]<0].head(3)

    if change > 0:
        explanation = "📈 Bill increased due to: " + ", ".join(top_positive["Feature"])
    elif change < 0:
        explanation = "📉 Bill decreased due to: " + ", ".join(top_negative["Feature"])
    else:
        explanation = "Major features balanced each other."

    st.subheader("📝 Explanation Summary")
    st.info(explanation)
```
