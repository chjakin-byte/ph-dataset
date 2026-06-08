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

    # Production collection configuration
    # We pull from Jan 1 2024 to current date.
    # In a full run you would not limit max_products, but for safety in the engine runner 
    # we default to a high threshold.
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    
    logger.info(f"Starting Historical Product Hunt data collection from {start_date} to {end_date}.")
    
    # Run collector
    try:
        # We increase the max_products significantly for a data backfill run.
        raw_data = collector.collect(start_date, end_date, max_products=5000)
        products = raw_data.get("products", [])
        comments = raw_data.get("comments", [])
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return
        
    # Setup snapshot directories based on run time
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    snapshot_dir = f"output/snapshots/{date_str}/run_{time_str}"
    os.makedirs(f"{snapshot_dir}/raw", exist_ok=True)
    os.makedirs(f"{snapshot_dir}/cleaned", exist_ok=True)
    os.makedirs("output/latest", exist_ok=True)
    
    # 1. Deduplicate
    unique_products_dict = {}
    for p in products:
        # Use Product ID or slug as unique identifier
        if p.id not in unique_products_dict:
            unique_products_dict[p.id] = p
    cleaned_products = list(unique_products_dict.values())
    
    # 2. Snapshot and Export
    products_path = f"{snapshot_dir}/raw/products.json"
    with open(products_path, "w") as f:
        json.dump([p.model_dump(mode='json') for p in cleaned_products], f, indent=2)
        
    comments_path = f"{snapshot_dir}/raw/comments.json"
    with open(comments_path, "w") as f:
        json.dump([c.model_dump(mode='json') for c in comments], f, indent=2)
        
    # Also save to "latest"
    with open("output/latest/products.json", "w") as f:
        json.dump([p.model_dump(mode='json') for p in cleaned_products], f, indent=2)
    with open("output/latest/comments.json", "w") as f:
        json.dump([c.model_dump(mode='json') for c in comments], f, indent=2)
        
    logger.info(f"Saved {len(cleaned_products)} deduplicated products and {len(comments)} comments to {snapshot_dir}.")

    # Generate Data Inventory Report (formerly Research Readiness)
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
    
    report_path = f"{snapshot_dir}/data_inventory_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    # Also save to "latest"
    with open("output/latest/data_inventory_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Saved Data Inventory Report to {report_path}")
    for k, v in report.items():
        logger.info(f"  {k}: {v}")

if __name__ == "__main__":
    main()
