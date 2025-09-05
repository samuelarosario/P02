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
    
    def _calculate_arrival_weekday(self, flight: Dict, api_weekday: int) -> int:
        """
        Calculate the correct arrival weekday considering timezone differences and overnight flights.
        
        For arrival data, if the flight crosses to the next day due to flight duration
        and timezone differences, we need to adjust the weekday accordingly.
        
        The Aviation Edge API appears to return weekdays based on arrival times, but for
        overnight flights, this can be incorrect. We need to correct the logic:
        - If departure time > arrival time: flight crosses midnight (overnight)
        - For arrivals API: subtract 1 from weekday to get the correct departure weekday reference
        - Handle week rollover: Monday (1) - 1 = Sunday (7)
        
        Args:
            flight (Dict): Flight data containing departure and arrival times
            api_weekday (int): Original weekday from API (appears to be arrival-based)
            
        Returns:
            int: Corrected weekday for proper database storage (1-7, where 1=Monday, 7=Sunday)
        """
        try:
            # Get departure and arrival times
            departure = flight.get('departure', {})
            arrival = flight.get('arrival', {})
            
            dep_time = departure.get('scheduledTime', '')
            arr_time = arrival.get('scheduledTime', '')
            
            # If we don't have both times, return the original weekday
            if not dep_time or not arr_time:
                return api_weekday
            
            # Parse times (format: "HH:MM" or "HHMM")
            def parse_time(time_str):
                time_str = time_str.replace(':', '')
                if len(time_str) >= 4:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:4])
                    return hours * 60 + minutes  # Convert to minutes since midnight
                return None
            
            dep_minutes = parse_time(dep_time)
            arr_minutes = parse_time(arr_time)
            
            if dep_minutes is None or arr_minutes is None:
                return api_weekday
            
            # Check if departure time is later than arrival time (indicates overnight flight)
            # This handles overnight flights where departure is late (e.g., 21:25) and 
            # arrival is early next day (e.g., 05:10)
            if dep_minutes > arr_minutes:
                # Overnight flight detected - API weekday appears to be arrival-based
                # Subtract 1 to get the correct departure weekday reference
                corrected_weekday = api_weekday - 1
                # Handle week rollover (Monday=1 -> Sunday=7)
                if corrected_weekday < 1:
                    corrected_weekday = 7
                
                # Debug info for PX11 specifically
                flight_number = flight.get('flight', {}).get('iataNumber', '')
                if flight_number == 'PX11':
                    print(f"   🐛 DEBUG PX11: {dep_time} -> {arr_time}, API weekday {api_weekday} -> corrected {corrected_weekday} (overnight -1)")
                else:
                    print(f"   🌃 Overnight flight detected: {dep_time} -> {arr_time}, weekday {api_weekday} -> {corrected_weekday} (overnight -1)")
                return corrected_weekday
            else:
                # Same day arrival, keep original weekday
                flight_number = flight.get('flight', {}).get('iataNumber', '')
                if flight_number == 'PX11':
                    print(f"   🐛 DEBUG PX11: {dep_time} -> {arr_time}, API weekday {api_weekday} (no change - same day)")
                return api_weekday
                
        except Exception as e:
            print(f"   ⚠️  Error calculating arrival weekday: {e}")
            return api_weekday
        
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
    
    def dump_raw_data_to_log(self, data: Any, airport_code: str = None, target_date: str = None, flight_type: str = "arrival"):
        """
        Dump all raw API data to dump.log file for debugging and analysis
        
        Args:
            data: Raw API response data to dump
            airport_code (str): Airport code for context
            target_date (str): Target date for context
            flight_type (str): Flight type (arrival/departure)
        """
        try:
            # Create dump.log in the project root
            dump_file_path = os.path.join(os.path.dirname(__file__), '..', 'dump.log')
            
            # Prepare dump entry with timestamp and context
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dump_entry = {
                'timestamp': timestamp,
                'airport_code': airport_code,
                'target_date': target_date,
                'flight_type': flight_type,
                'data_type': type(data).__name__,
                'data_count': len(data) if isinstance(data, (list, dict)) else 'N/A',
                'raw_data': data
            }
            
            # Check if dump.log exists to determine if we need a header
            file_exists = os.path.exists(dump_file_path)
            
            # Append to dump.log file
            with open(dump_file_path, 'a', encoding='utf-8') as f:
                if not file_exists:
                    f.write("=== AVIATION EDGE API RAW DATA DUMP LOG ===\n")
                    f.write("This file contains all raw API responses for debugging\n\n")
                
                f.write(f"\n{'='*80}\n")
                f.write(f"DUMP ENTRY: {timestamp}\n")
                f.write(f"Airport: {airport_code} | Date: {target_date} | Type: {flight_type}\n")
                f.write(f"Data Type: {type(data).__name__} | Count: {len(data) if isinstance(data, (list, dict)) else 'N/A'}\n")
                f.write(f"{'='*80}\n")
                f.write(json.dumps(dump_entry, indent=2, ensure_ascii=False))
                f.write(f"\n{'='*80}\n\n")
            
            print(f"   📝 Raw data dumped to: dump.log")
            
        except Exception as e:
            print(f"   ⚠️  Failed to dump raw data to log: {e}")
            
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
                    
                    # Dump raw data to dump.log
                    self.dump_raw_data_to_log(data, airport_code, target_date, flight_type)
                    
                    # Save raw API data to file for analysis
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    raw_data_file = f"raw_arrival_data_{airport_code}_{target_date}_{timestamp}.json"
                    raw_data_path = os.path.join(os.path.dirname(__file__), '..', 'temp scripts', raw_data_file)
                    
                    # Create temp scripts directory if it doesn't exist
                    os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)
                    
                    # Save complete raw data with metadata
                    raw_data_output = {
                        'collection_timestamp': timestamp,
                        'airport_code': airport_code,
                        'target_date': target_date,
                        'flight_type': flight_type,
                        'api_url': base_url,
                        'api_params': params,
                        'total_flights': len(data),
                        'raw_flights_data': data
                    }
                    
                    with open(raw_data_path, 'w', encoding='utf-8') as f:
                        json.dump(raw_data_output, f, indent=2, ensure_ascii=False)
                    
                    print(f"   💾 Raw data saved to: {raw_data_file}")
                    
                    # Extract weekday from each flight and add it to the data
                    enhanced_flights = []
                    for flight in data:
                        # Get weekday from API response - it's directly in the flight object as a string
                        weekday_str = flight.get('weekday', '')
                        weekday_number = None
                        
                        # Convert string weekday to integer (API returns weekday as string)
                        if weekday_str and weekday_str.isdigit():
                            api_weekday = int(weekday_str)
                            # Validate weekday is in range 1-7
                            if 1 <= api_weekday <= 7:
                                # Apply weekday correction for arrival flights
                                corrected_weekday = self._calculate_arrival_weekday(flight, api_weekday)
                                
                                # Add weekday number to flight data
                                enhanced_flight = flight.copy()
                                enhanced_flight['extracted_weekday'] = corrected_weekday
                                enhanced_flight['api_original_weekday'] = api_weekday  # Keep original for reference
                                enhanced_flights.append(enhanced_flight)
                            else:
                                print(f"   ⚠️  Invalid weekday value: {api_weekday}")
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
                        if airports_str.strip() == 'PROMPT_USER':
                            # Prompt user for airport input
                            print("🛫 Airport Selection Required")
                            user_airport = input("Enter airport IATA code for ARRIVAL data collection (e.g., MNL, POM, HND): ").strip().upper()
                            if user_airport:
                                airports = [user_airport]
                                print(f"✅ Selected airport: {user_airport}")
                                print()
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

