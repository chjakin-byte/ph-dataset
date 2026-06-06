from playwright.sync_api import sync_playwright
import json

def test_kickstarter_playwright():
    keywords = ["AI", "Backpack", "Productivity"]
    
    with sync_playwright() as p:
        # Launch Chromium headless
        browser = p.chromium.launch(headless=True)
        # Emulate a standard desktop view and set User Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        for keyword in keywords:
            print(f"\\n--- Testing Keyword: {keyword} ---")
            page = context.new_page()
            url = f"https://www.kickstarter.com/discover/advanced?term={keyword}"
            
            try:
                # Go to the discover page
                print(f"Navigating to {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Check if we got hit by Cloudflare block page
                title = page.title()
                if "Just a moment" in title or "Cloudflare" in title:
                    print(f"FAILED: Blocked by Cloudflare. Title: {title}")
                    page.close()
                    continue
                
                # Try to extract the data-projects JSON payload from the DOM
                react_container = page.locator('#react-discover')
                if react_container.count() > 0:
                    data_projects = react_container.get_attribute('data-projects')
                    if data_projects:
                        projects = json.loads(data_projects)
                        print(f"SUCCESS: Extracted {len(projects)} projects from JSON payload.")
                        
                        # Print details for up to 10 projects
                        for i, proj in enumerate(projects[:10]):
                            name = proj.get('name', 'N/A')
                            pledged = proj.get('pledged', 0)
                            backers = proj.get('backers_count', 0)
                            category = proj.get('category', {}).get('name', 'N/A')
                            project_url = proj.get('urls', {}).get('web', {}).get('project', 'N/A')
                            
                            print(f"  {i+1}. {name} | Category: {category} | Backers: {backers} | Pledged: ${pledged}")
                    else:
                        print("FAILED: '#react-discover' found but 'data-projects' attribute is empty.")
                else:
                    print("FAILED: Could not find '#react-discover' in the DOM. Layout changed or blocked silently.")
                    
            except Exception as e:
                print(f"Error testing {keyword}: {str(e)}")
            finally:
                page.close()
                
        browser.close()

if __name__ == "__main__":
    test_kickstarter_playwright()