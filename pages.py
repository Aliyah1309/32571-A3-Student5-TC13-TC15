"""Page helpers for the OpenCart account pages used in TC13-TC15.

Each helper wraps one page of the website so the test files only describe
*what* is tested, not *how* the page is driven.
"""
import time

from config import BASE_URL, VALID_PASSWORD, DEFAULT_PHONE, EMAIL_USER, EMAIL_DOMAIN


def unique_email(tag):
    """Return a new, never-registered variant of the tester's e-mail address."""
    return f"{EMAIL_USER}+{tag}{int(time.time() * 1000)}@{EMAIL_DOMAIN}"


def route(page):
    """Return the OpenCart route of the current page, e.g. 'account/address'."""
    url = page.url
    return url.split("route=")[1].split("&")[0] if "route=" in url else url


# --------------------------------------------------------------------------
# Account registration / login / logout (set-up steps, tested by Student 1)
# --------------------------------------------------------------------------
def register_account(page, email, first="Aliyah", last="Shaikh"):
    """Register a new customer through the public registration form."""
    page.goto(BASE_URL + "account/register")
    page.fill("#input-firstname", first)
    page.fill("#input-lastname", last)
    page.fill("#input-email", email)
    page.fill("#input-telephone", DEFAULT_PHONE)
    page.fill("#input-password", VALID_PASSWORD)
    page.fill("#input-confirm", VALID_PASSWORD)
    page.check("input[name=agree]")            # tick the Privacy Policy box
    page.click("input[value=Continue]")
    page.wait_for_url("**route=account/success**")


def login(page, email, password):
    """Log in through the Returning Customer form. Returns True on success."""
    page.goto(BASE_URL + "account/login")
    page.fill("#input-email", email)
    page.fill("#input-password", password)
    page.click("input[value=Login]")
    page.wait_for_load_state()
    return route(page) == "account/account"


def logout(page):
    page.goto(BASE_URL + "account/logout")
    page.wait_for_load_state()


def alert_texts(page):
    """All alert banners (success or warning) shown at the top of the content."""
    return [t.strip() for t in page.locator(".alert").all_inner_texts()]


def field_errors(page):
    """All red validation messages shown under form fields."""
    return [t.strip() for t in page.locator(".text-danger").all_inner_texts()]


# --------------------------------------------------------------------------
# F13 Address Book
# --------------------------------------------------------------------------
class AddressBookPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.goto(BASE_URL + "account/address")
        self.page.wait_for_load_state()

    def entries(self):
        """Text of every address card in the Address Book (one string each)."""
        rows = self.page.locator("#content table tr td.text-left")
        return [" | ".join(t.split("\n")) for t in rows.all_inner_texts()]

    def open_new_form(self):
        self.page.goto(BASE_URL + "account/address/add")
        self.page.wait_for_load_state("networkidle")

    def fill_form(self, first="", last="", address_1="", city="", postcode="",
                  country=None, zone=None, default=None):
        """Fill the New/Edit Address form.

        country: visible country name, "" to choose '--- Please Select ---',
                 or None to keep the page default.
        zone:    visible region name, or None to leave '--- Please Select ---'.
        default: True/False sets the Default Address radio; None leaves it.
        """
        p = self.page
        p.fill("#input-firstname", first)
        p.fill("#input-lastname", last)
        p.fill("#input-address-1", address_1)
        p.fill("#input-city", city)
        p.fill("#input-postcode", postcode)
        if country is not None:
            if country == "":
                p.select_option("#input-country", value="")
                p.wait_for_timeout(800)             # region list reloads by AJAX
            else:
                p.select_option("#input-country", label=country)
                # The site disables the Country box while it loads the regions by AJAX;
                # wait until it is enabled again and the region list is filled.
                p.wait_for_load_state("networkidle")
                p.wait_for_function(
                    "!document.querySelector('#input-country').disabled && "
                    "document.querySelectorAll('#input-zone option').length > 1")
                p.wait_for_timeout(300)
        if zone is not None:
            p.select_option("#input-zone", label=zone)
        if default is not None:
            p.check(f"input[name=default][value='{1 if default else 0}']")

    def submit(self):
        self.page.click("input[value=Continue]")
        self.page.wait_for_load_state()

    def add(self, **fields):
        self.open_new_form()
        self.fill_form(**fields)
        self.submit()

    def _row(self, text):
        """The table row whose address card contains `text`."""
        return self.page.locator("#content table tr", has_text=text).first

    def click_edit(self, text):
        self._row(text).locator("a:has-text('Edit')").click()
        self.page.wait_for_load_state("networkidle")

    def click_delete(self, text):
        self._row(text).locator("a:has-text('Delete')").click()
        self.page.wait_for_load_state()

    def form_values(self):
        p = self.page
        return {
            "first": p.input_value("#input-firstname"),
            "last": p.input_value("#input-lastname"),
            "address_1": p.input_value("#input-address-1"),
            "city": p.input_value("#input-city"),
            "postcode": p.input_value("#input-postcode"),
            "country": p.locator("#input-country option:checked").inner_text().strip(),
            "zone": p.locator("#input-zone option:checked").inner_text().strip(),
        }


# --------------------------------------------------------------------------
# F14 Edit Account (My Account > Edit your account information)
# --------------------------------------------------------------------------
class EditAccountPage:
    FIELDS = ("firstname", "lastname", "email", "telephone")

    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.goto(BASE_URL + "account/edit")
        self.page.wait_for_load_state()

    def values(self):
        return {f: self.page.input_value(f"#input-{f}") for f in self.FIELDS}

    def submit(self, skip_browser_validation=False, **fields):
        """Fill the given fields and click Continue.

        skip_browser_validation=True adds `novalidate` to the form so the value
        reaches the server even if Chrome's built-in e-mail check would block it.
        Returns the browser's own validation message for the e-mail box.
        """
        self.open()
        for name, value in fields.items():
            self.page.fill(f"#input-{name}", value)
        html5_msg = self.page.eval_on_selector(
            "#input-email", "el => el.validationMessage")
        if skip_browser_validation:
            self.page.eval_on_selector(
                "#content form", "f => f.setAttribute('novalidate', '')")
        self.page.click("input[value=Continue]")
        self.page.wait_for_load_state()
        return html5_msg


# --------------------------------------------------------------------------
# F15 Change Password (My Account > Change your password)
# --------------------------------------------------------------------------
class PasswordPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.goto(BASE_URL + "account/password")
        self.page.wait_for_load_state()

    def change(self, password, confirm=None):
        """Submit the Change Password form. confirm defaults to the same value."""
        self.open()
        self.page.fill("#input-password", password)
        self.page.fill("#input-confirm", password if confirm is None else confirm)
        self.page.click("input[value=Continue]")
        self.page.wait_for_load_state()
