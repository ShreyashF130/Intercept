# dummy_target.py
from pydantic import BaseModel

class InventoryItem(BaseModel):
    item_id: str
    price: float
    quantity: int
    is_available: bool