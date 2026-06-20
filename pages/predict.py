import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.authentication import auth_sidebar, is_authenticated
from utils.connect import connect
from utils.aed_rows import correct_gs_types
from utils.forecasting import compute_monthly_aggregates, project_flat_average, project_linear_regression

auth_sidebar()

st.title("Predict Balance")

if not is_authenticated():
    st.warning("⚠️ This feature requires login to access.")
    st.info("Please log in using the sidebar to access prediction features.")
    st.stop()

sheet = connect()
raw_data = sheet.get_values()
headers = raw_data[0]
values = raw_data[1:]
df = pd.DataFrame(values, columns=headers)
df = correct_gs_types(df)

monthly = compute_monthly_aggregates(df)

if len(monthly) < 2:
    st.warning("Not enough historical data to make a prediction. At least 2 months of data are required.")
    st.stop()

current_balance = df.sort_values("Date", ascending=False).iloc[0]["Total"]
current_date = pd.Timestamp.now()

target_date = st.date_input("Project my balance on this date", value=current_date + pd.DateOffset(months=3))
target_date = pd.Timestamp(target_date)

method = st.radio("Projection method", ["Flat average", "Linear regression"], horizontal=True)

if target_date <= current_date:
    st.warning("Pick a target date in the future.")
    st.stop()

if method == "Flat average":
    result = project_flat_average(monthly, current_balance, current_date, target_date)
else:
    result = project_linear_regression(monthly, current_balance, current_date, target_date)

if result["warning"]:
    st.info(result["warning"])

st.subheader(f"Prediction for {target_date.strftime('%Y-%m-%d')}")
cols = st.columns(4)
with cols[0]:
    st.metric("Avg Income/Month", f"€{result['avg_income']:.2f}")
with cols[1]:
    st.metric("Avg Expense/Month", f"€{result['avg_expense']:.2f}")
with cols[2]:
    st.metric("Months Ahead", result["months_ahead"])
with cols[3]:
    st.metric("Projected Balance", f"€{result['projected_balance']:.2f}")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=monthly["Date"], y=monthly["Net"].cumsum() + (current_balance - monthly["Net"].cumsum().iloc[-1]),
    mode="lines+markers", name="Historical Balance", line=dict(color="blue"),
))
fig.add_trace(go.Scatter(
    x=[current_date, target_date],
    y=[current_balance, result["projected_balance"]],
    mode="lines+markers", name=f"Projected Balance ({method})",
    line=dict(color="orange", dash="dash"),
))
fig.update_layout(
    title="Balance Projection", xaxis_title="Date", yaxis_title="Balance (€)",
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)
