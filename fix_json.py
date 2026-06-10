import re

with open("output/raw_historical_products.json", "r") as f:
    content = f.read()

# Fix the broken array end due to bad merge conflicts
# Pattern: "John Ruf"\n\n    "id": "1103937",
fixed_content = content.replace('"John Ruf"\n\n    "id"', '"John Ruf"\n    ]\n  },\n  {\n    "id"')

with open("output/raw_historical_products.json", "w") as f:
    f.write(fixed_content)
