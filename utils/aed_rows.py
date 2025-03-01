from typing import List, Optional
from utils.schema import Data, Categories
import streamlit as st
import pandas as pd
from datetime import datetime, date as datetype  # Rename imported date to avoid shadowing

def validate_row(row_data: List) -> Optional[Data]:
    """Validate row data using the BaseModel."""
    try:
        if isinstance(row_data[0], datetime):
            date_value = row_data[0]
        elif isinstance(row_data[0], datetype): 
            date_value = datetime.combine(row_data[0], datetime.min.time())
        else:
            date_value = datetime.strptime(row_data[0], "%Y-%m-%d")
        
        # Create Data object
        validated_data = Data(
            Date=date_value,
            Category=row_data[1],
            Amount=float(row_data[2]),
            Total=float(row_data[3]),
            Type=int(row_data[4])
        )
        return validated_data
    except Exception as e:
        print(f"Validation error: {e}")
        return None

def add_row(sheet, new_row):
    """Insert a new row with validation."""
    # Validate the row data
    validated_data = validate_row(new_row)
    
    if validated_data:
        try:
            # Convert validated data back to list format for sheet
            sheet_row = [
                validated_data.Date.strftime("%Y-%m-%d"),
                validated_data.Category.value,  # Use .value for enum
                validated_data.Amount,
                validated_data.Total,
                validated_data.Type
            ]
            sheet.insert_row(sheet_row, 2)
            print("Row added successfully!")
            return True
        except Exception as e:
            print(f"Error adding row to sheet: {e}")
            return False
    return False

# def edit_row(sheet, index, edited_row):
#     """Edit the row with validation."""
#     # Validate the edited row data
#     validated_data = validate_row(edited_row)
    
#     if validated_data:
#         try:
#             # Update cells with validated data
#             sheet.update_cell(index, 1, validated_data.Date.strftime("%Y-%m-%d"))
#             sheet.update_cell(index, 2, validated_data.Category)
#             sheet.update_cell(index, 3, validated_data.Amount)
#             sheet.update_cell(index, 4, validated_data.Total)
#             sheet.update_cell(index, 5, validated_data.Type)
#             print("Row updated successfully!")
#             return True
#         except Exception as e:
#             print(f"Error updating row in sheet: {e}")
#             return False
#     else:
#         print("Row validation failed!")
#         return False

def delete_row(sheet, index):
    """Delete the row at the specified index."""
    try:
        sheet.delete_rows(index)
        print("Row deleted successfully!")
        return True
    except Exception as e:
        print(f"Error deleting row: {e}")
        return False

def correct_gs_types(df)->pd.DataFrame:
    """Correct the types of the columns in the dataframe."""
    df["Date"] = pd.to_datetime(df["Date"])
    # df["Category"] = df["Category"].astype(Categories)
    # Convert Amount and Total with proper handling of decimal separators
    df['Amount'] = df['Amount'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
    df['Total'] = df['Total'].apply(lambda x: float(str(x).replace('.', '').replace(',', '.')))
    df['Type'] = df['Type'].astype(int)
    return df

# import numpy as np

# def add_row(sheet, new_row):
#     """Insert a new row at the specified index."""
#     sheet.insert_row(new_row, 2)
#     print("Row added successfully!")

# def edit_row(sheet, index, edited_row):
#     """Edit the row at the specified index."""
#     sheet.update_cell(index, 1, edited_row[0])
#     sheet.update_cell(index, 2, edited_row[1])
#     sheet.update_cell(index, 3, edited_row[2])
#     sheet.update_cell(index, 4, edited_row[3])
#     sheet.update_cell(index, 5, edited_row[4])
#     print("Row updated successfully!")

# def delete_row(sheet, index):
#     """Delete the row at the specified index."""
#     sheet.delete_rows(index)
#     print("Row deleted successfully!")