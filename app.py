import streamlit as st
import pandas as pd
import shap
import matplotlib.pyplot as plt
from model import smart_energy_assistant, best_xgb, features
from scenario_schedular import get_user_input

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Smart Energy Optimizer", layout="wide")

# ================= THEME =================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
.block-container {
    background-color: rgba(255,255,255,0.05);
    padding: 2rem;
    border-radius: 15px;
}
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
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #00ff9d);
    color: black;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}
[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.title("Smart Energy Consumption Optimizer")

tabs = st.tabs(["Prediction", "Scenario Simulator", "Explainability"])

# =================================================
# =============== PREDICTION TAB ==================
# =================================================
with tabs[0]:
    st.header("Bill Prediction")

    user_input = get_user_input("pred")
    threshold = st.slider("Appliance Share Alert Threshold (%)", 10, 50, 25)

    if st.button("Predict"):
        result = smart_energy_assistant(user_input, threshold=threshold)

        col1, col2 = st.columns(2)
        col1.metric("Predicted Bill", f"₹{result['Predicted Bill']}")
        col2.metric(
            "Prediction Month",
            f"{result['Prediction Month']}/{result['Prediction Year']}"
        )

        st.subheader("Appliance Cost Breakdown")

        costs_df = pd.DataFrame(
            result["Appliance Costs"].items(),
            columns=["Appliance", "Cost"]
        )

        colA, colB = st.columns(2)

        # ===== Bar chart (6 cm height) =====
        with colA:
            fig_bar, ax_bar = plt.subplots(figsize=(4.5, 2.0))
            ax_bar.bar(costs_df["Appliance"], costs_df["Cost"])
            ax_bar.set_ylabel("Cost")
            ax_bar.set_xlabel("Appliance")
            plt.xticks(rotation=90, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig_bar)

        # ===== Pie chart (same size) =====
        with colB:
            fig_pie, ax_pie = plt.subplots(figsize=(3.5, 2.0))
            ax_pie.pie(
                costs_df["Cost"],
                labels=costs_df["Appliance"],
                autopct='%1.1f%%',
                textprops={'fontsize':8}
            )
            ax_pie.set_title("Cost Distribution", fontsize=10)
            plt.tight_layout()
            st.pyplot(fig_pie)

        st.subheader("Usage Recommendations")

        for rec in result["Recommendations"]:
            formatted = rec.replace("•", "\n•")
            if "reduce" in rec.lower():
                st.warning(formatted)
            else:
                st.success(formatted)

# =================================================
# ============= SCENARIO TAB ======================
# =================================================
with tabs[1]:
    st.header("Scenario Simulator")

    user_input = get_user_input("sim")
    threshold = st.slider("Maximum Allowed Appliance Share (%)", 10, 50, 25)

    if st.button("Run Simulation"):
        original_bill = smart_energy_assistant(user_input)["Predicted Bill"]

        appliance_cols = [
            "ac_kwh","geyser_kwh","fridge_kwh",
            "wm_kwh","tv_kwh","fan_kwh","lighting_kwh"
        ]
        rate = user_input["rate"]

        costs = {col: user_input[col]*rate for col in appliance_cols}
        total_cost = sum(costs.values())

        modified_input = user_input.copy()

        for col, cost in costs.items():
            percent = (cost/total_cost)*100
            if percent > threshold:
                T = threshold/100
                O = total_cost - cost
                new_cost = (T*O)/(1-T)
                modified_input[col] = new_cost/rate

        optimized_bill = smart_energy_assistant(modified_input)["Predicted Bill"]
        saving = original_bill - optimized_bill

        col1, col2, col3 = st.columns(3)
        col1.metric("Original Bill", f"₹{round(original_bill,2)}")
        col2.metric("Optimized Bill", f"₹{round(optimized_bill,2)}")
        col3.metric("Saving", f"₹{round(saving,2)}")

# =================================================
# ============= EXPLAINABILITY TAB ================
# =================================================
with tabs[2]:
    st.header("Explainability")

    user_input = get_user_input("shap")

    if st.button("Explain Prediction"):
        result = smart_energy_assistant(user_input)
        predicted_bill = result["Predicted Bill"]
        previous_bill = user_input["prev_bill"]

        change = predicted_bill - previous_bill

        col1, col2, col3 = st.columns(3)
        col1.metric("Previous Bill", f"₹{previous_bill}")
        col2.metric("Predicted Bill", f"₹{predicted_bill}")
        col3.metric("Change", f"₹{round(change,2)}")

        user_df = pd.DataFrame([user_input])
        user_df["household_id"] = 0

        user_df["total_kwh"] = (
            user_df["ac_kwh"] + user_df["geyser_kwh"] + user_df["fridge_kwh"] +
            user_df["wm_kwh"] + user_df["tv_kwh"] + user_df["fan_kwh"] +
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

        shap_df = pd.DataFrame({
            "Feature": features,
            "Impact": shap_values[0]
        }).sort_values(by="Impact", key=abs, ascending=False)

        st.subheader("Top Influencing Features")
        st.bar_chart(shap_df.set_index("Feature").head(8))
