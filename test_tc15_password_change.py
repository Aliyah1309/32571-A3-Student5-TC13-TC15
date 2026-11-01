"""TC15 - F15 Password Change
https://opencart.abstracta.us/index.php?route=account/password
"""
import pytest

from config import VIEWPORT
from pages import BASE_URL, PasswordPage, alert_texts, field_errors, route, login, logout

pytestmark = pytest.mark.tc15

SUCCESS = "Success: Your password has been successfully updated."
LENGTH_MSG = "Password must be between 4 and 20 characters!"
MISMATCH_MSG = "Password confirmation does not match password!"


def test_tc15_s1_change_password(page, browser, account, shot, results):
    """Scenario 1 (positive): the new password works and the old one stops working."""
    pw = PasswordPage(page)
    pw.open()
    shot("change_password_form")
    results.note("Fields on the Change Password form",
                 page.locator("#content form label").all_inner_texts())

    # A second browser session logged in to the same account before the change
    other = browser.new_context(viewport=VIEWPORT, ignore_https_errors=True)
    other_page = other.new_page()
    login(other_page, account["email"], account["password"])

    new_password = "NewPass#2026"
    pw.change(new_password)
    shot("password_changed")
    alerts, landed = alert_texts(page), route(page)
    results.check("Change to 'NewPass#2026'",
                  SUCCESS in " ".join(alerts) and landed == "account/account",
                  f"'{SUCCESS}', My Account page", f"alert={alerts}, page={landed}")

    # Old password must now fail, new password must work
    logout(page)
    old_ok = login(page, account["email"], account["password"])
    shot("login_with_old_password")
    old_alert = alert_texts(page)
    logout(page)
    new_ok = login(page, account["email"], new_password)
    shot("login_with_new_password")
    results.check("Login with old password", not old_ok,
                  "refused with 'No match' warning", f"logged in={old_ok}, alert={old_alert}")
    results.check("Login with new password", new_ok,
                  "logged in to My Account", f"logged in={new_ok}")

    # Observation: is the other session still logged in after the change?
    other_page.goto(BASE_URL + "account/password")
    results.note("Other session after password change",
                 f"still on {route(other_page)} (logged in)"
                 if route(other_page) == "account/password" else f"sent to {route(other_page)}")
    other.close()
    results.finish()


def test_tc15_s2_confirmation_mismatch(page, account, shot, results):
    """Scenario 2 (negative): password and confirmation must match."""
    pw = PasswordPage(page)
    invalid_inputs = {
        "Different confirmation": ("NewPass#2026", "NewPass#2027", MISMATCH_MSG),
        "Confirmation left empty": ("NewPass#2026", "", MISMATCH_MSG),
        "Confirmation in different case": ("NewPass#2026", "newpass#2026", MISMATCH_MSG),
        "Both fields empty": ("", "", LENGTH_MSG),
    }
    for label, (password, confirm, message) in invalid_inputs.items():
        pw.change(password, confirm)
        shot(label)
        errs = field_errors(page)
        results.check(label, route(page) == "account/password" and message in errs,
                      f"refused with '{message}'",
                      f"page={route(page)}, errors={errs}, alert={alert_texts(page)}")

    # The original password must still be valid afterwards
    logout(page)
    still_ok = login(page, account["email"], account["password"])
    shot("original_password_still_works")
    results.check("Original password still works", still_ok,
                  "login with Test@12345 succeeds", f"logged in={still_ok}")
    results.finish()


def test_tc15_s3_password_length_boundaries(page, account, shot, results):
    """Scenario 3 (boundary values): the form states 4 to 20 characters."""
    pw = PasswordPage(page)
    current = account["password"]
    boundary_inputs = {
        "3 characters": ("Ab1", False),
        "4 characters": ("Ab1!", True),
        "20 characters": ("Abcdefgh1!Abcdefgh1!", True),
        "21 characters": ("Abcdefgh1!Abcdefgh1!X", False),
        "40 characters": ("Abcdefgh1!" * 4, False),
        "41 characters": ("Abcdefgh1!" * 4 + "X", False),
    }
    for label, (value, should_accept) in boundary_inputs.items():
        pw.change(value)
        shot(label)
        accepted = SUCCESS in " ".join(alert_texts(page))
        if accepted:
            current = value                     # the account now uses this password
        results.check(label, accepted == should_accept,
                      "accepted" if should_accept else f"refused with '{LENGTH_MSG}'",
                      f"{'accepted' if accepted else 'refused'}; "
                      f"alert={alert_texts(page)}, errors={field_errors(page)}")

    # Confirm the last accepted password is what the account really uses
    logout(page)
    ok = login(page, account["email"], current)
    results.note("Login with last accepted password",
                 f"{len(current)}-character password -> logged in={ok}")
    results.finish()
