import os
import json
from collections import Counter
from datetime import datetime

def main():
    products_file = "output/raw_historical_products.json"
    
    # Check for legacy comment files from earlier tests
    comments = []
    if os.path.exists("output/latest/comments.json"):
        with open("output/latest/comments.json", "r") as f:
            comments.extend(json.load(f))
    if os.path.exists("output/raw/producthunt_comments.json"):
        with open("output/raw/producthunt_comments.json", "r") as f:
            comments.extend(json.load(f))
            
    products = []
    if os.path.exists(products_file):
        with open(products_file, "r") as f:
            products = json.load(f)

    if not products:
        print("No products collected yet.")
        return

    # 1 & 2. Dates
    valid_dates = [p["launch_date"] for p in products if p.get("launch_date")]
    valid_dates.sort()
    earliest_date = valid_dates[0] if valid_dates else "N/A"
    latest_date = valid_dates[-1] if valid_dates else "N/A"

    # 3 & 4. Totals
    total_products = len(products)
    total_comments = len(comments)

    # 5. Top 20 by votes
    sorted_by_votes = sorted(products, key=lambda x: x.get("votes", 0), reverse=True)
    top_20_votes = sorted_by_votes[:20]

    # 6. Top 20 by comments
    sorted_by_comments = sorted(products, key=lambda x: x.get("comment_count", 0), reverse=True)
    top_20_comments = sorted_by_comments[:20]

    # 7. Top 20 Topics
    all_topics = []
    for p in products:
        all_topics.extend(p.get("topics", []))
    topic_counts = Counter(all_topics)
    top_20_topics = topic_counts.most_common(20)

    # 8. Vote distribution
    vote_dist = {"0": 0, "1-10": 0, "11-50": 0, "51-100": 0, "101-500": 0, "500+": 0}
    for p in products:
        v = p.get("votes", 0)
        if v == 0: vote_dist["0"] += 1
        elif v <= 10: vote_dist["1-10"] += 1
        elif v <= 50: vote_dist["11-50"] += 1
        elif v <= 100: vote_dist["51-100"] += 1
        elif v <= 500: vote_dist["101-500"] += 1
        else: vote_dist["500+"] += 1

    # 9. Comment distribution
    comment_dist = {"0": 0, "1-5": 0, "6-20": 0, "21-50": 0, "50+": 0}
    for p in products:
        c = p.get("comment_count", 0)
        if c == 0: comment_dist["0"] += 1
        elif c <= 5: comment_dist["1-5"] += 1
        elif c <= 20: comment_dist["6-20"] += 1
        elif c <= 50: comment_dist["21-50"] += 1
        else: comment_dist["50+"] += 1

    # 10. Date distribution (by month-year)
    date_dist_counter = Counter()
    for d in valid_dates:
        # e.g. "2024-01-01T08:00:00Z" -> "2024-01"
        month_str = d[:7] 
        date_dist_counter[month_str] += 1

    # Samples
    product_samples = products[:10]
    comment_samples = comments[:10] if comments else []

    # Write Report
    with open("DATA_VALIDATION_REPORT.md", "w") as f:
        f.write("# Product Hunt Data Validation Report\n\n")
        
        f.write("## Overview\n")
        f.write(f"- **Earliest product date:** {earliest_date}\n")
        f.write(f"- **Latest product date:** {latest_date}\n")
        f.write(f"- **Total products collected:** {total_products}\n")
        f.write(f"- **Total comments collected:** {total_comments}\n\n")
        
        f.write("## 1. Top 20 Products by Votes\n")
        for i, p in enumerate(top_20_votes, 1):
            f.write(f"{i}. **{p['product_name']}** ({p['votes']} votes) - *{p['tagline']}*\n")
            
        f.write("\n## 2. Top 20 Products by Comments\n")
        for i, p in enumerate(top_20_comments, 1):
            f.write(f"{i}. **{p['product_name']}** ({p['comment_count']} comments) - *{p['tagline']}*\n")
            
        f.write("\n## 3. Top 20 Tags/Topics\n")
        for i, (topic, count) in enumerate(top_20_topics, 1):
            f.write(f"{i}. {topic}: {count}\n")
            
        f.write("\n## 4. Distributions\n")
        f.write("### Vote Distribution\n")
        for k, v in vote_dist.items(): f.write(f"- {k}: {v}\n")
        f.write("### Comment Distribution\n")
        for k, v in comment_dist.items(): f.write(f"- {k}: {v}\n")
        f.write("### Date Distribution (Products per Month)\n")
        for k, v in sorted(date_dist_counter.items()): f.write(f"- {k}: {v}\n")
        
        f.write("\n## 5. Real Data Samples\n")
        f.write("### 10 Product Samples\n")
        f.write("```json\n")
        f.write(json.dumps(product_samples, indent=2))
        f.write("\n```\n")
        
        f.write("### 10 Comment Samples\n")
        f.write("```json\n")
        f.write(json.dumps(comment_samples, indent=2))
        f.write("\n```\n")

    print("DATA_VALIDATION_REPORT.md generated successfully.")

if __name__ == "__main__":
    main()
