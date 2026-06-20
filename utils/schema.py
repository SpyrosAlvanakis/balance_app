from pydantic import BaseModel, Field
from datetime import datetime


class Data(BaseModel):
    Date: datetime
    Category: str = Field(min_length=1)
    Amount: float
    Total: float
    Type: int
