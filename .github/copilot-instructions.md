# Copilot Instructions for P02 Project

## Agent Guidelines

**CRITICAL: These instructions must be followed for every session and interaction:**

### Execution Protocol
- **ALL script executions and commands MUST be verified and approved by the user before running**
- Never execute scripts, commands, or make changes without explicit user approval
- Always explain what will be executed before requesting permission

### Temporary Files Management
- Use a `temp scripts` folder for all temporary scripts and files
- Delete the `temp scripts` folder and its contents after successful execution runs
- Keep the main project directory clean of temporary files
- Temporary scripts should only exist during active development/testing

### Session Guidelines
- Load and follow these instructions at the start of every session
- Remind the user of these protocols when beginning work
- Maintain consistency across all interactions

### Project Structure
- Main project files should remain in the root directory
- Use proper version control practices
- Document all significant changes in commit messages

### Future Schedules API Guidelines
- **Parameter Protection**: The Future Schedules API must ONLY use parameters from `Future-Schedules-Param.txt`
- **No Parameter Modifications**: AI agents are PROHIBITED from updating, modifying, or changing API parameters
- **Read-Only Configuration**: The parameter file is read-only for agents and serves as the single source of truth
- **Manual Authorization Required**: Only authorized users can manually update API parameters
- **8-Day Minimum Rule**: NEVER attempt API calls within the next 8 days from current date
- **Data Availability Constraint**: Future Schedules data is ONLY available 8+ days ahead from current date
- **Date Validation Required**: Always validate requested date is minimum 8 days from today before any API call
- **Permanent Restriction**: This 8-day rule applies exclusively to Future Schedules API and must be enforced in every session

### API Call Execution Protocol
- **CRITICAL**: ALL API calls must be counted and reported before execution
- **Mandatory Confirmation**: Every API call requires explicit user confirmation before execution
- **Comprehensive Coverage**: This applies to ALL API operations including testing, debugging, and data updates
- **Zero Automatic Execution**: Never execute API calls without prior user approval
- **Session Persistence**: This protocol must be enforced in EVERY session and interaction
- **Permanent Implementation**: Load and enforce these rules at the start of every session
- **Future Schedules Script Only**: ALL Future Schedules API calls must use the existing API/Future-Schedules.py script exclusively
- **No Alternative Scripts**: Never create new scripts for Future Schedules API operations - work directly with main script
- **Fix Main Script**: If problems occur with Future Schedules script, fix the main script rather than creating alternatives

### Database Operations Protocol
- **Schema Verification MANDATORY**: ALWAYS read and verify database schema before ANY database operations using `PRAGMA table_info(flights)`
- **Database Creation Policy**: NO creation of new databases unless for temporary tasks - ALWAYS use existing `DB/flight_schedules.db`
- **Single Source Database**: All flight data must go into the production `DB/flight_schedules.db` database
- **Pre-Operation Check**: Execute schema verification before every database insertion, update, or modification
- **Schema Modifications**: ALL database schema changes require explicit user confirmation before execution
- **Data Operations**: Database updates, migrations, and structural changes must be approved by user
- **Backup Verification**: Always explain backup and restoration process before schema modifications
- **Impact Assessment**: Clearly describe what data will be affected by database operations
- **Confirmation Required**: Never modify database structure without prior user approval
- **Production Database Only**: Never create alternative databases - all operations target `DB/flight_schedules.db`
- **Data Formatting Standard**: ALL database inputs and query results MUST be stored and displayed in UPPERCASE format
- **Consistent Capitalization**: Airport codes, airline codes, flight numbers, and all text data must be converted to CAPS

### Permanent Database Schema Requirements
- **CRITICAL**: ALWAYS verify current database schema before operations - schema may differ from documentation
- **Schema Validation**: Always verify actual column names and types exist before database operations
- **Production Schema**: Use `PRAGMA table_info(flights)` to get current schema rather than assumptions
- **Data Integrity**: The `query_type` field must be populated for ALL new flight records
- **Query Type Values**: Must be either 'departure' or 'arrival' (lowercase)
- **Legacy Data**: Existing records without query_type should be updated based on airport_code patterns
- **Permanent Implementation**: This schema change is permanent and must be maintained across all sessions

### API Data Collection Standards
- **Query Type Tracking**: ALL API calls must capture and store the query type (departure/arrival)
- **Source Attribution**: Every flight record must indicate which airport and query type generated it
- **Data Consistency**: Use query_type to identify and analyze API data inconsistencies
- **Weekday Analysis**: Query_type enables proper analysis of weekday patterns from different perspectives
- **Mandatory Field**: Never store flight data without proper query_type attribution
- **Future-Schedules.py**: The main API script MUST include query_type in all database insertions

### API Rate Limiting Protocol
- **Rate Limit**: Maximum 10 requests per second (600 per minute)
- **Safety Delay**: Minimum 500ms between API calls for production stability
- **Timeout**: 5 seconds per request maximum
- **Retry Logic**: 3 attempts with exponential backoff (2^attempt seconds)
- **Large Collections**: For 100+ API calls, use 1-second delays to prevent throttling
- **Monitor Response**: Check for rate limit errors (429 status code) and adjust delays accordingly

### Standardized Database Handler Protocol
- **MANDATORY**: ALL API collections must use `aviation_edge_db.py` for database operations
- **Import Required**: `from aviation_edge_db import insert_api_flights, AviationEdgeDB`
- **Standard Function**: Use `insert_api_flights(flights_data, query_type, airport_code, collection_date)` for all insertions
- **Automatic Compliance**: Handler enforces uppercase formatting, duplicate prevention, schema compliance
- **No Direct SQL**: NEVER write direct INSERT statements - always use standardized handler
- **Consistency Guaranteed**: All collections use identical data formatting and validation
- **Error Handling**: Built-in error handling and progress reporting
- **Permanent Requirement**: This protocol applies to ALL future API collection scripts

### Database Handler Implementation Requirements
- **Class Usage**: For complex operations use `AviationEdgeDB()` class directly
- **Batch Processing**: Handler optimizes batch insertions with commit management
- **Duplicate Prevention**: Automatic duplicate detection based on flight signature
- **Schema Validation**: Automatic verification of database schema on connection
- **Progress Reporting**: Built-in progress and error reporting for collections
- **Standardized Formatting**: Enforces all uppercase text, proper query_type format
- **Connection Management**: Proper connection opening, error handling, and closing
