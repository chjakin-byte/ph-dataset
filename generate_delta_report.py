import os
import json
from datetime import datetime

STATE_FILE = "output/collection_state.json"
DATA_FILE = "output/raw_historical_products.json"
DELTA_STATE_FILE = "output/last_delta_state.json"
DELTA_REPORT = "DELTA_REPORT.md"

def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def get_date_range(products):
    if not products:
        return "N/A", "N/A"
    dates = [p.get("launch_date") for p in products if p.get("launch_date")]
    if not dates:
        return "N/A", "N/A"
    dates.sort()
    return dates[0], dates[-1]

def main():
    current_state = load_json(STATE_FILE, {})
    last_delta_state = load_json(DELTA_STATE_FILE, {})
    products = load_json(DATA_FILE, [])

    if not current_state:
        print("No current state available.")
        return

    # Calculate Deltas
    current_products = current_state.get("total_products_collected", 0)
    last_products = last_delta_state.get("total_products_collected", 0)
    new_products = current_products - last_products

    current_429s = current_state.get("total_429_events", 0)
    last_429s = last_delta_state.get("total_429_events", 0)
    new_429s = current_429s - last_429s

    earliest, latest = get_date_range(products)
    
    # Try to find the date range for JUST the new products if possible
    # We assume the last `new_products` items appended to the list are the newest additions.
    if new_products > 0 and new_products <= len(products):
        new_items = products[-new_products:]
        new_earliest, new_latest = get_date_range(new_items)
        date_range_str = f"{new_earliest} to {new_latest}"
    elif new_products == 0:
        date_range_str = "No new items"
    else:
        date_range_str = f"Entire set spans {earliest} to {latest}"

    dataset_size_mb = 0
    if os.path.exists(DATA_FILE):
        dataset_size_mb = os.path.getsize(DATA_FILE) / (1024 * 1024)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate Report
    with open(DELTA_REPORT, "w") as f:
        f.write("# Product Hunt Operational Delta Report\n\n")
        f.write(f"**Report Generated:** {timestamp}\n\n")
        f.write("## 1. Collection Progress (Since Last Checkpoint)\n")
        f.write(f"- **New Products Collected:** {new_products:,}\n")
        f.write(f"- **New Date Range Covered:** {date_range_str}\n")
        f.write(f"- **New 429 Rate Limit Events:** {new_429s}\n\n")
        
        f.write("## 2. Current State Snapshot\n")
        f.write(f"- **Total Lifetime Products:** {current_products:,}\n")
        f.write(f"- **Total Dataset Date Range:** {earliest} to {latest}\n")
        f.write(f"- **Current Checkpoint File:** `{STATE_FILE}`\n")
        f.write(f"- **Current Raw Dataset Size:** {dataset_size_mb:.2f} MB\n")

    # Save current state as the new baseline for next delta
    with open(DELTA_STATE_FILE, "w") as f:
        json.dump(current_state, f, indent=2)

    print(f"{DELTA_REPORT} generated successfully.")

if __name__ == "__main__":
    main()
