# Story 1-1 Real Database Connection Test Plan

## Test Objective
Validate semantic search infrastructure using **real Supabase database connections** with pgvector extension - **NO MOCKS ALLOWED**

## Database Connection Setup

### Real Connection Parameters
```python
# REAL DATABASE CONNECTION - NO MOCKS
import os
from sqlalchemy import create_engine
from pgvector.sqlalchemy import Vector

# Actual Supabase connection details
connection_string = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Real database engine
engine = create_engine(connection_string)
```

## Real Testing Scenarios

### 1. Database Schema Validation (AC#1)
**Objective**: Verify vector extension and table structure with real connection

**Test Steps:**
1. **Connect to actual Supabase database**
2. **Verify pgvector extension is installed**
3. **Validate vehicle_embeddings table structure**
4. **Test vector column type and indexing**

**Expected Results:**
- Connection successful with real credentials
- pgvector extension active in database
- Table structure supports vector operations
- Vector indexing configured for similarity search

### 2. Real Vector Store Population (AC#2)
**Objective**: Store actual vehicle embeddings using real pgvector operations

**Test Data:**
- **Real vehicle dataset**: 100+ actual vehicle descriptions
- **Real embedding generation**: Using actual RAG-Anything API
- **Actual vehicle metadata**: VINs, makes, models, years

**Test Steps:**
1. **Generate real embeddings** from vehicle descriptions
2. **Store actual vectors** in Supabase pgvector columns
3. **Validate vector dimensions** match embedding model
4. **Test batch insertion** performance with real data

**Validation Criteria:**
- All 100+ vehicles stored successfully
- Vector dimensions consistent (expected: 3072)
- Insert performance meets real database benchmarks
- No connection timeouts or failures

### 3. Real Vector Similarity Search (AC#3)
**Objective**: Execute actual similarity search queries with real embeddings

**Test Query Scenarios:**
```sql
-- REAL SIMILARITY SEARCH - NO MOCKS
SELECT
    id, vin, make, model, year,
    1 - (embedding <=> query_vector) as similarity_score
FROM vehicle_embeddings
WHERE 1 - (embedding <=> query_vector) > 0.8
ORDER BY similarity_score DESC
LIMIT 10;
```

**Test Cases:**
1. **Exact match queries**: Same vehicle, slight variations
2. **Similar vehicle queries**: Same make/model, different years
3. **Cross-category queries**: Different categories with similar features
4. **No results queries**: Vehicles with no matches

**Performance Validation:**
- Query response times < 500ms with real data
- Accuracy validated with known similar vehicles
- Consistent results across multiple queries

### 4. Real Search Performance Validation (AC#4)
**Objective**: Measure actual search performance with real database load

**Load Testing Scenarios:**
- **Concurrent queries**: 10 simultaneous similarity searches
- **Large dataset**: 1000+ vehicle embeddings
- **Complex queries**: Multi-vector similarity searches
- **Realistic load**: Pattern matching production usage

**Performance Metrics:**
```python
# REAL PERFORMANCE MEASUREMENT
import time

start_time = time.time()
results = execute_similarity_search(query_vector)
end_time = time.time()

actual_query_time = end_time - start_time
assert actual_query_time < 0.5, f"Query too slow: {actual_query_time}s"
```

**Success Criteria:**
- Average query time < 0.5 seconds (requirement: 2s)
- P95 query time < 1.0 second
- No connection failures under load
- Consistent performance across test runs

### 5. Real Result Accuracy Validation (AC#5)
**Objective**: Verify similarity search returns expected results with real data

**Test Method:**
1. **Manual validation**: Known similar vehicles
2. **Cross-validation**: Multiple query approaches
3. **Threshold testing**: Various similarity thresholds
4. **Edge cases**: Partial matches, category matches

**Validation Dataset:**
- 20 known vehicle pairs (similar vehicles)
- 20 known vehicle pairs (dissimilar vehicles)
- Mixed similarity scenarios (0.5-0.95 similarity scores)

**Success Metrics:**
- True positive rate > 85% for similar vehicles
- False positive rate < 15% for dissimilar vehicles
- Consistent ranking of similar vehicles
- Stable similarity scores across queries

## Real Error Scenario Testing

### Database Connection Failures
**Test Scenarios:**
1. **Invalid credentials**: Wrong password/username
2. **Network failures**: Connection timeouts
3. **Database unavailable**: Maintenance/downtime
4. **Rate limiting**: Connection pool exhaustion

**Expected Behavior:**
- Graceful error handling with user-friendly messages
- Automatic retry with exponential backoff
- Fallback to cached results when available
- Proper logging for debugging

### Vector Operation Failures
**Test Scenarios:**
1. **Invalid vector dimensions**: Wrong embedding size
2. **Corrupted vectors**: Malformed vector data
3. **Index failures**: Vector index corruption
4. **Query timeouts**: Complex similarity queries

**Expected Behavior:**
- Input validation with clear error messages
- Data integrity checks before operations
- Query optimization for complex searches
- Timeout handling with graceful degradation

## Real Performance Benchmarking

### Baseline Measurements
- **Single query**: Target < 0.5s (requirement: 2s)
- **Concurrent queries**: 10 simultaneous < 1.0s average
- **Dataset scaling**: Performance degradation < 20% at 10x data
- **Memory usage**: Stable under sustained load

### Production Simulation
- **Realistic query patterns**: Based on user behavior analysis
- **Peak load testing**: Simulate high traffic scenarios
- **Long-duration testing**: 24-hour stability validation
- **Resource monitoring**: CPU, memory, database connections

## Evidence Requirements

### Test Execution Evidence
- **Database connection logs**: Real connection establishment
- **Query execution plans**: Actual database query performance
- **Performance monitoring**: Real-time metrics collection
- **Error logs**: Real failure scenarios and recovery

### Validation Evidence
- **Data integrity checks**: Post-test data validation
- **Performance benchmarks**: Actual measured performance
- **Accuracy metrics**: Real similarity search validation
- **Error handling proof**: Real error scenario testing

---

## TARB Approval Requirements

### Must-Have Evidence
- [ ] Real Supabase connection establishment
- [ ] Actual pgvector vector operations
- [ ] Measured query performance with real data
- [ ] Validated similarity search accuracy
- [ ] Tested error handling with real failures

### Success Criteria
- All acceptance criteria validated with real connections
- Performance claims backed by actual measurements
- No mock/simulated testing used for validation
- End-to-end functionality demonstrated

**This test plan ensures Story 1-1 is validated with real database connections and actual performance measurements - no mock testing permitted.**