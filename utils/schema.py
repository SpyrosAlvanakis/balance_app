from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class Categories(str, Enum):
    Fun = "Fun"
    Mprikis = "Mprikis"
    Education = "Education"
    Supermarket = "Supermarket"
    Vodafone = "Vodafone"
    Fuel = "Fuel"
    Dad = "Dad"
    Mom = "Mom"
    Gym = "Gym"
    Other = "Other"
    Job = "Job"
    Efka = "Efka"
    Rent = "Rent"
    Subscriptions = "Subscriptions"
    Parking = "Parking"
    Haircut = "Haircut"
    Electricity = "Electricity"
    Water = "Water"
    Me = "Me"
    Family = "Family"
    Vacation = "Vacation"
    Accountant = "Accountant"
    Lena = "Lena"
    Health = "Health"
    Gifts = "Gifts"
    Allowance = "Allowance"
    Building_fees = "Building fees"
    Hobies = "Hobies"
    Private = "Private"
    MOTOmaintenance_oil_insurance = "MOTOmaintenance/oil/insurance"

# Define the schema for the request body
class Data(BaseModel):
    Date: datetime
    Category: Categories
    Amount: float
    Total: float
    Type: int