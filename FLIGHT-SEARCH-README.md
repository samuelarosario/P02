# Flight Search System

## Overview
Comprehensive flight search and analysis tool for the Aviation Edge flight database. This system focuses on actual flight routes (d### Troubleshooting

### Common Issues
1. **Database schema mismatch**: ALWAYS run `python verify_schema.py` first
2. **Database not found**: Ensure script runs from project root directory
3. **No results**: Check IATA codes are correct and uppercase
4. **Missing weekdays**: System automatically consolidates from all sources
5. **Column errors**: Use schema verification to get correct column names

### Error Messages
- Schema verification errors indicate database structure issues
- Database connection errors indicate path issues
- No results found suggests criteria too restrictive
- Calculation errors in duration indicate time format issuesarrival) regardless of how the data was collected (departure vs arrival queries).

## Features

### 🔍 **Route-Based Search**
- Search by actual flight routes (dep_iata_code → arr_iata_code)
- Consolidates data from multiple query sources
- Intelligent weekday pattern consolidation
- Clean table output format

### 📊 **Analysis Capabilities**
- Flight pair analysis (round-trip detection)
- Route summaries with statistics
- Airline network analysis
- Turnaround time calculations

### 🎯 **Key Advantages**
- **Query-type agnostic**: Focuses on actual routes, not data collection method
- **Data consolidation**: Merges weekday patterns from departure and arrival queries
- **Comprehensive coverage**: Shows complete operational picture
- **User-friendly**: Clean command-line interface with table output

## Installation

⚠️ **MANDATORY: Always verify database schema first**

```bash
cd "C:\Users\MY PC\Aviation Edge\P02"

# Step 1: MANDATORY schema verification
python verify_schema.py

# Step 2: Use Flight Search system
python Flight-Search.py --help
```

## Usage Examples

### Basic Flight Search
```bash
# Search specific flight
python Flight-Search.py --airline PR --flight 215

# Search route
python Flight-Search.py --origin MNL --destination POM

# Search airline
python Flight-Search.py --airline PR --limit 10
```

### Advanced Analysis
```bash
# Route summary
python Flight-Search.py --origin MNL --destination POM --route-summary

# Flight pair analysis (round-trip)
python Flight-Search.py --flight-pair 215 216 --airline PR

# Airline network summary
python Flight-Search.py --airline-summary PR
```

### Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--origin` | `-o` | Origin airport IATA code | `-o MNL` |
| `--destination` | `-d` | Destination airport IATA code | `-d POM` |
| `--airline` | `-a` | Airline IATA code | `-a PR` |
| `--flight` | `-f` | Flight number | `-f 215` |
| `--route-summary` | `-r` | Show route summary | `-r` |
| `--flight-pair` | `-p` | Analyze flight pair | `-p 215 216` |
| `--airline-summary` | `-s` | Show airline summary | `-s PR` |
| `--limit` | `-l` | Limit results | `-l 20` |

## Output Format

### Table Display
```
┌─────────┬─────────┬───────┬───────┬─────────┬──────────┬─────────────┐
│ Flight  │  Route  │ Depart│ Arrive│Duration │Operating │   Aircraft  │
│ Number  │         │ Time  │ Time  │         │   Days   │             │
├─────────┼─────────┼───────┼───────┼─────────┼──────────┼─────────────┤
│ PR215   │ MNL→POM │ 00:10 │ 08:05 │ 7h55m   │Tue,Fri,Sun│ AA321neo    │
│ PR216   │ POM→MNL │ 09:20 │ 13:00 │ 3h40m   │Tue,Fri,Sun│ AA321neo    │
└─────────┴─────────┴───────┴───────┴─────────┴──────────┴─────────────┘
```

### Flight Pair Analysis
```
Flight Pair Analysis: 215 & 216
Relationship: round_trip
215: MNL→POM - 00:10→08:05 - Weekdays: [2, 5, 7]
216: POM→MNL - 09:20→13:00 - Weekdays: [2, 5, 7]
Turnaround time: 1h 15m
```

## Technical Architecture

### Core Classes
- **FlightSearchSystem**: Main search engine
- **Route-based indexing**: Focuses on actual flight routes
- **Data consolidation**: Merges multiple query sources
- **Intelligent formatting**: Clean output presentation

### Database Integration
- **SQLite backend**: Uses existing flight_schedules.db
- **Query optimization**: Efficient SQL with proper indexing
- **Data validation**: Automatic database verification

### Search Capabilities
1. **Exact matching**: Precise flight number/route searches
2. **Pattern matching**: Flexible airline code handling
3. **Wildcard searches**: Partial criteria matching
4. **Consolidated results**: Unified weekday patterns

## Data Sources Integration

The system works with data collected from both:
- **Departure queries**: From origin airports (e.g., MNL departures)
- **Arrival queries**: At destination airports (e.g., POM arrivals)

**Key Innovation**: Automatically consolidates weekday patterns from different query sources to show complete operational picture.

## Future Enhancements

### Planned Features
- **Interactive mode**: Menu-driven interface
- **Export capabilities**: CSV/Excel output
- **Advanced filtering**: Time ranges, aircraft types
- **Route optimization**: Connection analysis
- **Historical trends**: Operational pattern analysis

### API Integration
- **Real-time updates**: Live data refresh
- **Batch processing**: Bulk route analysis
- **Automated reports**: Scheduled summaries

## Examples

### PR215/PR216 Analysis
This system perfectly demonstrates the weekday discrepancy discovery:
- **PR215**: Departure queries showed weekdays 2,7 vs Arrival queries showed 2,5,7
- **Result**: Friday operations (weekday 5) only visible through arrival queries
- **Solution**: System automatically consolidates to show complete pattern: Tuesday, Friday, Sunday

### MNL↔POM Route
Complete bidirectional route analysis showing:
- **Airlines**: Philippine Airlines (PR), PNG Air (PX)
- **Frequencies**: 3x weekly service patterns
- **Aircraft**: Airbus A321neo, Boeing 737-800
- **Connectivity**: Round-trip service with efficient turnarounds

## Best Practices

### Search Strategy
1. **Start broad**: Use airline or route filters
2. **Narrow down**: Add specific flight numbers
3. **Analyze patterns**: Use route summaries for overview
4. **Verify connections**: Use flight-pair analysis

### Data Interpretation
- **Weekday consolidation**: Shows complete operational pattern
- **Multiple records**: Same flight may appear from different query sources
- **Query type**: Indicates data collection method, not flight direction
- **Duration calculations**: Accounts for overnight flights and time zones

## Troubleshooting

### Common Issues
1. **Database not found**: Ensure script runs from project root directory
2. **No results**: Check IATA codes are correct and uppercase
3. **Missing weekdays**: System automatically consolidates from all sources

### Error Messages
- Database connection errors indicate path issues
- No results found suggests criteria too restrictive
- Calculation errors in duration indicate time format issues

## Support

This Flight Search System is part of the Aviation Edge P02 project and integrates with:
- **Database**: DB/flight_schedules.db
- **API Scripts**: Departure-Future-Schedules.py, Arrival-Future-Schedules.py
- **Analysis Tools**: Route analysis and weekday consolidation

For support or enhancements, refer to the project documentation and maintain compatibility with the existing dual-script architecture.
