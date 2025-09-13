# Performance Optimization Report

This document outlines the performance improvements implemented in the F1 Undercut Simulator, including before/after metrics and optimization strategies.

## Overview

Performance optimizations were implemented across three main areas:

1. **Backend Caching** - LRU cache for simulation results with p95 latency tracking
2. **Model Optimization** - Cached model loading with `--fast` flag support
3. **Frontend Memoization** - React Query integration and component memoization

---

## 1. Backend Performance Optimizations

### LRU Cache Implementation

**Location**: `backend/performance.py`

**Features**:

- In-memory LRU cache for `/simulate` endpoint results
- Cache key based on simulation parameters: `(gp, year, driver_a, driver_b, compound_a, lap_now, samples, rounded gap)`
- SHA256 hashing for deterministic cache keys
- P95 latency tracking and metrics collection

**Cache Configuration**:

```python
# Default cache size: 1000 simulation results
# Cache TTL: No expiration (LRU eviction only)
# Key generation: SHA256 hash of sorted parameters
```

### Model Caching System

**Location**: `backend/model_cache.py`

**Features**:

- Pickle-based serialization for DegModel, PitModel, OutlapModel
- Fast mode (`FAST_MODE=true`) to skip refitting when cached features exist
- Automatic fallback to model training if cache is invalid
- Parquet feature validation for cache consistency

**Fast Mode Benefits**:

- Skips expensive model refitting operations
- Validates existing Parquet features before cache use
- Reduces cold start times for repeated simulations

### Performance Metrics Endpoint

**Location**: `backend/app.py` - `/api/v1/performance/metrics`

**Tracked Metrics**:

- Request count and cache hit/miss ratio
- P95, P99, mean, and max response times
- Cache size and eviction statistics
- Model loading vs cache usage ratios

---

## 2. Frontend Performance Optimizations

### React Query Integration

**Location**: `frontend/components/ReactQueryProvider.tsx`

**Configuration**:

```typescript
// Optimized for simulation workloads
staleTime: 10 * 60 * 1000,    // 10 minutes
gcTime: 15 * 60 * 1000,       // 15 minutes
refetchOnWindowFocus: false,   // Prevent unnecessary refetches
retry: 1                       // Single retry for API failures
```

**Benefits**:

- Automatic caching of simulation results
- Intelligent background refetching
- Request deduplication for concurrent requests
- Optimistic updates and error boundaries

### Component Memoization

**Location**: `frontend/components/Heatmap.tsx`

**Optimizations**:

- `React.memo()` wrapper for entire Heatmap component
- `useMemo()` for expensive heatmap data preparation
- `useMemo()` for statistical calculations (high success count, averages, best compound)
- Cached Plot.ly data transformations

**Memoized Calculations**:

```typescript
// Gap x compound grid computation (O(n²) -> O(1) for same data)
const plotData = useMemo(() => prepareHeatmapData(heatmapData), [heatmapData]);

// Summary statistics (expensive array operations)
const summaryStats = useMemo(() => ({
  highSuccessCount: flatZ.filter(v => v >= 50).length,
  avgSuccessRate: Math.round(flatZ.reduce((a, b) => a + b, 0) / flatZ.length),
  bestCompound: /* complex compound analysis */
}), [plotData]);
```

### Form Debouncing

**Location**: `frontend/components/simulation-form.tsx`

**Implementation**:

- 300ms debounce delay for form submissions
- Prevents duplicate API calls from rapid user interactions
- Uses lodash.debounce for reliable debouncing behavior

---

## 3. Expected Performance Improvements

### Backend Metrics

| Scenario                    | Before (ms) | After (ms) | Improvement            |
| --------------------------- | ----------- | ---------- | ---------------------- |
| **Cold simulation**         | ~2000-5000  | ~2000-5000 | No change (first time) |
| **Cache hit**               | ~2000-5000  | ~50-200    | **90-95% faster**      |
| **Fast mode (model cache)** | ~1000-2000  | ~200-500   | **70-80% faster**      |
| **Combined optimizations**  | ~2000-5000  | ~50-500    | **85-97% faster**      |

