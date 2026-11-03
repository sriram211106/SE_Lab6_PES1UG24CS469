"""Lab 6 - Code (line) coverage tests for mobile_data_plan.py

Goal: make every statement in mobile_data_plan.py execute at least once.
Run:
    coverage run -m pytest CodeCoverageTest_mobile_data_plan.py
    coverage report -m
"""
import pytest
from mobile_data_plan import overage_charge, recharge_allowed, validity_status


# ---------------- overage_charge ----------------

def test_within_included_data():
    # standard plan includes 5 GB, 3 GB used -> nothing extra to pay
    assert overage_charge("standard", 3, False, False) == 0


def test_unknown_plan_raises():
    with pytest.raises(ValueError, match="unknown plan"):
        overage_charge("gold", 5, False, False)


def test_negative_data_raises():
    with pytest.raises(ValueError, match="invalid data usage"):
        overage_charge("basic", -1, False, False)


def test_home_small_overage():
    # standard: 5 GB included, 7 GB used -> 2 GB extra at the home rate 15
    assert overage_charge("standard", 7, False, False) == 2 * 15


def test_loyal_roaming_heavy_overage():
    # basic loyal: 2 + 1 = 3 GB included, 15 GB used -> 12 GB extra
    # roaming rate 40, extra > 10 adds 10, roaming adds another 5 -> 55
    assert overage_charge("basic", 15, True, True) == 12 * 55


# ---------------- recharge_allowed ----------------

def test_recharge_allowed():
    assert recharge_allowed(500, 1, False) is True


def test_recharge_kyc_pending_small_amount():
    assert recharge_allowed(150, 0, True) is True


def test_recharge_amount_too_large():
    assert recharge_allowed(2500, 0, False) is False


# ---------------- validity_status ----------------

def test_validity_prepaid_with_addon_active():
    # prepaid cutoff 0, addon +2 -> cutoff 2; 5 days left -> active
    assert validity_status(5, True, True) == "active"


def test_validity_postpaid_grace():
    # postpaid cutoff 3, no addon; 0 days left is below 3 but >= -12 -> grace
    assert validity_status(0, False, False) == "grace"


def test_validity_prepaid_expired():
    # prepaid cutoff 0; -20 is below the grace limit of -15 -> expired
    assert validity_status(-20, True, False) == "expired"
