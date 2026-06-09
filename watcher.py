import os
import json
import time
import subprocess

def get_product_count():
    try:
        if os.path.exists("output/collection_state.json"):
            with open("output/collection_state.json", "r") as f:
                state = json.load(f)
                return state.get("total_products_collected", 0)
    except:
        pass
    return 0

def generate_and_push(count):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Threshold reached ({count} products). Generating reports...")
    
    # Run all report generators
    subprocess.run(["python", "generate_reports.py"])
    subprocess.run(["python", "audit_data.py"])
    subprocess.run(["python", "generate_coverage_report.py"])
    subprocess.run(["python", "generate_delta_report.py"])
    
    # Git operations
    print("Committing and pushing reports...")
    reports = [
        "EXECUTIVE_DASHBOARD.md", 
        "DATA_SAMPLE_REPORT.md", 
        "DATA_AUDIT_REPORT.md", 
        "HISTORICAL_COVERAGE_REPORT.md",
        "DELTA_REPORT.md"
    ]
    subprocess.run(["git", "add"] + reports)
    commit_msg = f"chore: operational reports update at {count} products"
    subprocess.run(["git", "commit", "-m", commit_msg])
    
    # We use env variable to prevent prompts
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(["git", "push", "origin", "feat/producthunt-collector"], env=env)
    print("Push complete.\n")

def main():
    last_threshold = (get_product_count() // 1000) * 1000
    print(f"Watcher started. Current product count: {get_product_count()}. Last threshold: {last_threshold}")
    
    while True:
        time.sleep(60)
        current_count = get_product_count()
        current_threshold = (current_count // 1000) * 1000
        
        if current_threshold > last_threshold:
            generate_and_push(current_count)
            last_threshold = current_threshold

if __name__ == "__main__":
    main()
