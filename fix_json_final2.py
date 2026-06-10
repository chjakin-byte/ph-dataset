with open("output/raw_historical_products.json", "r") as f:
    content = f.read()

import re
# Another variation: "Kruno Sulic"\n    ]\n\n    "id"
fixed_content = re.sub(r'\]\n\n    "id"', r']\n  },\n  {\n    "id"', content)

with open("output/raw_historical_products.json", "w") as f:
    f.write(fixed_content)
