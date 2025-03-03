# import streamlit as st
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import plotly.express as px
# import plotly.graph_objects as go

# # Utils functions
# from utils.connect import connect
# from utils.aed_rows import correct_gs_types
# from utils.authentication import auth_sidebar, is_authenticated

# # Add authentication sidebar
# auth_sidebar()

# # Add a title
# st.title("Predict Monthly Balance")

# # Show login requirement for this page
# if not is_authenticated():
#     st.warning("⚠️ This feature requires login to access.")
#     st.info("Please log in using the sidebar or top-right button to access prediction features.")
#     st.stop()  # Stop execution for non-authenticated users

# # Connect to the Google Sheets API
# sheet = connect()

# # Get raw values including headers
# raw_data = sheet.get_values()
# headers = raw_data[0]
# values = raw_data[1:]

# # Create DataFrame with proper number parsing
# df = pd.DataFrame(values, columns=headers)

# # Correct the types of the columns
# df = correct_gs_types(df)

# # Calculate monthly aggregates for historical data
# df['YearMonth'] = df['Date'].dt.strftime('%Y-%m')
# monthly_data = df.groupby(['YearMonth', 'Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
# monthly_data.columns = ['YearMonth', 'Expenses', 'Income']  # Assuming Type 0 is Expenses, 1 is Income
# monthly_data['Net'] = monthly_data['Income'] - monthly_data['Expenses']
# monthly_data['Date'] = pd.to_datetime(monthly_data['YearMonth'] + '-01')
# monthly_data = monthly_data.sort_values('Date')

# # Display historical monthly data
# st.subheader("Historical Monthly Balance")
# st.dataframe(monthly_data[['YearMonth', 'Income', 'Expenses', 'Net']])

# # Create simple prediction based on averages
# if len(monthly_data) >= 3:
#     # Calculate averages based on last 3 months
#     last_3_months = monthly_data.tail(3)
#     avg_income = last_3_months['Income'].mean()
#     avg_expenses = last_3_months['Expenses'].mean()
#     predicted_net = avg_income - avg_expenses
    
#     # Display prediction
#     st.subheader("Prediction for Next Month")
#     cols = st.columns(3)
#     with cols[0]:
#         st.metric("Estimated Income", f"${avg_income:.2f}")
#     with cols[1]:
#         st.metric("Estimated Expenses", f"${avg_expenses:.2f}")
#     with cols[2]:
#         st.metric("Estimated Net", f"${predicted_net:.2f}")
    
#     # Create forecast visualization
#     st.subheader("Balance Forecast")
    
#     # Create future dates for forecast
#     last_date = monthly_data['Date'].max()
#     future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 4)]
    
#     # Create forecast dataframe
#     forecast_df = pd.DataFrame({
#         'Date': future_dates,
#         'Income': [avg_income] * 3,
#         'Expenses': [avg_expenses] * 3,
#         'Net': [predicted_net] * 3,
#         'Type': ['Forecast'] * 3
#     })
    
#     # Combine historical and forecast data
#     historical_viz = monthly_data[['Date', 'Income', 'Expenses', 'Net']].copy()
#     historical_viz['Type'] = 'Historical'
#     combined_df = pd.concat([historical_viz, forecast_df])
    
#     # Create visualization
#     fig = go.Figure()
    
#     # Add income line
#     fig.add_trace(go.Scatter(
#         x=historical_viz['Date'], 
#         y=historical_viz['Income'],
#         mode='lines+markers',
#         name='Historical Income',
#         line=dict(color='green', width=2)
#     ))
    
#     # Add expenses line
#     fig.add_trace(go.Scatter(
#         x=historical_viz['Date'], 
#         y=historical_viz['Expenses'],
#         mode='lines+markers',
#         name='Historical Expenses',
#         line=dict(color='red', width=2)
#     ))
    
#     # Add net line
#     fig.add_trace(go.Scatter(
#         x=historical_viz['Date'], 
#         y=historical_viz['Net'],
#         mode='lines+markers',
#         name='Historical Net',
#         line=dict(color='blue', width=2)
#     ))
    
#     # Add forecast lines (dashed)
#     fig.add_trace(go.Scatter(
#         x=forecast_df['Date'], 
#         y=forecast_df['Income'],
#         mode='lines+markers',
#         name='Forecast Income',
#         line=dict(color='green', width=2, dash='dash')
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=forecast_df['Date'], 
#         y=forecast_df['Expenses'],
#         mode='lines+markers',
#         name='Forecast Expenses',
#         line=dict(color='red', width=2, dash='dash')
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=forecast_df['Date'], 
#         y=forecast_df['Net'],
#         mode='lines+markers',
#         name='Forecast Net',
#         line=dict(color='blue', width=2, dash='dash')
#     ))
    
#     # Update layout
#     fig.update_layout(
#         title='Balance Forecast',
#         xaxis_title='Month',
#         yaxis_title='Amount',
#         hovermode='x unified',
#         legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
#     )
    
#     st.plotly_chart(fig, use_container_width=True)
    
#     # Add disclaimer
#     st.info("Note: This is a simple forecast based on the average of the last 3 months. Actual results may vary.")
# else:
#     st.warning("Not enough historical data to make predictions. At least 3 months of data are required.")