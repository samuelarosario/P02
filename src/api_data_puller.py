"""
API Data Puller - Main Module
A Python project for pulling data from API endpoints
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger

# Load environment variables
load_dotenv()

class APIDataPuller:
    """
    A class to handle API data pulling operations
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize the API Data Puller
        
        Args:
            base_url (str): Base URL for the API
            api_key (str): API key for authentication
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', '')
        self.api_key = api_key or os.getenv('API_KEY', '')
        self.timeout = int(os.getenv('TIMEOUT_SECONDS', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.requests_per_second = int(os.getenv('REQUESTS_PER_SECOND', '10'))
        
        # Setup headers
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'APIDataPuller/1.0'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'logs/api_data.log')
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logger
        logger.add(log_file, rotation="10 MB", level=log_level)
        
    def get_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Get data from an API endpoint
        
        Args:
            endpoint (str): API endpoint (relative to base URL)
            params (Dict): Query parameters
            
        Returns:
            Dict: API response data or None if failed
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to {url} (attempt {attempt + 1})")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                # Rate limiting
                time.sleep(1 / self.requests_per_second)
                
                logger.success(f"Successfully retrieved data from {url}")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
    def get_multiple_endpoints(self, endpoints: List[str]) -> Dict[str, Any]:
        """
        Get data from multiple endpoints
        
        Args:
            endpoints (List[str]): List of endpoints to call
            
        Returns:
            Dict: Dictionary with endpoint as key and response data as value
        """
        results = {}
        
        for endpoint in endpoints:
            logger.info(f"Fetching data from endpoint: {endpoint}")
            data = self.get_data(endpoint)
            results[endpoint] = data
            
        return results
        
    def save_to_file(self, data: Any, filename: str, format: str = 'json'):
        """
        Save data to file
        
        Args:
            data: Data to save
            filename (str): Output filename
            format (str): Output format ('json', 'csv', 'xlsx')
        """
        output_dir = os.getenv('OUTPUT_DIRECTORY', 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                if isinstance(data, dict):
                    df = pd.DataFrame([data])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
                
            elif format.lower() == 'xlsx':
                if isinstance(data, dict):
                    df = pd.DataFrame([data])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data)
                df.to_excel(filepath, index=False)
                
            logger.success(f"Data saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save data to {filepath}: {e}")

def main():
    """
    Main function - example usage
    """
    # Initialize the API puller
    puller = APIDataPuller()
    
    # Example: Get data from a single endpoint
    # data = puller.get_data('users')
    # if data:
    #     puller.save_to_file(data, 'users.json')
    
    # Example: Get data from multiple endpoints
    # endpoints = ['users', 'posts', 'comments']
    # all_data = puller.get_multiple_endpoints(endpoints)
    # 
    # for endpoint, data in all_data.items():
    #     if data:
    #         puller.save_to_file(data, f'{endpoint}.json')
    
    logger.info("API Data Puller initialized. Configure your endpoints and run data collection.")

if __name__ == "__main__":
    main()
