import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Utils functions
from utils.connect import connect
from utils.aed_rows import correct_gs_types 
from utils.authentication import auth_sidebar, is_authenticated
from utils.blur_css_helper import apply_blur_css

# Add authentication sidebar
auth_sidebar()

# Add a title
st.title("Balance Visualizations")

# Apply CSS for blurring if not authenticated
if not is_authenticated():
    st.info("Please log in to see clear visualizations and detailed data.")
    apply_blur_css()

# Connect to the Google Sheets API
sheet = connect()

# Get raw values including headers
raw_data = sheet.get_values()
headers = raw_data[0]
values = raw_data[1:]

# Create DataFrame with proper number parsing
df = pd.DataFrame(values, columns=headers)

# Correct the types of the columns
df = correct_gs_types(df)

# Sort data by Date for time series
df_sorted = df.sort_values(by="Date")

# Add period type selector
period_type = st.selectbox(
    "Select period type",
    ["Custom Range", "Specific Month", "Specific Week"]
)

# Date selection based on period type
if period_type == "Custom Range":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=pd.Timestamp.now() + pd.Timedelta(days=-30))
    with col2:
        end_date = st.date_input("End date", value=pd.Timestamp.now())
        
elif period_type == "Specific Month":
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Select month", range(1, 13))
    with col2:
        year = st.selectbox("Select year", range(2023, 2027))
    start_date = pd.Timestamp(year=year, month=month, day=1).date()
    end_date = (pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(1)).date()
    
else:  # Specific Week
    start_date = st.date_input("Select any date in the desired week", value=pd.Timestamp.now())
    end_date = start_date + pd.Timedelta(days=6)

# Convert dates to datetime for comparison
start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

# Filter dataframe by date
filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# Select visualization type
vis_type = st.radio(
    "Select visualization type",
    ["Category Distribution", "Total Over Time"],
    horizontal=True
)

if vis_type == "Category Distribution":
    # Create columns for side-by-side charts
    chart_col1, chart_col2 = st.columns(2)

    # Income pie chart in first column
    with chart_col1:
        income_df = filtered_df[filtered_df['Type'] == 1]
        income_by_category = income_df.groupby('Category')['Amount'].sum().reset_index()
        total_income = income_by_category['Amount'].sum()

        if not income_by_category.empty:
            fig_income = px.pie(
                income_by_category,
                values='Amount',
                names='Category',
                title=f'Income Distribution by Category',
                hole=0.7,  # Larger hole for better text visibility
            )
            
            # Remove percentage labels
            fig_income.update_traces(textposition='none')
            
            # Add total in center
            fig_income.add_annotation(
                text=f'Total<br>${total_income:,.2f}',
                x=0.5, y=0.5,
                font_size=15,
                showarrow=False
            )
            
            st.plotly_chart(fig_income, use_container_width=True)
            
            # Display cumulative income by category
            st.write("Cumulative Income by Category:")
            income_table = income_by_category.sort_values('Amount', ascending=False)
            income_table['Amount'] = income_table['Amount'].round(2)
            st.dataframe(income_table)

    # Expense pie chart in second column
    with chart_col2:
        expense_df = filtered_df[filtered_df['Type'] == 0]
        expense_by_category = expense_df.groupby('Category')['Amount'].sum().reset_index()
        total_expenses = expense_by_category['Amount'].sum()

        if not expense_by_category.empty:
            fig_expense = px.pie(
                expense_by_category,
                values='Amount',
                names='Category',
                title=f'Expense Distribution by Category',
                hole=0.7,  # Larger hole for better text visibility
            )
            
            # Remove percentage labels
            fig_expense.update_traces(textposition='none')
            
            # Add total in center
            fig_expense.add_annotation(
                text=f'Total<br>${total_expenses:,.2f}',
                x=0.5, y=0.5,
                font_size=15,
                showarrow=False
            )
            
            st.plotly_chart(fig_expense, use_container_width=True)
            
            # Display cumulative expenses by category
            st.write("Cumulative Expenses by Category:")
            expense_table = expense_by_category.sort_values('Amount', ascending=False)
            expense_table['Amount'] = expense_table['Amount'].round(2)
            st.dataframe(expense_table)

    # Add summary if authenticated
    if is_authenticated() and not income_by_category.empty and not expense_by_category.empty:
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with col2:
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
        
        with col3:
            balance = total_income - total_expenses
            st.metric("Balance", f"${balance:,.2f}", delta=f"${balance:,.2f}")

else:  # Total Over Time visualization - SIMPLE LINE CHART
    st.subheader("Balance Over Time")
    
    # Prepare time series data
    # First, filter the sorted dataframe by the selected date range
    time_df = df_sorted[(df_sorted['Date'] >= start_date) & (df_sorted['Date'] <= end_date)]
    
    if not time_df.empty:
        # Create a simple line chart for Total
        fig_time = px.line(
            time_df, 
            x='Date', 
            y='Total',
            title='Balance Over Time',
            labels={'Total': 'Balance ($)', 'Date': 'Date'},
            markers=True
        )
        
        # Update layout
        fig_time.update_layout(
            xaxis_title='Date',
            yaxis_title='Total Balance ($)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_time, use_container_width=True)
        
        # Show simple summary statistics
        if is_authenticated():
            st.subheader("Summary")
            
            # Calculate statistics
            start_balance = time_df.iloc[0]['Total'] if not time_df.empty else 0
            end_balance = time_df.iloc[-1]['Total'] if not time_df.empty else 0
            balance_change = end_balance - start_balance
            
            # Show metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Starting Balance", 
                    f"${start_balance:.2f}"
                )
            
            with col2:
                st.metric(
                    "Ending Balance", 
                    f"${end_balance:.2f}", 
                    delta=f"{balance_change:.2f}"
                )
    else:
        st.warning("No data available for the selected date range.")