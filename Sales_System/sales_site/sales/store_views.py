from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.conf import settings
import requests

from .models import Customer, Sale, SaleItem, Product


def _cart(request):
    """
    Cart shape in session:
    {
      "<sku>": {"name": str, "unit": str, "price": float, "qty": int}
    }
    """
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _inventory_base():
    return getattr(settings, "INVENTORY_API_BASE", "http://127.0.0.1:3001")


def _deduct_inventory_stock(ref_id: str, items):
    """
    Calls Inventory_System POST /stock/adjust
    items: [{"sku": "ABC-01", "qty": 2}, ...]
    Returns (ok: bool, data_or_error: dict/str)
    """
    url = f"{_inventory_base()}/stock/adjust"
    payload = {
        "refType": "SALE",
        "refId": ref_id,
        "items": items
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, f"{r.status_code} {r.text}"
    except Exception as e:
        return False, str(e)


def shop_home(request):
    products = Product.objects.filter(is_active=True, published_to_shop=True).order_by("name")
    cart = _cart(request)
    total_items = sum(item["qty"] for item in cart.values())
    return render(request, "sales/shop_home.html", {
        "products": products,
        "total_items": total_items,
    })


@require_POST
def add_to_cart(request):
    sku = request.POST.get("sku")
    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    try:
        p = Product.objects.get(sku=sku, is_active=True)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect("shop_home")

    if p.stock_qty <= 0:
        messages.error(request, f"{p.name} is out of stock.")
        return redirect("shop_home")

    cart = _cart(request)
    current_qty = cart.get(sku, {}).get("qty", 0)
    new_total = current_qty + max(qty, 1)

    if new_total > p.stock_qty:
        cart[sku] = {
            "name": p.name,
            "unit": p.unit,
            "price": float(p.effective_price),
            "qty": p.stock_qty,
        }
        _save_cart(request, cart)
        messages.warning(request, f"Only {p.stock_qty} × {p.name} available. Cart updated.")
        return redirect("shop_home")

    cart[sku] = {
        "name": p.name,
        "unit": p.unit,
        "price": float(p.effective_price),
        "qty": new_total,
    }
    _save_cart(request, cart)
    messages.success(request, f"Added {qty} × {p.name} to cart.")
    return redirect("shop_home")


@require_POST
def remove_from_cart(request):
    sku = request.POST.get("sku")
    cart = _cart(request)
    if sku in cart:
        cart.pop(sku, None)
        _save_cart(request, cart)
        messages.success(request, "Item removed from cart.")
    else:
        messages.error(request, "Item not found in cart.")
    return redirect("view_cart")


def view_cart(request):
    cart = _cart(request)
    items = []
    total = 0.0
    for sku, item in cart.items():
        line_total = float(item["qty"]) * float(item["price"])
        total += line_total
        items.append({"sku": sku, **item, "line_total": line_total})
    return render(request, "sales/cart.html", {"items": items, "total": total})


@require_POST
def update_cart(request):
    cart = _cart(request)
    messages_list = []

    for sku, item in list(cart.items()):
        try:
            new_qty = int(request.POST.get(f"qty_{sku}", item["qty"]))
        except ValueError:
            new_qty = item["qty"]

        if new_qty <= 0:
            cart.pop(sku, None)
            messages_list.append(f"Removed {item['name']}.")
            continue

        try:
            p = Product.objects.get(sku=sku, is_active=True)
        except Product.DoesNotExist:
            cart.pop(sku, None)
            messages_list.append(f"{item['name']} is no longer available.")
            continue

        if new_qty > p.stock_qty:
            item["qty"] = p.stock_qty
            messages_list.append(f"Capped {p.name} to {p.stock_qty} (available).")
        else:
            item["qty"] = new_qty

    _save_cart(request, cart)
    if messages_list:
        messages.warning(request, " ".join(messages_list))
    else:
        messages.success(request, "Cart updated.")
    return redirect("view_cart")


def checkout_form(request):
    cart = _cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("shop_home")
    return render(request, "sales/checkout.html")


@require_POST
@transaction.atomic
def place_order(request):
    """
    Create Customer, validate stock, create Sale + SaleItems,
    deduct Inventory stock via API, update local stock_qty to match,
    and clear the cart.
    """
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()

    if not name or not email:
        messages.error(request, "Name and email are required.")
        return redirect("checkout_form")

    customer, _ = Customer.objects.get_or_create(
        email=email, defaults={"name": name, "phone": phone}
    )

    updated = []
    if name and customer.name != name:
        customer.name = name
        updated.append("name")
    if phone and customer.phone != phone:
        customer.phone = phone
        updated.append("phone")
    if updated:
        customer.save(update_fields=updated)

    cart = _cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("shop_home")

    # Lock and validate local stock
    problems = []
    locked_products = {}
    for sku, item in cart.items():
        try:
            p = Product.objects.select_for_update().get(sku=sku, is_active=True)
        except Product.DoesNotExist:
            problems.append(f"{sku} is no longer available.")
            continue

        if item["qty"] > p.stock_qty:
            problems.append(f"{p.name} – only {p.stock_qty} left.")
        locked_products[sku] = p

    if problems:
        messages.error(request, "Cannot place order: " + " ".join(problems))
        return redirect("view_cart")

    # Create sale first (so we have a reference id)
    sale = Sale.objects.create(customer=customer, status="NEW")

    # Call Inventory to deduct stock
    inv_items = [{"sku": sku, "qty": int(item["qty"])} for sku, item in cart.items()]
    ok, inv_result = _deduct_inventory_stock(ref_id=f"S-{sale.pk}", items=inv_items)

    if not ok:
        # rollback whole transaction
        raise Exception(f"Inventory stock adjust failed: {inv_result}")

    # Update local Product.stock_qty using returned "after" values when available
    # inv_result shape: { results: [{ sku, ok, before, after, deducted }, ...] }
    results = inv_result.get("results", [])
    bad = [r for r in results if not r.get("ok")]
    if bad:
        raise Exception(f"Inventory refused some items: {bad}")

    after_map = {r["sku"]: r.get("after") for r in results if r.get("ok")}

    # Create sale items and set local stock_qty to match Inventory after
    for sku, item in cart.items():
        p = locked_products[sku]
        SaleItem.objects.create(
            sale=sale,
            sku=sku,
            product_name=p.name,
            unit=p.unit,
            qty=item["qty"],
            unit_price=p.effective_price,
        )
        if sku in after_map and after_map[sku] is not None:
            p.stock_qty = int(after_map[sku])
        else:
            # fallback, still decrement locally
            p.stock_qty -= int(item["qty"])
        p.save(update_fields=["stock_qty"])

    sale.save()
    _save_cart(request, {})
    return render(request, "sales/order_success.html", {"sale": sale})
