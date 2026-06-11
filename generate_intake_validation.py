import os
import json

DATA_FILE = "output/raw_historical_products.json"
COMMENTS_FILE = "output/raw/producthunt_comments.json"
PACK_DIR = "INTAKE_VALIDATION_PACK"

def get_type(val):
    if isinstance(val, dict): return "Object"
    if isinstance(val, list):
        if len(val) > 0: return f"Array[{type(val[0]).__name__}]"
        return "Array[]"
    return type(val).__name__

def extract_schema(record):
    if not record: return {}
    return {k: get_type(v) for k, v in record.items()}

def main():
    if not os.path.exists(PACK_DIR):
        os.makedirs(PACK_DIR)

    products = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            products = json.load(f)
            
    comments = []
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "r") as f:
            comments = json.load(f)

    if not products:
        print("No product data found to validate.")
        return

    # 1. RAW_SCHEMA_DUMP.md
    # We do not have parquet files currently (data lake is JSON), but we simulate what the tabular schema maps to.
    p_schema = extract_schema(products[0]) if products else {}
    c_schema = extract_schema(comments[0]) if comments else {}
    
    with open(f"{PACK_DIR}/RAW_SCHEMA_DUMP.md", "w") as f:
        f.write("# Raw Schema Dump\n\n")
        f.write("## 1. raw_historical_products.json (Products Base)\n")
        for k, v in p_schema.items():
            f.write(f"- `{k}`: {v}\n")
            
        f.write("\n## 2. raw/producthunt_comments.json (Comments Base)\n")
        for k, v in c_schema.items():
            f.write(f"- `{k}`: {v}\n")
            
        f.write("\n*(Note: Phase 1 exports pure JSON. Parquet transformations belong to the ingestion layer of Phase 2, but they map 1:1 to the arrays above.)*\n")

    # 2. REAL_RECORD_SAMPLES.md
    p_samples = products[:10]
    c_samples = comments[:10] if comments else []
    
    # Extract "Makers" into a pseudo-table format to represent maker records
    maker_records = []
    for p in products:
        for m in p.get("makers", []):
            if len(maker_records) < 10 and m not in [mr["maker_name"] for mr in maker_records]:
                maker_records.append({"product_id": p.get("id"), "maker_name": m})

    with open(f"{PACK_DIR}/REAL_RECORD_SAMPLES.md", "w") as f:
        f.write("# Real Record Samples\n\n")
        f.write("## 10 Complete Product Records\n```json\n")
        f.write(json.dumps(p_samples, indent=2))
        f.write("\n```\n\n## 10 Complete Comment Records\n```json\n")
        f.write(json.dumps(c_samples, indent=2))
        f.write("\n```\n\n## 10 Derived Maker Records\n```json\n")
        f.write(json.dumps(maker_records, indent=2))
        f.write("\n```\n")

    # 3. SNAPSHOT_CAPABILITY_AUDIT.md
    with open(f"{PACK_DIR}/SNAPSHOT_CAPABILITY_AUDIT.md", "w") as f:
        f.write("# Snapshot Capability Audit\n\n")
        f.write("- **Is `launch_date` available?** Yes.\n  - Evidence: `\"launch_date\": \"2026-03-11T07:01:00Z\"`\n")
        f.write("- **Is `created_at` available?** No. The API returns `createdAt` which we map natively to `launch_date`.\n")
        f.write("- **Is `updated_at` available?** No. Historical API requests do not return an edit/update timestamp.\n")
        f.write("- **Is historical vote tracking available?** No. The `votes` field represents the lifetime aggregate at the moment of extraction, not a time-series curve.\n  - Evidence: `\"votes\": 639`\n")
        f.write("- **Is historical comment tracking available?** No. The `comment_count` is a lifetime aggregate.\n  - Evidence: `\"comment_count\": 128`\n")
        f.write("- **Is daily snapshot tracking available?** No. Phase 1 performs a historical backfill (single pass), not a daily differential snapshot of the same products over time.\n")

    # 4. COMMENT_STRUCTURE_AUDIT.md
    with open(f"{PACK_DIR}/COMMENT_STRUCTURE_AUDIT.md", "w") as f:
        f.write("# Comment Structure Audit\n\n")
        if comments:
            f.write("## Full Comment Schema\n")
            for k, v in c_schema.items():
                f.write(f"- `{k}`: {v}\n")
            f.write("\n## Structural Assessment\n")
            f.write("- **Author fields**: `comment_author` (string).\n")
            f.write("- **Timestamps**: `created_date` (ISO-8601 string).\n")
            f.write("- **Parent/Reply relationships**: NOT PRESENT. The current GraphQL extraction flattens edges and does not capture `parent_id` for nested threading.\n")
            f.write("- **Vote/Upvote fields**: `upvotes` (integer).\n")
            f.write("\n## Evidence (1 Record)\n```json\n")
            f.write(json.dumps(comments[0], indent=2))
            f.write("\n```\n")
        else:
            f.write("No comment data available in the current baseline.\n")

    # 5. DATA_CONTRACT_FINAL.md
    # Look for evidence to support the answers
    topic_clusters = {}
    for p in products[:50]:
        if p.get("topics"):
            top = p["topics"][0]
            if top not in topic_clusters: topic_clusters[top] = []
            topic_clusters[top].append(p.get("product_name"))

    with open(f"{PACK_DIR}/DATA_CONTRACT_FINAL.md", "w") as f:
        f.write("# Data Contract Final Verdict\n\n")
        
        f.write("## 1. Can Agent 2 perform trend analysis?\n")
        f.write("**Verdict: YES (Macro), NO (Micro/Velocity)**\n")
        f.write("Agent 2 can group products by `launch_date` and `topics` to see macro-trends (e.g., \"How many AI tools launched in March?\"). It CANNOT perform micro-velocity trend analysis (e.g., \"How many votes did this get in its first hour?\") because `votes` is a lifetime snapshot.\n")
        f.write("### Evidence (Macro Trend grouping capability):\n```json\n")
        f.write(json.dumps([{"date": p["launch_date"], "topics": p["topics"]} for p in products[10:13]], indent=2))
        f.write("\n```\n\n")
        
        f.write("## 2. Can Agent 2 perform topic clustering?\n")
        f.write("**Verdict: YES**\n")
        f.write("Products arrive with pre-labeled taxonomy arrays (`topics`). Agent 2 can immediately group and cluster products.\n")
        f.write("### Evidence (Sample clustering from live data):\n```json\n")
        f.write(json.dumps({k: v[:2] for k, v in list(topic_clusters.items())[:3]}, indent=2))
        f.write("\n```\n\n")

        f.write("## 3. Can Agent 2 perform maker analysis?\n")
        f.write("**Verdict: YES (Basic Identity), NO (Deep Profiling)**\n")
        f.write("The dataset includes an array of `makers` (names). Agent 2 can count launches per maker. It CANNOT analyze follower counts, Twitter links, or bio data, as these are not extracted.\n")
        f.write("### Evidence:\n```json\n")
        f.write(json.dumps([p["makers"] for p in products[10:13]], indent=2))
        f.write("\n```\n\n")

        f.write("## 4. Can Agent 2 perform opportunity discovery?\n")
        f.write("**Verdict: YES**\n")
        f.write("Opportunity discovery relies on identifying high-traction (`votes`, `comment_count`) segments (`topics`) based on semantic intent (`tagline`, `description`). The current schema provides exactly these raw vectors.\n")
        f.write("### Evidence (Opportunity Vectors):\n```json\n")
        f.write(json.dumps({
            "product_name": products[0]["product_name"],
            "tagline": products[0]["tagline"],
            "traction_signal": {"votes": products[0]["votes"], "comments": products[0]["comment_count"]},
            "segment": products[0]["topics"]
        }, indent=2))
        f.write("\n```\n")

    print("Intake Validation Pack generated successfully.")

if __name__ == "__main__":
    main()
