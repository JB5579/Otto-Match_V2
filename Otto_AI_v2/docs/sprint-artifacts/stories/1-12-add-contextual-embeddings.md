# Story 1-12: Add Contextual Embeddings

**Story Status:** ✅ DONE | **Last Updated:** 2026-01-02 | **Implementation Verified:** YES

**Epic**: 1 - Semantic Vehicle Intelligence
**Story ID**: 1-12
**Status**: done
**Completed**: 2025-12-31
**Verified**: 2026-01-02
**Priority**: P2 - Medium
**Actual Effort**: 1 day

**Implementation:** `src/search/contextual_embedding_service.py` (7.7 KB) - ContextualEmbeddingService with category prefixes

---

## Summary

**As a** vehicle buyer searching semantically,
**I want** embeddings to understand vehicle categories,
**So that** "family vehicle" matches SUVs and minivans but not sports cars.

---

## Business Context

Current embeddings are generated from raw vehicle text without category context. This can cause semantic confusion:

- "Ford F-250" and "Ford Mustang" both contain "Ford" but serve different purposes
- "family vehicle" should match SUVs, not coupes
- "work truck" should match pickups, not luxury sedans

**Contextual embeddings** prepend category information:

```
Before: "2020 Ford F-250 Super Duty Lariat 4WD"
After:  "AUTOMOTIVE VEHICLE - TRUCK: 2020 Ford F-250 Super Duty Lariat 4WD"
```

This helps the embedding model understand the vehicle's purpose and category.

**Expected Impact**: Better category matching, ~5% precision improvement

---

## Acceptance Criteria

### AC1: Category-Aware Embedding Generation
**Given** a vehicle with type "Truck"
**When** an embedding is generated
**Then** the text is prefixed with "AUTOMOTIVE VEHICLE - TRUCK:"
**And** the embedding captures category context
**And** the process is transparent to callers

### AC2: Existing Vehicle Re-embedding
**Given** existing vehicles in the database
**When** re-embedding is triggered
**Then** all vehicles receive contextual embeddings
**And** progress is tracked and resumable
**And** original embeddings are preserved until verified

### AC3: Query Embedding Enhancement
**Given** a search query
**When** the query embedding is generated
**Then** it does NOT include category prefix (to match across categories)
**And** query embedding uses same model as vehicle embeddings

### AC4: Embedding Service Integration
**Given** `ContextualEmbeddingService`
**When** integrated with vehicle processing
**Then** new vehicles automatically receive contextual embeddings
**And** the service is configurable (enable/disable context)
**And** context templates are customizable

### AC5: Similarity Score Improvement
**Given** the query "family SUV"
**When** searching with contextual embeddings
**Then** SUVs and crossovers rank higher than sedans
**And** improvement is measurable via A/B testing

---

## Technical Implementation

### Files to Create

| File | Purpose |
|------|---------|
| `src/search/contextual_embedding_service.py` | Category-aware embedding generation |
| `scripts/reembed_vehicles.py` | One-time migration script |

### ContextualEmbeddingService Design

