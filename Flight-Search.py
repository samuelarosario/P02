#!/usr/bin/env python3
"""
Flight Search System
Comprehensive flight search and analysis tool for Aviation Edge flight database
Focuses on actual routes (dep_iata_code → arr_iata_code) regardless of query type

Author: Aviation Edge P02 Project
Version: 1.0
Date: September 2025
"""

import sqlite3
import os
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import argparse

class FlightSearchSystem:
    """Comprehensive flight search system focusing on actual routes"""
    
    def __init__(self, db_path: str = None):
        """Initialize the flight search system"""
        if db_path is None:
            # Default to project database location
            project_root = os.path.dirname(__file__)
            db_path = os.path.join(project_root, 'DB', 'flight_schedules.db')
        
        self.db_path = db_path
        self._verify_database()
    
    def _verify_database(self):
        """Verify database exists and is accessible"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM flights")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Database connected: {count:,} flights available")
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    def search_route(self, origin: str = None, destination: str = None, 
                    airline: str = None, flight_number: str = None, 
                    limit: int = None) -> List[Dict]:
        """
        Search flights by actual route regardless of how data was collected
        
        Args:
            origin: Departure airport IATA code (e.g., 'MNL')
            destination: Arrival airport IATA code (e.g., 'POM')
            airline: Airline IATA code (e.g., 'PR')
            flight_number: Flight number (e.g., '215' or 'PR215')
            limit: Maximum number of results to return
            
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
        
        if limit:
            query += f" LIMIT {limit}"
        
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
            return {
                "route": f"{origin}→{destination}", 
                "flights": 0, 
                "airlines": [], 
                "summary": "No flights found"
            }
        
        # Consolidate data from multiple records of same flight
        unique_flights = {}
        
        for flight in flights:
            flight_key = f"{flight['airline_iata_code']}{flight['flight_iata_number']}"
            
            if flight_key not in unique_flights:
                unique_flights[flight_key] = {
                    'airline': flight['airline_iata_code'],
                    'flight_number': flight['flight_iata_number'],
                    'route': f"{flight['dep_iata_code']}→{flight['arr_iata_code']}",
                    'schedule': f"{flight['dep_scheduled_time']}→{flight['arr_scheduled_time']}",
                    'aircraft': flight['aircraft_model_text'],
                    'weekdays': set()
                }
            
            # Add weekdays from this record
            for day in flight['weekdays'].split(','):
                if day.strip():
                    unique_flights[flight_key]['weekdays'].add(int(day.strip()))
        
        # Analyze the route
        airlines = set()
        aircraft_types = set()
        
        for flight_key, flight_data in unique_flights.items():
            airlines.add(flight_data['airline'])
            if flight_data['aircraft']:
                aircraft_types.add(flight_data['aircraft'])
        
        return {
            "route": f"{origin}→{destination}",
            "flights": len(flights),
            "unique_flights": len(unique_flights),
            "airlines": sorted(airlines),
            "aircraft_types": sorted(aircraft_types),
            "flight_details": unique_flights
        }
    
    def search_flight_pair(self, flight1: str, flight2: str, airline: str = None) -> Dict:
        """Analyze a pair of flights (typically outbound/return)"""
        
        flight1_data = self.search_route(airline=airline, flight_number=flight1)
        flight2_data = self.search_route(airline=airline, flight_number=flight2)
        
        # Consolidate weekdays for each flight
        def consolidate_weekdays(flight_records):
            all_weekdays = set()
            route = None
            schedule = None
            aircraft = None
            
            for record in flight_records:
                if route is None:
                    route = f"{record['dep_iata_code']}→{record['arr_iata_code']}"
                    schedule = f"{record['dep_scheduled_time']}→{record['arr_scheduled_time']}"
                    aircraft = record['aircraft_model_text']
                
                for day in record['weekdays'].split(','):
                    if day.strip():
                        all_weekdays.add(int(day.strip()))
            
            return {
                'route': route,
                'schedule': schedule,
                'aircraft': aircraft,
                'weekdays': sorted(all_weekdays)
            }
        
        flight1_consolidated = consolidate_weekdays(flight1_data) if flight1_data else None
        flight2_consolidated = consolidate_weekdays(flight2_data) if flight2_data else None
        
        analysis = {
            "flight1": {
                "number": flight1,
                "records": len(flight1_data),
                "data": flight1_consolidated
            },
            "flight2": {
                "number": flight2,
                "records": len(flight2_data),
                "data": flight2_consolidated
            }
        }
        
        # Check relationship
        if flight1_consolidated and flight2_consolidated:
            route1_parts = flight1_consolidated['route'].split('→')
            route2_parts = flight2_consolidated['route'].split('→')
            
            # Check if routes are reverse of each other (round trip)
            if (route1_parts[0] == route2_parts[1] and 
                route1_parts[1] == route2_parts[0]):
                analysis["relationship"] = "round_trip"
                analysis["route_pair"] = f"{flight1_consolidated['route']} ↔ {flight2_consolidated['route']}"
                
                # Calculate turnaround time if applicable
                if route1_parts[1] == route2_parts[0]:  # Same intermediate airport
                    try:
                        arr_time = flight1_consolidated['schedule'].split('→')[1]
                        dep_time = flight2_consolidated['schedule'].split('→')[0]
                        
                        arr_hour, arr_min = map(int, arr_time.split(':'))
                        dep_hour, dep_min = map(int, dep_time.split(':'))
                        
                        arr_minutes = arr_hour * 60 + arr_min
                        dep_minutes = dep_hour * 60 + dep_min
                        
                        if dep_minutes < arr_minutes:
                            dep_minutes += 24 * 60
                        
                        turnaround = dep_minutes - arr_minutes
                        turnaround_hours = turnaround // 60
                        turnaround_mins = turnaround % 60
                        
                        analysis["turnaround_time"] = f"{turnaround_hours}h {turnaround_mins}m"
                    except:
                        analysis["turnaround_time"] = "Unable to calculate"
            else:
                analysis["relationship"] = "different_routes"
        else:
            analysis["relationship"] = "insufficient_data"
        
        return analysis
    
    def display_flight_table(self, flights: List[Dict], title: str = "Flight Search Results"):
        """Display flights in clean table format"""
        if not flights:
            print(f"\n{title}")
            print("=" * len(title))
            print("No flights found matching criteria")
            return
        
        # Consolidate flights with same flight number
        consolidated = {}
        
        for flight in flights:
            flight_key = f"{flight['airline_iata_code']}{flight['flight_iata_number']}"
            
            if flight_key not in consolidated:
                consolidated[flight_key] = {
                    'airline': flight['airline_iata_code'],
                    'flight_number': flight['flight_iata_number'],
                    'route': f"{flight['dep_iata_code']}→{flight['arr_iata_code']}",
                    'dep_time': flight['dep_scheduled_time'],
                    'arr_time': flight['arr_scheduled_time'],
                    'aircraft': flight['aircraft_model_text'] or 'N/A',
                    'weekdays': set(),
                    'terminals': f"{flight['dep_terminal'] or '?'}→{flight['arr_terminal'] or '?'}"
                }
            
            # Add weekdays
            for day in flight['weekdays'].split(','):
                if day.strip():
                    consolidated[flight_key]['weekdays'].add(int(day.strip()))
        
        print(f"\n{title}")
        print("=" * len(title))
        
        # Display main table
        print("┌─────────┬─────────┬───────┬───────┬─────────┬──────────┬─────────────┐")
        print("│ Flight  │  Route  │ Depart│ Arrive│Duration │Operating │   Aircraft  │")
        print("│ Number  │         │ Time  │ Time  │         │   Days   │             │")
        print("├─────────┼─────────┼───────┼───────┼─────────┼──────────┼─────────────┤")
        
        day_names = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
        
        for flight_key in sorted(consolidated.keys()):
            flight = consolidated[flight_key]
            
            # Calculate duration
            try:
                dep_hour, dep_min = map(int, flight['dep_time'].split(':'))
                arr_hour, arr_min = map(int, flight['arr_time'].split(':'))
                
                dep_minutes = dep_hour * 60 + dep_min
                arr_minutes = arr_hour * 60 + arr_min
                
                if arr_minutes < dep_minutes:
                    arr_minutes += 24 * 60
                
                duration_minutes = arr_minutes - dep_minutes
                duration_hours = duration_minutes // 60
                duration_mins = duration_minutes % 60
                duration_str = f"{duration_hours}h{duration_mins:02d}m"
            except:
                duration_str = "N/A"
            
            # Format operating days
            sorted_weekdays = sorted(flight['weekdays'])
            operating_days = [day_names[day] for day in sorted_weekdays]
            days_str = ','.join(operating_days)
            
            # Format aircraft (shorten if needed)
            aircraft = flight['aircraft'].replace('AIRBUS ', 'A').replace('BOEING ', 'B')
            aircraft = aircraft.replace('A321-271N', 'A321neo').replace('737-81M', '737-800')
            if len(aircraft) > 11:
                aircraft = aircraft[:11]
            
            flight_display = f"{flight['airline']}{flight['flight_number'].replace(flight['airline'], '')}"
            
            print(f"│ {flight_display:<7} │{flight['route']:^9}│ {flight['dep_time']} │ {flight['arr_time']} │ {duration_str:<7} │{days_str:^10}│ {aircraft:<11} │")
        
        print("└─────────┴─────────┴───────┴───────┴─────────┴──────────┴─────────────┘")
        
        print(f"\nTotal: {len(consolidated)} unique flights ({len(flights)} database records)")
    
    def get_airline_summary(self, airline: str) -> Dict:
        """Get summary of all flights for a specific airline"""
        flights = self.search_route(airline=airline)
        
        if not flights:
            return {"airline": airline, "flights": 0, "routes": 0}
        
        # Analyze routes
        routes = set()
        destinations = set()
        origins = set()
        aircraft_types = set()
        
        for flight in flights:
            routes.add(f"{flight['dep_iata_code']}→{flight['arr_iata_code']}")
            destinations.add(flight['arr_iata_code'])
            origins.add(flight['dep_iata_code'])
            if flight['aircraft_model_text']:
                aircraft_types.add(flight['aircraft_model_text'])
        
        return {
            "airline": airline,
            "total_flights": len(flights),
            "unique_routes": len(routes),
            "destinations": len(destinations),
            "origins": len(origins),
            "aircraft_types": len(aircraft_types),
            "routes_list": sorted(routes)[:20]  # Top 20 routes
        }

