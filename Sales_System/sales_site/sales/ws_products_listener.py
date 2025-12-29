import os
import threading
import time
from decimal import Decimal, InvalidOperation

import requests
import socketio
from django.db import transaction

from .models import Product

INVENTORY_BASE = os.getenv("INVENTORY_BASE_URL", "http://127.0.0.1:3001")

sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=1,
    reconnection_delay_max=10,
)

def _to_decimal(value, default="0"):
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal(default)

def _status_to_is_active(status):
    return (status or "").upper() == "ACTIVE"

@transaction.atomic
def upsert_product(inv):
    sku = (inv.get("sku") or "").strip()
    if not sku:
        return

    Product.objects.update_or_create(
        sku=sku,
        defaults={
            "name": inv.get("name") or "",
            "description": inv.get("description") or "",
            "unit": inv.get("unit") or "pcs",
            "price": _to_decimal(inv.get("listPrice")),
            "stock_qty": int(inv.get("currentQty") or 0),
            "published_to_shop": bool(inv.get("publishedToShop")),
            "sale_price_override": (
                _to_decimal(inv.get("salePriceOverride"))
                if inv.get("salePriceOverride") not in (None, "")
                else None
            ),
            "is_active": _status_to_is_active(inv.get("status")),
        },
    )

def fetch_and_upsert_by_sku(sku):
    url = f"{INVENTORY_BASE}/products/{sku}"
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        upsert_product(r.json())

@transaction.atomic
def mark_product_deleted_in_sales(sku: str):
    sku = (sku or "").strip()
    if not sku:
        return
    # safer than hard delete for demo/history
    Product.objects.filter(sku=sku).update(is_active=False, published_to_shop=False)

@sio.event
def connect():
    print("[Sales WS] connected to Inventory")

@sio.on("products:changed")
def on_products_changed(data):
    sku = (data or {}).get("sku")
    action = (data or {}).get("action")
    print("[Sales WS] products:changed", sku, action)

    if not sku:
        return

    if action == "deleted":
        mark_product_deleted_in_sales(sku)
        return

    fetch_and_upsert_by_sku(sku)

def _run():
    while True:
        try:
            sio.connect(INVENTORY_BASE, transports=["websocket"])
            sio.wait()
        except Exception as e:
            print("[Sales WS] retrying:", e)
            time.sleep(2)

def start_in_background():
    threading.Thread(target=_run, daemon=True).start()
