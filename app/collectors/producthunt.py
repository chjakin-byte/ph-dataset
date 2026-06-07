import os
import requests
from typing import List, Dict, Any
from app.collectors.base import BaseCollector
from app.models.producthunt import ProductHuntProduct
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

    def collect(self, keywords: List[str], limit: int = 10) -> Dict[str, Any]:
        if not self.token:
            self._authenticate()
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        all_products = []
        
        for keyword in keywords:
            logger.info(f"Searching Product Hunt for: {keyword}")
            
            # Querying the global posts feed and filtering in memory since direct search
            # is limited in the v2 GraphQL API without enterprise features.
            query = """
            query($limit: Int!) {
              posts(first: $limit) {
                edges {
                  node {
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
            
            # Fetch more to allow for filtering, but keep limit low enough to pass complexity rules
            variables = {
                "limit": min(limit * 3, 50)
            }
            
            try:
                response = requests.post(self.api_url, headers=headers, json={"query": query, "variables": variables})
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                posts_edges = data.get("data", {}).get("posts", {}).get("edges", [])
            except Exception as e:
                logger.error(f"API request failed: {e}")
                continue

            if not posts_edges:
                logger.warning(f"No posts returned from API.")
                continue
                
            # Filter posts that match the keyword in name, tagline, description, or topics
            keyword_lower = keyword.lower()
            filtered_edges = []
            for edge in posts_edges:
                node = edge.get("node", {})
                name = (node.get("name") or "").lower()
                tagline = (node.get("tagline") or "").lower()
                desc = (node.get("description") or "").lower()
                topics = [t.get("node", {}).get("name", "").lower() for t in node.get("topics", {}).get("edges", [])]
                
                if keyword_lower in name or keyword_lower in tagline or keyword_lower in desc or any(keyword_lower in t for t in topics):
                    filtered_edges.append(edge)
            
            posts_edges = filtered_edges[:limit]
            
            if not posts_edges:
                logger.warning(f"No posts matched keyword '{keyword}' after filtering.")
                continue
            
            for post_edge in posts_edges:
                node = post_edge.get("node", {})
                
                topic_names = [t.get("node", {}).get("name") for t in node.get("topics", {}).get("edges", [])]
                maker_names = [m.get("name") for m in node.get("makers", [])]
                
                product = ProductHuntProduct(
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
            logger.info(f"Collected {len(posts_edges)} products for topic '{keyword}'.")
                
        return {"products": all_products}
