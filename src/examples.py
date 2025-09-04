"""
Example script showing how to use the API Data Puller
"""

from api_data_puller import APIDataPuller
import json

def example_basic_usage():
    """
    Basic example of using the API Data Puller
    """
    # Initialize with your API details
    puller = APIDataPuller(
        base_url="https://jsonplaceholder.typicode.com",
        api_key=""  # Not needed for this example API
    )
    
    # Get data from a single endpoint
    users_data = puller.get_data("users")
    if users_data:
        print(f"Retrieved {len(users_data)} users")
        puller.save_to_file(users_data, "users.json")
    
    # Get data from multiple endpoints
    endpoints = ["users", "posts", "albums"]
    all_data = puller.get_multiple_endpoints(endpoints)
    
    for endpoint, data in all_data.items():
        if data:
            print(f"Retrieved data from {endpoint}: {len(data)} items")
            puller.save_to_file(data, f"{endpoint}.json")

def example_with_parameters():
    """
    Example using query parameters
    """
    puller = APIDataPuller(
        base_url="https://jsonplaceholder.typicode.com"
    )
    
    # Get posts for a specific user
    posts_data = puller.get_data("posts", params={"userId": 1})
    if posts_data:
        print(f"Retrieved {len(posts_data)} posts for user 1")
        puller.save_to_file(posts_data, "user_1_posts.json")

if __name__ == "__main__":
    print("Running API Data Puller examples...")
    
    # Uncomment the examples you want to run
    # example_basic_usage()
    # example_with_parameters()
    
    print("Examples completed. Check the 'data' folder for output files.")
    print("Make sure to:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Copy .env.example to .env and configure your API settings")
    print("3. Update the examples with your actual API endpoints")
