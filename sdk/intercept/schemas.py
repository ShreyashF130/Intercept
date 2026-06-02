from pydantic import BaseModel, Field
from typing import Literal

class RefundCustomerSchema(BaseModel):
    order_id: str = Field(description="The unique order identifier, must start with 'ORD-' followed by numbers.")
    amount: float = Field(description="The total amount to refund. Must be strictly positive.")
    currency: Literal["USD", "EUR", "GBP"] = Field(description="The 3-letter currency code.")
    reason: str = Field(description="The reason for processing this refund request.")