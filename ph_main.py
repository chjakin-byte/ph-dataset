import os
import json
import time
from dotenv import load_dotenv
from app.collectors.producthunt import ProductHuntCollector
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    # Load environment variables (PH_CLIENT_ID, PH_CLIENT_SECRET)
    load_dotenv()
    
    start_time = time.time()
    
    try:
        collector = ProductHuntCollector()
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
        return

    keywords = ["AI", "Productivity", "Marketing"]
    logger.info(f"Starting Product Hunt data collection for keywords: {keywords}")
    
    # Run collector
    try:
        raw_data = collector.collect(keywords, limit=20)
        products = raw_data.get("products", [])
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return
        
    # Save output
    os.makedirs("output/raw", exist_ok=True)
    output_path = "output/raw/producthunt_raw.json"
    
    with open(output_path, "w") as f:
        json.dump([p.model_dump(mode='json') for p in products], f, indent=2)
        
    logger.info(f"Saved {len(products)} products to {output_path}")

    # Generate Data Quality Report
    total_products = len(products)
    
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
    
    # Determine API Success (simplistic calculation based on expected vs received, assuming 20 limit per 3 keywords)
    expected_products = len(keywords) * 20
    api_success_rate = (total_products / expected_products) * 100 if expected_products > 0 else 0

    end_time = time.time()
    runtime = end_time - start_time
    
    quality_report = {
        "Total products collected": total_products,
        "API success rate (%)": min(100.0, api_success_rate), # Cap at 100 in case API returns more
        "Missing field rate (%)": missing_field_rate,
        "Duplicate count": duplicate_count,
        "Runtime duration (s)": runtime
    }
    
    report_path = "output/data_quality_report.json"
    with open(report_path, "w") as f:
        json.dump(quality_report, f, indent=2)
        
    logger.info(f"Saved Data Quality Report to {report_path}")
    for k, v in quality_report.items():
        logger.info(f"  {k}: {v}")

if __name__ == "__main__":
    main()
