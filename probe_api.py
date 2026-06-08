import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("PH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PH_CLIENT_SECRET")
API_URL = "https://api.producthunt.com/v2/api/graphql"

def get_token():
    auth_url = "https://api.producthunt.com/v2/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(auth_url, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def make_query(token, first_n):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    query = """
    query($first: Int!) {
      posts(first: $first) {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    """
    response = requests.post(API_URL, headers=headers, json={"query": query, "variables": {"first": first_n}})
    return response

def main():
    print("Authenticating...")
    token = get_token()
    print("Token obtained.\n")

    print("--- 1. Testing Maximum Page Size ---")
    for size in [20, 50, 100, 250]:
        resp = make_query(token, size)
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                print(f"Size {size}: GraphQL Error -> {data['errors'][0].get('message')}")
            else:
                edges = data.get("data", {}).get("posts", {}).get("edges", [])
                print(f"Size {size}: Success. Returned {len(edges)} items.")
        else:
            print(f"Size {size}: HTTP Error {resp.status_code}")
        time.sleep(2)

    print("\n--- 2. Checking Rate Limit Headers ---")
    resp = make_query(token, 10)
    print("Headers returned by API:")
    rate_headers = {k: v for k, v in resp.headers.items() if 'rate' in k.lower() or 'retry' in k.lower()}
    if rate_headers:
        for k, v in rate_headers.items():
            print(f"  {k}: {v}")
    else:
        print("  No explicit rate limit headers found in 200 OK responses.")

    print("\n--- 3. Triggering 429 Burst Limit ---")
    count = 0
    start_time = time.time()
    last_reset = None
    try:
        while True:
            resp = make_query(token, 10)
            count += 1
            if resp.status_code == 429:
                elapsed = time.time() - start_time
                print(f"\nHit 429 Too Many Requests after {count} requests in {elapsed:.2f} seconds.")
                print("Headers on 429 response:")
                for k, v in resp.headers.items():
                    if 'rate' in k.lower() or 'retry' in k.lower():
                        print(f"  {k}: {v}")
                
                # Check cooldown
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    print(f"Server requested cooldown via Retry-After: {retry_after} seconds.")
                else:
                    print("No Retry-After header. Waiting 60 seconds to see if it clears...")
                    time.sleep(60)
                    resp_test = make_query(token, 10)
                    print(f"Status after 60s: {resp_test.status_code}")
                break
            
            if count % 10 == 0:
                print(f"  ... made {count} requests so far ...")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
