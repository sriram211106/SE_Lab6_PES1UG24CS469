"""Lab 6 - Branch coverage tests for mobile_data_plan.py

Goal: every decision (if / elif / and / return-condition) is exercised for both
its True and False outcome, including the boundary values.
Run:
    coverage run --branch -m pytest BranchCoverageTest_mobile_data_plan.py
    coverage report -m
"""
import pytest
from mobile_data_plan import (
    INCLUDED_GB,
    overage_charge,
    recharge_allowed,
    validity_status,
)


# =====================================================================
# overage_charge
# =====================================================================

# --- if plan not in INCLUDED_GB -------------------------------------

@pytest.mark.parametrize("plan", ["gold", "", "Basic", "PREMIUM", None])
def test_unknown_plan_raises(plan):
    # plan names are case-sensitive; anything not in the dict is rejected
    with pytest.raises(ValueError, match="unknown plan"):
        overage_charge(plan, 1, False, False)


def test_plan_checked_before_data():
    # both inputs are bad: the plan check runs first
    with pytest.raises(ValueError, match="unknown plan"):
        overage_charge("gold", -5, False, False)


@pytest.mark.parametrize("plan", sorted(INCLUDED_GB))
def test_every_known_plan_is_accepted(plan):
    assert overage_charge(plan, 0, False, False) == 0


# --- if data_gb < 0 -------------------------------------------------

@pytest.mark.parametrize("data_gb", [-1, -0.5, -100])
def test_negative_data_raises(data_gb):
    with pytest.raises(ValueError, match="invalid data usage"):
        overage_charge("basic", data_gb, False, False)


def test_zero_data_is_valid():
    # boundary: 0 is not < 0
    assert overage_charge("basic", 0, False, False) == 0


# --- if is_loyal and plan != "premium" ------------------------------

def test_loyal_basic_gets_bonus_gb():
    # basic 2 + 1 = 3 GB included -> 3 GB used is free
    assert overage_charge("basic", 3, False, True) == 0


def test_not_loyal_basic_no_bonus_gb():
    # same usage without loyalty -> 1 GB extra
    assert overage_charge("basic", 3, False, False) == 15


def test_loyal_standard_gets_bonus_gb():
    assert overage_charge("standard", 6, False, True) == 0
    assert overage_charge("standard", 7, False, True) == 15


def test_loyal_premium_gets_no_bonus_gb():
    # loyal is True but plan == "premium" -> condition False, still 10 GB
    assert overage_charge("premium", 11, False, True) == 15
    assert overage_charge("premium", 10, False, True) == 0


# --- if extra <= 0 --------------------------------------------------

def test_usage_below_included_is_free():
    assert overage_charge("standard", 3, False, False) == 0


def test_usage_exactly_included_is_free():
    # boundary: extra == 0
    assert overage_charge("standard", 5, False, False) == 0


def test_usage_just_over_included_is_charged():
    # boundary: extra == 1
    assert overage_charge("standard", 6, False, False) == 15


def test_fractional_overage():
    assert overage_charge("basic", 2.5, False, False) == pytest.approx(7.5)


# --- if is_roaming (base rate) + if extra > 10 + inner if is_roaming -

def test_home_small_overage():
    # not roaming, extra <= 10 -> rate 15
    assert overage_charge("basic", 7, False, False) == 5 * 15


def test_roaming_small_overage():
    # roaming, extra <= 10 -> rate 40
    assert overage_charge("basic", 7, True, False) == 5 * 40


def test_home_heavy_overage():
    # not roaming, extra > 10 -> 15 + 10 = 25, inner roaming check is False
    assert overage_charge("basic", 15, False, False) == 13 * 25


def test_roaming_heavy_overage():
    # roaming, extra > 10 -> 40 + 10 + 5 = 55, inner roaming check is True
    assert overage_charge("basic", 15, True, False) == 13 * 55


def test_extra_exactly_ten_has_no_surcharge():
    # boundary: extra == 10 is not > 10
    assert overage_charge("basic", 12, False, False) == 10 * 15
    assert overage_charge("basic", 12, True, False) == 10 * 40


