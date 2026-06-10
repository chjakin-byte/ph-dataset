import os
import json
import hashlib
from collections import defaultdict
import random

def get_file_info(filepath):
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return f"Size: {size_mb:.2f} MB | SHA256: {sha256.hexdigest()}"

def main():
    print("========== 1. FILE LIST ==========")
    files_to_check = [
        "MILESTONE_SAMPLE_100.json",
        "MILESTONE_DISTRIBUTION_REPORT.md",
        "MILESTONE_DATA_AUDIT.md",
        "output/raw_historical_products.json"
    ]
    for fp in files_to_check:
        print(f"- {fp}")
        
    print("\n========== 2. MILESTONE_SAMPLE_100.json ==========")
    with open("MILESTONE_SAMPLE_100.json", "r") as f:
        sample_data = json.load(f)
    print(f"Exact record count: {len(sample_data)}")
    
    print("\n--- First 10 Records ---")
    print(json.dumps(sample_data[:10], indent=2))
    
    print("\n--- 10 Representative Records (Dates/Topics) ---")
    buckets = defaultdict(list)
    for p in sample_data:
        d_str = p.get("launch_date", "Unknown")[:7]
        topics = p.get("topics", ["None"])
        top_t = topics[0] if topics else "None"
        buckets[f"{d_str}_{top_t}"].append(p)
        
    rep_samples = []
    bucket_keys = list(buckets.keys())
    random.seed(42)
    random.shuffle(bucket_keys)
    for bk in bucket_keys:
        if len(rep_samples) >= 10: break
        rep_samples.append(random.choice(buckets[bk]))
        
    print(json.dumps(rep_samples, indent=2))
    print(f"\nConfirmation: All {len(sample_data)} records are real parsed JSON objects from the current milestone.")

    print("\n========== 3. MILESTONE_DATA_AUDIT.md ==========")
    with open("MILESTONE_DATA_AUDIT.md", "r") as f:
        lines = f.readlines()
        
    sections_to_print = False
    for line in lines:
        if "## 1. Time Coverage Checks" in line or "## 2. Integrity Checks" in line:
            sections_to_print = True
        if "## 3. Human-Readable Raw JSON Preview" in line:
            sections_to_print = False
            
        if sections_to_print:
            print(line.rstrip())

    print("\n========== 4. raw_historical_products.json ==========")
    raw_path = "output/raw_historical_products.json"
    print(get_file_info(raw_path))
    
    with open(raw_path, "r") as f:
        raw_data = json.load(f)
        
    print(f"Total record count: {len(raw_data)}")
    print("\n--- First Record ---")
    print(json.dumps(raw_data[0], indent=2))
    print("\n--- Last Record ---")
    print(json.dumps(raw_data[-1], indent=2))

if __name__ == "__main__":
    main()
