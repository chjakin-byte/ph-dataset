import os
import json
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

def calculate_estimates(total_products, earliest_date_str, latest_date_str):
    if not total_products or not earliest_date_str or not latest_date_str:
        return "Insufficient data", "N/A", "N/A"
        
    try:
        e_date = datetime.fromisoformat(earliest_date_str.replace('Z', '+00:00'))
        l_date = datetime.fromisoformat(latest_date_str.replace('Z', '+00:00'))
        days_collected = (l_date - e_date).days
        if days_collected <= 0:
            days_collected = 1
            
        products_per_day = total_products / days_collected
        
        # Target: Jan 1 2024 to Present (~900 days approx)
        target_start = datetime(2024, 1, 1, tzinfo=e_date.tzinfo)
        total_target_days = (datetime.now(target_start.tzinfo) - target_start).days
        
        estimated_total_products = products_per_day * total_target_days
        remaining_days = total_target_days - days_collected
        
        # Assuming ~5000 products per 24h run as measured previously
        expected_days_to_finish = (estimated_total_products - total_products) / 5000.0
        
        size_per_product_bytes = os.path.getsize("output/raw_historical_products.json") / total_products
        estimated_size_mb = (estimated_total_products * size_per_product_bytes) / (1024 * 1024)
        
        return (
            f"~{int(estimated_total_products):,} products (based on {products_per_day:.1f} avg per day)",
            f"~{expected_days_to_finish:.1f} continuous running days",
            f"~{estimated_size_mb:.1f} MB (Raw JSON)"
        )
    except Exception as e:
        return str(e), "N/A", "N/A"

def extract_domain(url):
    if not url: return "No URL"
    try:
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else "Invalid URL"
    except:
        return "Invalid URL"

def main():
    file_path = "output/raw_historical_products.json"
    if not os.path.exists(file_path):
        print(f"{file_path} not found.")
        return
        
    with open(file_path, "r") as f:
        products = json.load(f)
        
    if not products:
        print("No products in file.")
        return
        
    total_products = len(products)
    
    # Duplicates & Completeness
    unique_ids = set()
    total_fields = 0
    missing_fields = 0
    
    for p in products:
        unique_ids.add(p.get("id"))
        for k, v in p.items():
            total_fields += 1
            if v is None or v == "" or (isinstance(v, list) and len(v) == 0):
                missing_fields += 1
                
    duplicate_pct = ((total_products - len(unique_ids)) / total_products) * 100
    completeness_pct = ((total_fields - missing_fields) / total_fields) * 100
    
    # Dates & Distributions
    valid_dates = [p["launch_date"] for p in products if p.get("launch_date")]
    valid_dates.sort()
    earliest_date = valid_dates[0] if valid_dates else "N/A"
    latest_date = valid_dates[-1] if valid_dates else "N/A"
    
    daily_counter = Counter()
    weekly_counter = Counter()
    domain_counter = Counter()
    topics_counter = Counter()
    makers_counter = Counter()
    
    for p in products:
        d_str = p.get("launch_date")
        if d_str:
            d_obj = datetime.fromisoformat(d_str.replace('Z', '+00:00'))
            daily_counter[d_obj.strftime("%Y-%m-%d")] += 1
            # ISO year and week
            y, w, _ = d_obj.isocalendar()
            weekly_counter[f"{y}-W{w:02d}"] += 1
            
        domain_counter[extract_domain(p.get("website"))] += 1
        
        for t in p.get("topics", []):
            topics_counter[t] += 1
            
        for m in p.get("makers", []):
            makers_counter[m] += 1
            
    # Sorting
    top_20_votes = sorted(products, key=lambda x: x.get("votes", 0), reverse=True)[:20]
    top_20_comments = sorted(products, key=lambda x: x.get("comment_count", 0), reverse=True)[:20]
    
    # Estimates
    est_coverage, est_completion, est_size = calculate_estimates(total_products, earliest_date, latest_date)

    # --- Write Dashboard ---
    with open("EXECUTIVE_DASHBOARD.md", "w") as f:
        f.write("# Product Hunt Executive Dashboard\n\n")
        f.write("## 1. High-Level Metrics\n")
        f.write(f"- **Total products collected:** {total_products:,}\n")
        f.write(f"- **Earliest product date:** {earliest_date}\n")
        f.write(f"- **Latest product date:** {latest_date}\n")
        f.write(f"- **Data Completeness:** {completeness_pct:.2f}%\n")
        f.write(f"- **Duplicate Rate:** {duplicate_pct:.2f}%\n\n")
        
        f.write("## 2. Estimates & Projections\n")
        f.write(f"- **Total historical coverage available:** {est_coverage}\n")
        f.write(f"- **Expected completion date:** {est_completion}\n")
        f.write(f"- **Expected final dataset size:** {est_size}\n\n")
        
        f.write("## 3. Top 20 Categories (Topics)\n")
        for i, (k, v) in enumerate(topics_counter.most_common(20), 1):
            f.write(f"{i}. {k}: {v}\n")
            
        f.write("\n## 4. Top 20 Makers\n")
        for i, (k, v) in enumerate(makers_counter.most_common(20), 1):
            f.write(f"{i}. {k}: {v}\n")
            
        f.write("\n## 5. Top Domains\n")
        for i, (k, v) in enumerate(domain_counter.most_common(20), 1):
            if k != "No URL":
                f.write(f"{i}. {k}: {v}\n")
                
        f.write("\n## 6. Daily Volume Distribution\n")
        for k, v in sorted(daily_counter.items()):
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## 7. Weekly Volume Distribution\n")
        for k, v in sorted(weekly_counter.items()):
            f.write(f"- {k}: {v}\n")
            
        f.write("\n## 8. Top 20 Products by Votes\n")
        for i, p in enumerate(top_20_votes, 1):
            f.write(f"{i}. **{p.get('product_name')}** ({p.get('votes')} votes) - {p.get('tagline')}\n")
            
        f.write("\n## 9. Top 20 Products by Comments\n")
        for i, p in enumerate(top_20_comments, 1):
            f.write(f"{i}. **{p.get('product_name')}** ({p.get('comment_count')} comments) - {p.get('tagline')}\n")

    # --- Write Sample Report ---
    with open("DATA_SAMPLE_REPORT.md", "w") as f:
        f.write("# Product Hunt Data Sample Report\n\n")
        f.write("| Launch Date | Name | Tagline | Votes | Comments | URL |\n")
        f.write("|-------------|------|---------|-------|----------|-----|\n")
        
        for p in products[:50]:
            name = str(p.get("product_name", "")).replace('|', '-')
            tagline = str(p.get("tagline", "")).replace('|', '-')
            f.write(f"| {p.get('launch_date')} | {name} | {tagline} | {p.get('votes')} | {p.get('comment_count')} | {p.get('website')} |\n")

    print(f"Generated EXECUTIVE_DASHBOARD.md and DATA_SAMPLE_REPORT.md for {total_products} products.")

if __name__ == "__main__":
    main()