def main():
    """Command line interface for flight search system"""
    parser = argparse.ArgumentParser(description='Aviation Edge Flight Search System')
    parser.add_argument('--origin', '-o', help='Origin airport IATA code (e.g., MNL)')
    parser.add_argument('--destination', '-d', help='Destination airport IATA code (e.g., POM)')
    parser.add_argument('--airline', '-a', help='Airline IATA code (e.g., PR)')
    parser.add_argument('--flight', '-f', help='Flight number (e.g., 215 or PR215)')
    parser.add_argument('--route-summary', '-r', action='store_true', 
                       help='Show route summary (requires origin and destination)')
    parser.add_argument('--flight-pair', '-p', nargs=2, metavar=('FLIGHT1', 'FLIGHT2'),
                       help='Analyze flight pair (e.g., 215 216)')
    parser.add_argument('--airline-summary', '-s', help='Show airline summary')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of results')
    
    args = parser.parse_args()
    
    try:
        searcher = FlightSearchSystem()
        
        if args.route_summary:
            if not args.origin or not args.destination:
                print("Error: Route summary requires both --origin and --destination")
                return
            
            summary = searcher.get_route_summary(args.origin, args.destination)
            print(f"\nRoute Summary: {summary['route']}")
            print(f"Unique flights: {summary['unique_flights']}")
            print(f"Airlines: {', '.join(summary['airlines'])}")
            print(f"Aircraft types: {', '.join(summary['aircraft_types'])}")
            
        elif args.flight_pair:
            airline = args.airline or input("Enter airline code (e.g., PR): ").strip()
            analysis = searcher.search_flight_pair(args.flight_pair[0], args.flight_pair[1], airline)
            
            print(f"\nFlight Pair Analysis: {args.flight_pair[0]} & {args.flight_pair[1]}")
            print(f"Relationship: {analysis['relationship']}")
            
            if analysis['flight1']['data']:
                f1 = analysis['flight1']['data']
                print(f"{args.flight_pair[0]}: {f1['route']} - {f1['schedule']} - Weekdays: {f1['weekdays']}")
            
            if analysis['flight2']['data']:
                f2 = analysis['flight2']['data']
                print(f"{args.flight_pair[1]}: {f2['route']} - {f2['schedule']} - Weekdays: {f2['weekdays']}")
            
            if 'turnaround_time' in analysis:
                print(f"Turnaround time: {analysis['turnaround_time']}")
                
        elif args.airline_summary:
            summary = searcher.get_airline_summary(args.airline_summary)
            print(f"\nAirline Summary: {summary['airline']}")
            print(f"Total flights: {summary['total_flights']}")
            print(f"Unique routes: {summary['unique_routes']}")
            print(f"Destinations served: {summary['destinations']}")
            print(f"Aircraft types: {summary['aircraft_types']}")
            print(f"Top routes: {', '.join(summary['routes_list'][:10])}")
            
        else:
            # Regular search
            flights = searcher.search_route(
                origin=args.origin,
                destination=args.destination,
                airline=args.airline,
                flight_number=args.flight,
                limit=args.limit
            )
            
            title = "Flight Search Results"
            if args.origin and args.destination:
                title = f"Flights: {args.origin} → {args.destination}"
            elif args.airline:
                title = f"{args.airline} Flights"
            
            searcher.display_flight_table(flights, title)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
