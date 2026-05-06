import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import only the pure function — no Playwright needed
from modules.scraper import _extract_country

TEST_CASES = [
    # (input, expected_output)
    ("United Kingdom",                              "United Kingdom"),
    ("London, England, United Kingdom",             "United Kingdom"),
    ("Manchester, England, United Kingdom",         "United Kingdom"),
    ("Greater Manchester Area",                     "United Kingdom"),   # Manchester → UK via 'England'? No, inner=Manchester→Other→title
    ("Greater Edinburgh Area",                      "United Kingdom"),   # Edinburgh→Scotland→UK? No, inner=Edinburgh→Other→title. Let's see
    ("Greater London Area",                         "United Kingdom"),   # inner=London → no alias → London... hmm
    ("Edinburgh, Scotland, United Kingdom",         "United Kingdom"),
    ("Austin, TX",                                  "United States"),
    ("New York, NY",                                "United States"),
    ("San Francisco, CA",                           "United States"),
    ("United States",                               "United States"),
    ("USA",                                         "United States"),
    ("Canada",                                      "Canada"),
    ("Toronto, Ontario, Canada",                    "Canada"),
    ("Berlin, Germany",                             "Germany"),
    ("Germany",                                     "Germany"),
    ("Paris, France",                               "France"),
    ("Remote",                                      "Remote"),
    ("Worldwide",                                   "Remote"),
    ("Singapore",                                   "Singapore"),
    ("Sydney, New South Wales, Australia",          "Australia"),
    ("Dubai, United Arab Emirates",                 "UAE"),
    ("",                                            "Other"),
]

passed = 0
failed = 0
for raw, expected in TEST_CASES:
    result = _extract_country(raw)
    status = "✅" if result == expected else "❌"
    if result != expected:
        failed += 1
        print(f"{status} '{raw}'\n     got='{result}'  expected='{expected}'")
    else:
        passed += 1
        print(f"{status} '{raw}' → '{result}'")

print(f"\n{passed}/{passed+failed} tests passed")