def weekly_collection():
    """
    Weekly collection wrapper that updates param file for 7 consecutive days
    and runs main() for each day starting from current date + 8 days
    """
    from datetime import datetime, timedelta
    
    print("🔄 Weekly Arrival Future Schedules Collection")
    print("� Collecting 7 consecutive days starting from current date + 8 days")
    print()
    
    # Calculate start date (current + 8 days for 8-day rule compliance)
    start_date = datetime.now() + timedelta(days=8)
    param_file = os.path.join(os.path.dirname(__file__), 'Arrival-Future-Schedules-Param.txt')
    
    # Get airport selection once for the entire week
    print("Airport Selection for Weekly Collection:")
    selected_airport = input("Enter airport IATA code for ARRIVAL data collection (e.g., MNL, POM, HND): ").strip().upper()
    print(f"Selected: {selected_airport}")
    print()
    total_days_processed = 0
    
    for day_offset in range(7):  # 7 days
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"� Day {day_offset + 1}/7: {date_str}")
        
        # Update parameter file with current date
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
            print(f"   🔄 Running arrival collection for {date_str}")
            main()
            
            total_days_processed += 1
            print(f"   ✅ Completed day {day_offset + 1}")
            print()
            
            # Small delay between days
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error processing {date_str}: {e}")
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
    
    print(f"🎉 Weekly collection completed!")
    print(f"📊 Processed {total_days_processed}/7 days")
    print(f"� Date range: {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    weekly_collection()
