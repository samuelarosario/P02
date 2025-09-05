#!/usr/bin/env python3
"""
Enhanced Flight Database Query Functions
Route-based flight searching that considers actual flight routes regardless of query type
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple

class FlightRouteSearcher:
    """Enhanced flight search focusing on actual routes regardless of query type"""
    
    def __init__(self, db_path: str = None):
        """Initialize the flight route searcher"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DB', 'flight_schedules.db')
        self.db_path = db_path
    
    def search_route(self, origin: str = None, destination: str = None, 
                    airline: str = None, flight_number: str = None) -> List[Dict]:
        """
        Search flights by actual route regardless of how data was collected
        
        Args:
            origin: Departure airport IATA code
            destination: Arrival airport IATA code  
            airline: Airline IATA code
            flight_number: Flight number (with or without airline prefix)
            
        Returns:
            List of flight dictionaries with complete route information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic query
        conditions = []
        params = []
        
        if origin:
            conditions.append("dep_iata_code = ?")
            params.append(origin.upper())
        
        if destination:
            conditions.append("arr_iata_code = ?") 
            params.append(destination.upper())
        
        if airline:
            conditions.append("airline_iata_code = ?")
            params.append(airline.upper())
        
        if flight_number:
            # Handle various flight number formats
            flight_clean = flight_number.upper()
            if airline and not flight_clean.startswith(airline.upper()):
                flight_clean = f"{airline.upper()}{flight_clean}"
            conditions.append("flight_iata_number = ?")
            params.append(flight_clean)
        
        base_query = """
        SELECT dep_iata_code, arr_iata_code, airline_iata_code, flight_iata_number,
               dep_scheduled_time, arr_scheduled_time, weekdays, query_type, airport_code,
               dep_terminal, arr_terminal, dep_gate, arr_gate,
               aircraft_model_code, aircraft_model_text, airline_name,
               created_at, updated_at, id
        FROM flights
        """
        
        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            query = base_query
        
        query += " ORDER BY airline_iata_code, flight_iata_number, dep_iata_code, arr_iata_code"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to dictionaries
        columns = ['dep_iata_code', 'arr_iata_code', 'airline_iata_code', 'flight_iata_number',
                  'dep_scheduled_time', 'arr_scheduled_time', 'weekdays', 'query_type', 'airport_code',
                  'dep_terminal', 'arr_terminal', 'dep_gate', 'arr_gate',
                  'aircraft_model_code', 'aircraft_model_text', 'airline_name',
                  'created_at', 'updated_at', 'id']
        
        flights = []
        for row in results:
            flight_dict = dict(zip(columns, row))
            flights.append(flight_dict)
        
        conn.close()
        return flights
    
    def get_route_summary(self, origin: str, destination: str) -> Dict:
        """Get comprehensive summary of a specific route"""
        flights = self.search_route(origin=origin, destination=destination)
        
        if not flights:
            return {"route": f"{origin}→{destination}", "flights": 0, "airlines": [], "summary": "No flights found"}
        
        # Analyze the route
        airlines = set()
        flight_numbers = set()
        aircraft_types = set()
        weekday_patterns = set()
        query_sources = set()
        
        for flight in flights:
            airlines.add(flight['airline_iata_code'])
            flight_numbers.add(flight['flight_iata_number'])
            if flight['aircraft_model_text']:
                aircraft_types.add(flight['aircraft_model_text'])
            weekday_patterns.add(flight['weekdays'])
            query_sources.add(f"{flight['query_type']} at {flight['airport_code']}")
        
        return {
            "route": f"{origin}→{destination}",
            "flights": len(flights),
            "unique_flights": len(flight_numbers),
            "airlines": sorted(airlines),
            "flight_numbers": sorted(flight_numbers),
            "aircraft_types": sorted(aircraft_types),
            "weekday_patterns": sorted(weekday_patterns),
            "data_sources": sorted(query_sources),
            "flight_details": flights
        }
    
    def analyze_flight_pair(self, flight_number1: str, flight_number2: str, airline: str = None) -> Dict:
        """Analyze a pair of flights (typically outbound/return)"""
        
        flight1_data = self.search_route(airline=airline, flight_number=flight_number1)
        flight2_data = self.search_route(airline=airline, flight_number=flight_number2)
        
        analysis = {
            "flight1": {
                "number": flight_number1,
                "records": len(flight1_data),
                "routes": list(set(f"{f['dep_iata_code']}→{f['arr_iata_code']}" for f in flight1_data)),
                "weekdays": list(set(f['weekdays'] for f in flight1_data)),
                "schedules": list(set(f"{f['dep_scheduled_time']}→{f['arr_scheduled_time']}" for f in flight1_data))
            },
            "flight2": {
                "number": flight_number2,
                "records": len(flight2_data),
                "routes": list(set(f"{f['dep_iata_code']}→{f['arr_iata_code']}" for f in flight2_data)),
                "weekdays": list(set(f['weekdays'] for f in flight2_data)),
                "schedules": list(set(f"{f['dep_scheduled_time']}→{f['arr_scheduled_time']}" for f in flight2_data))
            }
        }
        
        # Check if they form a round trip
        if (flight1_data and flight2_data and 
            len(analysis["flight1"]["routes"]) == 1 and len(analysis["flight2"]["routes"]) == 1):
            
            route1 = analysis["flight1"]["routes"][0]
            route2 = analysis["flight2"]["routes"][0]
            
            # Check if routes are reverse of each other
            if route1.split('→')[0] == route2.split('→')[1] and route1.split('→')[1] == route2.split('→')[0]:
                analysis["relationship"] = "round_trip"
                analysis["route_pair"] = f"{route1} ↔ {route2}"
            else:
                analysis["relationship"] = "different_routes"
        else:
            analysis["relationship"] = "unclear"
        
        return analysis

# Demonstration of the enhanced search capabilities
def demonstrate_enhanced_search():
    """Demonstrate the enhanced route-based search capabilities"""
    
    searcher = FlightRouteSearcher()
    
    print("🔍 ENHANCED ROUTE-BASED FLIGHT SEARCH")
    print("=" * 60)
    
    # 1. Route summary analysis
    print("\n📊 ROUTE SUMMARY: MNL → POM")
    print("-" * 40)
    mnl_pom_summary = searcher.get_route_summary("MNL", "POM")
    
    print(f"Route: {mnl_pom_summary['route']}")
    print(f"Total records: {mnl_pom_summary['flights']}")
    print(f"Unique flights: {mnl_pom_summary['unique_flights']}")
    print(f"Airlines: {', '.join(mnl_pom_summary['airlines'])}")
    print(f"Flight numbers: {', '.join(mnl_pom_summary['flight_numbers'])}")
    print(f"Data sources: {', '.join(mnl_pom_summary['data_sources'])}")
    
    # 2. Flight pair analysis  
    print("\n🔄 FLIGHT PAIR ANALYSIS: PR215 & PR216")
    print("-" * 40)
    pr_analysis = searcher.analyze_flight_pair("215", "216", "PR")
    
    print(f"PR215: {pr_analysis['flight1']['records']} records")
    print(f"  Routes: {', '.join(pr_analysis['flight1']['routes'])}")
    print(f"  Weekdays: {', '.join(pr_analysis['flight1']['weekdays'])}")
    
    print(f"PR216: {pr_analysis['flight2']['records']} records")
    print(f"  Routes: {', '.join(pr_analysis['flight2']['routes'])}")
    print(f"  Weekdays: {', '.join(pr_analysis['flight2']['weekdays'])}")
    
    print(f"Relationship: {pr_analysis['relationship']}")
    if 'route_pair' in pr_analysis:
        print(f"Route pair: {pr_analysis['route_pair']}")
    
    print("\n✅ ENHANCED SEARCH CAPABILITIES READY!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_enhanced_search()
