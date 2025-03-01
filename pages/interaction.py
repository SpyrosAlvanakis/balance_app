# Generic functions
import streamlit as st 
import pandas as pd
import numpy as np
import sys
import os

# Utils functions
from utils.connect import connect
from utils.aed_rows import add_row, delete_row, correct_gs_types #  edit_row,
from utils.schema import Categories, Data
from utils.authentication import check_password_widget

# authentication
if ('user' not in st.session_state) or (st.session_state['user'] is None):
    st.session_state['user'] = None
    check_password_widget()
if (st.session_state['user'] is None):
    st.stop()

# Add a title
st.title("Interaction")

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

st.dataframe(df)

# --- ADD NEW ENTRY ---
# In your Streamlit app
with st.expander("➕ Add Income/Expense", expanded=False):
    with st.form("add_entry"):
        date = st.date_input("Select Date")
        category = st.selectbox("Select Category", [cat.value for cat in Categories])  # Use enum values
        amount = st.number_input("Enter Amount", min_value=0.01, step=0.01)
        income = st.radio("Type", ["Expense", "Income"])

        submitted = st.form_submit_button("Add Entry")
        if submitted:
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

# # --- EDIT ENTRY ---
# with st.expander("✏️ Edit Entry", expanded=False):
#     row_to_edit = st.selectbox("Select a row to edit", df.index)

#     if row_to_edit is not None:
#         with st.form("edit_entry"):
#             # Pre-fill form with existing values
#             date = st.date_input("Edit Date", value=pd.to_datetime(df.loc[row_to_edit, "Date"]))
            
#             # Use Categories enum values for the selectbox
#             category = st.selectbox(
#                 "Edit Category", 
#                 [cat.value for cat in Categories],
#                 index=[cat.value for cat in Categories].index(df.loc[row_to_edit, "Category"])
#             )
            
#             amount = st.number_input(
#                 "Edit Amount", 
#                 min_value=0.01, 
#                 step=0.01, 
#                 value=float(df.loc[row_to_edit, "Amount"])
#             )

#             # Convert Type 0/1 to "Income"/"Expense"
#             current_type = "Income" if df.loc[row_to_edit, "Type"] == 1 else "Expense"
#             income = st.radio(
#                 "Edit Type", 
#                 ["Income", "Expense"], 
#                 index=["Income", "Expense"].index(current_type)
#             )

#             submitted = st.form_submit_button("Edit Entry")

#             if submitted:
#                 try:
#                     income_flag = 1 if income == "Income" else 0
                    
#                     # Calculate new total
#                     prev_total = df.loc[row_to_edit - 1, "Total"] if row_to_edit > 0 else 0
#                     new_total = prev_total + amount if income_flag == 1 else prev_total - amount
                    
#                     # Create row data for validation
#                     edited_row = [date, category, amount, new_total, income_flag]
                    
#                     # Attempt to edit row with validation
#                     if edit_row(sheet, row_to_edit + 2, edited_row):
#                         st.success(f"✅ Row {row_to_edit} updated successfully!")
#                         st.rerun()
#                     else:
#                         st.error("Failed to update entry. Please check the data and try again.")
                
#                 except Exception as e:
#                     st.error(f"An error occurred: {str(e)}")

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
            try:
                if delete_row(sheet, row_to_delete + 2):
                    st.success(f"✅ Row {row_to_delete} deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete entry. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")