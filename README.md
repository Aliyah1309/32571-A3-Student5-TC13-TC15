# Student 5 – System tests TC13–TC15 (OpenCart demo store)

Website under test: https://opencart.abstracta.us/

| Test case | Function | File |
|---|---|---|
| TC13 | F13 Address Book Management | `test_tc13_address_book.py` |
| TC14 | F14 Account Information Update | `test_tc14_account_information.py` |
| TC15 | F15 Password Change | `test_tc15_password_change.py` |
| (supplementary) | Logged-out access to F13–F15 pages | `test_guest_access.py` |

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest                    # everything
pytest -m tc13            # one test case (tc13 / tc14 / tc15 / guest)
pytest --html=results/report.html --self-contained-html
```

Every scenario registers its own test account using a variant of the tester's address
(`aliyah.shaikh+tc<timestamp>@student.uts.edu.au`, password `Test@12345`; set in `config.py`),
so the scenarios are independent and can run in any order.

## Output

- `screenshots/<test name>/NN_<step>.png` – full-page screenshot of every checked input
- `results/results.jsonl` – one line per input: expected, actual, Pass/Fail/Observation
- `results/run_log.txt`, `results/report.html` – the evidence run used in the report (31 Oct 2026)

Result of that run: 11 pytest tests passed and 3 failed (TC13 S2, TC14 S2 and TC15 S3). The failures are website
defects, not script errors (see the report).
