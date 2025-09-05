# P02 Aviation Edge Flight Analysis Project

## Project Status: Production Ready ✅

**Last Updated**: September 2025  
**Version**: Permanent Implementation with Standardized Database Handler  
**Database Records**: 186,409+ total flights across 16 airports

## Quick Start

### ⚠️ MANDATORY: Use Standardized Database Handler
```python
# ALL API collections must use this standardized approach
from aviation_edge_db import insert_api_flights, AviationEdgeDB

# Simple insertion (recommended for most cases)
flights_stored = insert_api_flights(
    flights_data=api_response_data,
    query_type="departure",  # or "arrival"
    airport_code="SYD", 
    collection_date="2025-09-14"
)

# Advanced usage with custom operations
db = AviationEdgeDB()
if db.connect():
    db.insert_flight_batch(flights_data, query_type, airport_code, date)
    summary = db.get_collection_summary()
    db.close()
```

### Flight Search System
```bash
cd "C:\Users\MY PC\Aviation Edge\P02"
python Flight-Search.py --help
python Flight-Search.py --airline PR --flight 215
```

### API Data Collection
```bash
# Use standardized collection scripts
python "temp scripts/australia_airports_collection_v2.py"
python "temp scripts/example_standardized_collection.py"
```

## Architecture Overview

### 🔧 **Core Components**

#### 1. Standardized Database Handler
- **File**: `aviation_edge_db.py`
- **Purpose**: Mandatory database operations for all API collections
- **Features**: Uppercase formatting, duplicate prevention, schema validation
- **Status**: **MANDATORY** - All scripts must use this handler

#### 2. Flight Search System
- **File**: `Flight-Search.py`
- **Purpose**: Comprehensive flight search and route analysis
- **Features**: Command-line interface, route-based search, weekday consolidation, table output
- **Status**: Production ready with full functionality

#### 3. API Collection Framework
- **Template**: `temp scripts/example_standardized_collection.py`
- **Purpose**: Standardized approach for all future API collections
- **Features**: Rate limiting, error handling, automatic compliance
- **Status**: **Required template** for all new collections

#### 4. Database System
- **File**: `DB/flight_schedules.db`
- **Records**: 9,869 flights with query_type tracking
- **Coverage**: Complete PR route network (440 flights, 158 routes)
- **Status**: Production database with comprehensive data

### 📊 **Key Discoveries**

#### Aviation Edge API Behavior
- **Weekday Discrepancies**: Different operational patterns visible from departure vs arrival queries
- **Example**: PR215 shows weekdays 2,7 from departure queries vs 2,5,7 from arrival queries
- **Solution**: Dual collection methodology captures complete operational picture

#### Route Analysis Insights
- **MNL↔POM Route**: Served by Philippine Airlines (PR) and PNG Air (PX)
- **PR215/PR216**: Round-trip service with 1h 15m turnaround time
- **Operational Days**: Tuesday, Friday, Sunday (weekdays 2,5,7)

## Usage Examples

### Flight Search Commands
```bash
# Individual flight analysis
python Flight-Search.py --airline PR --flight 215

# Route summary
python Flight-Search.py --origin MNL --destination POM --route-summary

# Flight pair analysis (round-trip detection)
python Flight-Search.py --flight-pair 215 216 --airline PR

# Airline network overview
python Flight-Search.py --airline-summary PR
```

### Database Queries
```bash
# ALWAYS check schema first before any database operations
python -c "import sqlite3; conn = sqlite3.connect('DB/flight_schedules.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(flights)'); columns = cursor.fetchall(); print('Database Schema:'); [print(f'{col[1]} {col[2]}') for col in columns]; conn.close()"

# Check database status
python -c "import sqlite3; db=sqlite3.connect('DB/flight_schedules.db'); print(f'Total flights: {db.execute(\"SELECT COUNT(*) FROM flights\").fetchone()[0]}'); db.close()"

# PR flights summary
python -c "import sqlite3; db=sqlite3.connect('DB/flight_schedules.db'); print(f'PR flights: {db.execute(\"SELECT COUNT(*) FROM flights WHERE airline_iata_code=\\\"PR\\\"\").fetchone()[0]}'); db.close()"
```

## Data Collection Protocol

### 🚨 **Critical Guidelines**

