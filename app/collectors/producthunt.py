import os
import time
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.collectors.base import BaseCollector
from app.models.producthunt import ProductHuntProduct, ProductHuntComment
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ProductHuntCollector(BaseCollector):
    def __init__(self):
        self.client_id = os.environ.get("PH_CLIENT_ID")
        self.client_secret = os.environ.get("PH_CLIENT_SECRET")
        self.token = None
        self.api_url = "https://api.producthunt.com/v2/api/graphql"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("PH_CLIENT_ID and PH_CLIENT_SECRET must be set in the environment.")

    @property
    def platform_name(self) -> str:
        return "ProductHunt"

    def _authenticate(self):
        auth_url = "https://api.producthunt.com/v2/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            logger.info("Successfully authenticated with Product Hunt API.")
        except Exception as e:
            logger.warning(f"Failed to authenticate with Product Hunt API: {e}. Using mock token for framework verification.")
            self.token = "MOCK_TOKEN"

    def _query_graphql(self, query: str, variables: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Executes a GraphQL query and handles 429 Rate Limits by sleeping.
        Returns a tuple of (data_dict, num_429_events_triggered).
        """
        if not self.token:
            self._authenticate()
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        rate_limit_events = 0
        
        while True:
            response = requests.post(self.api_url, headers=headers, json={"query": query, "variables": variables})
            
            if response.status_code == 429:
                rate_limit_events += 1
                reset_seconds = int(response.headers.get('x-rate-limit-reset', 900))
                # Add a 5 second buffer to the reset time to be safe
                sleep_time = reset_seconds + 5
                logger.warning(f"HTTP 429 Too Many Requests. Sleeping for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
                continue # Retry the request
                
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise ValueError(f"GraphQL returned errors: {data['errors']}")
            return data, rate_limit_events

    def collect_comments(self, slug: str) -> List[ProductHuntComment]:
        query = """
        query($slug: String!) {
          post(slug: $slug) {
            comments(first: 50) {
              edges {
                node {
                  body
                  createdAt
                  votesCount
                  user {
                    name
                  }
                }
              }
            }
          }
        }
        """
        variables = {"slug": slug}
        comments = []
        try:
            data, _ = self._query_graphql(query, variables)
            edges = data.get("data", {}).get("post", {}).get("comments", {}).get("edges", [])
            for edge in edges:
                node = edge.get("node", {})
                author = node.get("user", {}).get("name", "Unknown") if node.get("user") else "Unknown"
                
                c = ProductHuntComment(
                    product_slug=slug,
                    comment_text=node.get("body", ""),
                    comment_author=author,
                    created_date=node.get("createdAt", ""),
                    upvotes=node.get("votesCount", 0)
                )
                comments.append(c)
        except Exception as e:
            logger.error(f"Failed to fetch comments for {slug}: {e}")
            
        return comments

    def collect(self, start_date: datetime, end_date: datetime, max_products: int = 5000, fetch_comments: bool = True) -> Dict[str, Any]:
        """
        Collects historical data using month-by-month time slicing to avoid timeout/complexity limits.
        """
        logger.info(f"Starting historical collection from {start_date.isoformat()} to {end_date.isoformat()} (fetch_comments={fetch_comments})")
        
        all_products = []
        all_comments = []
        
        current_start = start_date
        
        total_429_events = 0

        # Loop through months
        while current_start < end_date and len(all_products) < max_products:
            # Modified to day-by-day slicing for safer continuous running
            current_end = min(current_start + relativedelta(days=1), end_date)
            
            start_str = current_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str = current_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            logger.info(f"Fetching slice: {start_str} to {end_str}")
            
            has_next = True
            cursor = None
            
            # Pagination loop within the month
            while has_next and len(all_products) < max_products:
                query = """
                query($postedAfter: DateTime!, $postedBefore: DateTime!, $after: String) {
                  posts(first: 20, postedAfter: $postedAfter, postedBefore: $postedBefore, after: $after) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    edges {
                      node {
                        id
                        slug
                        name
                        tagline
                        description
                        votesCount
                        commentsCount
                        createdAt
                        website
                        topics {
                          edges {
                            node {
                              name
                            }
                          }
                        }
                        makers {
                          name
                        }
                      }
                    }
                  }
                }
                """
                
                variables = {
                    "postedAfter": start_str,
                    "postedBefore": end_str,
                    "after": cursor
                }
                
                try:
                    data, rate_events = self._query_graphql(query, variables)
                    total_429_events += rate_events
                    posts_data = data.get("data", {}).get("posts", {})
                    edges = posts_data.get("edges", [])
                    page_info = posts_data.get("pageInfo", {})
                    
                    if not edges:
                        has_next = False
                        break
                        
                    for edge in edges:
                        if len(all_products) >= max_products:
                            break
                            
                        node = edge.get("node", {})
                        slug = node.get("slug", "")
                        
                        topic_names = [t.get("node", {}).get("name") for t in node.get("topics", {}).get("edges", [])]
                        maker_names = [m.get("name") for m in node.get("makers", [])]
                        
                        product = ProductHuntProduct(
                            id=node.get("id", ""),
                            slug=slug,
                            product_name=node.get("name", "Unknown"),
                            tagline=node.get("tagline", ""),
                            description=node.get("description", ""),
                            votes=node.get("votesCount", 0),
                            comment_count=node.get("commentsCount", 0),
                            topics=topic_names,
                            launch_date=node.get("createdAt"),
                            website=node.get("website", ""),
                            makers=maker_names
                        )
                        all_products.append(product)
                        
                        # Fetch comments for this product
                        if fetch_comments and product.comment_count > 0:
                            p_comments = self.collect_comments(slug)
                            all_comments.extend(p_comments)
                            
                    has_next = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor")
                    
                    # Be nice to the API
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error during time slice {start_str}: {e}")
                    has_next = False # Break this slice on error
                    
            current_start = current_end
            
        logger.info(f"Historical collection complete. Products: {len(all_products)}, Comments: {len(all_comments)}, 429s: {total_429_events}")
        return {
            "products": all_products,
            "comments": all_comments,
            "rate_limit_events": total_429_events,
            "last_cursor": cursor
        }
