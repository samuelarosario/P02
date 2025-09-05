"""
Aviation Edge Database Handler
Standardized database operations for all API collections
Ensures compliance with uppercase formatting and schema requirements
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class AviationEdgeDB:
    """
    Standardized database handler for Aviation Edge flight data
    Ensures consistent data formatting and schema compliance
    """
    
    def __init__(self, db_path: str = "DB/flight_schedules.db"):
        """
        Initialize database handler
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        
    def connect(self) -> bool:
        """
        Establish database connection and verify schema
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Verify schema exists
            cursor.execute("PRAGMA table_info(flights)")
            schema = cursor.fetchall()
            
            if not schema:
                raise Exception("flights table does not exist")
            
            # Check current record count
            cursor.execute("SELECT COUNT(*) FROM flights")
            count = cursor.fetchone()[0]
            print(f"✅ Database connected: {count:,} flights available")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def insert_flight_batch(self, flights_data: List[Dict], query_type: str, 
                          airport_code: str, collection_date: str) -> int:
        """
        Insert batch of flights into database with standardized formatting
        
        Args:
            flights_data (List[Dict]): List of flight data from API
            query_type (str): 'departure' or 'arrival'
            airport_code (str): Airport IATA code being queried
            collection_date (str): Date of collection (YYYY-MM-DD)
            
        Returns:
            int: Number of flights successfully inserted
        """
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")
        
        cursor = self.conn.cursor()
        inserted_count = 0
        updated_count = 0
        
        for flight in flights_data:
            try:
                # Extract and standardize flight data (ALL UPPERCASE per requirements)
                flight_data = self._extract_flight_data(flight, query_type, airport_code, collection_date)
                
                # Check if flight already exists
                flight_id, existing_weekdays = self._check_flight_exists(cursor, flight_data)
                
                if flight_id:
                    # Flight exists - merge weekdays
                    new_weekday = flight_data['weekdays']
                    merged_weekdays = self._merge_weekdays(existing_weekdays, new_weekday)
                    
                    if merged_weekdays != existing_weekdays:
                        # Update with merged weekdays
                        self._update_flight_weekdays(cursor, flight_id, merged_weekdays)
                        updated_count += 1
                else:
                    # New flight - insert
                    self._insert_single_flight(cursor, flight_data)
                    inserted_count += 1
                
            except Exception as e:
                flight_id = flight.get('flight', {}).get('iataNumber', 'Unknown')
                print(f"⚠️ Error processing flight {flight_id}: {e}")
                continue
        
        # Commit all changes
        self.conn.commit()
        print(f"💾 Stored {inserted_count} new flights, updated {updated_count} flights in database")
        
        return inserted_count + updated_count
    
    def _extract_flight_data(self, flight: Dict, query_type: str, airport_code: str, collection_date: str) -> Dict:
        """
        Extract and standardize flight data from API response with codeshare support
        ALL TEXT FIELDS CONVERTED TO UPPERCASE per copilot instructions
        
        Args:
            flight (Dict): Flight data from API
            query_type (str): 'departure' or 'arrival'
            airport_code (str): Airport code being queried
            collection_date (str): Collection date (YYYY-MM-DD) - not used for weekday calculation
            
        Returns:
            Dict: Standardized flight data with codeshare information
        """
        # Extract nested data safely
        airline = flight.get('airline', {})
        departure = flight.get('departure', {})
        arrival = flight.get('arrival', {})
        aircraft = flight.get('aircraft', {})
        flight_info = flight.get('flight', {})
        
        # Extract weekday directly from API response
        weekdays = str(flight.get('weekday', ''))
        
        # Determine codeshare information
        codeshare_data = flight.get('codeshared')
        
        if codeshare_data:
            # This is a marketing flight (codeshare)
            is_codeshare = True
            operating_airline = codeshare_data.get('airline', {})
            operating_flight = codeshare_data.get('flight', {})
            
            operating_airline_iata = str(operating_airline.get('iataCode', '')).upper()
            operating_flight_number = str(operating_flight.get('iataNumber', '')).upper()
            marketing_airline_iata = str(airline.get('iataCode', '')).upper()
            marketing_flight_number = str(flight_info.get('iataNumber', '')).upper()
            
            # Group ID based on operating flight
            codeshare_group_id = operating_airline_iata + operating_flight_number
        else:
            # This is an operating flight
            is_codeshare = False
            operating_airline_iata = str(airline.get('iataCode', '')).upper()
            operating_flight_number = str(flight_info.get('iataNumber', '')).upper()
            marketing_airline_iata = operating_airline_iata  # Same as operating
            marketing_flight_number = operating_flight_number  # Same as operating
            
            # Group ID based on this flight
            codeshare_group_id = operating_airline_iata + operating_flight_number
        
        # Standardized flight data (ALL UPPERCASE per requirements)
        return {
            'dep_iata_code': str(departure.get('iataCode', '')).upper(),
            'arr_iata_code': str(arrival.get('iataCode', '')).upper(),
            'airline_iata_code': str(airline.get('iataCode', '')).upper(),
            'flight_iata_number': str(flight_info.get('iataNumber', '')).upper(),
            'dep_scheduled_time': str(departure.get('scheduledTime', '')).upper(),
            'arr_scheduled_time': str(arrival.get('scheduledTime', '')).upper(),
            'weekdays': weekdays,
            'query_type': query_type.lower(),  # Lowercase as per schema requirement
            'airport_code': airport_code.upper(),
            'dep_terminal': str(departure.get('terminal', '')).upper(),
            'arr_terminal': str(arrival.get('terminal', '')).upper(),
            'dep_gate': str(departure.get('gate', '')).upper(),
            'arr_gate': str(arrival.get('gate', '')).upper(),
            'aircraft_model_code': str(aircraft.get('modelCode', '')).upper(),
            'aircraft_model_text': str(aircraft.get('modelText', '')).upper(),
            'airline_name': str(airline.get('name', '')).upper(),
            'raw_data': json.dumps(flight),  # Store complete raw API response
            'is_codeshare': is_codeshare,
            'operating_airline_iata': operating_airline_iata,
            'operating_flight_number': operating_flight_number,
            'marketing_airline_iata': marketing_airline_iata,
            'marketing_flight_number': marketing_flight_number,
            'codeshare_group_id': codeshare_group_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def _check_flight_exists(self, cursor: sqlite3.Cursor, flight_data: Dict) -> tuple:
        """
        Check if flight already exists and return ID and current weekdays
        Now considers codeshare information to properly identify duplicates
        
        Args:
            cursor: Database cursor
            flight_data (Dict): Flight data to check
            
        Returns:
            tuple: (flight_id, current_weekdays) or (None, None) if not found
        """
        # For codeshare flights, we need to check based on marketing details
        # to avoid duplicating the same marketing flight
        cursor.execute("""
            SELECT id, weekdays FROM flights 
            WHERE marketing_airline_iata = ? 
            AND marketing_flight_number = ?
            AND dep_iata_code = ? 
            AND arr_iata_code = ? 
            AND dep_scheduled_time = ?
            AND query_type = ?
        """, (
            flight_data['marketing_airline_iata'],
            flight_data['marketing_flight_number'],
            flight_data['dep_iata_code'],
            flight_data['arr_iata_code'],
            flight_data['dep_scheduled_time'],
            flight_data['query_type']
        ))
        
        result = cursor.fetchone()
        if result:
            return result[0], result[1]  # flight_id, weekdays
        return None, None
    
    def _merge_weekdays(self, existing_weekdays: str, new_weekday: str) -> str:
        """
        Merge new weekday with existing weekdays
        
        Args:
            existing_weekdays (str): Existing weekdays (e.g., "1,2,3")
            new_weekday (str): New weekday to add (e.g., "6")
            
        Returns:
            str: Merged weekdays (e.g., "1,2,3,6")
        """
        if not existing_weekdays:
            return new_weekday
            
        existing_set = set(existing_weekdays.split(','))
        existing_set.add(new_weekday)
        return ','.join(sorted(existing_set, key=int))
    
    def _update_flight_weekdays(self, cursor: sqlite3.Cursor, flight_id: int, merged_weekdays: str):
        """
        Update flight record with merged weekdays
        
        Args:
            cursor: Database cursor
            flight_id (int): Flight record ID
            merged_weekdays (str): Merged weekdays string
        """
        cursor.execute("""
            UPDATE flights 
            SET weekdays = ?, updated_at = ?
            WHERE id = ?
        """, (merged_weekdays, datetime.now().isoformat(), flight_id))
    
    def _insert_single_flight(self, cursor: sqlite3.Cursor, flight_data: Dict):
        """
        Insert single flight record into database with codeshare support
        
        Args:
            cursor: Database cursor
            flight_data (Dict): Standardized flight data
        """
        cursor.execute("""
            INSERT INTO flights (
                dep_iata_code, arr_iata_code, airline_iata_code, flight_iata_number,
                dep_scheduled_time, arr_scheduled_time, weekdays, query_type, airport_code,
                dep_terminal, arr_terminal, dep_gate, arr_gate,
                aircraft_model_code, aircraft_model_text, airline_name, raw_data,
                is_codeshare, operating_airline_iata, operating_flight_number,
                marketing_airline_iata, marketing_flight_number, codeshare_group_id,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flight_data['dep_iata_code'],
            flight_data['arr_iata_code'],
            flight_data['airline_iata_code'],
            flight_data['flight_iata_number'],
            flight_data['dep_scheduled_time'],
            flight_data['arr_scheduled_time'],
            flight_data['weekdays'],
            flight_data['query_type'],
            flight_data['airport_code'],
            flight_data['dep_terminal'],
            flight_data['arr_terminal'],
            flight_data['dep_gate'],
            flight_data['arr_gate'],
            flight_data['aircraft_model_code'],
            flight_data['aircraft_model_text'],
            flight_data['airline_name'],
            flight_data['raw_data'],
            flight_data['is_codeshare'],
            flight_data['operating_airline_iata'],
            flight_data['operating_flight_number'],
            flight_data['marketing_airline_iata'],
            flight_data['marketing_flight_number'],
            flight_data['codeshare_group_id'],
            flight_data['created_at'],
            flight_data['updated_at']
        ))
    
    def get_flight_count(self) -> int:
        """
        Get total number of flights in database
        
        Returns:
            int: Total flight count
        """
        if not self.conn:
            raise Exception("Database not connected")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM flights")
        return cursor.fetchone()[0]
    
    def get_collection_summary(self, airport_code: str = None, 
                             query_type: str = None) -> Dict:
        """
        Get collection summary statistics
        
        Args:
            airport_code (str, optional): Filter by airport
            query_type (str, optional): Filter by query type
            
        Returns:
            Dict: Collection statistics
        """
        if not self.conn:
            raise Exception("Database not connected")
        
        cursor = self.conn.cursor()
        
        # Build query with optional filters
        conditions = []
        params = []
        
        if airport_code:
            conditions.append("airport_code = ?")
            params.append(airport_code.upper())
        
        if query_type:
            conditions.append("query_type = ?")
            params.append(query_type.lower())
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Get summary statistics
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_flights,
                COUNT(DISTINCT airport_code) as airports,
                COUNT(DISTINCT airline_iata_code) as airlines,
                MIN(created_at) as first_record,
                MAX(created_at) as latest_record
            FROM flights{where_clause}
        """, params)
        
        result = cursor.fetchone()
        
        return {
            'total_flights': result[0],
            'airports': result[1],
            'airlines': result[2],
            'first_record': result[3],
            'latest_record': result[4]
        }

# Convenience function for standard usage
def insert_api_flights(flights_data: List[Dict], query_type: str, 
                      airport_code: str, collection_date: str,
                      db_path: str = None) -> int:
    """
    Convenience function to insert flights using standardized handler
    
    Args:
        flights_data (List[Dict]): Flight data from API
        query_type (str): 'departure' or 'arrival' 
        airport_code (str): Airport IATA code
        collection_date (str): Collection date (YYYY-MM-DD)
        db_path (str): Database path (optional, will auto-detect if None)
        
    Returns:
        int: Number of flights inserted
    """
    # Auto-detect database path if not provided
    if db_path is None:
        import os
        # Get the directory where this module is located
        module_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(module_dir, "DB", "flight_schedules.db")
    
    db = AviationEdgeDB(db_path)
    
    if not db.connect():
        return 0
    
    try:
        inserted_count = db.insert_flight_batch(
            flights_data, query_type, airport_code, collection_date
        )
        return inserted_count
    finally:
        db.close()

if __name__ == "__main__":
    # Test the database handler
    db = AviationEdgeDB()
    if db.connect():
        summary = db.get_collection_summary()
        print(f"Database Summary: {summary}")
        db.close()
