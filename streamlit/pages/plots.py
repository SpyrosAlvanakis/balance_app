import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Set the Utils path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
# Utils functions
from connect import connect
from aed_rows import correct_gs_types 

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

# Add a title
st.title("Balance plots")

# Add period type selector
period_type = st.selectbox(
    "Select period type",
    ["Custom Range", "Specific Month", "Specific Week"]
)

# Date selection based on period type
if period_type == "Custom Range":
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=pd.Timestamp.now() + pd.Timedelta(days=7))
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