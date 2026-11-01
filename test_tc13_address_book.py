"""TC13 - F13 Address Book Management
https://opencart.abstracta.us/index.php?route=account/address
"""
import pytest

from pages import AddressBookPage, alert_texts, field_errors, route

pytestmark = pytest.mark.tc13

ADDED = "Your address has been successfully added"
UPDATED = "Your address has been successfully updated"
DELETED = "Your address has been successfully deleted"

# A valid Australian address used as the starting point for every input
BASE = dict(first="Aliyah", last="Shaikh", address_1="15 Broadway",
            city="Ultimo", postcode="2007", country="Australia",
            zone="New South Wales")


def test_tc13_s1_add_valid_addresses(page, account, shot, results):
    """Scenario 1 (positive + edge): valid addresses of different shapes are saved."""
    book = AddressBookPage(page)
    book.open()
    shot("empty_address_book")
    results.note("Empty Address Book message", page.locator("#content p").first.inner_text())

    valid_inputs = {
        "Standard Australian address": dict(BASE),
        "Accents and apostrophes": dict(BASE, first="Zoë", last="O'Brien",
                                        address_1="Level 2, 1 King's Cross Rd",
                                        city="Sydney", postcode="2011"),
        "Minimum lengths (1/1/3/2 chars)": dict(BASE, first="A", last="B",
                                                address_1="1 A", city="Ry",
                                                postcode="2112"),
        "Script tag in Address 1": dict(BASE, address_1="<script>alert('xss')</script>"),
    }
    for label, data in valid_inputs.items():
        before = len(book.entries())
        book.add(**data)
        shot(f"added_{label}")
        entries = book.entries()
        saved = any(data["address_1"] in e and data["first"] in e for e in entries)
        ok = (ADDED in " ".join(alert_texts(page)) and route(page) == "account/address"
              and len(entries) == before + 1 and saved and not page.dialogs)
        results.check(label, ok,
                      f"'{ADDED}', entry shown as typed, entries {before}->{before + 1}",
                      f"alert={alert_texts(page)}, entries {before}->{len(entries)}, "
                      f"last entry='{entries[-1] if entries else ''}', dialogs={page.dialogs}")
    results.finish()


def test_tc13_s2_reject_invalid_addresses(page, account, shot, results):
    """Scenario 2 (negative + boundary): invalid input is rejected with a message."""
    book = AddressBookPage(page)

    # 1) Completely empty form (page default country is United Kingdom)
    book.open_new_form()
    book.submit()
    shot("empty_form")
    expected_all = ["First Name must be between 1 and 32 characters!",
                    "Last Name must be between 1 and 32 characters!",
                    "Address must be between 3 and 128 characters!",
                    "City must be between 2 and 128 characters!",
                    "Postcode must be between 2 and 10 characters!",
                    "Please select a region / state!"]
    errs = field_errors(page)
    results.check("Empty form", all(e in errs for e in expected_all)
                  and route(page) == "account/address/add", expected_all, errs)

    # 2) One invalid field at a time, everything else valid
    invalid_inputs = {
        "First Name 33 chars": (dict(BASE, first="A" * 33),
                                "First Name must be between 1 and 32 characters!"),
        "First Name spaces only": (dict(BASE, first="   "),
                                   "First Name must be between 1 and 32 characters!"),
        "Last Name 33 chars": (dict(BASE, last="L" * 33),
                               "Last Name must be between 1 and 32 characters!"),
        "Address 1 two chars": (dict(BASE, address_1="ab"),
                                "Address must be between 3 and 128 characters!"),
        "City one char": (dict(BASE, city="X"),
                          "City must be between 2 and 128 characters!"),
        "No country selected": (dict(BASE, country="", zone=None),
                                "Please select a country!"),
        "No region selected": (dict(BASE, zone=None),
                               "Please select a region / state!"),
        "UK postcode 11 chars": (dict(BASE, country="United Kingdom", zone="Bristol",
                                      postcode="12345678901"),
                                 "Postcode must be between 2 and 10 characters!"),
        "AU postcode 11 chars": (dict(BASE, postcode="12345678901"),
                                 "Postcode must be between 2 and 10 characters!"),
    }
    for label, (data, message) in invalid_inputs.items():
        book.open()
        before = book.entries()
        book.add(**data)
        shot(label)
        errs, alerts = field_errors(page), alert_texts(page)
        stayed = route(page) == "account/address/add"
        book.open()
        after = book.entries()
        new = [e for e in after if e not in before]
        results.check(label, stayed and message in errs and len(after) == len(before),
                      f"rejected with '{message}', no entry added",
                      f"route={'account/address/add' if stayed else 'account/address'}, "
                      f"errors={errs}, alert={alerts}, new entry={new}")
        if new:
            shot(f"{label}_saved_entry")
    results.finish()


