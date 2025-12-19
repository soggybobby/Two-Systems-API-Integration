import requests
from django.conf import settings


def adjust_stock_for_sale(ref_id: str, items: list[dict]):
    """
    items:
      [{"sku": "ABC-01", "qty": 2}, ...]
    """
    base = getattr(settings, "INVENTORY_API_BASE", "http://127.0.0.1:3001")
    url = f"{base}/stock/adjust"

    payload = {
        "refType": "SALE",
        "refId": str(ref_id),
        "items": items,
    }

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
