import numpy as np

def add_row(sheet, new_row):
    """Insert a new row at the specified index."""
    sheet.insert_row(new_row, 2)
    print("Row added successfully!")

def edit_row(sheet, index, edited_row):
    """Edit the row at the specified index."""
    sheet.update_cell(index, 1, edited_row[0])
    sheet.update_cell(index, 2, edited_row[1])
    sheet.update_cell(index, 3, edited_row[2])
    sheet.update_cell(index, 4, edited_row[3])
    sheet.update_cell(index, 5, edited_row[4])
    print("Row updated successfully!")

def delete_row(sheet, index):
    """Delete the row at the specified index."""
    sheet.delete_rows(index)
    print("Row deleted successfully!")