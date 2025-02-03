# Generic functions
import streamlit as st 
import pandas as pd
import numpy as np
import sys
import os

# Set the Utils path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))

# Utils functions
from connect import connect
from aed_rows import add_row, edit_row, delete_row

# Connect to the Google Sheets API
sheet = connect()

# Add a title
st.title("Interaction")

# Fetch and display the current data
df = pd.DataFrame(sheet.get_all_records())

# Ensure 'Date' is treated as datetime for proper sorting
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Sort data by Date (latest first)
df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

st.dataframe(df)

# --- ADD NEW ENTRY ---
with st.expander("➕ Add Income/Expense", expanded=False):
    with st.form("add_entry"):
        date = st.date_input("Select Date")
        category = st.selectbox("Select Category", df["Category"].unique())
        amount = st.number_input("Enter Amount", min_value=0.01, step=0.01)
        income = st.radio("Type", ["Expense", "Income"])

        submitted = st.form_submit_button("Add Entry")
        if submitted:
            income_flag = 1 if income == "Income" else 0

            # Compute new Total
            last_total = df.iloc[0]["Total"] if not df.empty else 0
            new_total = last_total + amount if income_flag == 1 else last_total - amount

            # Convert date to string format
            date_str = date.strftime("%Y-%m-%d")

            # Insert new row at the top (index 2 because 1 is header in Sheets)
            new_row = [date_str, category, amount, new_total, income_flag]
            add_row(sheet, new_row)

            st.success(f"✅ {income} of {amount} added successfully!")
            st.rerun()

# --- EDIT ENTRY ---
with st.expander("✏️ Edit Entry", expanded=False):
    row_to_edit = st.selectbox("Select a row to edit", df.index)

    if row_to_edit is not None:
        with st.form("edit_entry"):
            date = st.date_input("Edit Date", value=pd.to_datetime(df.loc[row_to_edit, "Date"]))
            category = st.selectbox("Edit Category", df["Category"].unique(), 
                                    index=list(df["Category"]).index(df.loc[row_to_edit, "Category"]))
            amount = st.number_input("Edit Amount", min_value=0.01, step=0.01, 
                                    value=float(df.loc[row_to_edit, "Amount"]))

            # ✅ Convert Income 0/1 to "Income"/"Expense"
            current_income = "Income" if df.loc[row_to_edit, "Income"] == 1 else "Expense"
            income = st.radio("Edit Type", ["Income", "Expense"], 
                            index=["Income", "Expense"].index(current_income))

            submitted = st.form_submit_button("Edit Entry")

            if submitted:
                income_flag = 1 if income == "Income" else 0
                prev_total = df.loc[row_to_edit - 1, "Total"] if row_to_edit > 0 else 0
                new_total = prev_total + amount if income_flag == 1 else prev_total - amount
                
                date_str = date.strftime("%Y-%m-%d")
                edited_row = [date_str, category, amount, new_total, income_flag]

                edit_row(sheet, row_to_edit + 2, edited_row)  # +2 because Google Sheets indexing starts from 1
                st.success(f"✅ Row {row_to_edit} updated successfully!")
                st.rerun()

# --- DELETE ENTRY ---
with st.expander("🗑️ Delete Entry", expanded=False):
    row_to_delete = st.selectbox("Select a row to delete", df.index)
    if st.button("Delete Selected Row"):
        delete_row(sheet, row_to_delete + 2)  # +2 because Sheets uses 1-based indexing
        st.success(f"✅ Row {row_to_delete} deleted successfully!")
        st.rerun()
