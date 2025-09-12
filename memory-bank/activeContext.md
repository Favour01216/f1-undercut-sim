# Active Context

## Current Focus: API Client Service Refactoring

### Immediate Tasks

Refactoring the existing OpenF1 and Jolpica API services to implement:

- New class structures with specific method signatures
- Synchronous requests library instead of async httpx
- Parquet caching with date-based filenames
- HTTP retry logic with exponential backoff
- Safety Car (SC) and Virtual Safety Car (VSC) lap filtering
- Comprehensive logging for all API fetches

### Recent Changes

- Identified existing async-based services that need refactoring
- Current services use httpx async client, need to switch to requests
- Caching mechanism needs implementation for `/features/` directory
- Method signatures need standardization

### Next Steps

1. Create new git branch and protect main
2. Refactor OpenF1Client with get_laps() and get_pit_events() methods
3. Refactor JolpicaClient with get_results() and get_schedule() methods
4. Implement Parquet caching system
5. Add retry logic and logging

### Technical Considerations

- Switch from async/await pattern to synchronous requests
- Implement exponential backoff for HTTP errors
- Create filename convention: {gp}_{year}_{date}.parquet
- Filter out SC/VSC laps from OpenF1 data
- Add comprehensive logging for debugging and monitoring

### Dependencies

- requests library (replacing httpx)
- pandas for DataFrame operations
- pyarrow for Parquet file handling
- logging for fetch tracking
- time/exponential backoff for retry logic