#### API Call Authorization
- **MANDATORY**: All API calls require explicit user confirmation
- **Protocol**: Count and report API calls before execution
- **Coverage**: Applies to ALL API operations (testing, debugging, updates)
- **Enforcement**: Zero automatic execution without approval

#### Future Schedules API Rules
- **8-Day Minimum**: NEVER attempt calls within 8 days from current date
- **Parameter Protection**: ONLY use parameters from `Future-Schedules-Param.txt`
- **Read-Only**: AI agents prohibited from modifying API parameters
- **Script Requirement**: ALL Future Schedules calls must use existing scripts

#### Database Standards
- **Schema Verification**: ALWAYS read and verify database schema before any database operations
- **Query Type Tracking**: All flights must include query_type (departure/arrival)
- **Uppercase Format**: All text data stored in CAPS (airport codes, airlines, etc.)
- **Schema Protection**: Database modifications require user confirmation
- **Pre-Operation Check**: Execute `PRAGMA table_info(flights)` before database insertions/updates
- **Database Creation Policy**: NO creation of new databases unless for temporary tasks - ALWAYS use existing `DB/flight_schedules.db`

## Project Structure

```
P02/
├── Flight-Search.py              # Main flight search system
├── verify_schema.py              # MANDATORY schema verification utility
├── FLIGHT-SEARCH-README.md       # Detailed usage documentation
├── README.md                     # This project overview
├── API/
│   ├── Departure-Future-Schedules.py  # Departure data collection
│   ├── Arrival-Future-Schedules.py    # Arrival data collection
│   └── Future-Schedules-Param.txt     # API parameters (READ-ONLY)
├── DB/
│   ├── flight_schedules.db       # Production database
│   └── flight_route_search.py    # Route search utilities
└── temp scripts/                 # Temporary analysis files (auto-cleaned)
```

## Technical Specifications

### Database Schema
```sql
-- Current Production Schema (as of Sept 2025)
-- ALWAYS verify with: PRAGMA table_info(flights)
CREATE TABLE flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weekdays TEXT,
    airport_code TEXT,
    dep_iata_code TEXT,
    dep_icao_code TEXT,
    dep_terminal TEXT,
    dep_gate TEXT,
    dep_scheduled_time TEXT,
    arr_iata_code TEXT,
    arr_icao_code TEXT,
    arr_terminal TEXT,
    arr_gate TEXT,
    arr_scheduled_time TEXT,
    aircraft_model_code TEXT,
    aircraft_model_text TEXT,
    airline_name TEXT,
    airline_iata_code TEXT,
    airline_icao_code TEXT,
    flight_number TEXT,
    flight_iata_number TEXT,
    flight_icao_number TEXT,
    raw_data TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    query_type TEXT  -- 'departure' or 'arrival'
);
```

### API Integration
- **Provider**: Aviation Edge Future Schedules API
- **Rate Limit**: 500ms between calls with exponential backoff
- **Collection Strategy**: Dual perspective (departure + arrival queries)
- **Date Range**: 8+ days ahead with 2-week extended collection capability

## Performance Metrics

### Database Statistics
- **Total Flights**: 9,869 records
- **Departure Records**: 8,997 (91%)
- **Arrival Records**: 872 (9%)
- **PR Airline Coverage**: 440 flights across 158 unique routes
- **Route Completeness**: Full MNL↔POM bidirectional coverage

### API Call History
- **POM Departures**: 14 successful calls
- **POM Arrivals**: 14 successful calls (39 flights processed)
- **Success Rate**: 100% with proper rate limiting
- **Data Quality**: Complete weekday pattern discovery

## Operational Guidelines

### Session Management
- **Instructions Loading**: Copilot instructions loaded at session start
- **Protocol Enforcement**: API authorization rules maintained consistently
- **Temporary Files**: Use `temp scripts/` folder, auto-cleanup after execution
- **Version Control**: Maintain clean main directory structure

### Future Development
- **Enhancement Ready**: Flight-Search.py designed for iterative improvements
- **Scalable Architecture**: Dual-script system supports expanded collection
- **Data Foundation**: Comprehensive database enables advanced analytics
- **User Access**: Command-line interface provides immediate utility

## Success Criteria ✅