def test_extra_eleven_has_surcharge():
    # boundary: extra == 11 is > 10
    assert overage_charge("basic", 13, False, False) == 11 * 25
    assert overage_charge("basic", 13, True, False) == 11 * 55


def test_loyal_premium_roaming_heavy():
    # all flags on with premium: no bonus GB, roaming heavy rate
    assert overage_charge("premium", 25, True, True) == 15 * 55


def test_loyal_standard_home_heavy():
    # 5 + 1 = 6 included, 20 used -> 14 extra at 25
    assert overage_charge("standard", 20, False, True) == 14 * 25


# =====================================================================
# recharge_allowed
# =====================================================================

# --- if is_kyc_pending ----------------------------------------------

@pytest.mark.parametrize(
    "amount, expected",
    [(0, True), (199, True), (200, True), (201, False), (5000, False)],
)
def test_kyc_pending_limit(amount, expected):
    # boundary at 200 (inclusive)
    assert recharge_allowed(amount, 0, True) is expected


def test_kyc_pending_ignores_pending_recharges():
    # KYC branch returns before pending_recharges is ever checked
    assert recharge_allowed(100, 10, True) is True


# --- if amount > 2000 -----------------------------------------------

@pytest.mark.parametrize(
    "amount, expected",
    [(1999, True), (2000, True), (2001, False), (10000, False)],
)
def test_amount_limit_without_kyc(amount, expected):
    # boundary at 2000 (inclusive)
    assert recharge_allowed(amount, 0, False) is expected


def test_large_amount_rejected_even_with_no_pending():
    assert recharge_allowed(2500, 0, False) is False


# --- return pending_recharges <= 2 -----------------------------------

@pytest.mark.parametrize(
    "pending, expected",
    [(0, True), (1, True), (2, True), (3, False), (7, False)],
)
def test_pending_recharge_limit(pending, expected):
    # boundary at 2 (inclusive)
    assert recharge_allowed(500, pending, False) is expected


# =====================================================================
# validity_status
# =====================================================================
# cutoff table:
#   prepaid, no addon  -> 0      prepaid, addon  -> 2
#   postpaid, no addon -> 3      postpaid, addon -> 5
# "active"  if days_left >= cutoff
# "grace"   if days_left >= cutoff - 15
# "expired" otherwise

@pytest.mark.parametrize(
    "is_prepaid, has_addon, cutoff",
    [
        (True, False, 0),
        (True, True, 2),
        (False, False, 3),
        (False, True, 5),
    ],
)
class TestValidityBoundaries:
    def test_active_at_cutoff(self, is_prepaid, has_addon, cutoff):
        assert validity_status(cutoff, is_prepaid, has_addon) == "active"

    def test_active_above_cutoff(self, is_prepaid, has_addon, cutoff):
        assert validity_status(cutoff + 30, is_prepaid, has_addon) == "active"

    def test_grace_just_below_cutoff(self, is_prepaid, has_addon, cutoff):
        assert validity_status(cutoff - 1, is_prepaid, has_addon) == "grace"

    def test_grace_at_lower_limit(self, is_prepaid, has_addon, cutoff):
        assert validity_status(cutoff - 15, is_prepaid, has_addon) == "grace"

    def test_expired_just_below_grace(self, is_prepaid, has_addon, cutoff):
        assert validity_status(cutoff - 16, is_prepaid, has_addon) == "expired"


def test_prepaid_zero_days_is_active():
    assert validity_status(0, True, False) == "active"


def test_postpaid_zero_days_is_grace():
    assert validity_status(0, False, False) == "grace"


def test_addon_moves_prepaid_from_active_to_grace():
    # 1 day left: active without addon (cutoff 0), grace with addon (cutoff 2)
    assert validity_status(1, True, False) == "active"
    assert validity_status(1, True, True) == "grace"


def test_far_past_is_expired():
    assert validity_status(-100, False, True) == "expired"
