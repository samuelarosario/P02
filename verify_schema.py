#!/usr/bin/env python3
"""
Database Schema Verification Utility
MANDATORY: Run this before any database operations
"""

import sqlite3
import os
import sys

def verify_database_schema(db_path=None):
    """
    Verify and display current database schema
    MANDATORY before any database operations
    """
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), 'DB', 'flight_schedules.db')
    
    try:
        print("🔍 DATABASE SCHEMA VERIFICATION")
        print("=" * 50)
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"❌ Database not found: {db_path}")
            return None
        
        # Connect and get schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(flights)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ No flights table found")
            conn.close()
            return None
        
        print("✅ Current flights table schema:")
        print("-" * 50)
        
        schema_dict = {}
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            print(f"{col_name:<25} {col_type:<15} {'NOT NULL' if not_null else ''}")
            schema_dict[col_name] = col_type
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM flights")
        row_count = cursor.fetchone()[0]
        
        print("-" * 50)
        print(f"📊 Total records: {row_count:,}")
        
        # Check for query_type column
        if 'query_type' in schema_dict:
            cursor.execute("SELECT query_type, COUNT(*) FROM flights GROUP BY query_type")
            query_types = cursor.fetchall()
            print("🔍 Query type distribution:")
            for qt, count in query_types:
                print(f"   {qt}: {count:,} records")
        else:
            print("⚠️  No query_type column found")
        
        conn.close()
        
        print("=" * 50)
        print("✅ Schema verification complete")
        
        return schema_dict
        
    except Exception as e:
        print(f"❌ Schema verification error: {e}")
        return None

def get_column_mapping():
    """
    Get mapping of common column names to actual schema
    """
    schema = verify_database_schema()
    if not schema:
        return None
    
    # Common mappings based on current schema
    mapping = {
        'departure_time': 'dep_scheduled_time',
        'arrival_time': 'arr_scheduled_time',
        'departure_airport': 'dep_iata_code',
        'arrival_airport': 'arr_iata_code',
        'aircraft_type': 'aircraft_model_text',
        'flight_number': 'flight_iata_number',
        'airline_code': 'airline_iata_code'
    }
    
    print("\n📋 COLUMN MAPPING GUIDE")
    print("=" * 50)
    print("Use these actual column names:")
    for common, actual in mapping.items():
        if actual in schema:
            print(f"{common:<20} → {actual}")
    
    return mapping

if __name__ == "__main__":
    print("🚨 MANDATORY DATABASE SCHEMA CHECK")
    print("Run this before ANY database operations!")
    print()
    
    schema = verify_database_schema()
    if schema:
        get_column_mapping()
        print("\n✅ Ready for database operations")
    else:
        print("\n❌ Database verification failed")
        sys.exit(1)
