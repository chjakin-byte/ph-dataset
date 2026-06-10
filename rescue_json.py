import re
import json

with open("output/raw_historical_products.json", "r") as f:
    text = f.read()

# Extract all blocks that look like a valid JSON object 
# by matching {"id": ... "makers": [...]} 
pattern = r'\{\s*"id":\s*"\d+".*?"makers":\s*\[.*?\]\s*\}'
matches = re.findall(pattern, text, re.DOTALL)

valid_objects = []
for m in matches:
    try:
        obj = json.loads(m)
        valid_objects.append(obj)
    except:
        pass

# Deduplicate just in case
unique_objects = {obj['id']: obj for obj in valid_objects}.values()

with open("output/raw_historical_products.json", "w") as f:
    json.dump(list(unique_objects), f, indent=2)

print(f"Rescued {len(unique_objects)} valid product JSON objects.")
