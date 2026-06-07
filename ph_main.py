import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from app.collectors.producthunt import ProductHuntCollector
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    load_dotenv()
    
    start_time = time.time()
    
    try:
        collector = ProductHuntCollector()
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
        return

    # For testing and Sandbox safety, we pull a very small slice first (e.g. Jan 1 to Jan 2 2024) 
    # to prove the mechanism without hitting rate limits or timeouts. 
    # The requirement is "Build historical dataset from 2024-01-01 until current date."
    # We will limit max_products to 20 for this test run.
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    
    logger.info(f"Starting Historical Product Hunt data collection.")
    
    # Run collector
    try:
        raw_data = collector.collect(start_date, end_date, max_products=20)
        products = raw_data.get("products", [])
        comments = raw_data.get("comments", [])
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return
        
    # Setup directories
    os.makedirs("output/raw", exist_ok=True)
    
    products_path = "output/raw/producthunt_products.json"
    with open(products_path, "w") as f:
        json.dump([p.model_dump(mode='json') for p in products], f, indent=2)
        
    comments_path = "output/raw/producthunt_comments.json"
    with open(comments_path, "w") as f:
        json.dump([c.model_dump(mode='json') for c in comments], f, indent=2)
        
    logger.info(f"Saved {len(products)} products and {len(comments)} comments.")

    # Generate Research Readiness Report
    total_products = len(products)
    total_comments = len(comments)
    
    earliest_date = None
    latest_date = None
    
    if products:
        dates = [p.launch_date for p in products if p.launch_date]
        if dates:
            dates.sort()
            earliest_date = dates[0]
            latest_date = dates[-1]
    
    # Calculate missing fields
    total_fields_checked = 0
    missing_fields_count = 0
    for p in products:
        fields = p.model_dump()
        for k, v in fields.items():
            total_fields_checked += 1
            if v is None or v == "" or (isinstance(v, list) and len(v) == 0):
                missing_fields_count += 1
                
    missing_field_rate = (missing_fields_count / total_fields_checked) * 100 if total_fields_checked > 0 else 0
    
    # Calculate duplicates (by product name)
    unique_names = set(p.product_name for p in products)
    duplicate_count = total_products - len(unique_names)
    duplicate_rate = (duplicate_count / total_products) * 100 if total_products > 0 else 0
    
    avg_comments = (total_comments / total_products) if total_products > 0 else 0

    report = {
        "Total products collected": total_products,
        "Total comments collected": total_comments,
        "Earliest date": earliest_date,
        "Latest date": latest_date,
        "Duplicate rate (%)": duplicate_rate,
        "Missing field rate (%)": missing_field_rate,
        "Average comments per product": avg_comments
    }
    
    report_path = "output/research_readiness_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Saved Research Readiness Report to {report_path}")
    for k, v in report.items():
        logger.info(f"  {k}: {v}")

if __name__ == "__main__":
    main()
