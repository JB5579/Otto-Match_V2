# Real Vehicle Dataset Preparation for Testing

## Dataset Requirements
**Purpose**: Provide real vehicle data for Stories 1-1 & 1-2 remediation testing with **actual RAG-Anything processing** and **real database storage**

## Dataset Specifications

### Target Dataset Size
- **Minimum**: 1,000 unique vehicles
- **Optimal**: 5,000 unique vehicles
- **Data Types**: Text descriptions, images, metadata
- **Quality**: Production-ready, real-world data

### Vehicle Categories Distribution
| Category | Target Count | Data Requirements |
|----------|--------------|-------------------|
| Sedans | 300 | Make, model, year, images, descriptions |
| SUVs | 400 | Make, model, year, trim levels, images |
| Trucks | 200 | Make, model, year, payload, towing specs |
| Luxury | 100 | Premium brands, features, high-res images |

## Data Collection Strategy

### Source 1: Public Vehicle APIs
**NHTVIN Database Integration**
```python
# REAL VEHICLE DATA API - NO MOCKS
import requests

def fetch_vehicle_data(vin):
    """Fetch real vehicle data from NHTVIN API"""
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    response = requests.get(url)
    return response.json()

# Sample VINs for diverse vehicle dataset
sample_vins = [
    "1HGCM82633A004352",  # Honda Accord
    "2FTRX18W1XCA12345",  # Ford F-150
    "1YVGF22S925543210",  # Toyota Camry
    # ... more VINs
]
```

### Source 2: Automotive Marketplaces
**Edmunds & Kelley Blue Book Data**
- Real vehicle specifications
- Actual market pricing
- Genuine feature descriptions
- Professional vehicle images

### Source 3: Manufacturer Data
**Official OEM Specifications**
- Accurate technical specifications
- Real feature descriptions
- Authentic trim level details
- Production images and assets

## Data Structure Requirements

### Vehicle Metadata Schema
```json
{
  "vin": "1HGCM82633A004352",
  "make": "Honda",
  "model": "Accord",
  "year": 2003,
  "trim": "LX",
  "category": "Sedan",
  "price": 25000,
  "mileage": 75000,
  "engine": "2.4L Inline-4",
  "transmission": "5-Speed Automatic",
  "fuel_type": "Gasoline",
  "drivetrain": "Front-Wheel Drive",
  "description": "Well-maintained Honda Accord LX with low mileage...",
  "features": [
    "Power windows",
    "Air conditioning",
    "AM/FM radio",
    "Cruise control"
  ]
}
```

### Image Requirements
- **Primary Images**: 5-10 high-quality exterior shots
- **Interior Images**: 3-5 interior detail shots
- **Resolution**: Minimum 1024x768 pixels
- **Format**: JPEG with compression quality 85%
- **File Size**: 100KB - 2MB per image

### Text Description Requirements
- **Length**: 200-500 characters per vehicle
- **Content**: Key features, condition, unique selling points
- **Quality**: Natural language, not template-based
- **Variability**: Different phrasing for similar vehicles

## Dataset Generation Plan

### Phase 1: Base Dataset Collection (Days 1-3)
**Tasks:**
- [ ] Collect 500 VINs from diverse vehicle categories
- [ ] Query NHTVIN API for basic vehicle data
- [ ] Scrape Edmunds for detailed specifications
- [ ] Gather manufacturer data for accuracy validation

### Phase 2: Description Generation (Days 4-5)
**Tasks:**
- [ ] Generate natural language descriptions
- [ ] Ensure variability in phrasing and content
- [ ] Include realistic vehicle condition details
- [ ] Add feature highlights and selling points

### Phase 3: Image Collection (Days 6-7)
**Tasks:**
- [ ] Source high-quality vehicle images
- [ ] Organize by vehicle VIN and category
- [ ] Ensure consistent image quality and format
- [ ] Validate image metadata and licensing

### Phase 4: Data Validation (Day 8)
**Tasks:**
- [ ] Verify data completeness and accuracy
- [ ] Check for duplicates and inconsistencies
- [ ] Validate image-text correspondence
- [ ] Format data for processing pipeline

## Quality Assurance Requirements

### Data Completeness
- **Required Fields**: VIN, make, model, year, description
- **Optional Fields**: Trim, mileage, price, features
- **Image Requirements**: Minimum 3 images per vehicle
- **Text Quality**: Natural, descriptive language

### Data Accuracy
- **VIN Validation**: Verify against manufacturer databases
- **Specification Accuracy**: Cross-reference multiple sources
- **Image Verification**: Ensure correct vehicle images
- **Description Accuracy**: Match actual vehicle features

### Data Variety
- **Make Distribution**: Multiple manufacturers
- **Model Range**: Different vehicle classes and types
- **Year Range**: 2010-2024 vehicles
- **Price Range**: Various market segments

## Processing Pipeline

### Data Ingestion
```python
# REAL DATA PROCESSING - NO MOCKS
def load_vehicle_dataset():
    """Load and validate real vehicle dataset"""
    vehicles = []
    for vin in vehicle_vins:
        # Fetch real vehicle data
        vehicle_data = fetch_vehicle_data(vin)

        # Validate required fields
        if validate_vehicle_data(vehicle_data):
            vehicles.append(vehicle_data)

    return vehicles
```

### Image Processing
```python
# REAL IMAGE PROCESSING - NO MOCKS
def process_vehicle_images(vehicle_vin, image_paths):
    """Process real vehicle images for RAG-Anything API"""
    processed_images = []
    for image_path in image_paths:
        # Validate image format and quality
        if validate_image_quality(image_path):
            processed_images.append(image_path)

    return processed_images
```

### Text Generation
```python
# REAL TEXT PROCESSING - NO MOCKS
def generate_vehicle_description(vehicle_data):
    """Generate natural vehicle description"""
    # Combine specifications into natural language
    base_desc = f"{vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}"
    features = ", ".join(vehicle_data['features'][:5])

    return f"{base_desc} with features: {features}. {vehicle_data['additional_info']}"
```

## Storage and Management

### File Organization
```
vehicle-dataset/
├── metadata/
│   ├── vehicle-data.json
│   ├── vin-mappings.csv
│   └── data-sources.json
├── images/
│   ├── {vin}/
│   │   ├── exterior-1.jpg
│   │   ├── interior-1.jpg
│   │   └── details-1.jpg
└── descriptions/
    ├── {vin}-description.txt
    └── {vin}-features.txt
```

### Database Storage
- **Metadata**: PostgreSQL database with full-text search
- **Images**: Cloud storage with CDN distribution
- **Processing**: RAG-Anything API for embedding generation
- **Backups**: Daily automated backup procedures

## Usage for Story Testing

### Story 1-1 (Database Testing)
- **Vector Storage**: Store vehicle embeddings in pgvector
- **Similarity Search**: Test with real vehicle similarities
- **Performance**: Benchmark with real dataset size

### Story 1-2 (Image Processing)
- **RAG-Anything Integration**: Process real vehicle images
- **Batch Processing**: Test with 1000+ real images
- **Accuracy**: Validate embedding quality

---

**This dataset preparation ensures real, production-ready vehicle data for comprehensive testing of Stories 1-1 and 1-2 with actual RAG-Anything processing and real database operations.**