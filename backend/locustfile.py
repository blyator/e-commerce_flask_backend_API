"""
Load Testing Suite for The Shop API
Tests authentication, product browsing, cart operations, and checkout flows
"""
from locust import HttpUser, task, between, events
import random
import json


class BaseUser(HttpUser):
    """Base user class with authentication"""
    abstract = True
    wait_time = between(1, 3)
    # Pointing to the live domain
    host = "https://serverdashboard.qzz.io"
    
    def on_start(self):
        """Login user at start of session"""
        self.token = None
        self.user_id = None
        self.login()
    
    def login(self):
        """Authenticate and get JWT token"""
        credentials = {
            "email": "user@demo.com",  # Use test user
            "password": "demo1234"
        }
        
        # Added /shop-api prefix
        with self.client.post("/shop-api/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                response.success()
            else:
                response.failure(f"Login failed: {response.text}")


class BrowsingUser(BaseUser):
    """User who browses products but doesn't buy"""
    weight = 3  # 60% of users are browsers
    
    @task(10)
    def view_products(self):
        """Browse all products"""
        self.client.get("/shop-api/products/", headers=self._get_auth_headers())
    
    @task(5)
    def view_products_with_filter(self):
        """Browse products with search/filter"""
        params = {
            "search": random.choice(["", "skin", "hair", "makeup"]),
            "category": random.choice(["all", "skincare", "makeup", "haircare"]),
            "sort": random.choice(["newest", "price-low", "price-high", "rating", "name"])
        }
        self.client.get("/shop-api/products/", params=params, headers=self._get_auth_headers())
    
    @task(3)
    def view_categories(self):
        """View product categories"""
        self.client.get("/shop-api/products/categories", headers=self._get_auth_headers())
    
    @task(2)
    def view_cart(self):
        """Check cart"""
        self.client.get("/shop-api/cart", headers=self._get_auth_headers())
    
    def _get_auth_headers(self):
        """Return authorization headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


class ShoppingUser(BaseUser):
    """User who adds items to cart and checks out"""
    weight = 2  # 40% of users are shoppers
    
    def on_start(self):
        super().on_start()
        self.cart_items = []
    
    @task(5)
    def view_products(self):
        """Browse products"""
        self.client.get("/shop-api/products/", headers=self._get_auth_headers())
    
    @task(3)
    def add_to_cart(self):
        """Add random product to cart"""
        response = self.client.get("/shop-api/products/", headers=self._get_auth_headers())
        if response.status_code == 200:
            products = response.json().get("products", [])
            if products:
                product = random.choice(products)
                product_id = product.get("id")
                
                cart_data = {
                    "product_id": product_id,
                    "quantity": random.randint(1, 3)
                }
                
                with self.client.post("/shop-api/cart", json=cart_data, 
                                    headers=self._get_auth_headers(), 
                                    catch_response=True) as resp:
                    if resp.status_code in [200, 201]:
                        resp.success()
                    else:
                        resp.failure(f"Add to cart failed: {resp.text}")
    
    @task(2)
    def view_cart(self):
        """View cart contents"""
        self.client.get("/shop-api/cart", headers=self._get_auth_headers())
    
    @task(1)
    def checkout(self):
        """Perform checkout (limited to avoid too many orders)"""
        cart_response = self.client.get("/shop-api/cart", headers=self._get_auth_headers())
        
        if cart_response.status_code == 200:
            cart = cart_response.json()
            if cart:  # Only checkout if cart has items
                shipping_info = {
                    "shipping_info": {
                        "firstName": "Test",
                        "lastName": "User",
                        "email": "test@example.com",
                        "city": "Nairobi",
                        "county": "Nairobi County",
                        "shipping": 150.00
                    }
                }
                
                with self.client.post("/shop-api/orders/checkout", json=shipping_info,
                                    headers=self._get_auth_headers(),
                                    catch_response=True) as resp:
                    if resp.status_code == 201:
                        resp.success()
                        # Clear cart after successful checkout
                        self.client.delete("/shop-api/cart/clear", headers=self._get_auth_headers())
                    else:
                        resp.failure(f"Checkout failed: {resp.text}")
    
    def _get_auth_headers(self):
        """Return authorization headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


class AnonymousUser(HttpUser):
    """Anonymous user browsing without login"""
    weight = 1
    wait_time = between(2, 5)
    # Pointing to the live domain
    host = "https://serverdashboard.qzz.io"
    
    @task(10)
    def view_public_products(self):
        """View products without authentication"""
        self.client.get("/shop-api/products/")
    
    @task(5)
    def view_public_categories(self):
        """View categories without authentication"""
        self.client.get("/shop-api/products/categories")


# Event hooks for test metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, 
               response, context, exception, **kwargs):
    """Log slow requests"""
    if response_time > 1000:  # Log requests over 1 second
        print(f"⚠️  Slow request: {request_type} {name} took {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary when test stops"""
    print("\n" + "="*50)
    print("LOAD TEST COMPLETED")
    print("="*50)
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
    print("="*50)