"""Data Adapter - Converts between nested submission format and flat system format."""

import json
from typing import Union


def normalize_transaction(data: dict) -> dict:
    """Convert nested submission format to flat format expected by the system.

    Nested format (submissions):
        {sellers: [{name, id, ...}], buyers: [...], property: {...}, transaction: {...}}

    Flat format (system):
        {seller_name, seller_id, ..., buyer_name, ..., property_address, ..., price, ...}
    """
    # If already flat (has seller_name), return as-is
    if "seller_name" in data:
        return data

    flat = {}

    # Primary seller (first in list)
    sellers = data.get("sellers", [])
    if sellers:
        primary = sellers[0]
        flat["seller_name"] = primary.get("name", "")
        flat["seller_id"] = primary.get("id", "")
        flat["seller_address"] = primary.get("address", "")
        flat["seller_phone"] = primary.get("phone", "")
        flat["seller_email"] = primary.get("email", "")
        flat["seller_marital_status"] = primary.get("marital_status", "")

    # Primary buyer (first in list)
    buyers = data.get("buyers", [])
    if buyers:
        primary = buyers[0]
        flat["buyer_name"] = primary.get("name", "")
        flat["buyer_id"] = primary.get("id", "")
        flat["buyer_address"] = primary.get("address", "")
        flat["buyer_phone"] = primary.get("phone", "")
        flat["buyer_email"] = primary.get("email", "")
        flat["buyer_marital_status"] = primary.get("marital_status", "")

    # Property
    prop = data.get("property", {})
    flat["property_address"] = prop.get("address", "")
    flat["block_number"] = str(prop.get("block_number", ""))
    flat["parcel_number"] = str(prop.get("parcel_number", ""))
    flat["sub_parcel"] = str(prop.get("sub_parcel", ""))
    flat["area_sqm"] = str(prop.get("area_sqm", ""))
    flat["rooms"] = str(prop.get("rooms", ""))
    flat["floor"] = str(prop.get("floor", ""))
    flat["property_type"] = prop.get("property_type", "apartment")
    flat["parking"] = prop.get("parking", "none")
    flat["storage"] = prop.get("storage", "no")

    # Transaction
    trans = data.get("transaction", {})
    flat["price"] = str(trans.get("price", ""))
    flat["signing_date"] = trans.get("signing_date", "")
    flat["delivery_date"] = trans.get("delivery_date", "")

    # Notes
    flat["notes"] = data.get("seller_notes", data.get("notes", ""))

    # Keep all sellers/buyers for multi-party contracts
    flat["all_sellers"] = sellers
    flat["all_buyers"] = buyers

    return flat


def denormalize_transaction(flat: dict) -> dict:
    """Convert flat system format back to nested submission format."""
    nested = {
        "sellers": flat.get("all_sellers", [{
            "name": flat.get("seller_name", ""),
            "id": flat.get("seller_id", ""),
            "address": flat.get("seller_address", ""),
            "phone": flat.get("seller_phone", ""),
            "email": flat.get("seller_email", ""),
            "marital_status": flat.get("seller_marital_status", ""),
        }]),
        "buyers": flat.get("all_buyers", [{
            "name": flat.get("buyer_name", ""),
            "id": flat.get("buyer_id", ""),
            "address": flat.get("buyer_address", ""),
            "phone": flat.get("buyer_phone", ""),
            "email": flat.get("buyer_email", ""),
            "marital_status": flat.get("buyer_marital_status", ""),
        }]),
        "property": {
            "address": flat.get("property_address", ""),
            "block_number": flat.get("block_number", ""),
            "parcel_number": flat.get("parcel_number", ""),
            "sub_parcel": flat.get("sub_parcel", ""),
            "area_sqm": _to_num(flat.get("area_sqm", 0)),
            "rooms": _to_num(flat.get("rooms", 0)),
            "floor": int(_to_num(flat.get("floor", 0))),
            "property_type": flat.get("property_type", "apartment"),
            "parking": flat.get("parking", "none"),
            "storage": flat.get("storage", "no"),
        },
        "transaction": {
            "price": int(_to_num(flat.get("price", 0))),
            "signing_date": flat.get("signing_date", ""),
            "delivery_date": flat.get("delivery_date", ""),
        },
        "seller_notes": flat.get("notes", ""),
    }
    return nested


def load_transaction_file(path: str) -> dict:
    """Load a transaction JSON file and normalize it to flat format."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return normalize_transaction(data)


def _to_num(val) -> float:
    """Safely convert value to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0
