from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
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


def shop_home(request):
    """
    Storefront home – show active products from DB.
    """
    products = Product.objects.filter(is_active=True).order_by("name")
    cart = _cart(request)
    total_items = sum(item["qty"] for item in cart.values())
    return render(request, "sales/shop_home.html", {
        "products": products,
        "total_items": total_items,
    })


@require_POST
def add_to_cart(request):
    """
    Add a product to the cart. Uses DB product and validates stock.
    """
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
        # cap at available stock
        cart[sku] = {
            "name": p.name,
            "unit": p.unit,
            "price": float(p.price),
            "qty": p.stock_qty,
        }
        _save_cart(request, cart)
        messages.warning(request, f"Only {p.stock_qty} × {p.name} available. Cart updated.")
        return redirect("shop_home")

    # ok to add
    cart[sku] = {
        "name": p.name,
        "unit": p.unit,
        "price": float(p.price),
        "qty": new_total,
    }
    _save_cart(request, cart)
    messages.success(request, f"Added {qty} × {p.name} to cart.")
    return redirect("shop_home")


@require_POST
def remove_from_cart(request):
    """
    Remove a single item from the cart by SKU.
    """
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
    """
    Render the cart with line totals and grand total.
    """
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
    """
    Bulk update quantities. Removes items if qty <= 0.
    Caps quantities to available stock.
    """
    cart = _cart(request)
    messages_list = []

    for sku, item in list(cart.items()):
        # read desired qty
        try:
            new_qty = int(request.POST.get(f"qty_{sku}", item["qty"]))
        except ValueError:
            new_qty = item["qty"]

        if new_qty <= 0:
            cart.pop(sku, None)
            messages_list.append(f"Removed {item['name']}.")
            continue

        # stock check
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
    """
    Simple guest checkout form.
    """
    cart = _cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("shop_home")
    return render(request, "sales/checkout.html")


@require_POST
@transaction.atomic
def place_order(request):
    """
    Create (or reuse) a Customer, validate stock, create Sale + SaleItems,
    decrement stock, and clear the cart.
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
    # keep customer details fresh
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

    # Validate stock (lock rows to avoid races)
    problems = []
    locked_products = {}  # sku -> Product
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

    # Create sale + items, decrement stock
    sale = Sale.objects.create(customer=customer, status="NEW")
    for sku, item in cart.items():
        p = locked_products[sku]
        SaleItem.objects.create(
            sale=sale,
            sku=sku,
            product_name=p.name,
            unit=p.unit,
            qty=item["qty"],
            unit_price=p.price,  # trust DB price at checkout
        )
        p.stock_qty -= item["qty"]
        p.save(update_fields=["stock_qty"])

    # recompute total on sale
    sale.save()

    # clear cart
    _save_cart(request, {})

    return render(request, "sales/order_success.html", {"sale": sale})