def test_tc13_s3_edit_and_delete_rules(page, account, shot, results):
    """Scenario 3: edit an address, then check the delete rules."""
    book = AddressBookPage(page)

    # Only address on the account
    book.add(**BASE)
    book.open()
    shot("one_address")

    # a) The only address cannot be deleted
    book.click_delete("15 Broadway")
    shot("delete_only_address")
    msg = "Warning: You must have at least one address!"
    alerts = alert_texts(page)
    book.open()
    results.check("Delete the only address",
                  msg in " ".join(alerts) and any("15 Broadway" in e for e in book.entries()),
                  f"'{msg}', address kept", f"alert={alerts}, entries={book.entries()}")

    # b) Edit: form is pre-filled with the saved values, and changes are saved
    book.click_edit("15 Broadway")
    prefill = book.form_values()
    shot("edit_form_prefilled")
    book.fill_form(first="Aliyah", last="Shaikh", address_1="1 Macquarie St",
                   city="Sydney", postcode="2000")
    book.submit()
    shot("after_edit")
    entries = book.entries()
    results.check("Edit address (pre-fill)",
                  prefill["address_1"] == "15 Broadway" and prefill["city"] == "Ultimo"
                  and prefill["zone"] == "New South Wales",
                  "form shows 15 Broadway / Ultimo / New South Wales", prefill)
    results.check("Edit address (save)",
                  UPDATED in " ".join(alert_texts(page))
                  and any("1 Macquarie St" in e and "Sydney 2000" in e for e in entries)
                  and not any("15 Broadway" in e for e in entries),
                  f"'{UPDATED}', card shows 1 Macquarie St, Sydney 2000",
                  f"alert={alert_texts(page)}, entries={entries}")

    # c) Add a second address with special characters and make it the default
    book.add(**dict(BASE, first="Zoë", last="O'Brien",
                    address_1="Level 2, 1 King's Cross Rd", city="Parramatta",
                    postcode="2150", default=True))
    book.click_edit("King's Cross")
    prefill = book.form_values()
    results.check("Special characters kept on edit form",
                  prefill["first"] == "Zoë" and prefill["last"] == "O'Brien",
                  "Zoë / O'Brien", f"{prefill['first']} / {prefill['last']}")
    book.open()
    shot("two_addresses")

    # d) The default address cannot be deleted
    book.click_delete("King's Cross")
    shot("delete_default_address")
    msg = "Warning: You can not delete your default address!"
    alerts = alert_texts(page)
    book.open()
    results.check("Delete the default address",
                  msg in " ".join(alerts) and any("King's Cross" in e for e in book.entries()),
                  f"'{msg}', address kept", f"alert={alerts}, entries={book.entries()}")

    # e) A non-default address can be deleted
    book.click_delete("Macquarie")
    shot("delete_non_default_address")
    alerts = alert_texts(page)
    entries = book.entries()
    results.check("Delete a non-default address",
                  DELETED in " ".join(alerts) and len(entries) == 1
                  and "King's Cross" in entries[0],
                  f"'{DELETED}', only the default address remains",
                  f"alert={alerts}, entries={entries}")
    results.note("Confirmation prompt before Delete", f"dialogs shown: {page.dialogs}")
    results.finish()
