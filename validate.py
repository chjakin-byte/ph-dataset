import os
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from app.collectors.producthunt import ProductHuntCollector
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def run_validation(days: int, fetch_comments: bool = False):
    load_dotenv()
    collector = ProductHuntCollector()
    
    end_date = datetime.now()
    start_date = end_date - relativedelta(days=days)
    
    logger.info(f"--- Validating {days} days ({start_date.date()} to {end_date.date()}) ---")
    
    start_time = time.time()
    
    # We use a very high max_products to ensure we hit the true limit or collect everything
    raw_data = collector.collect(start_date, end_date, max_products=100000, fetch_comments=fetch_comments)
    
    duration = time.time() - start_time
    
    products = raw_data.get("products", [])
    
    # Calculate Metrics
    total_products = len(products)
    
    if fetch_comments:
        total_comments = len(raw_data.get("comments", []))
    else:
        # Estimate comments from the metadata
        total_comments = sum(p.comment_count for p in products)
        
    total_makers = sum(len(p.makers) for p in products)
    total_topics = sum(len(p.topics) for p in products)
    
    # Completeness
    total_fields = 0
    missing_fields = 0
    for p in products:
        fields = p.model_dump()
        for k, v in fields.items():
            total_fields += 1
            if v is None or v == "" or (isinstance(v, list) and len(v) == 0):
                missing_fields += 1
                
    missing_pct = (missing_fields / total_fields) * 100 if total_fields > 0 else 0
    
    # Duplicates (by ID)
    unique_ids = set(p.id for p in products)
    duplicate_pct = ((total_products - len(unique_ids)) / total_products) * 100 if total_products > 0 else 0
    
    products_per_second = total_products / duration if duration > 0 else 0
    
    return {
        "days": days,
        "duration_sec": round(duration, 2),
        "products_collected": total_products,
        "comments_estimated": total_comments,
        "makers_collected": total_makers,
        "topics_collected": total_topics,
        "throughput_products_per_sec": round(products_per_second, 2),
        "missing_field_pct": round(missing_pct, 2),
        "duplicate_pct": round(duplicate_pct, 2)
    }

def main():
    intervals = [1, 7, 30, 90, 365]
    results = []
    
    for days in intervals:
        # We only fetch comments for the 1-day run to verify pipeline mechanics without timing out.
        # For 7, 30, 90, 365 we disable comment fetching to validate pure product/maker/topic scale.
        res = run_validation(days, fetch_comments=(days == 1))
        results.append(res)
        logger.info(f"Result for {days} days: {json.dumps(res, indent=2)}")
        
        # Save intermediate in case of crash
        with open("capacity_validation_raw.json", "w") as f:
            json.dump(results, f, indent=2)
            
if __name__ == "__main__":
    main()
