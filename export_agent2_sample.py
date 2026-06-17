import os
import json
import random

DATA_FILE = "output/raw_historical_products.json"
EXPORT_DIR = "data_exports"
EXPORT_FILE = os.path.join(EXPORT_DIR, "dashboard_validation_sample.json")

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r") as f:
        products = json.load(f)

    total_products = len(products)
    if total_products == 0:
        print("No products available to export.")
        return

    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    # We need to extract 500 - 1000 real products. Let's take exactly 1000.
    sample_size = 1000 if total_products >= 1000 else total_products
    
    # Take a diverse slice rather than just the first 1000 or last 1000
    random.seed(42)  # Deterministic
    raw_sample = random.sample(products, sample_size)

    mapped_sample = []
    for p in raw_sample:
        # The prompt requires specific field names. We map our internal schema to those exact names.
        mapped_record = {
            "product_name": p.get("product_name"),
            "tagline": p.get("tagline"),
            "description": p.get("description"),
            "topics": p.get("topics", []),
            "votes": p.get("votes", 0),
            "comments": p.get("comment_count", 0),  # Mapping comment_count to comments
            # Mapping makers array to maker. If multiple, we just pass the array as they are all makers. 
            # If the downstream expects a string, it will have to handle the array, or we can just pass the array.
            # Passing the raw array ensures no data loss.
            "maker": p.get("makers", []), 
            "launch_date": p.get("launch_date")
        }
        mapped_sample.append(mapped_record)

    with open(EXPORT_FILE, "w") as f:
        json.dump(mapped_sample, f, indent=2)

    print(f"Successfully exported {sample_size} raw records to {EXPORT_FILE}.")

if __name__ == "__main__":
    main()
