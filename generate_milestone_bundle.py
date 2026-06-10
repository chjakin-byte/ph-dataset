import os
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

DATA_FILE = "output/raw_historical_products.json"

def extract_domain(url):
    if not url: return "None"
    try:
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else "None"
    except:
        return "Invalid"

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r") as f:
        products = json.load(f)

    total_products = len(products)
    if total_products == 0:
        print("No products available to audit.")
        return

    print(f"Processing milestone bundle for {total_products} products...")

    # --- 1. Sample Verification (100 Recent Records) ---
    # We take the last 100 products to show the most recently collected
    samples_100 = products[-100:] if len(products) >= 100 else products
    with open("MILESTONE_SAMPLE_100.json", "w") as f:
        json.dump(samples_100, f, indent=2)

    # --- 2. Distribution Checks ---
    topic_counter = Counter()
    maker_counter = Counter()
    domain_counter = Counter()
    vote_dist = {"0": 0, "1-10": 0, "11-50": 0, "51-100": 0, "101-500": 0, "500+": 0}
    comment_dist = {"0": 0, "1-5": 0, "6-20": 0, "21-50": 0, "50+": 0}
    date_dist = Counter()

    for p in products:
        # Topics
        for t in p.get("topics", []): topic_counter[t] += 1
        # Makers
        for m in p.get("makers", []): maker_counter[m] += 1
        # Domains
        domain_counter[extract_domain(p.get("website"))] += 1
        # Votes
        v = p.get("votes", 0)
        if v == 0: vote_dist["0"] += 1
        elif v <= 10: vote_dist["1-10"] += 1
        elif v <= 50: vote_dist["11-50"] += 1
        elif v <= 100: vote_dist["51-100"] += 1
        elif v <= 500: vote_dist["101-500"] += 1
        else: vote_dist["500+"] += 1
        # Comments
        c = p.get("comment_count", 0)
        if c == 0: comment_dist["0"] += 1
        elif c <= 5: comment_dist["1-5"] += 1
        elif c <= 20: comment_dist["6-20"] += 1
        elif c <= 50: comment_dist["21-50"] += 1
        else: comment_dist["50+"] += 1
        # Date
        d_str = p.get("launch_date")
        if d_str:
            date_only = d_str[:10]
            date_dist[date_only] += 1

    with open("MILESTONE_DISTRIBUTION_REPORT.md", "w") as f:
        f.write("# Milestone Distribution Report\n\n")
        
        f.write("## 1. Top 20 Topics\n")
        for i, (k, v) in enumerate(topic_counter.most_common(20), 1):
            f.write(f"{i}. {k} ({v})\n")
            
        f.write("\n## 2. Top 20 Makers\n")
        for i, (k, v) in enumerate(maker_counter.most_common(20), 1):
            f.write(f"{i}. {k} ({v})\n")
            
        f.write("\n## 3. Top 20 Domains\n")
        for i, (k, v) in enumerate(domain_counter.most_common(20), 1):
            f.write(f"{i}. {k} ({v})\n")
            
        f.write("\n## 4. Votes Distribution\n")
        for k, v in vote_dist.items(): f.write(f"- {k}: {v}\n")
        
        f.write("\n## 5. Comment Count Distribution\n")
        for k, v in comment_dist.items(): f.write(f"- {k}: {v}\n")
        
        f.write("\n## 6. Date Distribution (Last 14 dates)\n")
        # Sort dates descending and take last 14
        sorted_dates = sorted(date_dist.items(), key=lambda x: x[0], reverse=True)[:14]
        for k, v in sorted_dates: f.write(f"- {k}: {v} products\n")

    # --- 3. Integrity Checks & 4. Time Coverage Checks ---
    unique_ids = set()
    semantic_names = Counter()
    field_missing_counts = defaultdict(int)
    field_total_counts = defaultdict(int)
    malformed_count = 0
    suspicious_count = 0
    valid_dates_dt = []

    for p in products:
        unique_ids.add(p.get("id"))
        
        name = p.get("product_name", "")
        if name:
            semantic_names[name.lower()] += 1
        else:
            malformed_count += 1
            
        if p.get("votes", 0) == 0 and p.get("comment_count", 0) == 0:
            suspicious_count += 1

        for k, v in p.items():
            field_total_counts[k] += 1
            if v is None or v == "" or (isinstance(v, list) and len(v) == 0):
                field_missing_counts[k] += 1
                
        d_str = p.get("launch_date")
        if d_str:
            dt = datetime.fromisoformat(d_str.replace('Z', '+00:00'))
            valid_dates_dt.append(dt)

    duplicate_pct = ((total_products - len(unique_ids)) / total_products) * 100
    semantic_dupes = {k: v for k, v in semantic_names.items() if v > 1}

    # Coverage
    valid_dates_dt.sort()
    earliest_dt = valid_dates_dt[0] if valid_dates_dt else None
    latest_dt = valid_dates_dt[-1] if valid_dates_dt else None
    days_covered = 0
    missing_dates = []
    
    if earliest_dt and latest_dt:
        days_covered = (latest_dt.date() - earliest_dt.date()).days + 1
        expected_dates = set((earliest_dt.date() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_covered))
        actual_dates = set(d.strftime("%Y-%m-%d") for d in valid_dates_dt)
        missing_dates = sorted(list(expected_dates - actual_dates))

    with open("MILESTONE_DATA_AUDIT.md", "w") as f:
        f.write("# Milestone Data Audit Report\n\n")
        f.write(f"**Total Dataset Checked:** {total_products:,}\n\n")
        
        f.write("## 1. Integrity Checks\n")
        f.write(f"- **Exact ID Duplicate Percentage:** {duplicate_pct:.4f}%\n")
        f.write(f"- **Malformed Records (No Name):** {malformed_count}\n")
        f.write(f"- **Suspicious Records (0 votes, 0 comments):** {suspicious_count}\n\n")
        
        f.write("### Missing Field Percentages\n")
        for field, total in sorted(field_total_counts.items()):
            missing = field_missing_counts.get(field, 0)
            pct = (missing / total) * 100 if total > 0 else 0
            f.write(f"- **{field}:** {pct:.2f}% missing ({missing} records)\n")
            
        f.write("\n### Semantic Duplicate Examples (Same Name, Diff ID)\n")
        if semantic_dupes:
            for i, (k, v) in enumerate(list(semantic_dupes.items())[:10]):
                f.write(f"- '{k}': {v} times\n")
        else:
            f.write("- None detected.\n")
            
        f.write("\n## 2. Time Coverage Checks\n")
        f.write(f"- **Earliest Timestamp:** {earliest_dt.isoformat() if earliest_dt else 'N/A'}\n")
        f.write(f"- **Latest Timestamp:** {latest_dt.isoformat() if latest_dt else 'N/A'}\n")
        f.write(f"- **Calendar Days Covered:** {days_covered} days\n\n")
        
        f.write("### Missing Dates or Gaps\n")
        if missing_dates:
            for d in missing_dates:
                f.write(f"- {d}\n")
        else:
            f.write("✅ No missing dates in the covered calendar range. Time progression is contiguous.\n")

    print("Milestone bundle generated: MILESTONE_SAMPLE_100.json, MILESTONE_DISTRIBUTION_REPORT.md, MILESTONE_DATA_AUDIT.md")

if __name__ == "__main__":
    main()
