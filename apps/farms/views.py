from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Farm
from .forms import FarmForm

from decimal import Decimal, InvalidOperation
from django.contrib import messages
from .models import Farm, FarmEconomics
@login_required
def farm_list(request):
    farms = Farm.objects.filter(owner=request.user)
    return render(request, "farms/farm_list.html", {"farms": farms})


@login_required
def farm_create(request):
    form = FarmForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        farm = form.save(commit=False)
        farm.owner = request.user
        farm.save()
        return redirect("farm_list")

    return render(request, "farms/farm_form.html", {
        "form": form,
        "title": "Add Farm",
    })


@login_required
def farm_edit(request, pk):
    farm = get_object_or_404(Farm, pk=pk, owner=request.user)
    form = FarmForm(request.POST or None, instance=farm)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("farm_list")

    return render(request, "farms/farm_form.html", {
        "form": form,
        "title": "Edit Farm",
    })


@login_required
def farm_delete(request, pk):
    farm = get_object_or_404(Farm, pk=pk, owner=request.user)

    if request.method == "POST":
        farm.delete()
        return redirect("farm_list")

    return render(request, "farms/farm_confirm_delete.html", {
        "farm": farm,
    })

@login_required
def farm_economics(request):
    farms = Farm.objects.filter(owner=request.user)
    records = FarmEconomics.objects.filter(farm__owner=request.user)

    if request.method == "POST":
        try:
            farm = get_object_or_404(
                Farm, pk=request.POST.get("farm_id"), owner=request.user
            )

            area = Decimal(request.POST.get("area_acres", "0"))
            expected_yield = Decimal(request.POST.get("expected_yield_kg", "0"))
            price = Decimal(request.POST.get("price_per_kg", "0"))

            cost_fields = [
                "seed_cost", "fertilizer_cost", "labour_cost",
                "irrigation_cost", "pesticide_cost",
                "equipment_cost", "other_cost",
            ]

            costs = {}
            for field in cost_fields:
                value = Decimal(request.POST.get(field) or "0")
                if not value.is_finite() or value < 0:
                    raise ValueError("Costs cannot be negative.")
                costs[field] = value

            if not area.is_finite() or area <= 0:
                raise ValueError("Area must be greater than zero.")

            if not expected_yield.is_finite() or expected_yield < 0:
                raise ValueError("Expected yield cannot be negative.")

            if not price.is_finite() or price < 0:
                raise ValueError("Sale price cannot be negative.")

            total_cost = sum(costs.values(), Decimal("0"))
            revenue = expected_yield * price
            profit = revenue - total_cost

            record = FarmEconomics.objects.create(
                farm=farm,
                area_acres=area,
                expected_yield_kg=expected_yield,
                price_per_kg=price,
                total_cost=total_cost,
                revenue=revenue,
                profit=profit,
                **costs,
            )

            return render(request, "farms/economics.html", {
                "farms": farms,
                "records": records,
                "estimate": record,
                "selected_farm": farm,
            })

        except (ValueError, InvalidOperation, TypeError):
            messages.error(
                request,
                "Please enter valid numbers. Costs, yield and sale price "
                "must be zero or greater, and area must be greater than zero."
            )

    return render(request, "farms/economics.html", {
        "farms": farms,
        "records": records,
    })


@login_required
def farm_economics_history(request):
    records = FarmEconomics.objects.filter(
        farm__owner=request.user
    ).select_related("farm")

    return render(request, "farms/economics_history.html", {
        "records": records,
    })