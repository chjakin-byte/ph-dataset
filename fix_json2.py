with open("output/raw_historical_products.json", "r") as f:
    content = f.read()

fixed_content = content.replace('"Josh O\'Brien"\n\n    "id"', '"Josh O\'Brien"\n    ]\n  },\n  {\n    "id"')

with open("output/raw_historical_products.json", "w") as f:
    f.write(fixed_content)