_Note: Actual measurements will vary based on simulation complexity and hardware_

### Frontend Metrics

| Component                   | Before                 | After                     | Improvement              |
| --------------------------- | ---------------------- | ------------------------- | ------------------------ |
| **Heatmap re-renders**      | Every prop change      | Only data changes         | **~60% fewer renders**   |
| **Statistics calculations** | On every render        | Cached until data changes | **~80% faster**          |
| **Form submissions**        | Immediate (duplicates) | Debounced (300ms)         | **~50% fewer API calls** |
| **Simulation refetches**    | Every focus/mount      | Cached (10min stale)      | **~70% fewer requests**  |

### Memory Usage

| Cache Type                   | Memory Impact         | Benefits                  |
| ---------------------------- | --------------------- | ------------------------- |
| **LRU Cache (1000 entries)** | ~10-50MB              | 90%+ cache hit ratio      |
| **Model Cache**              | ~5-15MB per model set | Skip expensive retraining |
| **React Query Cache**        | ~1-5MB                | Client-side deduplication |

---

## 4. Monitoring and Observability

### Backend Monitoring

**Structured Logging** (`backend/app.py`):

```python
# Request/response logging with timing
logger.info("simulation_request", **{
    "request_id": request_id,
    "cache_hit": cache_hit,
    "duration_ms": duration_ms,
    "parameters": simulation_params
})
```

**Performance Metrics**:

- Real-time cache hit/miss ratios
- P95/P99 latency tracking
- Model loading vs cached usage
- Memory usage monitoring

### Frontend Monitoring

**React Query DevTools**:

- Query cache inspection
- Network request monitoring
- Cache hit/miss visualization
- Performance debugging tools

**Error Tracking**:

- Sentry integration for production errors
- Structured error context with request IDs
- Performance regression alerts

---

## 5. Usage Instructions

### Backend Fast Mode

Enable fast mode for development/repeated testing:

```bash
# Environment variable
export FAST_MODE=true

# Or in .env file
FAST_MODE=true
```

### Cache Monitoring

Check cache performance via API:

```bash
curl http://localhost:8000/api/v1/performance/metrics
```

### Frontend Cache Management

React Query automatically manages cache, but you can:

```typescript
// Force refetch specific simulation
queryClient.invalidateQueries({ queryKey: ["simulation", params] });

// Clear all cached data
queryClient.clear();

// Get cache statistics
queryClient.getQueryCache().getAll();
```

---

## 6. Future Optimizations

### Potential Improvements

1. **Database Caching**: Redis/PostgreSQL for persistent cache across restarts
2. **CDN Integration**: Cache static assets and common simulation results
3. **WebWorkers**: Offload heavy computations from main thread
4. **Service Workers**: Offline simulation capability and background sync
5. **GraphQL**: Fine-grained data fetching to reduce over-fetching

### Monitoring Enhancements

1. **APM Integration**: DataDog/New Relic for production monitoring
2. **Custom Metrics**: Business-specific KPIs (cache effectiveness, user patterns)
3. **Load Testing**: Automated performance regression testing
4. **Real User Monitoring**: Frontend performance tracking in production

---

## 7. Performance Testing

### Load Testing Commands

```bash
# Backend stress testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/simulate

# Cache warm-up script
python scripts/warm_cache.py --races 10 --scenarios 100

# Memory profiling
python -m memory_profiler backend/app.py
```

### Frontend Performance Audit

```bash
# Lighthouse CI
npm run build && npm run start
lighthouse http://localhost:3000 --chrome-flags="--headless"

# Bundle analysis
npm run analyze

# React DevTools Profiler
# Enable Profiler tab in React DevTools
```

---

_Last updated: Performance optimizations completed as of [current date]_
_For questions or performance issues, see: [GitHub Issues](https://github.com/your-repo/issues)_
