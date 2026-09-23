"""Offline exercise calculator. This does not invoke AWS or redeem points."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_FLOOR

def quote(points, tier, total, category="standard"):
    if isinstance(points, bool) or not isinstance(points, int) or points < 0:
        raise ValueError("Points must be a nonnegative integer")
    rates = {"Silver": Decimal("0"), "Gold": Decimal(".10"), "Platinum": Decimal(".15")}
    earn = {"standard": 1, "device": 2, "fresh": 5}
    if tier not in rates or category not in earn:
        raise ValueError("Unknown tier or category")
    try:
        amount = Decimal(str(total))
        if not amount.is_finite() or not 0 <= amount <= Decimal("1000000000"):
            raise ValueError("Invalid amount")
        if amount != amount.quantize(Decimal(".01")):
            raise ValueError("At most two decimal places")
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc
    blocks = min(points // 500, int(amount * Decimal(".5") // 5))
    redeemed = blocks * 500
    subtotal = amount - Decimal(redeemed) / 100
    savings = (subtotal * rates[tier]).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    final = subtotal - savings
    earned = int((final * earn[category]).to_integral_value(rounding=ROUND_FLOOR))
    return {"execution": "offline_exercise", "points_redeemed": redeemed,
            "tier_discount_pct": int(rates[tier] * 100), "final_total": format(final, ".2f"),
            "remaining_points": points-redeemed, "points_earned": earned,
            "balance_after_purchase": points-redeemed+earned}

if __name__ == "__main__":
    import json
    print(json.dumps(quote(4250, "Gold", "150.00"), indent=2))
