import json

with open("output/raw_historical_products.json", "r") as f:
    products = json.load(f)

sorted_p = sorted(products, key=lambda x: x.get("launch_date", ""))
last_date = sorted_p[-1].get("launch_date") if sorted_p else None

with open("output/collection_state.json", "r") as f:
    state = json.load(f)

state["total_products_collected"] = len(products)
if last_date:
    state["last_processed_date"] = last_date

with open("output/collection_state.json", "w") as f:
    json.dump(state, f, indent=2)

print(f"State file synced to {len(products)} products at date {last_date}")
