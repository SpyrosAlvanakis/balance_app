# Generic functions
import streamlit as st 
import pandas as pd
import numpy as np
import sys
import os

# Utils functions
from utils.connect import connect
from utils.aed_rows import add_row, delete_row, correct_gs_types
from utils.schema import Categories, Data
from utils.authentication import auth_sidebar, is_authenticated

# Add a title
st.title("Balance Data")

# Show authentication sidebar
auth_sidebar()

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

# Sort data by Date (latest first)
df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

# Display dataframe with CSS blurring if not authenticated
if is_authenticated():
    # Show the current total
    st.subheader(f'Current total: {df.Total.iloc[0]}')

    # Show normal dataframe
    st.dataframe(df, use_container_width=True)
else:
    # Show blurred dataframe with a message
    st.info("Please log in to see clear data and interact with the application.")
    
    # Apply CSS for blurring - more aggressive blur and targeting the specific elements
    st.markdown("""
    <style>
    /* Target the Streamlit dataframe */
    .stDataFrame, .stTable {
        filter: blur(8px);
        pointer-events: none;
    }
    
    /* Target inner elements to ensure blur works across browsers */
    .stDataFrame div, .stTable div, 
    .stDataFrame span, .stTable span,
    .stDataFrame td, .stTable td,
    .stDataFrame th, .stTable th {
        filter: blur(6px) !important;
    }
    
    /* Ensures the table headers are also blurred */
    [data-testid="StyledDataFrameDataCell"],
    [data-testid="StyledDataFrameHeaderCell"] {
        filter: blur(6px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display dataframe directly - the CSS will apply the blur
    st.dataframe(df)

# --- ADD NEW ENTRY ---
with st.expander("➕ Add Income/Expense", expanded=False):
    with st.form("add_entry"):
        date = st.date_input("Select Date")
        category = st.selectbox("Select Category", [cat.value for cat in Categories])
        amount = st.number_input("Enter Amount", min_value=0.01, step=0.01)
        income = st.radio("Type", ["Expense", "Income"])

        submitted = st.form_submit_button("Add Entry")
        if submitted:
            if is_authenticated():
                try:
                    income_flag = 1 if income == "Income" else 0

                    # Compute new Total
                    last_total = df.iloc[0]["Total"] if not df.empty else 0
                    new_total = last_total + amount if income_flag == 1 else last_total - amount

                    # Convert date to string format
                    date_str = date.strftime("%Y-%m-%d")

                    # Create new row
                    new_row = [date_str, category, amount, new_total, income_flag]
                    
                    # Add row with validation
                    if add_row(sheet, new_row):
                        st.success(f"✅ {income} of {amount} added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add entry. Please check the data and try again.")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("💡 Log in to add or delete entries")
        
# --- DELETE ENTRY ---
with st.expander("🗑️ Delete Entry", expanded=False):
    row_to_delete = st.selectbox("Select a row to delete", df.index)
    
    # Show current row data before deletion
    if row_to_delete is not None:
        st.write("Selected row data:")
        selected_row = df.loc[row_to_delete]
        st.write({
            "Date": selected_row["Date"].strftime("%Y-%m-%d"),
            "Category": selected_row["Category"],
            "Amount": selected_row["Amount"],
            "Type": "Income" if selected_row["Type"] == 1 else "Expense"
        })
        
        # Add confirmation checkbox
        confirm_delete = st.checkbox("I confirm I want to delete this entry")
        
        if st.button("Delete Selected Row", disabled=not confirm_delete):
            if is_authenticated():
                try:
                    if delete_row(sheet, row_to_delete + 2):
                        st.success(f"✅ Row {row_to_delete} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("💡 Log in to add or delete entries")
