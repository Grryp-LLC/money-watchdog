"""Privacy guard for anything that ends up on a shareable image or caption.

Rules (enforced, not advisory):
  * no email addresses, URLs, phone numbers, account/card/order numbers (any run of 4+ digits
    that is not a dollar amount or a year), "ending in 1234"-style fragments
  * no personal names from the user's deny-list (their own name, household members)
  * dollar amounts are rounded to whole dollars
  * anonymous mode replaces merchant names with a category alias
"""
import re

CATEGORY_ALIASES = {
    "streaming": "A Streaming Service", "music": "A Music App", "cloud": "A Cloud Storage Plan",
    "fitness": "A Gym Membership", "phone": "A Phone Plan", "bank": "A Bank", "shopping": "A Shopping Club",
    "news": "A News Subscription", "software": "A Software Subscription", "food": "A Meal Kit",
    "utility": "A Utility Bill", "insurance": "An Insurance Policy", "telecom": "An Internet Provider",
    "gaming": "A Gaming Pass", "delivery": "A Delivery Membership", "generic": "A Mystery Subscription",
}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL = re.compile(r"(https?://\S+|www\.\S+)", re.I)
PHONE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
ENDING = re.compile(r"\b(ending|ends)\s+(in|with)\s+\S+|\b(x{2,}|\*{2,}|•{2,})\s?\d{2,}", re.I)
MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})*|\d+)(\.\d{1,2})?")
LONGNUM = re.compile(r"(?<![\$\d.,])\d{4,}(?![\d.,]*%)")


def round_money(text: str) -> str:
    def repl(m):
        whole = float(m.group(1).replace(",", "") + (m.group(2) or ""))
        return "$" + f"{round(whole):,}"
    return MONEY.sub(repl, text)


def scrub(text: str, deny_names=()) -> str:
    if not text:
        return text
    t = EMAIL.sub("[redacted]", text)
    t = URL.sub("", t)
    t = ENDING.sub("", t)
    t = PHONE.sub("", t)
    t = round_money(t)
    t = LONGNUM.sub(lambda m: m.group(0) if 1990 <= int(m.group(0)) <= 2100 else "", t)
    for n in deny_names or ():
        if n and len(n) >= 2:
            t = re.sub(re.escape(n), "", t, flags=re.I)
    return re.sub(r"\s{2,}", " ", t).strip()


def lint(text: str, deny_names=()) -> list:
    """Return a list of problems found in text that is about to be published."""
    probs = []
    if EMAIL.search(text): probs.append("email address")
    if URL.search(text): probs.append("url")
    if ENDING.search(text): probs.append("card/account fragment")
    if re.search(r"\$\s?\d+\.\d{1,2}", text): probs.append("unrounded amount")
    for m in LONGNUM.finditer(text):
        if not (1990 <= int(m.group(0)) <= 2100): probs.append("long number " + m.group(0))
    for n in deny_names or ():
        if n and re.search(re.escape(n), text, re.I): probs.append("denied name")
    return probs


def display_merchant(merchant: str, category: str, anonymous: bool, deny_names=()) -> str:
    if anonymous:
        return CATEGORY_ALIASES.get((category or "generic").lower(), CATEGORY_ALIASES["generic"])
    return scrub(merchant, deny_names)
