import streamlit as st 

st.title("Balance App")

st.markdown("""
## Welcome to the balance app!

This application helps you manage and visualize your personal finances. You can:

- View and manage your income and expenses
- Visualize your financial data with interactive charts
- Predict future expenses based on historical data

**Note:** You can view blurred data without logging in, but you'll need to log in to interact with the app fully.
""")

# Show features with images
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("💵 Track Expenses")
    st.info("Add and categorize your expenses to keep track of where your money goes.")

with col2:
    st.subheader("📊 Visualize Data")
    st.info("See beautiful charts that help you understand your spending habits.")

with col3:
    st.subheader("🔮 Predict Trends")
    st.info("Use historical data to predict future expenses and plan ahead.")
