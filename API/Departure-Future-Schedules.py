"""
Future-Schedules API Data Puller
A Python script for pulling future schedule data from API endpoints
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

class FutureSchedules:
    """
    A class to handle future schedules API data pulling operations
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize the Future Schedules API Data Puller
        
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
            'User-Agent': 'FutureSchedules/1.0'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        print(f"Future Schedules API initialized for: {self.base_url}")
        
    def get_future_schedules(self, endpoint: str, days_ahead: int = 8, params: Dict = None) -> Optional[Dict]:
        """
        Get future schedule data from an API endpoint
        
        Args:
            endpoint (str): API endpoint for schedules
            days_ahead (int): Number of days ahead to fetch schedules
            params (Dict): Additional query parameters
            
        Returns:
            Dict: API response data or None if failed
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Calculate date range for future schedules
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Default parameters for future schedules
        schedule_params = {
            'start_date': start_date,
            'end_date': end_date,
            'status': 'scheduled'
        }
        
        # Merge with user-provided parameters
        if params:
            schedule_params.update(params)
        
        for attempt in range(self.max_retries):
            try:
                print(f"Fetching future schedules from {url} (attempt {attempt + 1})")
                print(f"Date range: {start_date} to {end_date}")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=schedule_params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                # Rate limiting
                time.sleep(1 / self.requests_per_second)
                
                print(f"Successfully retrieved future schedules from {url}")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    print(f"All retry attempts failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
    def get_schedules_by_date_range(self, endpoint: str, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Get schedules for a specific date range
        
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
            'status': 'scheduled'
        }
        
        return self.get_future_schedules(endpoint, params=params)
        
    def save_schedules_to_file(self, data: Any, filename: str, format: str = 'json'):
        """
        Save schedule data to file
        
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
        timestamped_filename = f"{name}_{timestamp}{ext}"
        
        filepath = os.path.join(output_dir, timestamped_filename)
        
        try:
            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                if isinstance(data, dict) and 'schedules' in data:
                    df = pd.DataFrame(data['schedules'])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
                df.to_csv(filepath, index=False)
                
            elif format.lower() == 'xlsx':
                if isinstance(data, dict) and 'schedules' in data:
                    df = pd.DataFrame(data['schedules'])
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
                df.to_excel(filepath, index=False)
                
            print(f"Schedule data saved to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Failed to save schedule data to {filepath}: {e}")
            return None

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
    Main function - Execute departure collections based on parameter file
    """
    # Initialize the Future Schedules puller
    schedules = FutureSchedules()
    
    print("🔄 Future Schedules API Data Collector")
    print("📊 Executing departure data collection")
    print()
    
    # Read parameters from file
    param_file = os.path.join(os.path.dirname(__file__), 'Departure-Future-Schedules-Param.txt')
    airports = []
    target_date = None
    
    try:
        with open(param_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('iataCode=') and not line.startswith('#'):
                    if not airports:  # Only take the first valid entry
                        airports_str = line.split('=')[1]
                        if airports_str.strip() == 'PROMPT_USER':
                            # Prompt user for airport input
                            print("🛫 Airport Selection Required")
                            user_airport = input("Enter airport IATA code for DEPARTURE data collection (e.g., MNL, POM, HND): ").strip().upper()
                            if user_airport:
                                airports = [user_airport]
                                print(f"✅ Selected airport: {user_airport}")
                            else:
                                print("❌ No airport provided, exiting")
                                return
                        else:
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
    
    print(f"📋 Configuration:")
    print(f"   Airports: {', '.join(airports)}")
    print(f"   Date: {target_date}")
    print(f"   Type: departure")
    print()
    
    # Execute collections
    total_stored = 0
    total_retrieved = 0
    
    for airport in airports:
        print(f"🔄 Processing {airport} departures for {target_date}")
        
        try:
            # Get flights using the Aviation Edge method
            flights = schedules.get_aviation_edge_flights(airport, 'departure', target_date)
            
            if flights:
                retrieved_count = len(flights)
                total_retrieved += retrieved_count
                
                print(f"   ✅ Retrieved: {retrieved_count} flights")
                
                # Store in database using standardized handler
                stored_count = insert_api_flights(
                    flights_data=flights,
                    query_type='departure',
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
    print("📊 DEPARTURE COLLECTION SUMMARY")
    print("=" * 40)
    print(f"Airports processed: {', '.join(airports)}")
    print(f"Target date: {target_date}")
    print(f"Total flights retrieved: {total_retrieved}")
    print(f"Total new flights stored: {total_stored}")
    print(f"Duplicates prevented: {total_retrieved - total_stored}")
    
    print("\n✅ Departure collection completed!")

def weekly_collection():
    """
    Weekly collection wrapper that updates param file for 7 consecutive days
    and runs main() for each day starting from current date + 8 days
    Prompts for airport selection once and uses it for all 7 days
    """
    from datetime import datetime, timedelta
    
    print("Weekly Departure Future Schedules Collection")
    print("Collecting 7 consecutive days starting from current date + 8 days")
    print()
    
    # Calculate start date (current + 8 days for 8-day rule compliance)
    start_date = datetime.now() + timedelta(days=8)
    param_file = os.path.join(os.path.dirname(__file__), 'Departure-Future-Schedules-Param.txt')
    
    # Get airport selection once for the entire week
    print("Airport Selection for Weekly Collection:")
    selected_airport = input("Enter airport IATA code for DEPARTURE data collection (e.g., MNL, POM, HND): ").strip().upper()
    print(f"Selected: {selected_airport}")
    print()
    
    total_days_processed = 0
    
    for day_offset in range(7):  # 7 days
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"Day {day_offset + 1}/7: {date_str}")
        
        # Update parameter file with current date and selected airport
        try:
            # Read current param file
            with open(param_file, 'r') as f:
                lines = f.readlines()
            
            # Update both date and iataCode lines
            updated_lines = []
            for line in lines:
                if line.strip().startswith('date=') and not line.strip().startswith('#'):
                    updated_lines.append(f'date={date_str}\n')
                elif line.strip().startswith('iataCode=') and not line.strip().startswith('#'):
                    updated_lines.append(f'iataCode={selected_airport}\n')
                else:
                    updated_lines.append(line)
            
            # Write updated param file
            with open(param_file, 'w') as f:
                f.writelines(updated_lines)
            
            print(f"   Updated parameter file: date={date_str}, airport={selected_airport}")
            
            # Run main collection for this date
            print(f"   Running departure collection for {date_str}")
            main()
            
            total_days_processed += 1
            print(f"   Completed day {day_offset + 1}")
            print()
            
            # Small delay between days
            time.sleep(2)
            
        except Exception as e:
            print(f"   Error processing {date_str}: {e}")
            continue
    
    # Restore PROMPT_USER to parameter file after weekly collection
    try:
        with open(param_file, 'r') as f:
            lines = f.readlines()
        
        updated_lines = []
        for line in lines:
            if line.strip().startswith('iataCode=') and not line.strip().startswith('#'):
                updated_lines.append(f'iataCode=PROMPT_USER\n')
            else:
                updated_lines.append(line)
        
        with open(param_file, 'w') as f:
            f.writelines(updated_lines)
        
        print("Parameter file restored to PROMPT_USER for future use")
    except Exception as e:
        print(f"Warning: Could not restore PROMPT_USER to parameter file: {e}")
    
    print(f"Weekly collection completed!")
    print(f"Processed {total_days_processed}/7 days")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    weekly_collection()
