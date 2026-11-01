"""pytest fixtures for Student 5 (TC13-TC15).

- browser        : one Chromium instance for the whole run
- page           : a fresh, logged-out browser context for every scenario
- shot           : saves a numbered full-page screenshot for the current scenario
- account        : registers a brand-new customer and logs it in
- other_account  : a second registered customer (used for duplicate e-mail checks)
- results        : soft-check recorder; every input is checked and logged to
                   results/results.jsonl before the scenario passes or fails
"""
import json
import os
import re

import pytest
from playwright.sync_api import sync_playwright

from config import VIEWPORT, VALID_PASSWORD
from pages import register_account, login, logout, unique_email

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots")
RESULTS = os.path.join(HERE, "results", "results.jsonl")


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport=VIEWPORT, ignore_https_errors=True)
    pg = ctx.new_page()
    # Fail loudly if any input ever triggers a JavaScript dialog (e.g. XSS)
    pg.dialogs = []
    pg.on("dialog", lambda d: (pg.dialogs.append(d.message), d.dismiss()))
    yield pg
    ctx.close()


@pytest.fixture
def shot(page, request):
    """shot('name') -> screenshots/<test name>/<nn>_<name>.png"""
    folder = os.path.join(SHOTS, request.node.name)
    os.makedirs(folder, exist_ok=True)
    counter = {"n": 0}

    def take(name):
        counter["n"] += 1
        safe = re.sub(r"[^a-z0-9_]+", "_", name.lower())
        path = os.path.join(folder, f"{counter['n']:02d}_{safe}.png")
        page.screenshot(path=path, full_page=True)
        return path
    return take


@pytest.fixture
def account(page):
    """Register a fresh customer, then log in. Returns its credentials."""
    email = unique_email("tc")
    register_account(page, email)
    logout(page)
    assert login(page, email, VALID_PASSWORD), "set-up login failed"
    return {"email": email, "password": VALID_PASSWORD}


@pytest.fixture
def other_account(browser):
    """A second customer registered in a separate browser context."""
    ctx = browser.new_context(viewport=VIEWPORT, ignore_https_errors=True)
    pg = ctx.new_page()
    email = unique_email("other")
    register_account(pg, email, first="Other", last="Customer")
    ctx.close()
    return {"email": email}


class Recorder:
    """Soft assertions: every input is checked and logged; failures are
    collected and raised together at the end of the scenario."""

    def __init__(self, test_name):
        self.test_name = test_name
        self.failures = []
        os.makedirs(os.path.dirname(RESULTS), exist_ok=True)

    def check(self, label, passed, expected, actual):
        row = {"test": self.test_name, "input": label, "expected": expected,
               "actual": actual, "status": "Pass" if passed else "Fail"}
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{row['status']}] {label}: expected={expected!r} actual={actual!r}")
        if not passed:
            self.failures.append(f"{label}: expected {expected!r}, got {actual!r}")

    def note(self, label, actual):
        """Record an observation that does not affect pass/fail."""
        row = {"test": self.test_name, "input": label, "expected": "-",
               "actual": actual, "status": "Observation"}
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[Observation] {label}: {actual!r}")

    def finish(self):
        assert not self.failures, "\n".join(self.failures)


@pytest.fixture
def results(request):
    return Recorder(request.node.name)
