INCLUDED_GB = {"basic": 2, "standard": 5, "premium": 10}


def overage_charge(plan, data_gb, is_roaming, is_loyal):
    if plan not in INCLUDED_GB:
        raise ValueError("unknown plan")
    if data_gb < 0:
        raise ValueError("invalid data usage")
    included = INCLUDED_GB[plan]
    if is_loyal and plan != "premium":
        included += 1
    extra = data_gb - included
    if extra <= 0:
        return 0
    if is_roaming:
        rate = 40
    else:
        rate = 15
    if extra > 10:
        rate = rate + 10
        if is_roaming:
            rate += 5
    return extra * rate


def recharge_allowed(amount, pending_recharges, is_kyc_pending):
    if is_kyc_pending:
        return amount <= 200
    if amount > 2000:
        return False
    return pending_recharges <= 2


def validity_status(days_left, is_prepaid, has_addon):
    if is_prepaid:
        cutoff = 0
    else:
        cutoff = 3
    if has_addon:
        cutoff += 2
    if days_left >= cutoff:
        return "active"
    elif days_left >= cutoff - 15:
        return "grace"
    return "expired"
