with open("output/raw_historical_products.json", "r") as f:
    content = f.read()

import re
# The broken merge artifact wiped out the end of the array `]\n  },\n  {`
# Let's fix ALL occurrences of `"maker_name"\n\n    "id"` globally using regex
fixed_content = re.sub(r'("[^"]+")\n\n    "id"', r'\1\n    ]\n  },\n  {\n    "id"', content)

with open("output/raw_historical_products.json", "w") as f:
    f.write(fixed_content)
