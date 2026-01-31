# Story 5.4b: Wire PDF Pipeline to Database Persistence & Semantic Search

**Epic**: 5 - Lead Intelligence Generation
**Story ID**: 5.4b
**Status**: ready-for-dev
**Context Reference**: `docs/sprint-artifacts/stories/5-4b-wire-pdf-pipeline-to-database-persistence.context.xml`
**Created**: 2025-12-30
**Priority**: P0 - Critical Blocker
**Estimated Effort**: 1-2 days

---

## 📋 Story Summary

**As a** seller uploading a condition report PDF,
**I want** my vehicle listing to be saved to the database and immediately searchable,
**So that** buyers can discover my vehicle through Otto AI conversations and semantic search.

---

## 🎯 Business Context

This story completes the vehicle ingestion pipeline by wiring the existing PDF extraction (Story 5.4) to actual database persistence. Without this, uploaded vehicles are processed but lost - they don't appear in search results and Otto AI cannot discuss them.

**Current State**: PDF → VehicleListingArtifact → ❌ void
**Target State**: PDF → VehicleListingArtifact → ✅ Supabase → ✅ pgvector → ✅ Searchable

---

## ✅ Acceptance Criteria

### AC1: Vehicle Listing Persistence
**Given** a seller uploads a condition report PDF
**When** the PDF is successfully processed into a VehicleListingArtifact
**Then** the vehicle data is saved to the `vehicle_listings` table in Supabase
**And** all vehicle specifications (VIN, make, model, year, etc.) are persisted
**And** the listing status is set to 'active'
**And** a unique listing_id is generated and returned

### AC2: Image Persistence & Storage URLs
**Given** a VehicleListingArtifact with extracted images
**When** the artifact is persisted
**Then** all images are saved to the `vehicle_images` table
**And** images are uploaded to Supabase Storage with optimized variants
**And** storage URLs (original, web, thumbnail) are stored in the database
**And** images are linked to the listing via listing_id and VIN

### AC3: Text Embedding Generation & Storage
**Given** a vehicle listing is being persisted
**When** the vehicle data is saved
**Then** a text embedding is generated from the vehicle description
**And** the embedding is stored in the `text_embedding` column (vector(3072))
**And** the pgvector index is updated for similarity search

### AC4: Condition Issues Persistence
**Given** a VehicleListingArtifact with condition issues
**When** the artifact is persisted
**Then** all condition issues are saved to `vehicle_condition_issues` table
**And** issues are categorized (exterior, interior, mechanical, tiresWheels)
**And** severity levels are preserved

### AC5: API Endpoints Return Real Data
**Given** vehicles have been uploaded and persisted
**When** I call `GET /api/listings`
**Then** I receive actual vehicle listings from the database (not placeholders)
**And** results are paginated and filterable by make, model, year, price

**Given** I have a specific listing_id
**When** I call `GET /api/listings/{listing_id}`
**Then** I receive the complete listing details including images and condition

### AC6: Semantic Search Works
**Given** vehicles with embeddings exist in the database
**When** I call `GET /api/listings/{listing_id}/similar`
**Then** I receive semantically similar vehicles using pgvector similarity
**And** results are ranked by similarity score

### AC7: Otto AI Can Query Vehicles
**Given** a vehicle has been uploaded and persisted with embeddings
**When** Otto AI searches for vehicles matching user preferences
**Then** the uploaded vehicle appears in search results if relevant
**And** Otto AI can describe the vehicle's specifications accurately

---

## 🏗️ Technical Implementation

### Files to Modify

| File | Changes Required |
|------|------------------|
| `src/services/vehicle_embedding_service.py` | Implement `_store_vehicle_embeddings()` with actual Supabase inserts |
| `src/api/listings_api.py` | Wire endpoints to database queries, remove placeholders |
| `src/services/pdf_ingestion_service.py` | Call embedding service after processing |

### Files to Create

| File | Purpose |
|------|---------|
| `src/repositories/listing_repository.py` | Data access layer for vehicle_listings CRUD |
| `src/repositories/image_repository.py` | Data access layer for vehicle_images CRUD |

### Database Integration

