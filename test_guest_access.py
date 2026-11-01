"""Supplementary check (not counted in TC13-TC15 totals):
a logged-out visitor cannot open the F13-F15 account pages."""
import pytest

from config import BASE_URL
from pages import route

pytestmark = pytest.mark.guest

PROTECTED = {
    "F13 Address Book": "account/address",
    "F13 New Address": "account/address/add",
    "F13 Edit Address": "account/address/edit&address_id=1",
    "F14 Edit Account": "account/edit",
    "F15 Change Password": "account/password",
}


@pytest.mark.parametrize("name", PROTECTED)
def test_guest_is_redirected_to_login(page, results, name):
    page.goto(BASE_URL + PROTECTED[name])
    page.wait_for_load_state()
    landed = route(page)
    results.check(f"Guest opens {name}", landed == "account/login",
                  "redirected to account/login", landed)
    results.finish()
