from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Listing


@login_required
def marketplace(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            title = request.POST.get("title", "").strip()
            category = request.POST.get("category", "")
            description = request.POST.get("description", "").strip()
            price = request.POST.get("price", "").strip()
            quantity = request.POST.get("quantity", "").strip()
            location = request.POST.get("location", "").strip()
            contact = request.POST.get("contact", "").strip()

            valid_categories = dict(Listing.CATEGORY_CHOICES)

            try:
                price_value = float(price)
            except (TypeError, ValueError):
                price_value = 0

            if not all([
                title, category, description, price, quantity, location, contact
            ]):
                messages.error(request, "Please fill in all fields.")
            elif category not in valid_categories:
                messages.error(request, "Please select a valid category.")
            elif price_value <= 0:
                messages.error(request, "Price must be greater than zero.")
            else:
                Listing.objects.create(
                    seller=request.user,
                    title=title,
                    category=category,
                    description=description,
                    price=price_value,
                    quantity=quantity,
                    location=location,
                    contact=contact,
                )
                messages.success(request, "Your listing was added.")
                return redirect("marketplace")

        elif action == "delete":
            listing_id = request.POST.get("listing_id")
            listing = get_object_or_404(
                Listing,
                pk=listing_id,
                seller=request.user,
            )
            listing.delete()
            messages.success(request, "Your listing was deleted.")
            return redirect("marketplace")

    listings = Listing.objects.select_related("seller").all()

    return render(request, "marketplace/listings.html", {
        "listings": listings,
        "categories": Listing.CATEGORY_CHOICES,
    })