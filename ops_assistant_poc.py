import os
import json
import requests

def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"File {filepath} not found or could not be read: {e}"

def generate_gemini_summary(reports_content, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    You are an Operations Assistant monitoring a Product Hunt data collection pipeline.
    Analyze the following status reports and extract exactly these 6 data points into a short, structured summary:
    1. Current collector status
    2. Latest product count
    3. Latest date covered
    4. 429 / cooldown status
    5. Anomaly warning (if any, otherwise say "None detected")
    6. One-line next action
    
    Keep it extremely concise. Do not add markdown headers like "##", just use bullet points.
    
    --- REPORTS CONTENT ---
    {reports_content}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Failed to query Gemini API: {e}")
        # Fallback summary if Gemini fails so we still get operational awareness
        return "⚠️ Gemini API Error: Could not generate summary. Please check the raw reports manually."

def post_github_issue_comment(summary, token, repo, issue_number):
    if not issue_number or issue_number == "0":
        print("Issue number not set or is 0. Skipping comment post.")
        return
        
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {"body": f"🤖 **Gemini Ops Assistant (Hourly Update)**\n\n{summary}"}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully posted comment to Issue #{issue_number}")
    except Exception as e:
        print(f"Failed to post to GitHub Issue: {e}")

def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repo = os.environ.get("GITHUB_REPOSITORY")
    issue_number = os.environ.get("OPS_ISSUE_NUMBER", "0")

    if not gemini_api_key:
        print("Warning: GEMINI_API_KEY not found in environment.")
    
    reports = [
        "EXECUTIVE_DASHBOARD.md",
        "DATA_AUDIT_REPORT.md",
        "DELTA_REPORT.md",
        "HISTORICAL_COVERAGE_REPORT.md"
    ]
    
    concatenated_content = ""
    for r in reports:
        concatenated_content += f"\n\n--- {r} ---\n" + read_file(r)

    print("Generating summary via Gemini...")
    summary = generate_gemini_summary(concatenated_content, gemini_api_key)
    print("Summary generated:\n", summary)
    
    if github_token and github_repo:
        post_github_issue_comment(summary, github_token, github_repo, issue_number)
    else:
        print("GITHUB_TOKEN or GITHUB_REPOSITORY not set. Skipping GitHub post.")

if __name__ == "__main__":
    main()
