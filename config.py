"""Shared settings for Student 5's tests (TC13-TC15)."""

BASE_URL = "https://opencart.abstracta.us/index.php?route="

# Tester's e-mail. The site allows each address to be registered only once, so every
# test account uses a "+tag" variant: aliyah.shaikh+<tag><timestamp>@student.uts.edu.au
EMAIL_USER = "aliyah.shaikh"
EMAIL_DOMAIN = "student.uts.edu.au"

# Password given to every freshly registered test account
VALID_PASSWORD = "Test@12345"

# Telephone used at registration
DEFAULT_PHONE = "0412345678"

# Browser window size used for every test (matches the screenshots in the report)
VIEWPORT = {"width": 1280, "height": 900}
