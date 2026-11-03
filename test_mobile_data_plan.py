import pytest
from mobile_data_plan import overage_charge, recharge_allowed, validity_status

# Example test cases:
def test_within_included_data():
    assert overage_charge("standard", 3, False, False) == 0

def test_recharge_allowed():
    assert recharge_allowed(500, 1, False) is True

# Write the rest of the test cases so that the code is 90-100% covered.