### Primary Objectives Completed
- ✅ **PR215 Investigation**: Weekday discrepancies resolved through dual-query methodology
- ✅ **Route Analysis**: Complete MNL↔POM route coverage with operational insights
- ✅ **System Architecture**: Permanent dual-script implementation operational
- ✅ **Flight Search**: Production-ready search system with command-line interface
- ✅ **Data Quality**: Comprehensive database with query-type tracking

### Validated Outcomes
- ✅ **API Behavior Understanding**: Different perspectives reveal different operational patterns
- ✅ **Data Consolidation**: Route-based search provides complete flight picture
- ✅ **User Interface**: Clean table output with intuitive command-line options
- ✅ **Future Ready**: Architecture supports ongoing development and enhancements

## Support & Maintenance

### Immediate Use
The system is ready for immediate use with full functionality. No additional setup required.

### Future Enhancements
The architecture supports planned improvements including:
- Interactive menu interface
- Export capabilities (CSV/Excel)
- Advanced filtering options
- Historical trend analysis
- Automated reporting

### Contact
This system is part of the Aviation Edge P02 project with permanent implementation status.
For questions or enhancements, refer to session protocols and maintain compatibility with existing architecture.

---

**Project Status**: ✅ **PRODUCTION READY**  
**Next Phase**: User-driven enhancements and feature additions
   - **Manual Updates Only**: Parameter changes must be made manually by authorized users
   - **8-Day Rule**: Do NOT attempt API calls within the next 8 days from current date - data is only available 8+ days ahead
   - **Date Validation**: Always validate that requested date is at least 8 days from today before making API calls

6. **API Call Execution Protocol**:
   - **Mandatory Counting**: ALL API calls must be counted and reported before execution
   - **Confirmation Required**: All API calls require explicit user confirmation before execution
   - **Applies to All Operations**: This includes testing, debugging, and data update operations
   - **No Automatic Execution**: Never execute API calls without prior approval
   - **Permanent Rule**: This protocol must be followed in every session and interaction with this project
   - **Future Schedules Script Only**: ALL Future Schedules API calls must use the existing API/Future-Schedules.py script exclusively
   - **No Alternative Scripts**: Never create new scripts for Future Schedules API operations - work directly with main script
   - **Fix Main Script**: If problems occur with Future Schedules script, fix the main script rather than creating alternatives

## Features

- **HTTP API Client**: Built on `requests` with retry logic and rate limiting
- **Multiple Output Formats**: JSON, CSV, and Excel support
- **Environment Configuration**: Secure API key management with `.env` files
- **Comprehensive Logging**: Detailed logging with `loguru`
- **Async Support**: Optional async HTTP client with `httpx` and `aiohttp`
- **Data Processing**: Built-in pandas integration for data manipulation

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Run Examples**:
   ```bash
   cd API
   python Future-Schedules.py
   ```

4. **Configure Parameters**:
   - Edit `API/Future-Schedules-Param.txt` to set your API parameters
   - This file contains all parameter configurations for future API calls
   - Use preset configurations or customize for your specific needs

## Project Structure

```
API/
├── Future-Schedules.py        # Main API client for schedule data
└── Future-Schedules-Param.txt # Parameter configuration file for future API calls
DB/                            # All database-related scripts and files
src/
├── config.py                  # Configuration management
└── examples.py                # Usage examples
```

## Agent Instructions

**Important Guidelines for AI Agent Interactions:**

1. **Execution Verification**: All script executions and commands must be verified and approved by me before running.

2. **Temporary Scripts Management**: 
   - Use a `temp scripts` folder for all temporary scripts and files
   - Delete the `temp scripts` folder and its contents after successful execution runs
   - Do not leave temporary files in the project directory

3. **Session Guidelines**: These instructions should be loaded and followed each time I connect or start a new session with the agent.

4. **Data Guidelines**: 
   - **No Mock Data Creation**: Do not create, generate, or use mock/fake data in this project
   - Work only with real API endpoints and actual data sources
   - All data should come from legitimate external APIs

5. **Future Schedules API Guidelines**:
   - **Parameter Protection**: Future Schedules API will ONLY use parameters from `Future-Schedules-Param.txt`
   - **No Parameter Modifications**: AI Agent should NOT update, modify, or change these parameters
   - **Read-Only Configuration**: The parameter file serves as the single source of truth for API configuration
   - **Manual Updates Only**: Parameter changes must be made manually by authorized users
