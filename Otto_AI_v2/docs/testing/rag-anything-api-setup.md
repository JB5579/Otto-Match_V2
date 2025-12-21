# RAG-Anything API Setup for Live Integration Testing

## API Configuration
**Purpose**: Establish real RAG-Anything API connection for Story 1-2 remediation testing with **actual embedding generation** - **NO MOCKS ALLOWED**

## API Access Setup

### Authentication Configuration
```python
# REAL RAG-ANYTHING API - NO MOCKS
import os
import requests
from typing import List, Dict

# Actual API configuration
RAG_ANYTHING_API_KEY = os.getenv("RAG_ANYTHING_API_KEY")
RAG_ANYTHING_BASE_URL = "https://api.rag-anything.com/v1"

class RAGAnythingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = RAG_ANYTHING_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
```

### Connection Validation
```python
# REAL API CONNECTION TEST
def validate_api_connection():
    """Test real RAG-Anything API connectivity"""
    try:
        response = requests.get(
            f"{RAG_ANYTHING_BASE_URL}/health",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Real RAG-Anything API connection successful")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Real API connection error: {e}")
        return False
```

## Real Image Processing Pipeline

### Image Upload and Processing
```python
# REAL IMAGE PROCESSING - NO MOCKS
def process_vehicle_images(image_paths: List[str]) -> Dict:
    """
    Process real vehicle images through RAG-Anything API
    Returns actual embeddings, descriptions, and metadata
    """
    processing_results = []

    for image_path in image_paths:
        # Validate image file
        if not validate_image_file(image_path):
            continue

        # Prepare real image data
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        # Real API call to RAG-Anything
        try:
            response = requests.post(
                f"{RAG_ANYTHING_BASE_URL}/process-image",
                headers=headers,
                files={"image": image_data},
                data={
                    "vehicle_context": "automotive",
                    "embedding_model": "multimodal-v1",
                    "extract_features": "true"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                processing_results.append({
                    "image_path": image_path,
                    "embedding": result["embedding"],  # Real 3072-dim vector
                    "description": result["description"],  # Real AI-generated description
                    "features": result["extracted_features"],
                    "confidence": result["confidence_score"]
                })
            else:
                print(f"❌ Real API processing failed for {image_path}: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Real API error for {image_path}: {e}")

    return processing_results
```

### Batch Processing with Rate Limits
```python
# REAL BATCH PROCESSING - NO MOCKS
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class RateLimitedProcessor:
    def __init__(self, max_requests_per_minute=60):
        self.max_rpm = max_requests_per_minute
        self.request_times = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """Enforce real rate limits"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if now - t < 60]

            if len(self.request_times) >= self.max_rpm:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            self.request_times.append(now)

    def process_batch(self, vehicle_batch: List[Dict]) -> List[Dict]:
        """Process real batch of vehicles with actual rate limiting"""
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            for vehicle in vehicle_batch:
                self.wait_if_needed()  # Real rate limiting

                future = executor.submit(
                    self.process_single_vehicle,
                    vehicle["images"],
                    vehicle["metadata"]
                )
                futures.append(future)

            for future in futures:
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Real batch processing error: {e}")

        return results
```

## Real Performance Testing

### API Response Time Validation
```python
# REAL PERFORMANCE MEASUREMENT
def measure_api_performance(test_images: List[str]) -> Dict:
    """Measure real RAG-Anything API performance"""
    performance_metrics = {
        "response_times": [],
        "success_rate": 0,
        "error_count": 0,
        "total_requests": len(test_images)
    }

    successful_requests = 0

    for image_path in test_images:
        start_time = time.time()

        try:
            # Real API call with timing
            response = process_single_image(image_path)

            end_time = time.time()
            response_time = end_time - start_time
            performance_metrics["response_times"].append(response_time)

            if response and response.get("embedding"):
                successful_requests += 1
            else:
                performance_metrics["error_count"] += 1

        except Exception as e:
            performance_metrics["error_count"] += 1
            end_time = time.time()
            performance_metrics["response_times"].append(end_time - start_time)

    # Calculate real performance metrics
    performance_metrics["success_rate"] = (successful_requests / len(test_images)) * 100
    performance_metrics["avg_response_time"] = sum(performance_metrics["response_times"]) / len(performance_metrics["response_times"])
    performance_metrics["p95_response_time"] = sorted(performance_metrics["response_times"])[int(0.95 * len(performance_metrics["response_times"]))]

    return performance_metrics
```

