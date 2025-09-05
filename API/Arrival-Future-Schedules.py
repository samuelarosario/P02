"""
Arrival-Future-Schedules API Data Puller
A Python script for pulling future arrival schedule data from API endpoints
Dedicated to querying ARRIVAL flights at airports
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from aviation_edge_db import insert_api_flights

# Load environment variables
load_dotenv()

class ArrivalFutureSchedules:
    """
    A class to handle arrival future schedules API data pulling operations
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize the Arrival Future Schedules API Data Puller
        
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
            'User-Agent': 'ArrivalFutureSchedules/1.0'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        print(f"Arrival Future Schedules API initialized for: {self.base_url}")
        
    def get_arrival_schedules(self, endpoint: str, days_ahead: int = 8, params: Dict = None) -> Optional[Dict]:
        """
        Get arrival schedule data from an API endpoint
        
        Args:
            endpoint (str): API endpoint to call
            days_ahead (int): Number of days ahead to fetch (minimum 8)
            params (Dict): Additional parameters for the API call
            
        Returns:
            Dict: API response data or None if failed
        """
        if days_ahead < 8:
            print(f"⚠️  WARNING: days_ahead must be minimum 8 days. Got: {days_ahead}")
            days_ahead = 8
            
        # Calculate target date
        target_date = datetime.now() + timedelta(days=days_ahead)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Build parameters
        api_params = {
            'date': date_str,
            'type': 'arrival',  # Force arrival type
            'key': self.api_key
        }
        
        if params:
            api_params.update(params)
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        print(f"🔄 Making arrival API call to: {url}")
        print(f"📅 Target date: {date_str} (arrival flights)")
        print(f"📋 Parameters: {api_params}")
        
        # Rate limiting
        time.sleep(1.0 / self.requests_per_second)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=api_params,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                print(f"📡 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Successfully retrieved arrival data")
                    return data
                elif response.status_code == 404:
                    print("❌ No arrival data found (404)")
                    return None
                else:
                    print(f"⚠️  Unexpected status code: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        print(f"🔄 Retrying in {2 ** attempt} seconds...")
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    print(f"All retry attempts failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
    def get_schedules_by_date_range(self, endpoint: str, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Get arrival schedules for a specific date range
        
        Args:
            endpoint (str): API endpoint
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            Dict: Schedule data or None if failed
        """
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'status': 'scheduled',
            'type': 'arrival'  # Force arrival type
        }
        
        return self.get_arrival_schedules(endpoint, params=params)
        
    def save_schedules_to_file(self, data: Any, filename: str, format: str = 'json'):
        """
        Save arrival schedule data to file
        
        Args:
            data: Schedule data to save
            filename (str): Output filename
            format (str): Output format ('json', 'csv', 'xlsx')
        """
        output_dir = os.getenv('OUTPUT_DIRECTORY', 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        timestamped_filename = f"{name}_arrivals_{timestamp}{ext}"
        
        filepath = os.path.join(output_dir, timestamped_filename)
        
        try:
            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                if isinstance(data, dict) and 'schedules' in data:
                    df = pd.DataFrame(data['schedules'])
                else:
                    df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8')
                
            elif format.lower() == 'xlsx':
                if isinstance(data, dict) and 'schedules' in data:
                    df = pd.DataFrame(data['schedules'])
                else:
                    df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_excel(filepath, index=False, engine='openpyxl')
                
            print(f"✅ Arrival data saved to: {filepath}")
            
        except Exception as e:
            print(f"❌ Failed to save arrival data: {e}")
            
    def get_multiple_airports_arrivals(self, airports: List[str], endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """
        Get arrival data for multiple airports
        
        Args:
            airports (List[str]): List of airport IATA codes
            endpoint (str): API endpoint to call
            params (Dict): Additional parameters for the API call
            
        Returns:
            Dict: Dictionary with airport as key and response data as value
        """
        results = {}
        
        for airport in airports:
            print(f"🔄 Fetching arrival data for airport: {airport}")
            
            # Ensure arrival type and airport code
            airport_params = {'iataCode': airport, 'type': 'arrival'}
            if params:
                airport_params.update(params)
                
            data = self.get_arrival_schedules(endpoint, params=airport_params)
            results[airport] = data
            
            # Brief pause between airport queries
            time.sleep(1)
            
        return results

    def get_aviation_edge_flights(self, airport_code: str, flight_type: str, target_date: str) -> Optional[List[Dict]]:
        """
        Get flight data from Aviation Edge API with proper weekday extraction
        
        Args:
            airport_code (str): Airport IATA code (e.g., 'MNL', 'POM')
            flight_type (str): 'departure' or 'arrival'
            target_date (str): Target date in YYYY-MM-DD format (8+ days ahead)
            
        Returns:
            List[Dict]: Flight data with extracted weekday information
        """
        # Aviation Edge API endpoint
        base_url = "https://aviation-edge.com/v2/public/flightsFuture"
        
        # Get API key from environment
        api_key = os.getenv('AVIATION_EDGE_API_KEY', '58b694-b40ef9')
        
        # API parameters
        params = {
            'key': api_key,
            'iataCode': airport_code.upper(),
            'type': flight_type.lower(),
            'date': target_date
        }
        
        print(f"🔗 Aviation Edge API Call: {flight_type.upper()} flights for {airport_code} on {target_date}")
        print(f"   URL: {base_url}")
        print(f"   Params: iataCode={airport_code}, type={flight_type}, date={target_date}")
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   ✅ Success: {len(data)} flights returned")
                    
                    # Extract weekday from each flight and add it to the data
                    enhanced_flights = []
                    for flight in data:
                        # Get weekday from API response - it's directly in the flight object as a string
                        weekday_str = flight.get('weekday', '')
                        weekday_number = None
                        
                        # Convert string weekday to integer (API returns weekday as string)
                        if weekday_str and weekday_str.isdigit():
                            weekday_number = int(weekday_str)
                            # Validate weekday is in range 1-7
                            if 1 <= weekday_number <= 7:
                                # Add weekday number to flight data
                                enhanced_flight = flight.copy()
                                enhanced_flight['extracted_weekday'] = weekday_number
                                enhanced_flights.append(enhanced_flight)
                            else:
                                print(f"   ⚠️  Invalid weekday value: {weekday_number}")
                        else:
                            print(f"   ⚠️  No valid weekday data: '{weekday_str}'")
                    
                    print(f"   📊 Enhanced {len(enhanced_flights)} flights with weekday data")
                    return enhanced_flights
                else:
                    print(f"   ⚠️  Unexpected response format: {type(data)}")
                    print(f"   Response: {str(data)[:200]}")
                    return []
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return []

    def store_aviation_edge_flights(self, flights: List[Dict], airport_code: str, flight_type: str, target_date: str) -> int:
        """
        Store Aviation Edge flight data in database using standardized handler
        
        Args:
            flights (List[Dict]): Flight data from Aviation Edge API
            airport_code (str): Airport code
            flight_type (str): 'departure' or 'arrival'
            target_date (str): Target date used for the query
            
        Returns:
            int: Number of flights stored/updated
        """
        if not flights:
            print(f"No flights to store for {airport_code} {flight_type}")
            return 0
        
        # Use standardized database handler
        stored_count = insert_api_flights(
            flights_data=flights,
            query_type=flight_type.lower(),
            airport_code=airport_code.upper(),
            collection_date=target_date
        )
        
        print(f"✅ Stored {stored_count} flights using standardized database handler")
        return stored_count

def main():
    """
    Main function - Execute arrival collections based on parameter file
    """
    # Initialize the Arrival Future Schedules puller
    schedules = ArrivalFutureSchedules()
    
    print("🔄 Arrival Future Schedules API Data Collector")
    print("� Executing arrival data collection")
    print()
    
    # Read parameters from file
    param_file = os.path.join(os.path.dirname(__file__), 'Arrival-Future-Schedules-Param.txt')
    airports = []
    target_date = None
    
    try:
        with open(param_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('iataCode=') and not line.startswith('#'):
                    if not airports:  # Only take the first valid entry
                        airports_str = line.split('=')[1]
                        airports = [code.strip() for code in airports_str.split(',') if code.strip()]
                elif line.startswith('date=') and not line.startswith('#'):
                    if not target_date:  # Only take the first valid entry
                        target_date = line.split('=')[1].strip()
    except Exception as e:
        print(f"❌ Error reading parameter file: {e}")
        return
    
    if not airports or not target_date:
        print(f"❌ Missing parameters: airports={airports}, date={target_date}")
        return
    
    print(f"� Configuration:")
    print(f"   Airports: {', '.join(airports)}")
    print(f"   Date: {target_date}")
    print(f"   Type: arrival")
    print()
    
    # Execute collections
    total_stored = 0
    total_retrieved = 0
    
    for airport in airports:
        print(f"� Processing {airport} arrivals for {target_date}")
        
        try:
            # Get flights using the Aviation Edge method
            flights = schedules.get_aviation_edge_flights(airport, 'arrival', target_date)
            
            if flights:
                retrieved_count = len(flights)
                total_retrieved += retrieved_count
                
                print(f"   ✅ Retrieved: {retrieved_count} flights")
                
                # Store in database using standardized handler
                stored_count = insert_api_flights(
                    flights_data=flights,
                    query_type='arrival',
                    airport_code=airport,
                    collection_date=target_date
                )
                
                total_stored += stored_count
                print(f"   ✅ Stored: {stored_count} new flights")
                
                if stored_count == 0:
                    print(f"   ℹ️  All flights already exist (duplicates prevented)")
                
            else:
                print(f"   ❌ No data retrieved for {airport}")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error processing {airport}: {e}")
            continue
    
    print()
    print("📊 ARRIVAL COLLECTION SUMMARY")
    print("=" * 40)
    print(f"Airports processed: {', '.join(airports)}")
    print(f"Target date: {target_date}")
    print(f"Total flights retrieved: {total_retrieved}")
    print(f"Total new flights stored: {total_stored}")
    print(f"Duplicates prevented: {total_retrieved - total_stored}")
    
    print("\n✅ Arrival collection completed!")

if __name__ == "__main__":
    main()
    """
    Main function for arrival schedule data collection
    Executing POM arrival collection to find missing MNL→POM flights
    """
    # Initialize the Arrival Future Schedules puller
    schedules = ArrivalFutureSchedules()
    
    print("🔄 Arrival Future Schedules API Data Collector")
    print("📍 Executing POM arrival collection to find missing MNL→POM flights")
    print()
    
    # Configuration for POM arrival collection
    airports = ['POM']  # Port Moresby arrivals
    flight_types = ['arrival']  # Fixed to arrival for this script
    dates = ['2025-09-19', '2025-09-20', '2025-09-21']  # Multiple dates for better coverage
    
    print(f"� Target: Flights arriving AT {airports[0]}")
    print(f"📅 Dates: {', '.join(dates)}")
    print(f"🔍 Looking for MNL→POM and other routes to POM")
    print()
    
    total_flights = 0
    
    # Execute API calls for each date
    for date in dates:
        print(f"� Processing date: {date}")
        
        for airport in airports:
            for flight_type in flight_types:
                # Execute Aviation Edge API call
                flights = schedules.get_aviation_edge_flights(airport, flight_type, date)
                
                if flights:
                    # Store flights in database
                    stored = schedules.store_aviation_edge_flights(flights, airport, flight_type, date)
                    total_flights += stored
                    print(f"   ✅ {stored} flights stored for {airport} {flight_type}")
                else:
                    print(f"   ❌ No flights found for {airport} {flight_type}")
                
                # Small delay between API calls
                import time
                time.sleep(1)
        
        print()
    
    print(f"🎉 POM arrival collection completed!")
    print(f"📊 Total flights processed: {total_flights}")
    print(f"🔍 Check database for new MNL→POM flights discovered via arrival queries")
    print("📋 This complements the departure data we already have")

if __name__ == "__main__":
    main()