```python
# Example implementation for _store_vehicle_embeddings
async def _store_vehicle_embeddings(
    self,
    artifact: VehicleListingArtifact,
    text_embedding: List[float],
    image_embeddings: List[Dict]
) -> str:
    # 1. Insert into vehicle_listings
    listing_result = await supabase.table('vehicle_listings').insert({
        'vin': artifact.vehicle.vin,
        'year': artifact.vehicle.year,
        'make': artifact.vehicle.make,
        'model': artifact.vehicle.model,
        'trim': artifact.vehicle.trim,
        'odometer': artifact.vehicle.odometer,
        'drivetrain': artifact.vehicle.drivetrain,
        'transmission': artifact.vehicle.transmission,
        'engine': artifact.vehicle.engine,
        'exterior_color': artifact.vehicle.exterior_color,
        'interior_color': artifact.vehicle.interior_color,
        'condition_score': artifact.condition.score,
        'condition_grade': artifact.condition.grade,
        'description_text': self._create_searchable_text(artifact),
        'text_embedding': text_embedding,
        'status': 'active',
        'listing_source': 'pdf_upload'
    }).execute()

    listing_id = listing_result.data[0]['id']

    # 2. Insert images
    for img, emb in zip(artifact.images, image_embeddings):
        await supabase.table('vehicle_images').insert({
            'listing_id': listing_id,
            'vin': artifact.vehicle.vin,
            'category': img.category,
            'vehicle_angle': img.vehicle_angle,
            'description': img.description,
            'suggested_alt': img.suggested_alt,
            'quality_score': img.quality_score,
            'visible_damage': img.visible_damage,
            'web_url': img.storage_url,
            'thumbnail_url': img.thumbnail_url,
            'image_embedding': emb.get('embedding')
        }).execute()

    return listing_id
```

### API Endpoint Updates

```python
# listings_api.py - Replace placeholder with real query
@listings_router.get("/", response_model=List[ListingSummary])
async def list_listings(limit: int = 20, offset: int = 0, ...):
    result = await supabase.table('vehicle_listing_summaries') \
        .select('*') \
        .range(offset, offset + limit - 1) \
        .execute()
    return [ListingSummary(**row) for row in result.data]
```

---

## 🔗 Dependencies

### Prerequisites (All Complete)
- ✅ Story 5.4 (partial) - PDF extraction working
- ✅ Story 1-1 - Semantic search infrastructure
- ✅ Story 1-2 - Multimodal vehicle data processing
- ✅ Database schema created (`src/services/database_schema.sql`)

### External Dependencies
- Supabase project with pgvector extension enabled
- OpenAI API key for text-embedding-3-large
- Supabase Storage bucket for images

---

## 🧪 Test Plan

### Unit Tests
- [ ] `test_listing_repository_save()` - Verify CRUD operations
- [ ] `test_embedding_generation()` - Verify embedding dimensions
- [ ] `test_image_storage()` - Verify URL generation

### Integration Tests
- [ ] `test_full_pipeline()` - PDF upload → Database → Search
- [ ] `test_api_returns_real_data()` - Verify no placeholders
- [ ] `test_semantic_search()` - Query returns relevant results

### End-to-End Validation
```bash
# 1. Upload test PDF
curl -X POST http://localhost:8000/api/listings/upload \
  -F "file=@test_condition_report.pdf"

# 2. Verify listing in database
# (Use Supabase MCP or dashboard)

# 3. Query listings API
curl http://localhost:8000/api/listings

# 4. Test semantic search
curl http://localhost:8000/api/listings/{id}/similar

# 5. Test Otto AI can find vehicle
# (Via conversation endpoint)
```

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Upload → Searchable time | < 10 seconds |
| Database persistence | 100% of processed artifacts |
| Embedding generation | 100% success rate |
| API response (list) | < 200ms |
| Semantic search relevance | Top result is correct 80%+ |

---

## 🚫 Out of Scope

- Seller authentication/authorization (Story 4.6)
- Lead notification on upload (Story 5.5)
- Analytics dashboard (Story 5.7)
- Subscription tier limits (Story 5.8)

---

## 📝 Definition of Done

- [ ] All acceptance criteria pass
- [ ] `GET /api/listings` returns real database data
- [ ] `GET /api/listings/{id}` returns complete listing
- [ ] `GET /api/listings/{id}/similar` uses pgvector search
- [ ] Uploaded vehicles appear in Otto AI search results
- [ ] Unit and integration tests pass
- [ ] Code reviewed and approved
- [ ] sprint-status.yaml updated to reflect completion

---

## 🔄 Post-Completion

After this story is complete:
1. Mark Story 5.4 as fully DONE (AC4 now met)
2. Proceed to Epic 3 (frontend) with confidence
3. Consider running Epic 5 retrospective
