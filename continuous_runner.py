import os
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from app.collectors.producthunt import ProductHuntCollector
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
STATE_FILE = "output/collection_state.json"
DATA_FILE = "output/raw_historical_products.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "last_processed_date": None,
        "total_products_collected": 0,
        "total_comments_collected": 0,
        "total_429_events": 0
    }

def save_state(state):
    os.makedirs("output", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def append_data(products, comments):
    os.makedirs("output", exist_ok=True)
    existing_products = []
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            existing_products = json.load(f)
            
    # Quick ID deduplication
    existing_ids = set(p.get("id") for p in existing_products)
    
    for p in products:
        p_dict = p.model_dump(mode="json")
        if p_dict["id"] not in existing_ids:
            existing_products.append(p_dict)
            existing_ids.add(p_dict["id"])
            
    with open(DATA_FILE, "w") as f:
        json.dump(existing_products, f, indent=2)

def main():
    load_dotenv()
    collector = ProductHuntCollector()
    state = load_state()
    
    # Target: 90 days ago to today
    end_date_target = datetime.now()
    start_date_target = end_date_target - relativedelta(days=90)
    
    # Determine where to resume
    if state["last_processed_date"]:
        current_start = datetime.fromisoformat(state["last_processed_date"])
        logger.info(f"Resuming collection from {current_start}")
    else:
        current_start = start_date_target
        logger.info(f"Starting fresh collection from {current_start}")
        
    print("\n===========================================")
    print(" Product Hunt Continuous Collector Started")
    print("===========================================\n")

    # Run in 1-day batches
    while current_start < end_date_target:
        current_end = current_start + relativedelta(days=1)
        if current_end > end_date_target:
            current_end = end_date_target
            
        print(f"--- Batch: {current_start.date()} to {current_end.date()} ---")
        
        batch_start_time = time.time()
        
        # We explicitly turn off fetch_comments here to do Phase 1 (Product Backfill) 
        # as dictated by the API intelligence report. 
        # But if the prompt requires comment counts in the summary, we rely on commentsCount estimate
        # or we can fetch them. The prompt says "Keep product-first collection decoupled from comment enrichment."
        # so we set fetch_comments=False.
        
        try:
            raw_data = collector.collect(current_start, current_end, max_products=5000, fetch_comments=False)
        except Exception as e:
            print(f"Fatal error during collection batch: {e}")
            break
            
        duration = time.time() - batch_start_time
        
        products = raw_data.get("products", [])
        comments = raw_data.get("comments", [])
        rate_events = raw_data.get("rate_limit_events", 0)
        
        # Estimate comments from products if decoupled
        comments_estimated = sum(p.comment_count for p in products)
        
        append_data(products, comments)
        
        state["last_processed_date"] = current_end.isoformat()
        state["total_products_collected"] += len(products)
        state["total_comments_collected"] += len(comments) # 0 if decoupled
        state["total_429_events"] += rate_events
        save_state(state)
        
        throughput = len(products) / duration if duration > 0 else 0
        
        # Output required summary
        print("\n[ RUN SUMMARY ]")
        print(f"1. Products collected: {len(products)} (Batch) / {state['total_products_collected']} (Total)")
        print(f"2. Comments enriched: {len(comments)} (Estimated total comments available: {comments_estimated})")
        print(f"3. Number of 429 events: {rate_events}")
        print(f"4. Average throughput: {throughput:.2f} products/sec")
        print(f"5. Next resume point: {current_end.isoformat()}")
        print(f"6. Status: CONTINUING...\n")
        
        current_start = current_end

    print("===========================================")
    print(" Collection Target Reached or Stopped.")
    print("===========================================")

if __name__ == "__main__":
    main()