```python
class ContextualEmbeddingService:
    """Generate embeddings with category context"""

    # Context templates by vehicle type
    CATEGORY_TEMPLATES = {
        "Truck": "AUTOMOTIVE VEHICLE - TRUCK",
        "Pickup": "AUTOMOTIVE VEHICLE - TRUCK",
        "SUV": "AUTOMOTIVE VEHICLE - SUV/CROSSOVER",
        "Crossover": "AUTOMOTIVE VEHICLE - SUV/CROSSOVER",
        "Sedan": "AUTOMOTIVE VEHICLE - SEDAN/CAR",
        "Coupe": "AUTOMOTIVE VEHICLE - SPORTS/COUPE",
        "Convertible": "AUTOMOTIVE VEHICLE - SPORTS/CONVERTIBLE",
        "Minivan": "AUTOMOTIVE VEHICLE - FAMILY/MINIVAN",
        "Van": "AUTOMOTIVE VEHICLE - COMMERCIAL/VAN",
        "Hatchback": "AUTOMOTIVE VEHICLE - COMPACT/HATCHBACK",
        "Wagon": "AUTOMOTIVE VEHICLE - WAGON/ESTATE",
    }

    DEFAULT_TEMPLATE = "AUTOMOTIVE VEHICLE"

    def __init__(self, embedding_service: OttoAIEmbeddingService):
        self.embedding_service = embedding_service
        self.enable_context = True

    async def generate_vehicle_embedding(
        self,
        vehicle_text: str,
        vehicle_type: Optional[str] = None
    ) -> List[float]:
        """Generate contextual embedding for a vehicle"""

        if self.enable_context and vehicle_type:
            context = self.CATEGORY_TEMPLATES.get(
                vehicle_type,
                self.DEFAULT_TEMPLATE
            )
            contextual_text = f"{context}: {vehicle_text}"
        else:
            contextual_text = vehicle_text

        request = EmbeddingRequest(text=contextual_text)
        response = await self.embedding_service.generate_embedding(request)

        return response.embedding

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query (no category prefix)"""
        request = EmbeddingRequest(text=query)
        response = await self.embedding_service.generate_embedding(request)
        return response.embedding

    def create_vehicle_text(self, vehicle: Dict[str, Any]) -> str:
        """Create searchable text from vehicle data"""
        parts = [
            str(vehicle.get('year', '')),
            vehicle.get('make', ''),
            vehicle.get('model', ''),
            vehicle.get('trim', ''),
            vehicle.get('description_text', '')
        ]
        return " ".join(filter(None, parts))
```

### Re-embedding Migration Script

```python
# scripts/reembed_vehicles.py
async def reembed_all_vehicles():
    """Re-embed all vehicles with contextual embeddings"""

    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    embedding_service = OttoAIEmbeddingService()
    await embedding_service.initialize(...)

    contextual_service = ContextualEmbeddingService(embedding_service)

    # Get all vehicles
    result = supabase.table('vehicle_listings') \
        .select('id, vin, year, make, model, trim, vehicle_type, description_text') \
        .execute()

    total = len(result.data)
    print(f"Re-embedding {total} vehicles...")

    for i, vehicle in enumerate(result.data):
        try:
            # Create vehicle text
            text = contextual_service.create_vehicle_text(vehicle)

            # Generate contextual embedding
            embedding = await contextual_service.generate_vehicle_embedding(
                text,
                vehicle.get('vehicle_type')
            )

            # Update database
            supabase.table('vehicle_listings').update({
                'text_embedding': embedding
            }).eq('id', vehicle['id']).execute()

            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{total}")

        except Exception as e:
            print(f"Error re-embedding {vehicle['vin']}: {e}")

    print("Re-embedding complete!")

if __name__ == "__main__":
    asyncio.run(reembed_all_vehicles())
```

### Files to Modify

| File | Changes |
|------|---------|
| `src/semantic/embedding_service.py` | Integrate contextual service |
| `src/semantic/vehicle_processing_service.py` | Use contextual embeddings |
| `src/services/pdf_ingestion_service.py` | Pass vehicle_type to embedding |

---

## Dependencies

### Prerequisites
- Story 1-9 (Hybrid Search) - For testing improvement
- Story 1-11 (Re-ranking) - For A/B comparison

### External
- OpenRouter with embedding model access
- Sufficient API quota for re-embedding

---

## Test Plan

### Unit Tests
- [ ] `test_category_template_mapping()` - Correct prefix applied
- [ ] `test_query_no_context()` - Query embeddings unchanged
- [ ] `test_unknown_vehicle_type()` - Fallback to default

### Integration Tests
- [ ] `test_contextual_vs_plain()` - Compare similarity scores
- [ ] `test_category_matching()` - "family SUV" matches SUVs

### A/B Testing
- [ ] Run 50% traffic with contextual, 50% without
- [ ] Measure precision@5 difference
- [ ] Measure click-through rate difference

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Category match precision | > 90% |
| Re-embedding throughput | > 100 vehicles/minute |
| Similarity score improvement | +5% for category queries |
| Regression test | No decrease for non-category queries |

---

## Definition of Done

- [ ] `ContextualEmbeddingService` implemented
- [ ] Category templates defined for all vehicle types
- [ ] Re-embedding script created and tested
- [ ] All existing vehicles re-embedded
- [ ] Integration with vehicle processing pipeline
- [ ] Unit tests pass
- [ ] A/B test shows improvement
- [ ] Code reviewed and approved