### Throughput Validation
```python
# REAL THROUGHPUT TESTING
def test_processing_throughput(vehicle_count: int, duration_minutes: int = 10) -> Dict:
    """Test real processing throughput over time"""
    print(f"🔄 Testing real throughput: {vehicle_count} vehicles over {duration_minutes} minutes")

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    processed_count = 0
    error_count = 0
    processing_times = []

    while time.time() < end_time and processed_count < vehicle_count:
        vehicle_start = time.time()

        try:
            # Process real vehicle with actual API calls
            result = process_vehicle_batch([get_next_vehicle()])

            if result:
                processed_count += 1
                vehicle_time = time.time() - vehicle_start
                processing_times.append(vehicle_time)
            else:
                error_count += 1

        except Exception as e:
            error_count += 1
            print(f"❌ Real throughput test error: {e}")

    # Calculate real throughput metrics
    total_time = time.time() - start_time
    actual_throughput = processed_count / (total_time / 60)  # vehicles per minute

    return {
        "vehicles_processed": processed_count,
        "errors": error_count,
        "duration_seconds": total_time,
        "throughput_vpm": actual_throughput,
        "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0
    }
```

## Real Error Scenario Testing

### API Failure Scenarios
```python
# REAL ERROR TESTING
def test_error_scenarios():
    """Test real API error handling"""

    # Test 1: Invalid API key
    test_invalid_auth()

    # Test 2: Rate limit exceeded
    test_rate_limit_handling()

    # Test 3: Invalid image format
    test_invalid_image_handling()

    # Test 4: Network timeouts
    test_network_timeout_handling()

def test_invalid_auth():
    """Test real authentication error handling"""
    invalid_headers = {"Authorization": "Bearer invalid_key"}

    try:
        response = requests.post(
            f"{RAG_ANYTHING_BASE_URL}/process-image",
            headers=invalid_headers,
            files={"image": b"fake_image_data"},
            timeout=10
        )

        if response.status_code == 401:
            print("✅ Real auth error handling working")
        else:
            print(f"❌ Unexpected auth response: {response.status_code}")

    except Exception as e:
        print(f"❌ Real auth error handling failed: {e}")

def test_rate_limit_handling():
    """Test real rate limit error handling"""
    rapid_requests = 100  # Exceed rate limit
    rate_limit_errors = 0

    for i in range(rapid_requests):
        try:
            response = requests.post(
                f"{RAG_ANYTHING_BASE_URL}/process-image",
                headers=headers,
                files={"image": b"test_image_data"},
                timeout=5
            )

            if response.status_code == 429:  # Rate limit exceeded
                rate_limit_errors += 1

        except Exception:
            pass

    if rate_limit_errors > 0:
        print(f"✅ Real rate limiting detected: {rate_limit_errors} errors")
    else:
        print("⚠️  No rate limiting detected in rapid requests")
```

## Data Quality Validation

### Embedding Quality Testing
```python
# REAL EMBEDDING VALIDATION
def validate_embedding_quality(processed_results: List[Dict]) -> Dict:
    """Validate quality of real embeddings"""

    quality_metrics = {
        "embedding_dimensions": [],
        "confidence_scores": [],
        "description_lengths": [],
        "feature_counts": []
    }

    for result in processed_results:
        if result.get("embedding"):
            # Validate real embedding dimensions
            embedding_dim = len(result["embedding"])
            quality_metrics["embedding_dimensions"].append(embedding_dim)

            # Validate confidence scores
            if "confidence" in result:
                quality_metrics["confidence_scores"].append(result["confidence"])

            # Validate description quality
            if "description" in result:
                quality_metrics["description_lengths"].append(len(result["description"]))

            # Validate feature extraction
            if "features" in result:
                quality_metrics["feature_counts"].append(len(result["features"]))

    # Calculate quality statistics
    return {
        "avg_embedding_dim": sum(quality_metrics["embedding_dimensions"]) / len(quality_metrics["embedding_dimensions"]),
        "avg_confidence": sum(quality_metrics["confidence_scores"]) / len(quality_metrics["confidence_scores"]) if quality_metrics["confidence_scores"] else 0,
        "avg_description_length": sum(quality_metrics["description_lengths"]) / len(quality_metrics["description_lengths"]) if quality_metrics["description_lengths"] else 0,
        "expected_embedding_dim": 3072,  # RAG-Anything standard
        "quality_passed": all(dim == 3072 for dim in quality_metrics["embedding_dimensions"])
    }
```

## API Integration Checklist

### Pre-Testing Requirements
- [ ] **API Key Validated**: Test authentication with real API
- [ ] **Rate Limits Confirmed**: Understand actual API rate limits
- [ ] **Endpoint Testing**: Validate all required API endpoints
- [ ] **Error Handling**: Test real error scenarios and recovery

### Performance Requirements
- [ ] **Response Time**: < 2 seconds per image (requirement)
- [ ] **Batch Processing**: 50+ vehicles/minute (requirement: 25/min)
- [ ] **Concurrent Processing**: 5+ simultaneous requests
- [ ] **Error Recovery**: Graceful handling of API failures

### Quality Requirements
- [ ] **Embedding Dimensions**: Consistent 3072-dim vectors
- [ ] **Description Quality**: Natural language, meaningful content
- [ ] **Feature Extraction**: Relevant automotive features identified
- [ ] **Confidence Scores**: > 0.7 for high-quality images

---

**This RAG-Anything API setup ensures real integration testing with actual embedding generation, authentic performance measurement, and comprehensive error scenario validation for Story 1-2 remediation.**