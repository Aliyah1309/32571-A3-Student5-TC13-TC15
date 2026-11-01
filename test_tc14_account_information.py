"""TC14 - F14 Account Information Update
https://opencart.abstracta.us/index.php?route=account/edit
"""
import pytest

from pages import (EditAccountPage, alert_texts, field_errors, route, login,
                   logout, unique_email)

pytestmark = pytest.mark.tc14

SUCCESS = "Success: Your account has been successfully updated."


def test_tc14_s1_update_with_valid_details(page, account, shot, results):
    """Scenario 1 (positive + boundary): valid changes are saved and used for login."""
    edit = EditAccountPage(page)
    edit.open()
    shot("edit_form_before")

    # a) Change every field, including the e-mail used to log in
    new_email = unique_email("tc14new")
    data = {"firstname": "Aaliyah", "lastname": "Shaikh-Khan",
            "email": new_email, "telephone": "+61 2 9876 5432"}
    edit.submit(**data)
    shot("after_update")
    alerts = alert_texts(page)
    landed = route(page)
    edit.open()
    saved = edit.values()
    shot("edit_form_reopened")
    results.check("Change name, phone and e-mail",
                  SUCCESS in " ".join(alerts) and landed == "account/account" and saved == data,
                  f"'{SUCCESS}', My Account page, values saved = {data}",
                  f"alert={alerts}, page={landed}, saved={saved}")

    # b) The new e-mail logs in and the old e-mail no longer does
    logout(page)
    old_ok = login(page, account["email"], account["password"])
    shot("login_with_old_email")
    logout(page)
    new_ok = login(page, new_email, account["password"])
    results.check("Login after e-mail change", new_ok and not old_ok,
                  "old e-mail refused, new e-mail accepted",
                  f"old e-mail login={old_ok}, new e-mail login={new_ok}")

    # c) Boundary values: 32-character names and a 3-character telephone
    data = {"firstname": "F" * 32, "lastname": "L" * 32, "telephone": "123"}
    edit.submit(**data)
    alerts = alert_texts(page)
    shot("boundary_values_saved")
    edit.open()
    saved = edit.values()
    results.check("Boundary: 32-char names, 3-char phone",
                  SUCCESS in " ".join(alerts)
                  and all(saved[k] == v for k, v in data.items()),
                  f"'{SUCCESS}', values saved", f"alert={alerts}, saved={saved}")
    results.finish()


def test_tc14_s2_reject_invalid_details(page, account, shot, results):
    """Scenario 2 (negative + boundary): invalid values are refused, data unchanged."""
    edit = EditAccountPage(page)
    edit.open()
    original = edit.values()

    invalid_inputs = {
        "All fields empty": ({"firstname": "", "lastname": "", "email": "", "telephone": ""},
                             ["First Name must be between 1 and 32 characters!",
                              "Last Name must be between 1 and 32 characters!",
                              "E-Mail Address does not appear to be valid!",
                              "Telephone must be between 3 and 32 characters!"], False),
        "First Name 33 chars": ({"firstname": "A" * 33},
                                ["First Name must be between 1 and 32 characters!"], False),
        "Last Name 33 chars": ({"lastname": "B" * 33},
                               ["Last Name must be between 1 and 32 characters!"], False),
        "E-mail 'aliyah@' (server check)": ({"email": "aliyah@"},
                                            ["E-Mail Address does not appear to be valid!"], True),
        "E-mail 'aliyah@example'": ({"email": "aliyah@example"},
                                    ["E-Mail Address does not appear to be valid!"], False),
        "Telephone 2 chars": ({"telephone": "12"},
                              ["Telephone must be between 3 and 32 characters!"], False),
        "Telephone 33 chars": ({"telephone": "4" * 33},
                               ["Telephone must be between 3 and 32 characters!"], False),
    }
    # Chrome's own e-mail check for 'aliyah@' (before the server is reached)
    html5 = edit.submit(email="aliyah@")
    shot("browser_blocks_bad_email")
    results.check("E-mail 'aliyah@' (browser check)",
                  bool(html5) and route(page) == "account/edit",
                  "form not sent, browser message shown", f"browser message='{html5}'")

    for label, (data, messages, bypass) in invalid_inputs.items():
        edit.submit(skip_browser_validation=bypass, **data)
        shot(label)
        errs = field_errors(page)
        stayed = route(page) == "account/edit"
        edit.open()
        unchanged = edit.values() == original
        results.check(label, stayed and all(m in errs for m in messages) and unchanged,
                      f"refused with {messages}, details unchanged",
                      f"stayed on form={stayed}, errors={errs}, details unchanged={unchanged}")

    # Letters in the telephone field (checked last because it may be saved)
    edit.submit(telephone="abc-defg")
    shot("telephone_letters")
    alerts, errs = alert_texts(page), field_errors(page)
    edit.open()
    shot("telephone_letters_reopened")
    saved_phone = edit.values()["telephone"]
    results.check("Telephone 'abc-defg' (letters)",
                  saved_phone == original["telephone"],
                  "refused with a validation message, telephone unchanged",
                  f"alert={alerts}, errors={errs}, saved telephone='{saved_phone}'")
    results.finish()


def test_tc14_s3_duplicate_email(page, account, other_account, shot, results):
    """Scenario 3 (negative): an e-mail owned by another customer is refused."""
    edit = EditAccountPage(page)
    taken = other_account["email"]
    msg = "Warning: E-Mail address is already registered!"

    for label, value in {"Exact e-mail of another customer": taken,
                         "Same e-mail in upper case": taken.upper()}.items():
        edit.submit(email=value)
        shot(label)
        alerts = alert_texts(page)
        stayed = route(page) == "account/edit"
        edit.open()
        kept = edit.values()["email"] == account["email"]
        results.check(label, stayed and msg in " ".join(alerts) and kept,
                      f"'{msg}', own e-mail kept",
                      f"alert={alerts}, stayed on form={stayed}, own e-mail kept={kept}")

    # Positive control: saving the customer's own e-mail is not a duplicate
    edit.submit(email=account["email"])
    shot("own_email_resaved")
    alerts = alert_texts(page)
    results.check("Re-save own e-mail", SUCCESS in " ".join(alerts),
                  f"'{SUCCESS}'", f"alert={alerts}")
    results.finish()
