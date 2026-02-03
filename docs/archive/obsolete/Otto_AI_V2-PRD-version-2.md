# Otto.AI Product Requirements Document

## AI-Powered Vehicle Discovery & Lead Generation Platform

**Version:** 2.0  
**Date:** November 2025  
**Project Codename:** Otto.AI  
**Document Status:** Development Ready - BMAD Method / Claude Code

---

## Executive Summary

Otto.AI is a next-generation AI-powered vehicle discovery platform that serves **two distinct customers**:

1. **Buyers (Discovery Users)**: People who want an enjoyable, conversational experience exploring vehicles. They're not just searching—they're discovering, learning, and having fun conversations with Otto AI about their automotive dreams and practical needs.

2. **Sellers (Lead Subscribers)**: Dealers and individuals who provide inventory to Otto.AI and receive **high-quality, insight-rich leads** with actionable intelligence on how to close the sale based on everything Otto learned during discovery conversations.

The platform transforms the traditional "search and filter" car shopping experience into **conversational discovery**—where Otto AI acts as a knowledgeable friend who remembers everything about you, learns your preferences over time, and genuinely helps you find the perfect vehicle while generating invaluable sales intelligence for sellers.

**Core Value Propositions**:
- **For Buyers**: "The most enjoyable way to find your next car—like talking to a car-obsessed friend who knows everything and remembers you."
- **For Sellers**: "Leads that come with a playbook—know exactly what matters to this buyer and how to close the deal."

---

## Table of Contents

1. [Vision & Goals](#1-vision--goals)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Data Ingestion & Listing Management](#3-data-ingestion--listing-management)
4. [Core Platform Features](#4-core-platform-features)
5. [Otto Concierge AI System](#5-otto-concierge-ai-system)
6. [User Experience & Interface](#6-user-experience--interface)
7. [Lead Generation & Handoff](#7-lead-generation--handoff)
8. [Technical Requirements](#8-technical-requirements)
9. [Data Models](#9-data-models)
10. [API Specifications](#10-api-specifications)
11. [Security & Compliance](#11-security--compliance)
12. [Analytics & Reporting](#12-analytics--reporting)
13. [Development Phases](#13-development-phases)
14. [Success Metrics](#14-success-metrics)
15. [Appendices](#15-appendices)
16. [BMAD Method & Claude Code Integration](#16-bmad-method--claude-code-integration)

---

## 1. Vision & Goals

### 1.1 Product Vision

Otto.AI transforms vehicle shopping from a frustrating, adversarial experience into a personalized, AI-guided discovery journey. Like having a knowledgeable friend who understands your needs, budget, and preferences, Otto helps buyers find their perfect vehicle match while generating high-intent leads for sellers.

### 1.2 Primary Goals

| Goal | Description | Success Metric |
|------|-------------|----------------|
| **Buyer Delight** | Create the most intuitive, personalized car shopping experience | NPS > 70, Session duration > 8 min |
| **Lead Quality** | Deliver leads with 3x higher conversion than traditional sources | Lead-to-sale conversion > 15% |
| **Seller Value** | Provide actionable buyer intelligence that accelerates sales | Time-to-sale reduction > 30% |
| **Market Efficiency** | Match buyers to vehicles faster with higher satisfaction | Match-to-purchase rate > 40% |

### 1.3 Dual-Customer Model: The Otto.AI Flywheel

```
                    ┌─────────────────────────────────┐
                    │         OTTO.AI FLYWHEEL        │
                    └─────────────────────────────────┘
                                    
     BUYERS                                              SELLERS
     ──────                                              ───────
                                    
  ┌──────────────┐                              ┌──────────────┐
  │  Discovery   │                              │   Quality    │
  │   Delight    │                              │  Inventory   │
  │              │                              │              │
  │ • Fun chats  │                              │ • More cars  │
  │ • Otto knows │◄────────────────────────────►│ • Better data│
  │   me         │                              │ • Fresh stock│
  │ • Perfect    │                              │              │
  │   matches    │                              │              │
  └──────┬───────┘                              └──────┬───────┘
         │                                             │
         │                                             │
         ▼                                             ▼
  ┌──────────────┐                              ┌──────────────┐
  │   Engaged    │                              │   Insight-   │
  │   Sessions   │                              │   Rich Leads │
  │              │                              │              │
  │ • Deep       │         ┌────────┐          │ • Buyer      │
  │   preferences│────────►│  OTTO  │─────────►│   journey    │
  │ • Emotional  │         │   AI   │          │ • Preferences│
  │   connection │         │LEARNING│          │ • Objections │
  │ • Trust      │         └────────┘          │ • Hot buttons│
  └──────┬───────┘                              └──────┬───────┘
         │                                             │
         │                                             │
         ▼                                             ▼
  ┌──────────────┐                              ┌──────────────┐
  │  Reservations│                              │  Higher      │
  │  & Referrals │                              │  Conversions │
  │              │                              │              │
  │ • Hold cars  │                              │ • Know how   │
  │ • Tell       │◄────────────────────────────►│   to close   │
  │   friends    │    More buyers = more value  │ • Faster     │
  │ • Return     │    More sellers = more cars  │   sales      │
  └──────────────┘                              └──────────────┘
```

#### For Buyers: The Discovery Experience

**What makes Otto.AI different from CarGurus, Autotrader, etc.:**

1. **Conversational, Not Transactional**
   - Users don't fill out forms and wait for spam calls
   - They have genuine conversations about what they want
   - Otto asks thoughtful questions, learns preferences, and remembers everything

2. **Otto Remembers You** (Powered by Zep Cloud)
   - Return visits pick up where you left off
   - "Last time you were interested in the Rivian R1S—they just got a new one in Glacier White. Want to see it?"
   - Preferences evolve over time as Otto learns

3. **Real Knowledge, Real-Time** (Powered by Groq compound-beta)
   - Otto knows current market prices, reviews, common issues
   - "The 2024 Model Y actually has better range than the 2023—about 20 miles more"
   - Not hallucinating—pulling real data via web search

4. **Fun, Not Frustrating**
   - Exploring cars should be enjoyable
   - Otto celebrates discoveries, shares enthusiasm, makes the process feel human
   - No pressure, no sales tactics from Otto

#### For Sellers: The Lead Intelligence Platform

**What makes Otto.AI leads different:**

1. **Leads Come With a Playbook**
   - Not just "John Smith wants to see this car"
   - Full context: "John has two kids, prioritizes safety, is comparing to the Model X, concerned about charging infrastructure, budget ceiling is $85k, prefers dark colors, wife needs to approve"

2. **Conversation Intelligence**
   - Actual quotes from the buyer's conversation
   - Questions they asked (indicating concerns)
   - Features they got excited about
   - Competitive vehicles they're considering

3. **Recommended Sales Approach**
   - "Lead with the safety ratings—this buyer mentioned kids 4 times"
   - "Be prepared to address charging—they asked multiple questions about range anxiety"
   - "Don't push white or silver—they specifically said no light colors"

4. **Qualification Built In**
   - By the time someone reserves, they've had a real conversation
   - Budget, timeline, trade-in, financing needs—all captured naturally
   - Not tire-kickers; these are engaged, educated buyers

### 1.4 Key Differentiators

- **Conversational Discovery**: Natural language AI that understands intent, not just keywords
- **Intelligent Matching**: ML-driven match percentages based on stated and inferred preferences
- **Rich Lead Context**: Sellers receive complete buyer journey, preferences, and conversation history
- **Real-Time Social Proof**: Live activity indicators create urgency and trust
- **Seamless Reservation**: One-click holds that convert browsers into committed buyers

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OTTO.AI PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  DATA INGESTION  │    │   CORE PLATFORM  │    │   LEAD DELIVERY  │       │
│  │                  │    │                  │    │                  │       │
│  │ • Condition PDFs │    │ • Search/Browse  │    │ • Lead Packaging │       │
│  │ • Dealer APIs    │───▶│ • Otto Concierge │───▶│ • CRM Integration│       │
│  │ • Manual Entry   │    │ • Reservations   │    │ • Notifications  │       │
│  │ • Photo Upload   │    │ • Comparisons    │    │ • Analytics      │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                        DATA LAYER                                  │       │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │       │
│  │  │Vehicles │  │  Users  │  │Sessions │  │  Leads  │  │Analytics│ │       │
│  │  │   DB    │  │   DB    │  │   DB    │  │   DB    │  │   DB    │ │       │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                        AI/ML LAYER                                 │       │
│  │  • LLM Integration (Claude API)    • Matching Algorithm           │       │
│  │  • Preference Learning             • Price Intelligence           │       │
│  │  • Conversation Management         • Recommendation Engine        │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interactions

```
SELLER FLOW:
Condition Report → PDF Parser → Data Enrichment → Listing Creation → Publication

BUYER FLOW:
Landing → Preferences → Search/Browse → Otto Chat → Compare → Reserve → Lead

LEAD FLOW:
Reservation → Lead Package Assembly → Seller Notification → CRM Push → Follow-up
```

---

## 3. Data Ingestion & Listing Management

### 3.1 Vehicle Data Ingestion

The platform supports multiple data ingestion methods to accommodate various seller types and workflows.

#### 3.1.1 Condition Report PDF Processing (OpenRouter Vision)

**Input Format**: Standard automotive condition reports (like the attached Lexus ES 350 example)

**Processing Pipeline using OpenRouter Vision:**

```
PDF Upload → OpenRouter Vision API → Structured Extraction → Validation → Enrichment → Storage
                     │
                     ▼
            ┌─────────────────────────────────────────────────────────┐
            │ OpenRouter Vision Model (e.g., GPT-4V, Claude Vision)   │
            │                                                         │
            │ Prompt: "Extract all vehicle information from this      │
            │ condition report. Return structured JSON with:          │
            │ - VIN, Year, Make, Model, Trim                         │
            │ - Odometer reading                                      │
            │ - Condition score and grade                             │
            │ - All issues by category (exterior, interior, etc.)    │
            │ - Tire depths and wheel condition                       │
            │ - Key features and packages                             │
            │ - Seller/dealer information"                            │
            └─────────────────────────────────────────────────────────┘
```

**Why OpenRouter for PDF Processing:**
- Access to best vision models (GPT-4V, Claude Vision) via single API
- Handles varied PDF formats (no brittle parsing rules)
- Extracts data from images within PDFs (damage photos, etc.)
- Cost-effective model selection based on document complexity

**Extraction Example (from attached Lexus ES 350 PDF):**

```json
{
  "vin": "58ADZ1B17NU117484",
  "year": 2022,
  "make": "Lexus",
  "model": "ES",
  "trim": "ES 350",
  "odometer": 19966,
  "condition": {
    "score": 4.3,
    "grade": "Clean"
  },
  "drivetrain": "Front Wheel Drive",
  "transmission": "Automatic",
  "engine": "6-Cylinder",
  "colors": {
    "exterior": "Black",
    "interior": "Black"
  },
  "seller": {
    "name": "Beaver Toyota of Cumming",
    "type": "dealer"
  },
  "issues": {
    "exterior": [
      { "location": "Front Bumper", "type": "Paint Chipped", "severity": "minor" },
      { "location": "Front Hood", "type": "Paint Chipped", "severity": "minor" },
      { "location": "Passenger Quarter", "type": "Small Dent", "severity": "minor" }
    ],
    "interior": [],
    "mechanical": [
      { "type": "Warning Light", "description": "Blind Spot Monitor", "severity": "minor" }
    ],
    "tiresWheels": [
      { "location": "Passenger Front", "type": "Wheel Cosmetic Damage", "severity": "minor" }
    ]
  },
  "tires": {
    "driverFront": { "depth": "6/32+", "condition": "good" },
    "driverRear": { "depth": "6/32+", "condition": "good" },
    "passengerFront": { "depth": "6/32+", "condition": "good" },
    "passengerRear": { "depth": "6/32+", "condition": "good" }
  },
  "features": {
    "sunroof": true,
    "infotainment": "Fully Functional",
    "climateControl": "Fully Functional",
    "airbags": "No Issues"
  },
  "keys": {
    "smartKeys": 1,
    "otherKeys": 0
  }
}
```

**Extracted Fields from Condition Reports**:

| Category | Fields |
|----------|--------|
| **Identity** | VIN, Year, Make, Model, Trim, Stock Number |
| **Condition** | Overall Score (e.g., 4.3 Clean), Odometer Reading |
| **Mechanical** | Engine, Transmission, Drivetrain, Diagnostic Codes |
| **Exterior** | Body Damage (location, severity), Paint Issues, Glass Condition |
| **Interior** | Seat Condition, Electronics Function, Odor/Environmental |
| **Tires/Wheels** | Tread Depth (all 4), Wheel Damage, Spare Status |
| **Safety** | Airbag Status, Warning Lights, Safety Feature Operation |
| **Keys** | Smart Keys Count, Other Keys Count |
| **Title** | Title State, Title Status, Lien Status |
| **Source** | Dealer Name, Location, Inspection Date |

**Data Quality Rules**:
- VIN must pass checksum validation
- Odometer must be reasonable for vehicle age
- Required fields: VIN, Year, Make, Model, Odometer, Condition Score
- Automatic flagging for salvage/flood/lemon titles

#### 3.1.2 Dealer API Integration

**Supported Formats**:
- vAuto / HomeNet feeds
- DealerSocket API
- Custom dealer inventory APIs
- ADF/XML standard format

**Sync Frequency**: Real-time webhooks preferred, minimum 15-minute polling

#### 3.1.3 Manual Entry Portal

**Seller Dashboard Features**:
- Guided listing creation wizard
- VIN decoder auto-fill
- Photo upload with AI enhancement suggestions
- Pricing guidance based on market data
- Condition report template generation

### 3.2 Listing Enrichment & Embedding Pipeline

Raw data is automatically enriched and embedded for AI-powered discovery:

#### 3.2.1 Enrichment Sources

| Enrichment Type | Source | Output |
|-----------------|--------|--------|
| **Market Pricing** | Historical sales, current listings, Groq web search | Fair price range, savings calculation |
| **Feature Decoding** | VIN + trim database (via API) | Full feature list, package identification |
| **Photo Enhancement** | OpenRouter image models | Background removal, consistent lighting, damage highlighting |
| **Description Generation** | Groq compound-beta | Compelling listing copy, highlight callouts |
| **Match Scoring** | RAG + Zep preferences | Per-user match percentages |

#### 3.2.2 Embedding Generation for RAG

Each listing is converted into a searchable embedding for semantic matching:

```typescript
// Listing to Embedding Pipeline
async function createListingEmbedding(listing: VehicleListing): Promise<void> {
  
  // 1. Generate rich text description for embedding
  const embeddingText = generateEmbeddingText(listing);
  
  // 2. Create embedding via OpenRouter
  const embedding = await openrouter.embeddings.create({
    model: "text-embedding-3-small",  // or alternative
    input: embeddingText
  });
  
  // 3. Store in Supabase pgvector
  await supabase.from('vehicle_embeddings').insert({
    vehicle_id: listing.id,
    embedding: embedding.data[0].embedding,
    metadata: {
      make: listing.make,
      model: listing.model,
      year: listing.year,
      price: listing.listPrice,
      fuel_type: listing.fuelType,
      body_style: listing.bodyStyle,
      features: listing.keyFeatures,
      condition_score: listing.conditionScore,
      location: listing.location
    }
  });
}

function generateEmbeddingText(listing: VehicleListing): string {
  return `
    ${listing.year} ${listing.make} ${listing.model} ${listing.trim}
    ${listing.bodyStyle} with ${listing.engine.description}
    ${listing.fuelType === 'electric' ? `${listing.range} miles of range` : `${listing.mpg} MPG`}
    ${listing.drivetrain} drivetrain, ${listing.seating} passenger seating
    ${listing.exteriorColor} exterior, ${listing.interiorColor} ${listing.interiorMaterial} interior
    Key features: ${listing.keyFeatures.join(', ')}
    ${listing.conditionGrade} condition with ${listing.odometer} miles
    ${generateUseCaseText(listing)}
    Price: $${listing.listPrice.toLocaleString()}
    Located in ${listing.location.city}, ${listing.location.state}
  `.trim();
}

function generateUseCaseText(listing: VehicleListing): string {
  const useCases: string[] = [];
  
  if (listing.seating >= 7) useCases.push('great for families');
  if (listing.fuelType === 'electric') useCases.push('zero emissions');
  if (listing.keyFeatures.includes('AWD')) useCases.push('all-weather capable');
  if (listing.keyFeatures.includes('Performance')) useCases.push('sporty driving');
  if (listing.bodyStyle === 'SUV' && listing.towingCapacity > 5000) 
    useCases.push('towing and hauling');
  if (listing.range > 300) useCases.push('long road trips without charging anxiety');
  
  return useCases.length > 0 ? `Perfect for: ${useCases.join(', ')}` : '';
}
```

**Example Embedding Text (for the Lexus ES 350):**

```
2022 Lexus ES ES 350
Sedan with 6-Cylinder engine
25 city / 34 highway MPG
Front Wheel Drive, 5 passenger seating
Black exterior, Black leather interior
Key features: Premium Safety, Luxury, Comfort, Sunroof, Advanced Tech
Clean condition with 19,966 miles
Perfect for: comfortable commuting, executive transportation
Price: $32,500
Located in Cumming, GA
```

This enables semantic searches like:
- "comfortable car for commuting" → matches "comfortable commuting"
- "black luxury sedan" → matches "Black", "Luxury", "Sedan"
- "good gas mileage" → matches "25 city / 34 highway MPG"

### 3.3 Listing Data Model

```typescript
interface VehicleListing {
  // Core Identity
  id: string;
  vin: string;
  stockNumber?: string;
  
  // Vehicle Details
  year: number;
  make: string;
  model: string;
  trim: string;
  bodyStyle: string;
  
  // Specifications
  engine: EngineSpec;
  transmission: TransmissionType;
  drivetrain: DrivetrainType;
  fuelType: FuelType;
  range?: number; // For EVs
  batteryCapacity?: number; // For EVs
  seating: number;
  
  // Condition
  odometer: number;
  conditionScore: number; // 1-5 scale
  conditionGrade: 'Rough' | 'Average' | 'Clean' | 'Extra Clean' | 'Exceptional';
  
  // Issues (from condition report)
  issues: {
    exterior: IssueDetail[];
    interior: IssueDetail[];
    mechanical: IssueDetail[];
    tiresWheels: IssueDetail[];
  };
  
  // Appearance
  exteriorColor: string;
  interiorColor: string;
  interiorMaterial: string;
  
  // Features
  keyFeatures: FeatureTag[]; // AWD, Performance, EV, FSD, etc.
  packages: string[];
  options: string[];
  
  // Pricing
  listPrice: number;
  msrp?: number;
  savings?: number;
  priceHistory: PriceEvent[];
  
  // Media
  photos: PhotoAsset[];
  videos?: VideoAsset[];
  virtualTour?: string;
  
  // Seller
  seller: SellerReference;
  dealerName: string;
  location: GeoLocation;
  
  // Status
  status: ListingStatus;
  availability: AvailabilityStatus;
  reservedBy?: string;
  reservationExpires?: Date;
  
  // Engagement
  viewCount: number;
  saveCount: number;
  inquiryCount: number;
  
  // Timestamps
  listedAt: Date;
  updatedAt: Date;
  soldAt?: Date;
}
```

---

## 4. Core Platform Features

### 4.1 Search & Discovery

#### 4.1.1 Smart Search Bar

**Capabilities**:
- Natural language queries: "red SUV under $40k with good gas mileage"
- Make/model/feature typeahead
- Recent searches
- Saved searches with alerts

#### 4.1.2 Filter System

**Filter Categories**:

| Category | Filters |
|----------|---------|
| **Type** | SUVs, Sedans, Trucks, Coupes, Electric, Hybrid |
| **Price** | Range slider, Under $30k/$50k/$75k/$100k presets |
| **Make/Model** | Multi-select with popularity sorting |
| **Year** | Range selector |
| **Mileage** | Range selector with presets |
| **Features** | AWD, Sunroof, Leather, Navigation, etc. |
| **Color** | Exterior and interior |
| **Fuel Type** | Gas, Electric, Hybrid, Diesel |
| **Body Style** | Sedan, SUV, Truck, Coupe, Convertible, Van |
| **Drivetrain** | FWD, RWD, AWD, 4WD |

**Filter Chip Bar** (Quick access, as shown in UI):
- Dynamic based on user preferences
- Highlighted when active
- One-click toggle

#### 4.1.3 Vehicle Grid

**Tile Components**:
- Hero image with carousel dots
- Match percentage badge (94%, 92%, etc.)
- Year/Make/Model/Trim
- Key specs (range, battery, trim level)
- Price with savings badge
- Status badges (Popular, Trending, Limited Stock)
- Feature tags (EV, AWD, Performance, Luxury)
- "More like this" / "Less like this" feedback buttons

**Grid Behaviors**:
- Infinite scroll with lazy loading
- Real-time re-sorting on preference updates
- Animated tile insertion for new matches
- Skeleton loading states

### 4.2 Vehicle Detail Modal

**Layout Sections** (per UI screenshot):

1. **Header**
   - "NEW LISTING" badge (when applicable)
   - Year Make Model Trim title
   - Close button

2. **Media Gallery**
   - Image carousel with thumbnails
   - Video preview capability
   - 360° view (where available)

3. **Social Proof Badges**
   - "X people viewing"
   - "Offer Made"
   - "Reserved - Expires [time]"
   - "Popular"
   - "Trending"

4. **Pricing Block**
   - Current price (large)
   - Savings amount and percentage
   - Original/MSRP price (strikethrough)
   - Price confidence indicator

5. **Vehicle Specifications Grid**
   - Year, Make, Model, Trim
   - Mileage, Range, Battery
   - Engine, Drivetrain, Seating
   - Color, Interior

6. **Key Features Tags**
   - Visual tag chips (AWD, Performance, EV, FSD, Premium Safety, Advanced Tech, Spacious, Premium Comfort)
   - Clickable for filter

7. **Otto Concierge Box**
   - AI avatar
   - Personalized recommendation text
   - Match percentage with criteria

8. **Action Buttons**
   - "Request to Hold This Vehicle" (primary CTA)
   - "Compare to Similar Models" (secondary)

### 4.3 Comparison Tool

**Comparison Modal Features**:
- Side-by-side spec table
- Up to 3 vehicles
- Highlighted differences
- Winner indicators per category
- "Choose This One" CTA

**Comparison Categories**:
- Price & Savings
- Range/MPG
- Horsepower
- Acceleration (0-60)
- Seating Capacity
- Cargo Space
- Key Features
- Safety Ratings

### 4.4 Sidebar Components

#### 4.4.1 New Arrivals
- Thumbnail list of latest inventory
- "New" badges
- Quick-add to comparison

#### 4.4.2 Community Activity
- Real-time user actions
- "User X just reserved a [Vehicle]"
- "User Y liked the [Vehicle]"
- "User Z is comparing [Vehicle A] and [Vehicle B]"

#### 4.4.3 Market Insights
- Trend charts (demand indicators)
- Average savings statistics
- Segment highlights

---

## 5. Otto Concierge AI System

### 5.1 AI Architecture: The Otto Brain

Otto's intelligence comes from the orchestration of multiple specialized services, each contributing a critical capability:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE OTTO AI BRAIN                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                         ┌───────────────────────┐                               │
│                         │     USER MESSAGE      │                               │
│                         │ "Show me sporty EVs   │                               │
│                         │  under $80k"          │                               │
│                         └───────────┬───────────┘                               │
│                                     │                                            │
│              ┌──────────────────────┼──────────────────────┐                    │
│              │                      │                      │                    │
│              ▼                      ▼                      ▼                    │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐              │
│   │   ZEP CLOUD     │   │  RAG ANYTHING   │   │ GROQ compound-  │              │
│   │                 │   │  + SUPABASE     │   │     beta        │              │
│   │  WHO IS THIS    │   │                 │   │                 │              │
│   │    USER?        │   │  WHAT CARS      │   │  REAL-TIME      │              │
│   │                 │   │   MATCH?        │   │  KNOWLEDGE      │              │
│   │ • Past sessions │   │                 │   │                 │              │
│   │ • Preferences   │   │ • Vector search │   │ • Web search    │              │
│   │ • Personality   │   │ • Filter combo  │   │ • Current prices│              │
│   │ • Hot buttons   │   │ • Inventory     │   │ • Reviews       │              │
│   │ • Deal breakers │   │   availability  │   │ • News/recalls  │              │
│   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘              │
│            │                     │                     │                        │
│            └─────────────────────┼─────────────────────┘                        │
│                                  │                                              │
│                                  ▼                                              │
│                    ┌─────────────────────────┐                                  │
│                    │   GROQ compound-beta    │                                  │
│                    │                         │                                  │
│                    │   RESPONSE SYNTHESIS    │                                  │
│                    │                         │                                  │
│                    │ Context:                │                                  │
│                    │ • User memory (Zep)     │                                  │
│                    │ • Vehicle matches (RAG) │                                  │
│                    │ • Real-time data (Web)  │                                  │
│                    │                         │                                  │
│                    │ Output:                 │                                  │
│                    │ • Natural response      │                                  │
│                    │ • UI update commands    │                                  │
│                    │ • Memory updates        │                                  │
│                    └───────────┬─────────────┘                                  │
│                                │                                                │
│              ┌─────────────────┼─────────────────┐                              │
│              │                 │                 │                              │
│              ▼                 ▼                 ▼                              │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                  │
│   │   ZEP CLOUD     │ │    FRONTEND     │ │    SUPABASE     │                  │
│   │   Memory Write  │ │    UI Update    │ │   Log Session   │                  │
│   │                 │ │                 │ │                 │                  │
│   │ Store new       │ │ • Re-sort grid  │ │ • Conversation  │                  │
│   │ preferences:    │ │ • Highlight     │ │   history       │                  │
│   │ "sporty"        │ │   matches       │ │ • Engagement    │                  │
│   │ "EV"            │ │ • Add filter    │ │   metrics       │                  │
│   │ "budget $80k"   │ │   chips         │ │ • Lead scoring  │                  │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Groq compound-beta: The Conversational Engine

**Why compound-beta is perfect for Otto:**

1. **Built-in Web Search**: Otto doesn't hallucinate about current prices, reviews, or specs. When a user asks "Is the Model Y worth it in 2024?", Otto pulls real reviews, real pricing data, and real comparisons.

2. **Agent Capabilities**: compound-beta can decide when to search, what to search for, and how to synthesize multiple sources—exactly what a car-buying advisor needs.

3. **Speed**: Groq's inference speed means conversations feel natural, not laggy. Sub-second response times keep users engaged.

**System Prompt Structure for Otto:**

```markdown
# Otto AI System Prompt

You are Otto, a friendly and knowledgeable automotive discovery assistant. 
You help people find their perfect vehicle through natural conversation.

## Your Personality
- Warm, enthusiastic about cars, but never pushy
- You're like a car-obsessed friend who happens to know everything
- You celebrate discoveries and share genuine excitement
- You ask ONE question at a time, never overwhelm
- You use emojis sparingly but naturally 🚗

## Your Knowledge
- You have access to real-time web search for current prices, reviews, and news
- You have the user's conversation history and learned preferences (provided in context)
- You have the current vehicle inventory (provided via RAG results)

## Your Goals
1. Help the user discover vehicles they'll love
2. Learn their preferences naturally through conversation
3. Guide them toward a reservation when ready (never push)
4. Capture insights that will help sellers serve them better

## Response Format
Always respond with JSON:
{
  "message": "Your conversational response",
  "ui_actions": [
    {"type": "filter", "action": "add", "filter": "ev"},
    {"type": "sort", "by": "match_score"},
    {"type": "highlight", "vehicle_ids": ["abc", "def"]}
  ],
  "memory_updates": {
    "preferences": {"fuel_type": "electric", "budget_max": 80000},
    "facts": {"has_kids": true, "commute_miles": 45}
  },
  "lead_signals": {
    "intent_level": "medium",
    "timeline": "1-2 months",
    "key_concerns": ["range anxiety"]
  }
}

## Current Context
[User memory from Zep will be injected here]
[RAG vehicle results will be injected here]
[Current conversation history will be injected here]
```

### 5.3 Zep Cloud: The Memory That Makes Otto Feel Human

**Zep Cloud's Role:**

Zep provides **long-term memory** that persists across sessions. This is what makes Otto feel like a friend who remembers you, not a chatbot that resets every conversation.

**Memory Categories:**

```typescript
interface OttoUserMemory {
  // Identity & Demographics (inferred)
  identity: {
    name?: string;
    location?: string;
    familySize?: number;
    hasKids?: boolean;
    occupation?: string;
  };
  
  // Vehicle Preferences (learned over time)
  preferences: {
    // Hard preferences (strong signals)
    hardNo: string[];        // "no white cars", "no CVT transmission"
    mustHave: string[];      // "needs AWD", "must have 3rd row"
    
    // Soft preferences (weak signals)
    likes: string[];         // "prefers sporty", "likes tech features"
    dislikes: string[];      // "not a fan of Tesla interior"
    
    // Scored preferences (confidence-weighted)
    fuelType: { value: string; confidence: number };
    bodyStyle: { value: string; confidence: number };
    priceRange: { min: number; max: number; confidence: number };
    brandAffinity: { brand: string; score: number }[];
  };
  
  // Usage Context
  useCases: {
    primaryUse: string;      // "daily commute", "family trips"
    secondaryUses: string[];
    commuteMiles?: number;
    parkingSituation?: string;
    chargingAccess?: string; // For EVs
  };
  
  // Purchase Context
  purchaseContext: {
    timeline: string;
    financingNeeds: string;
    hasTradeIn: boolean;
    tradeInVehicle?: string;
    decisionMakers: string[];  // "wife needs to approve"
  };
  
  // Conversation Style
  conversationStyle: {
    verbosity: 'brief' | 'detailed';
    techSavvy: boolean;
    priceSensitive: boolean;
    emotionalVsRational: number;  // 0-1 scale
  };
  
  // Journey State
  journey: {
    stage: 'browsing' | 'researching' | 'comparing' | 'deciding' | 'ready';
    vehiclesExplored: string[];
    currentFavorites: string[];
    rejectedVehicles: { id: string; reason: string }[];
  };
  
  // Session History (summaries)
  sessionSummaries: {
    date: Date;
    summary: string;
    keyLearnings: string[];
    vehiclesDiscussed: string[];
  }[];
}
```

**How Zep Memory Flows Through Conversations:**

```
SESSION 1 (New User):
───────────────────────
User: "I'm looking for an electric SUV"
Otto: [No prior memory, starts fresh]
      "Great choice! Electric SUVs are fantastic. Quick question—will this 
       be a family vehicle or more for personal use?"
User: "Family—we have two young kids"

Zep Memory Created:
{
  identity: { hasKids: true, familySize: 4 },
  preferences: { fuelType: { value: "electric", confidence: 0.9 } },
  useCases: { primaryUse: "family" }
}

SESSION 2 (Return User, 3 days later):
──────────────────────────────────────
User: "Hey Otto, I'm back"
Otto: [Retrieves Zep memory]
      "Welcome back! 👋 Last time we were exploring electric SUVs for your 
       family. I've been keeping an eye out—there's a new Rivian R1S that 
       just came in with the 7-seat configuration. It's forest green, which 
       might be nice for the kids! Want to take a look?"

This is MAGIC for users—Otto actually remembers.
```

### 5.4 RAG Pipeline: Finding the Right Vehicles

**RAG Anything + Supabase pgvector Integration:**

```typescript
// Vehicle embedding structure
interface VehicleEmbedding {
  vehicle_id: string;
  
  // Dense embedding (semantic meaning)
  embedding: number[];  // 1536 dimensions
  
  // Sparse metadata (for filtering)
  metadata: {
    make: string;
    model: string;
    year: number;
    price: number;
    fuel_type: string;
    body_style: string;
    features: string[];
    colors: string[];
    location: { lat: number; lng: number };
  };
}

// RAG Query Flow
async function findMatchingVehicles(
  userQuery: string,
  userMemory: OttoUserMemory,
  filters?: VehicleFilters
): Promise<VehicleMatch[]> {
  
  // 1. Generate query embedding
  const queryEmbedding = await openrouter.embed(userQuery);
  
  // 2. Build filter conditions from user memory
  const memoryFilters = buildFiltersFromMemory(userMemory);
  
  // 3. Hybrid search: semantic + filters
  const results = await supabase.rpc('match_vehicles', {
    query_embedding: queryEmbedding,
    match_threshold: 0.7,
    match_count: 20,
    filters: { ...filters, ...memoryFilters }
  });
  
  // 4. Re-rank based on user preferences
  const ranked = rerankByPreferences(results, userMemory);
  
  // 5. Calculate match scores
  return ranked.map(v => ({
    ...v,
    matchScore: calculateMatchScore(v, userMemory)
  }));
}
```

**What Gets Embedded:**

Each vehicle listing is embedded as a rich text document:

```
2024 Rivian R1S Adventure Package
Electric SUV with 321 miles of range
Quad motor AWD with 835 horsepower, 0-60 in 3.0 seconds
7 passenger seating with 3rd row
Forest Green exterior, Ocean Coast interior
Features: Air suspension, 360 camera, driver assist, panoramic roof
Adventure-ready with off-road capability and gear tunnel storage
Price: $78,000 | Location: Atlanta, GA
```

This allows semantic queries like:
- "something good for camping" → matches "adventure-ready", "gear tunnel"
- "fast electric family car" → matches "835 horsepower", "7 passenger"
- "green SUV" → matches "Forest Green", "SUV"

**Supported Intents**:

| Intent Category | Examples |
|-----------------|----------|
| **Preference Expression** | "I want something sporty", "Budget is around $50k" |
| **Feature Inquiry** | "Does it have AWD?", "What's the range?" |
| **Comparison Request** | "Compare this to the Lucid", "What's better value?" |
| **Color/Style** | "Show me darker colors", "I prefer cream interiors" |
| **Price Negotiation** | "Is there any flexibility on price?", "What about financing?" |
| **Action Requests** | "Reserve this one", "Schedule a test drive" |
| **General Questions** | "How does charging work?", "What warranty is included?" |

#### 5.1.2 Conversation State Management

```typescript
interface ConversationState {
  sessionId: string;
  userId: string;
  
  // Accumulated Preferences
  preferences: {
    vehicleType: string[];
    priceRange: { min: number; max: number };
    priorityFeatures: string[];
    colorPreferences: { exterior: string[]; interior: string[] };
    rangeRequirements?: number;
    performancePriority: 'high' | 'medium' | 'low';
    luxuryPriority: 'high' | 'medium' | 'low';
    familyNeeds: boolean;
    commuteMiles?: number;
  };
  
  // Journey Tracking
  vehiclesViewed: string[];
  vehiclesLiked: string[];
  vehiclesDisliked: string[];
  comparisons: string[][];
  
  // Current Context
  currentVehicle?: string;
  currentComparison?: string[];
  lastQuestion?: string;
  pendingAction?: string;
  
  // Conversation History
  messages: ConversationMessage[];
  
  // Decision Stage
  stage: 'discovery' | 'narrowing' | 'comparing' | 'deciding' | 'reserving';
}
```

### 5.2 Conversation Flow Patterns

#### 5.2.1 Opening Greeting

```
Otto: Hi [Name] 👋 I've found [X] [category] that closely match your preferences. 
I'm seeing strong options from [Brand A], [Brand B], and [Brand C]. 
Would you like to start by focusing on [Option A] or [Option B]?
```

**Personalization Elements**:
- User's name (if known)
- Inferred category from initial filters
- Top brand matches
- Binary choice to start conversation

#### 5.2.2 Preference Elicitation

**Strategy**: Ask one question at a time, never overwhelm

**Question Patterns**:
- "Would you prefer X or Y?"
- "What matters most: A, B, or C?"
- "Do you see yourself in [scenario]?"
- "Which pulls you more strongly?"

#### 5.2.3 Recommendation Presentation

**Pattern**:
```
Otto: [Acknowledgment of preference]. The [Vehicle] is [compelling reason]:
- [Spec 1]
- [Spec 2]
- [Spec 3]
[Contextual savings/value callout]

Would you like to [next step option A] or [next step option B]?
```

#### 5.2.4 Comparison Facilitation

**Pattern**:
```
Otto: Comparison complete:
- The [Vehicle A] is [advantage] but [trade-off].
- The [Vehicle B] gives you [advantage] but [trade-off].

Do you see yourself prioritizing [Option A factor] or [Option B factor]?
```

#### 5.2.5 Urgency & Social Proof

**Triggers**:
- Multiple viewers on same vehicle
- Existing offers
- Low stock
- Recent similar reservations

**Pattern**:
```
Otto: Quick note, [Name]—there are currently [X] other Otto members viewing this exact car, 
and someone has already made an offer. Would you like me to hold it for you right now 
so it doesn't get snapped up?
```

#### 5.2.6 Reservation Confirmation

**Pattern**:
```
Otto: ✅ Done! I've reserved the [Full Vehicle Description] in your name.
[UI updates to show Reserved state]

Confirmation is on its way to your email—includes deposit steps and expected delivery windows. 🎉

[Name], congratulations—you found your dream car! 🚘✨
```

#### 5.2.7 Next Steps Offering

**Pattern**:
```
Otto: One more thing—would you like me to share your contact information with the seller 
so they can reach out directly? I can also schedule a test drive or a time for you to visit 
and see the vehicle in person. [Personalized excitement about vehicle feature]!

[CTA Buttons appear in chat]
```

### 5.3 UI Synchronization

The Otto Concierge must trigger UI updates in real-time as the conversation progresses.

**Update Types**:

| Conversation Event | UI Update |
|--------------------|-----------|
| Preference stated (e.g., "range is important") | Grid re-sorts, filter chips update, new tiles slide in |
| Color preference | Filtered results animate, color-specific options appear |
| Vehicle interest | Detail modal preloads, "More like this" suggestions |
| Comparison request | Compare modal slides to center |
| Reservation request | Social proof badges update, "Reserved for You" state |
| Final confirmation | Success banner, email sent, next step CTAs |

### 5.5 Conversation Flow Patterns

---

## 6. User Experience & Interface

### 6.1 Design System

#### 6.1.1 Brand Identity

**Colors** (from UI screenshots):
- Primary: Teal (#00A0B0) - Otto branding
- Secondary: Orange gradient - highlights, CTAs
- Success: Green (#4CAF50) - savings, availability
- Warning: Amber (#FFC107) - urgency, expiration
- Error: Red (#F44336) - hold button, alerts
- Neutral: Gray scale - backgrounds, text

**Typography**:
- Headers: Modern sans-serif (e.g., Inter, SF Pro)
- Body: Highly readable at all sizes
- Match Badges: Bold, circular, green background

#### 6.1.2 Component Library

**Core Components**:
- Vehicle Tile (grid and list variants)
- Filter Chips
- Match Badge
- Price Display (with savings)
- Feature Tags
- Social Proof Badges
- Otto Chat Widget
- Comparison Table
- Reservation Button States
- Success Banners

### 6.2 Page Architecture

#### 6.2.1 Main Search Results Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Otto Logo]        [Search Bar]                    [Profile] [🔔]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Find Your Perfect Match                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐                    │
│  │ SUVs   │ │Electric│ │ Luxury │ │Under $50k  │  [+ More Filters]  │
│  └────────┘ └────────┘ └────────┘ └────────────┘                    │
│                                                                      │
│  ┌────────────────────────────────────────────┐ ┌─────────────────┐ │
│  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │ │ New Arrivals    │ │
│  │ │94%   │ │92%   │ │89%   │ │91%   │       │ │ ─────────────── │ │
│  │ │Tesla │ │Lucid │ │Porsche│ │Merc  │       │ │ 🚗 Rivian R1S   │ │
│  │ │Model S│ │Air   │ │Taycan│ │EQS   │       │ │ 🚗 Polestar 3   │ │
│  │ │      │ │      │ │      │ │SUV   │       │ │ 🚗 Cadillac     │ │
│  │ │$94,500│ │$138k │ │$185k │ │$126k │       │ ├─────────────────┤ │
│  │ │[More]│ │[More]│ │[More]│ │[More]│       │ │ Community       │ │
│  │ └──────┘ └──────┘ └──────┘ └──────┘       │ │ Activity        │ │
│  │ ┌──────┐ ┌──────┐                          │ │ ─────────────── │ │
│  │ │88%   │ │87%   │                          │ │ Alex P. just    │ │
│  │ │Audi  │ │BMW   │                          │ │ reserved...     │ │
│  │ │e-tron│ │i7    │                          │ ├─────────────────┤ │
│  │ └──────┘ └──────┘                          │ │ Market Insights │ │
│  └────────────────────────────────────────────┘ │ ─────────────── │ │
│                                                  │ EV demand up 15%│ │
│                                                  └─────────────────┘ │
│                                                                      │
│                                          ┌─────────────────────────┐│
│                                          │ Otto Concierge Chat     ││
│                                          │ ─────────────────────── ││
│                                          │ 🤖 Hi! I've found 6     ││
│                                          │ luxury EVs matching...  ││
│                                          │                         ││
│                                          │ [Ask Otto anything...]  ││
│                                          └─────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

#### 6.2.2 Vehicle Detail Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│ [X]                                                                  │
│ ┌─────────────────────────┐  ┌───────────────────────────────────┐ │
│ │ NEW LISTING             │  │ 👁 6 people viewing               │ │
│ │                         │  │ 🏷 Offer Made                      │ │
│ │ 2023 Tesla Model S Plaid│  │ ⏱ Reserved - Expires              │ │
│ │                         │  │                                    │ │
│ │    [  Image Carousel  ] │  │        $94,500                     │ │
│ │    [📸] [📸] [📸] [▶️]   │  │        Save $5,500                 │ │
│ │                         │  │   ┌──────────────────────────┐    │ │
│ │ ────────────────────────│  │   │Savings ($5,500) ████████│    │ │
│ │ VEHICLE SPECIFICATIONS  │  │   └──────────────────────────┘    │ │
│ │ Year: 2023   Range: 520 │  │        $100,000  →  $94,500       │ │
│ │ Make: Tesla  Battery:111│  │                                    │ │
│ │ Model: Model S Drivetrain│  │ ─────────────────────────────────│ │
│ │ Trim: Plaid  Seating: 5 │  │ OTTO CONCIERGE                    │ │
│ │ Mileage: 398 Color: Grey│  │ 🤖 Based on your preferences,     │ │
│ │ Engine: Dual Interior:  │  │ this 2023 Tesla Model S matches   │ │
│ │ Motor       White Prem  │  │ 92% of your criteria. It's a      │ │
│ │                         │  │ premium EV with exceptional       │ │
│ │ ────────────────────────│  │ performance and range.            │ │
│ │ KEY FEATURES            │  │                                    │ │
│ │ [AWD][Performance][EV]  │  │ ┌───────────────────────────────┐ │ │
│ │ [FSD][Premium Safety]   │  │ │🔒 Request to Hold This Vehicle│ │ │
│ │ [Advanced Tech][Spacious]│ │ └───────────────────────────────┘ │ │
│ │ [Premium Comfort]       │  │ ┌───────────────────────────────┐ │ │
│ │                         │  │ │ 🔄 Compare to Similar Models  │ │ │
│ └─────────────────────────┘  └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Responsive Design

**Breakpoints**:
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: < 768px

**Mobile Adaptations**:
- Single column vehicle grid
- Full-screen detail modal
- Bottom sheet Otto chat
- Collapsible filter drawer
- Thumb-friendly CTAs

### 6.4 Animation & Micro-interactions

**Key Animations**:
- Tile slide-in on new matches
- Match badge pulse on preference update
- Smooth modal transitions
- Chat message typing indicator
- Reserved state confetti/celebration
- Social proof badge fade-in

---

## 7. Lead Generation & Handoff

### 7.1 Lead Lifecycle

```
Discovery → Engagement → Interest → Reservation → Lead Package → Seller Delivery → Follow-up
```

### 7.2 Lead Scoring

**Scoring Factors**:

| Factor | Weight | Scoring Criteria |
|--------|--------|------------------|
| **Reservation Made** | 40% | Full points if reserved |
| **Session Depth** | 15% | Time spent, vehicles viewed, comparisons |
| **Conversation Engagement** | 15% | Questions asked, preferences stated |
| **Profile Completeness** | 10% | Contact info, financing pre-approval |
| **Timeline Urgency** | 10% | Stated purchase timeline |
| **Budget Alignment** | 10% | Stated budget vs. vehicle price |

**Score Tiers**:
- 🔥 **Hot** (85-100): Reserved vehicle, full profile, urgent timeline
- 🟡 **Warm** (60-84): High engagement, strong interest, some info gaps
- 🔵 **Cool** (30-59): Browsing stage, early discovery
- ⚪ **Cold** (<30): Minimal engagement

### 7.3 Lead Package Contents: The Seller's Playbook

When a lead is delivered to a seller, it includes everything they need to close the deal. This is not a traditional "contact form submission"—it's **sales intelligence**.

#### 7.3.1 Lead Package Structure

```typescript
interface OttoLeadPackage {
  // ═══════════════════════════════════════════════════════════════
  // SECTION 1: LEAD OVERVIEW
  // ═══════════════════════════════════════════════════════════════
  leadSummary: {
    id: string;
    score: number;                    // 0-100
    tier: 'hot' | 'warm' | 'cool';
    headline: string;                 // "Family buyer, safety-focused, ready in 2 weeks"
    createdAt: Date;
    reservationId?: string;
    reservationExpires?: Date;
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 2: BUYER CONTACT
  // ═══════════════════════════════════════════════════════════════
  buyer: {
    name: string;
    email: string;
    phone?: string;
    preferredContact: 'email' | 'phone' | 'text';
    bestTimeToContact?: string;       // "Evenings after 6pm"
    timezone: string;
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 3: VEHICLE INTEREST
  // ═══════════════════════════════════════════════════════════════
  vehicle: {
    id: string;
    vin: string;
    title: string;                    // "2024 Rivian R1S Adventure"
    listPrice: number;
    reserved: boolean;
    reservationExpires?: Date;
    
    // What drew them to THIS vehicle
    attractionFactors: string[];      // ["range", "7 seats", "adventure capability"]
    concernsAboutVehicle: string[];   // ["price at top of budget", "charging network"]
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 4: BUYER PROFILE (The Gold)
  // ═══════════════════════════════════════════════════════════════
  buyerProfile: {
    // Demographics (inferred from conversation)
    demographics: {
      familySituation: string;        // "Married with 2 young kids"
      location: string;               // "Suburbs of Atlanta"
      lifestyle: string;              // "Active, outdoorsy, weekend trips"
    };

    // What they're looking for
    priorities: {
      ranked: string[];               // ["safety", "range", "space", "value"]
      mustHaves: string[];            // ["3rd row", "AWD", "300+ mile range"]
      niceToHaves: string[];          // ["panoramic roof", "premium audio"]
      dealBreakers: string[];         // ["no white/silver", "no CVT"]
    };

    // Budget reality
    budget: {
      stated: { min: number; max: number };
      apparent: { min: number; max: number };  // Based on vehicles viewed
      flexibility: 'firm' | 'somewhat flexible' | 'flexible';
      financingNeeded: boolean;
      preApproved: boolean;
      tradeIn?: {
        vehicle: string;
        estimatedValue: number;
      };
    };

    // Decision dynamics
    decisionMaking: {
      primaryDecider: boolean;        // Is this the main decision maker?
      otherDeciders: string[];        // ["wife", "needs wife approval"]
      decisionStyle: string;          // "analytical, needs data"
      concerns: string[];             // What might stop them
    };

    // Timeline
    timeline: {
      urgency: 'immediate' | 'this_week' | '1-2_weeks' | '1_month' | 'flexible';
      drivingFactors: string[];       // ["current lease ending", "new baby coming"]
      constraints: string[];          // ["needs to sell current car first"]
    };
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 5: CONVERSATION INTELLIGENCE
  // ═══════════════════════════════════════════════════════════════
  conversationIntelligence: {
    // Direct quotes that reveal intent
    keyQuotes: {
      quote: string;
      context: string;
      insight: string;
    }[];
    // Example:
    // {
    //   quote: "Safety is huge for us with the kids",
    //   context: "When comparing Model X vs R1S",
    //   insight: "Lead with safety ratings and features"
    // }

    // Questions they asked (reveal concerns)
    questionsAsked: {
      question: string;
      topic: string;
      wasAnswered: boolean;
    }[];

    // What got them excited
    positiveSignals: string[];        // ["loved the gear tunnel", "impressed by range"]
    
    // What gave them pause
    hesitations: string[];            // ["worried about charging on road trips"]

    // Competitive consideration
    competitive: {
      vehiclesCompared: string[];     // ["Tesla Model X", "Mercedes EQS SUV"]
      competitiveAdvantages: string[];// "R1S has better off-road, Tesla has Supercharger network"
      competitiveDisadvantages: string[];
    };
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 6: RECOMMENDED SALES APPROACH
  // ═══════════════════════════════════════════════════════════════
  salesPlaybook: {
    // Opening strategy
    openingApproach: string;
    // "Start by asking about their family's weekend adventures—they mentioned 
    //  camping trips and the kids loving outdoor activities"

    // Key talking points (in order of importance)
    talkingPoints: {
      point: string;
      why: string;
      supporting: string;
    }[];
    // Example:
    // {
    //   point: "Safety ratings and features",
    //   why: "Mentioned kids/safety 4 times in conversation",
    //   supporting: "NHTSA 5-star, 8 airbags, driver assist suite"
    // }

    // Objections to prepare for
    anticipatedObjections: {
      objection: string;
      likelihood: 'high' | 'medium' | 'low';
      suggestedResponse: string;
    }[];

    // What to avoid
    thingsToAvoid: string[];
    // ["Don't push white or silver colors", "Don't compare to Tesla Supercharger network"]

    // Closing signals to watch for
    closingSignals: string[];
    // ["They asked about delivery timeline", "Wife approved over the phone"]

    // Suggested next steps
    suggestedNextSteps: {
      step: string;
      timing: string;
      method: string;
    }[];
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 7: JOURNEY DATA
  // ═══════════════════════════════════════════════════════════════
  journey: {
    firstVisit: Date;
    totalSessions: number;
    totalTimeMinutes: number;
    
    sessionsBreakdown: {
      date: Date;
      duration: number;
      vehiclesViewed: string[];
      actions: string[];
    }[];

    vehicleInteractions: {
      vehicleId: string;
      vehicleTitle: string;
      viewCount: number;
      timeSpent: number;
      actions: string[];              // ["viewed", "compared", "saved", "reserved"]
      sentiment: 'positive' | 'neutral' | 'negative';
    }[];

    searchHistory: string[];          // Natural language searches
    filtersUsed: string[];
  };

  // ═══════════════════════════════════════════════════════════════
  // SECTION 8: CONVERSATION TRANSCRIPT
  // ═══════════════════════════════════════════════════════════════
  transcript: {
    conversationId: string;
    messageCount: number;
    highlights: ConversationMessage[]; // Key messages, not full transcript
    fullTranscriptUrl: string;         // Link to complete conversation
  };
}
```

#### 7.3.2 Example Lead Package (Rendered for Seller)

```
═══════════════════════════════════════════════════════════════════════════════
                         OTTO.AI LEAD PACKAGE
═══════════════════════════════════════════════════════════════════════════════

🔥 HOT LEAD | Score: 92/100 | Reserved Vehicle
───────────────────────────────────────────────────────────────────────────────

VEHICLE: 2024 Rivian R1S Adventure - Forest Green
         VIN: 7PDSGAAX5NN001234
         List Price: $78,500
         ⏱️ RESERVED - Expires in 47 hours

───────────────────────────────────────────────────────────────────────────────

BUYER CONTACT
─────────────
Name:           John Mitchell
Email:          john.mitchell@email.com
Phone:          (404) 555-1234
Best Contact:   Phone, evenings after 6pm EST
Timezone:       America/New_York

───────────────────────────────────────────────────────────────────────────────

BUYER AT A GLANCE
─────────────────
"Active family dad looking for an adventure-ready EV. Prioritizes safety 
for his two young kids. Budget-conscious but willing to stretch for the 
right vehicle. Wife is co-decision maker and needs to see it in person."

Family:         Married, 2 kids (ages 4 and 7)
Location:       Alpharetta, GA (suburb of Atlanta)
Lifestyle:      Outdoorsy, weekend camping trips, soccer dad duties
Timeline:       Ready to buy within 2 weeks (current lease ending)
Budget:         $70-80k (firm ceiling at $80k)
Trade-In:       2021 Toyota Highlander, ~$32k value
Financing:      Pre-approved through their credit union

───────────────────────────────────────────────────────────────────────────────

🎯 RECOMMENDED SALES APPROACH
─────────────────────────────

OPENING:
Start by asking about their family's weekend adventures—John mentioned camping 
trips to the North Georgia mountains and the kids loving outdoor activities. 
Build rapport around shared interests before diving into the vehicle.

TOP TALKING POINTS (in priority order):

1. SAFETY FEATURES ⭐⭐⭐
   Why: Mentioned kids/safety 6 times across conversations
   Key Points:
   - NHTSA 5-star overall rating
   - "Guardian" driver monitoring system
   - 11 airbags including 3rd row
   - Quote from John: "Safety is huge for us with the kids"

2. ADVENTURE CAPABILITY ⭐⭐
   Why: Family takes monthly camping trips, excited about gear tunnel
   Key Points:
   - Gear tunnel for outdoor equipment
   - 14" ground clearance (adjustable)
   - 7,700 lb towing capacity
   - Demonstrated excitement: "The gear tunnel is genius!"

3. RANGE FOR ROAD TRIPS ⭐⭐
   Why: Asked multiple questions about charging and range anxiety
   Key Points:
   - 321 miles of range
   - Rivian Adventure Network access
   - "We mapped your typical Alpharetta to Blue Ridge route—you'd 
      arrive with ~40% battery, no charging needed"

ANTICIPATED OBJECTIONS:

⚠️ HIGH: "What about charging on road trips?"
   Response: Offer to map out their typical routes. Rivian Adventure 
   Network has 3 chargers on the way to North Georgia. Also mention 
   home charging covers 95% of their driving.

⚠️ MEDIUM: "The price is at the top of our budget"
   Response: With their trade-in ($32k estimate) and the EV tax credit 
   ($7,500), effective price drops to ~$39k. Monthly payment likely 
   similar to current Highlander lease.

⚠️ MEDIUM: "My wife needs to see it"
   Response: Already anticipated! Offer a family test drive where kids 
   can experience the space. Weekend appointment preferred.

THINGS TO AVOID:
❌ Don't compare to Tesla Supercharger network (he expressed frustration 
   with Tesla's customer service in past ownership)
❌ Don't push any light colors—specifically said "no white or silver"
❌ Don't emphasize 0-60 speed (wife is nervous about fast cars)

CLOSING SIGNALS TO WATCH:
✓ Asks about delivery timeline
✓ Wants to schedule wife/family visit
✓ Asks about exact out-the-door price
✓ Discusses trade-in logistics

───────────────────────────────────────────────────────────────────────────────

CONVERSATION HIGHLIGHTS
───────────────────────

💬 "Safety is huge for us with the kids. That's non-negotiable."
   Context: When comparing Model X vs R1S

💬 "We take the kids camping at least once a month. That gear tunnel 
    is genius—our tent and sleeping bags would fit perfectly."
   Context: Discussing adventure capability

💬 "The Tesla Supercharger network is better, but honestly we had a 
    terrible experience with Tesla service when we had a Model 3. 
    Not going back there."
   Context: When considering Model X as alternative

💬 "My wife is going to want to see it in person. She's skeptical 
    about EVs but I think once she sits in it she'll love it."
   Context: Discussing decision-making process

───────────────────────────────────────────────────────────────────────────────

COMPETITIVE INTELLIGENCE
────────────────────────

Also Considering:
• Tesla Model X Long Range ($79,990) - Ruled out due to bad past experience
• Mercedes EQS SUV ($125,950) - Over budget, eliminated

Why R1S Won:
• Best combination of adventure capability + family space
• Price within budget (especially with trade + tax credit)
• Positive brand perception vs Tesla experience

───────────────────────────────────────────────────────────────────────────────

JOURNEY SUMMARY
───────────────

First Visit:       Nov 22, 2024
Total Sessions:    4
Total Time:        47 minutes
Vehicles Viewed:   8
Vehicles Compared: 3

Session Timeline:
• Nov 22 (12 min): Initial discovery, browsed electric SUVs
• Nov 24 (15 min): Compared R1S vs Model X vs EQS SUV
• Nov 26 (8 min):  Deep dive on R1S, asked about charging
• Nov 28 (12 min): Reserved R1S, discussed with Otto about next steps

[📄 View Full Conversation Transcript]

═══════════════════════════════════════════════════════════════════════════════
```

### 7.4 Lead Delivery Methods

#### 7.4.1 Real-Time Notifications

- Email to seller with lead summary
- SMS alert for hot leads
- Dashboard notification
- Mobile push notification

#### 7.4.2 CRM Integration

**Supported Platforms**:
- Salesforce
- HubSpot
- VinSolutions
- DealerSocket
- Elead
- Custom webhook

**Push Data**:
- Full lead package as structured data
- Attached conversation transcript
- Journey timeline
- Recommended follow-up tasks

#### 7.4.3 Seller Dashboard

**Lead Management Features**:
- Lead inbox with filtering
- Lead detail view
- Status tracking (New → Contacted → Qualified → Sold)
- Response time tracking
- Performance analytics

### 7.5 Seller Portal & Subscription Model

#### 7.5.1 Seller Onboarding Flow

```
1. SIGN UP
   └─ Business verification
   └─ Dealer license validation (if applicable)
   └─ Contact setup

2. INVENTORY SETUP
   └─ Bulk upload via CSV/API
   └─ Condition report PDF upload
   └─ Photo upload with AI enhancement
   └─ Pricing guidance

3. SUBSCRIPTION SELECTION
   └─ Choose tier based on inventory size
   └─ Set lead preferences (geography, vehicle types)
   └─ Payment setup

4. GO LIVE
   └─ Listings appear on Otto.AI
   └─ Start receiving leads
```

#### 7.5.2 Seller Dashboard Features

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SELLER DASHBOARD                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ LEAD INBOX                                                    [Filter ▼]    ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ 🔥 HOT    John M. - 2024 Rivian R1S        Reserved    2 hrs ago    [View] ││
│  │ 🔥 HOT    Sarah K. - 2023 Tesla Model S    Reserved    5 hrs ago    [View] ││
│  │ 🟡 WARM   Mike R. - 2024 Mercedes EQS      Viewing     1 day ago    [View] ││
│  │ 🟡 WARM   Lisa T. - 2024 Porsche Taycan    Comparing   2 days ago   [View] ││
│  │ 🔵 COOL   Alex P. - 2024 Cadillac Lyriq    Browsing    3 days ago   [View] ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌────────────────────────────┐  ┌────────────────────────────────────────────┐ │
│  │ PERFORMANCE THIS MONTH     │  │ INVENTORY STATUS                          │ │
│  │ ─────────────────────────  │  │ ─────────────────────────────────────────  │ │
│  │ Leads Received: 47         │  │ Active Listings: 23                        │ │
│  │ Avg Response Time: 23 min  │  │ Reserved: 4                                │ │
│  │ Contact Rate: 94%          │  │ Pending Upload: 2                          │ │
│  │ Conversion Rate: 18%       │  │ Needs Attention: 1                         │ │
│  │ Revenue from Otto: $42,500 │  │ Avg Match Score: 87%                       │ │
│  └────────────────────────────┘  └────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ RECENT ACTIVITY                                                             ││
│  │ ────────────────────────────────────────────────────────────────────────────││
│  │ • 2024 Rivian R1S received 12 views today (+150% vs avg)                   ││
│  │ • 3 users comparing your 2023 Model S vs competitor listings               ││
│  │ • Price reduction recommended: 2022 Lexus ES (15 days, low engagement)     ││
│  │ • New review mention: User praised your quick response time                 ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 7.5.3 Subscription Tiers

| Feature | Starter | Growth | Pro | Enterprise |
|---------|---------|--------|-----|------------|
| **Monthly Price** | $299 | $599 | $999 | Custom |
| **Active Listings** | 10 | 50 | 200 | Unlimited |
| **Lead Package Detail** | Basic | Full | Full + AI Insights | Full + Custom |
| **Response Time SLA** | - | 24 hrs | 2 hrs | 1 hr |
| **CRM Integration** | Email only | Basic | Advanced | Custom |
| **API Access** | - | Read only | Full | Full + Priority |
| **Dedicated Support** | Email | Chat | Phone | Account Manager |
| **Analytics** | Basic | Standard | Advanced | Custom Reports |
| **Photo Enhancement** | - | ✓ | ✓ + Video | ✓ + Virtual Tour |
| **Lead Routing** | - | - | ✓ | Advanced Rules |

#### 7.5.4 Seller Value Metrics

**What sellers see that proves Otto.AI value:**

1. **Lead Quality Score Distribution**
   - % of leads that are Hot vs Warm vs Cool
   - Comparison to industry benchmarks

2. **Conversion Funnel**
   - Lead → Contact → Appointment → Sale
   - With time-in-stage metrics

3. **Sales Intelligence Usage**
   - Did using Otto's recommended approach improve close rate?
   - A/B comparison: Otto leads vs traditional leads

4. **ROI Calculator**
   - Cost per lead
   - Cost per sale
   - Revenue attribution

### 7.6 Lead Follow-up Automation

**Automated Sequences**:

| Trigger | Action | Timing |
|---------|--------|--------|
| New reservation | Email confirmation to buyer | Immediate |
| Reservation created | Lead notification to seller | Immediate |
| No seller response | Escalation notification | 2 hours |
| Reservation expiring | Reminder to buyer | 12 hours before |
| Reservation expired | Re-engagement email | Immediate |
| Lead not contacted | Manager alert | 24 hours |

---

## 8. Technical Requirements

### 8.1 Technology Stack

#### 8.1.1 AI/ML Services (Critical Path)

| Service | Purpose | Why This Choice |
|---------|---------|-----------------|
| **Groq API** (compound-beta) | Otto AI Chat Engine | Agent-based chat with built-in web search—Otto has real-time knowledge of car specs, reviews, pricing trends, and market data. No hallucination on current info. |
| **OpenRouter** | Multi-model orchestration | Access to best-in-class models for specific tasks: embeddings, vision (photo analysis), image generation, video processing |
| **Zep Cloud** | User Memory & Personalization | Long-term memory across sessions. Otto remembers previous conversations, learned preferences, and continuously refines understanding of each user. This is the "magic" that makes Otto feel like a friend. |
| **Supabase (pgvector)** | RAG Vector Store | Semantic search over vehicle listings. When user describes what they want in natural language, we find matching vehicles via embedding similarity. |
| **RAG Anything** | Search & Retrieval Pipeline | Orchestrates the RAG workflow—chunks listings, generates embeddings, handles hybrid search (semantic + filters) |

#### 8.1.2 Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Next.js 14+ (App Router) | SSR for SEO, streaming for chat, React ecosystem |
| Language | TypeScript | Type safety across full stack |
| Styling | Tailwind CSS | Rapid development, design system consistency |
| State | Zustand + React Query | Client state + server state with caching |
| Animation | Framer Motion | Smooth vehicle card animations, chat transitions |
| UI Components | shadcn/ui + custom | Accessible, matches design system |
| Real-time | WebSocket (native) | Live chat, viewer counts, reservation updates |

#### 8.1.3 Backend & Infrastructure

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | **Supabase PostgreSQL** | Primary data store, row-level security, real-time subscriptions |
| Vector Store | **Supabase pgvector** | Co-located with relational data, hybrid queries |
| Authentication | **Supabase Auth** | OAuth, magic links, RLS integration |
| Storage | **Supabase Storage** | Vehicle photos, condition report PDFs |
| CDN | **Cloudflare** | Edge caching, image optimization, DDoS protection |
| API Layer | Next.js API Routes + Edge Functions | Serverless, globally distributed |
| Background Jobs | Supabase Edge Functions + pg_cron | Lead packaging, notification delivery |
| Hosting | Vercel | Seamless Next.js deployment, preview URLs |

#### 8.1.4 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            OTTO.AI ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   BUYER EXPERIENCE                          SELLER EXPERIENCE                    │
│   ───────────────                           ─────────────────                    │
│   Next.js Frontend                          Seller Dashboard                     │
│        │                                           │                             │
│        ▼                                           ▼                             │
│   ┌─────────────────────────────────────────────────────────────┐               │
│   │                     CLOUDFLARE CDN                           │               │
│   │              (Edge Caching, Image Optimization)              │               │
│   └─────────────────────────────────────────────────────────────┘               │
│                              │                                                   │
│                              ▼                                                   │
│   ┌─────────────────────────────────────────────────────────────┐               │
│   │                    NEXT.JS API LAYER                         │               │
│   │                 (Vercel Edge Functions)                      │               │
│   └─────────────────────────────────────────────────────────────┘               │
│          │              │              │              │                          │
│          ▼              ▼              ▼              ▼                          │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐                   │
│   │   GROQ    │  │ OPENROUTER│  │    ZEP    │  │ SUPABASE  │                   │
│   │           │  │           │  │   CLOUD   │  │           │                   │
│   │ compound- │  │ Embeddings│  │           │  │ PostgreSQL│                   │
│   │   beta    │  │  Vision   │  │  Session  │  │ pgvector  │                   │
│   │           │  │  Image    │  │  Memory   │  │  Storage  │                   │
│   │  Chat AI  │  │  Video    │  │  User     │  │   Auth    │                   │
│   │  + Search │  │           │  │ Learning  │  │           │                   │
│   └───────────┘  └───────────┘  └───────────┘  └───────────┘                   │
│          │              │              │              │                          │
│          └──────────────┴──────────────┴──────────────┘                          │
│                              │                                                   │
│                              ▼                                                   │
│   ┌─────────────────────────────────────────────────────────────┐               │
│   │                    RAG ANYTHING                              │               │
│   │         (Semantic Search & Retrieval Pipeline)               │               │
│   │                                                              │               │
│   │  User: "I want something sporty but practical"               │               │
│   │       ↓                                                      │               │
│   │  Embedding → pgvector similarity → Hybrid filters            │               │
│   │       ↓                                                      │               │
│   │  Returns: BMW M3, Audi S4, Mercedes C43 AMG...              │               │
│   └─────────────────────────────────────────────────────────────┘               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 8.1.5 Data Flow: Discovery Conversation

```
User Message: "I'm thinking about getting an electric SUV for my family"
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. ZEP CLOUD - Memory Retrieval                                 │
│    • Previous sessions: "User has 2 kids, lives in suburbs"     │
│    • Past preferences: "Dislikes white cars, needs 3rd row"     │
│    • Learning: "Values safety features, budget-conscious"       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. RAG ANYTHING - Vehicle Retrieval                             │
│    • Query embedding: "electric SUV family"                     │
│    • Filters: EV=true, seating>=6, !white                       │
│    • Results: Rivian R1S, Tesla Model X, Mercedes EQS SUV...    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. GROQ (compound-beta) - Response Generation                   │
│    Context:                                                     │
│    • User memory from Zep                                       │
│    • Matching vehicles from RAG                                 │
│    • Real-time web search (reviews, pricing, news)             │
│                                                                 │
│    Output: Personalized response with vehicle recommendations   │
│            + UI actions (update grid, highlight matches)        │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. ZEP CLOUD - Memory Update                                    │
│    • Store: "User interested in electric SUVs"                  │
│    • Store: "Family use case confirmed"                         │
│    • Update preference scores                                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SUPABASE - Session Logging                                   │
│    • Log message to conversation history                        │
│    • Update user engagement metrics                             │
│    • Track vehicle impressions                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load (FCP) | < 1.5s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |
| API Response Time | < 200ms (p95) | Server metrics |
| Search Results | < 500ms | Server metrics |
| Otto Chat Response | < 2s | End-to-end |
| Availability | 99.9% | Uptime monitoring |

### 8.3 Scalability Requirements

| Metric | Initial | Scale Target |
|--------|---------|--------------|
| Concurrent Users | 1,000 | 100,000 |
| Listings | 10,000 | 1,000,000 |
| Daily Sessions | 50,000 | 5,000,000 |
| Daily Leads | 500 | 50,000 |

---

## 9. Data Models

### 9.1 Core Entities

#### 9.1.1 User

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  
  // Profile
  avatar?: string;
  location?: GeoLocation;
  timezone: string;
  
  // Preferences (accumulated)
  preferences: UserPreferences;
  
  // Engagement
  savedVehicles: string[];
  searchHistory: SearchQuery[];
  
  // Status
  role: 'buyer' | 'seller' | 'admin';
  status: 'active' | 'suspended';
  createdAt: Date;
  lastActiveAt: Date;
}
```

#### 9.1.2 Seller

```typescript
interface Seller {
  id: string;
  type: 'dealer' | 'individual';
  
  // Identity
  businessName: string;
  contactName: string;
  email: string;
  phone: string;
  
  // Location
  address: Address;
  serviceArea: GeoPolygon;
  
  // Settings
  notificationPreferences: NotificationSettings;
  crmIntegration?: CRMConfig;
  
  // Performance
  responseTimeAvg: number;
  leadConversionRate: number;
  rating: number;
  
  // Status
  subscription: SubscriptionTier;
  status: 'active' | 'paused' | 'suspended';
}
```

#### 9.1.3 Session

```typescript
interface Session {
  id: string;
  userId?: string;
  anonymousId?: string;
  
  // Journey
  startedAt: Date;
  lastActivityAt: Date;
  
  // Tracking
  pageViews: PageView[];
  vehicleViews: VehicleView[];
  searches: SearchEvent[];
  filterChanges: FilterEvent[];
  
  // Otto Conversation
  conversationId?: string;
  
  // Attribution
  source: TrafficSource;
  device: DeviceInfo;
  location: GeoLocation;
}
```

#### 9.1.4 Conversation

```typescript
interface Conversation {
  id: string;
  sessionId: string;
  userId?: string;
  
  // Messages
  messages: ConversationMessage[];
  
  // State
  state: ConversationState;
  
  // Outcome
  outcome: 'reservation' | 'lead' | 'abandoned' | 'ongoing';
  vehicleReserved?: string;
  
  // Timestamps
  startedAt: Date;
  lastMessageAt: Date;
}

interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  
  // Actions triggered
  uiActions?: UIAction[];
  
  // Preferences captured
  preferencesExtracted?: Partial<UserPreferences>;
}
```

#### 9.1.5 Reservation

```typescript
interface Reservation {
  id: string;
  
  // Parties
  vehicleId: string;
  userId: string;
  sellerId: string;
  
  // Status
  status: 'pending' | 'confirmed' | 'expired' | 'cancelled' | 'converted';
  
  // Timing
  createdAt: Date;
  expiresAt: Date;
  convertedAt?: Date;
  
  // Deposit
  depositRequired: boolean;
  depositAmount?: number;
  depositPaid: boolean;
  
  // Lead
  leadId?: string;
}
```

#### 9.1.6 Lead

```typescript
interface Lead {
  id: string;
  
  // Parties
  buyerId: string;
  sellerId: string;
  vehicleId: string;
  reservationId?: string;
  
  // Package
  package: LeadPackage;
  score: number;
  tier: LeadTier;
  
  // Lifecycle
  status: 'new' | 'contacted' | 'qualified' | 'negotiating' | 'sold' | 'lost';
  
  // Tracking
  createdAt: Date;
  firstContactAt?: Date;
  soldAt?: Date;
  salePrice?: number;
  
  // Attribution
  conversationId: string;
  sessionIds: string[];
}
```

### 9.2 Database Schema (PostgreSQL)

```sql
-- Core tables
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  phone VARCHAR(50),
  preferences JSONB DEFAULT '{}',
  role VARCHAR(50) DEFAULT 'buyer',
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sellers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(50) NOT NULL,
  business_name VARCHAR(255) NOT NULL,
  contact_name VARCHAR(255),
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  address JSONB,
  service_area GEOGRAPHY(POLYGON),
  notification_preferences JSONB DEFAULT '{}',
  crm_integration JSONB,
  subscription VARCHAR(50) DEFAULT 'basic',
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vin VARCHAR(17) UNIQUE NOT NULL,
  seller_id UUID REFERENCES sellers(id),
  
  -- Core details
  year INTEGER NOT NULL,
  make VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  trim VARCHAR(100),
  body_style VARCHAR(50),
  
  -- Specs
  engine JSONB,
  transmission VARCHAR(50),
  drivetrain VARCHAR(50),
  fuel_type VARCHAR(50),
  range_miles INTEGER,
  seating INTEGER,
  
  -- Condition
  odometer INTEGER,
  condition_score DECIMAL(2,1),
  condition_grade VARCHAR(50),
  issues JSONB DEFAULT '{}',
  
  -- Appearance
  exterior_color VARCHAR(100),
  interior_color VARCHAR(100),
  
  -- Features
  key_features TEXT[],
  
  -- Pricing
  list_price INTEGER NOT NULL,
  msrp INTEGER,
  savings INTEGER,
  
  -- Media
  photos JSONB DEFAULT '[]',
  
  -- Status
  status VARCHAR(50) DEFAULT 'available',
  location GEOGRAPHY(POINT),
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  user_id UUID REFERENCES users(id),
  messages JSONB DEFAULT '[]',
  state JSONB DEFAULT '{}',
  outcome VARCHAR(50),
  vehicle_reserved UUID REFERENCES vehicles(id),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID REFERENCES vehicles(id) NOT NULL,
  user_id UUID REFERENCES users(id) NOT NULL,
  seller_id UUID REFERENCES sellers(id) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  expires_at TIMESTAMPTZ NOT NULL,
  deposit_required BOOLEAN DEFAULT FALSE,
  deposit_amount INTEGER,
  deposit_paid BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  buyer_id UUID REFERENCES users(id) NOT NULL,
  seller_id UUID REFERENCES sellers(id) NOT NULL,
  vehicle_id UUID REFERENCES vehicles(id) NOT NULL,
  reservation_id UUID REFERENCES reservations(id),
  conversation_id UUID REFERENCES conversations(id),
  package JSONB NOT NULL,
  score INTEGER NOT NULL,
  tier VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'new',
  first_contact_at TIMESTAMPTZ,
  sold_at TIMESTAMPTZ,
  sale_price INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_vehicles_seller ON vehicles(seller_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_price ON vehicles(list_price);
CREATE INDEX idx_vehicles_make_model ON vehicles(make, model);
CREATE INDEX idx_leads_seller ON leads(seller_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_reservations_vehicle ON reservations(vehicle_id);
CREATE INDEX idx_reservations_expires ON reservations(expires_at);
```

---

## 10. API Specifications

### 10.1 REST API Endpoints

#### 10.1.1 Vehicle APIs

```yaml
# Search vehicles
GET /api/v1/vehicles
  Query:
    - q: string (natural language search)
    - make: string[]
    - model: string[]
    - year_min: number
    - year_max: number
    - price_min: number
    - price_max: number
    - body_style: string[]
    - fuel_type: string[]
    - features: string[]
    - sort: 'match' | 'price_asc' | 'price_desc' | 'newest'
    - page: number
    - limit: number
  Response: { vehicles: Vehicle[], total: number, page: number }

# Get vehicle details
GET /api/v1/vehicles/:id
  Response: Vehicle (full details)

# Get similar vehicles
GET /api/v1/vehicles/:id/similar
  Query:
    - limit: number
  Response: { vehicles: Vehicle[] }

# Compare vehicles
POST /api/v1/vehicles/compare
  Body: { vehicleIds: string[] }
  Response: { comparison: ComparisonResult }
```

#### 10.1.2 Conversation APIs

```yaml
# Create conversation
POST /api/v1/conversations
  Body: { sessionId: string, userId?: string }
  Response: { conversationId: string }

# Send message
POST /api/v1/conversations/:id/messages
  Body: { content: string }
  Response: { 
    message: ConversationMessage,
    uiActions: UIAction[] 
  }

# Get conversation history
GET /api/v1/conversations/:id
  Response: Conversation
```

#### 10.1.3 Reservation APIs

```yaml
# Create reservation
POST /api/v1/reservations
  Body: { vehicleId: string, userId: string }
  Response: { reservation: Reservation }

# Get reservation
GET /api/v1/reservations/:id
  Response: Reservation

# Cancel reservation
DELETE /api/v1/reservations/:id
  Response: { success: boolean }
```

#### 10.1.4 Lead APIs (Seller)

```yaml
# Get leads
GET /api/v1/sellers/:sellerId/leads
  Query:
    - status: string[]
    - tier: string[]
    - from: date
    - to: date
    - page: number
  Response: { leads: Lead[], total: number }

# Get lead details
GET /api/v1/leads/:id
  Response: Lead (full package)

# Update lead status
PATCH /api/v1/leads/:id
  Body: { status: string, notes?: string }
  Response: Lead
```

### 10.2 WebSocket Events

```yaml
# Client → Server
ws:join_vehicle - Join vehicle room for updates
ws:leave_vehicle - Leave vehicle room
ws:typing - User typing indicator

# Server → Client
ws:vehicle_update - Vehicle status change (reserved, sold)
ws:viewer_count - Current viewers on vehicle
ws:new_offer - New offer made on vehicle
ws:chat_message - Otto response
ws:ui_action - UI update command
```

---

## 11. Security & Compliance

### 11.1 Authentication & Authorization

- **Buyer Auth**: OAuth 2.0 (Google, Apple, Email magic link)
- **Seller Auth**: Email/password + 2FA required
- **API Auth**: JWT with refresh tokens
- **Role-Based Access**: Buyer, Seller, Admin roles

### 11.2 Data Protection

| Data Type | Protection |
|-----------|------------|
| PII (email, phone) | Encrypted at rest (AES-256) |
| Passwords | bcrypt hashing |
| API Keys | Vault storage |
| Conversations | Encrypted storage |
| Financial Data | PCI DSS compliance |

### 11.3 Privacy Compliance

- **GDPR**: Consent management, data export, deletion rights
- **CCPA**: California consumer privacy compliance
- **Data Retention**: 3-year retention policy, automated deletion

### 11.4 AI Safety

- **Content Filtering**: No generation of harmful content
- **Hallucination Prevention**: All vehicle specs from verified database
- **Bias Mitigation**: Regular audits of recommendation fairness
- **Transparency**: Clear AI disclosure in conversations

---

## 12. Analytics & Reporting

### 12.1 Buyer Analytics

**Session Metrics**:
- Session duration
- Pages per session
- Vehicles viewed
- Search-to-view conversion
- View-to-reservation conversion

**Engagement Metrics**:
- Otto conversation starts
- Messages per conversation
- Preference completion rate
- Feature interaction heatmaps

### 12.2 Seller Analytics

**Lead Metrics**:
- Lead volume by period
- Lead quality distribution
- Response time tracking
- Conversion rates by stage

**Performance Metrics**:
- Listing views
- Reservation rate
- Time-to-sale
- Price realization (vs. list)

### 12.3 Platform Analytics

**Health Metrics**:
- DAU/MAU
- Inventory turnover
- Match accuracy (post-purchase surveys)
- NPS score

**Business Metrics**:
- Revenue per lead
- Customer acquisition cost
- Lifetime value
- Seller retention

---

## 13. Development Phases

### Phase 1: Foundation (Weeks 1-4)

**Milestone: Core Infrastructure & Data Pipeline**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **Database Setup** | Supabase project, schema, RLS policies | Supabase |
| **Auth System** | OAuth (Google, Apple), magic link, user profiles | Supabase Auth |
| **Storage** | Photo/PDF upload, CDN integration | Supabase Storage + Cloudflare |
| **PDF Ingestion** | Condition report parser, structured extraction | OpenRouter Vision |
| **Listing CRUD** | Create, edit, delete listings; seller portal basics | Next.js + Supabase |
| **Vector Store** | pgvector setup, embedding pipeline | Supabase pgvector + OpenRouter |

**Exit Criteria:**
- Can upload a condition report PDF and create a listing
- Listings are embedded and searchable via semantic query
- Basic seller dashboard functional

### Phase 2: Discovery Engine (Weeks 5-8)

**Milestone: Otto AI Core Conversations**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **RAG Pipeline** | Semantic search, hybrid filtering, result ranking | RAG Anything + Supabase |
| **Otto Chat Backend** | Groq integration, prompt engineering, response streaming | Groq API (compound-beta) |
| **Memory System** | User memory CRUD, preference learning, session persistence | Zep Cloud |
| **Chat UI** | Chat widget, message rendering, typing indicators | Next.js + WebSocket |
| **UI Sync** | Real-time grid updates from Otto responses | React + Zustand |

**Exit Criteria:**
- Users can have full conversations with Otto
- Otto remembers users across sessions
- Chat responses trigger UI updates (filtering, highlighting)
- RAG returns relevant vehicles based on natural language

### Phase 3: Buyer Experience (Weeks 9-12)

**Milestone: Full Discovery Flow**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **Search Results Page** | Filter chips, vehicle grid, match badges, sidebar | Next.js + Tailwind |
| **Vehicle Detail Modal** | Image carousel, specs, features, Otto recommendation | React + Framer Motion |
| **Comparison Tool** | Side-by-side compare, spec tables, winner indicators | React |
| **Social Proof** | Real-time viewer counts, activity feed | Supabase Realtime |
| **Reservation System** | Hold vehicle, expiration, confirmation flow | Supabase + Edge Functions |
| **User Accounts** | Profile, saved vehicles, search history | Supabase Auth |

**Exit Criteria:**
- Complete buyer journey from landing to reservation
- Social proof elements showing real-time activity
- Comparison tool functional
- Reservation flow with expiration

### Phase 4: Lead Generation (Weeks 13-16)

**Milestone: Seller Value Delivery**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **Lead Package Assembly** | Full lead package generation from conversation data | Edge Functions |
| **Lead Scoring** | Scoring algorithm, tier assignment | Supabase Functions |
| **Seller Dashboard** | Lead inbox, lead detail view, status tracking | Next.js |
| **Notifications** | Email, SMS, push notifications for new leads | Resend + Twilio |
| **CRM Integration** | Webhook system, Salesforce/HubSpot connectors | Edge Functions |
| **Analytics** | Seller performance metrics, conversion tracking | Supabase + Charts |

**Exit Criteria:**
- Leads delivered to sellers with full playbook
- Seller dashboard functional with inbox and analytics
- At least one CRM integration working
- Notification system delivering alerts

### Phase 5: Scale & Polish (Weeks 17-20)

**Milestone: Production Ready**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **Performance** | Edge caching, image optimization, query optimization | Cloudflare + Vercel |
| **Mobile Polish** | Responsive refinement, PWA, touch optimizations | Next.js |
| **Seller Onboarding** | Guided setup, bulk upload, subscription management | Stripe + Supabase |
| **Dealer API** | Inventory sync, real-time availability | REST API |
| **Monitoring** | Error tracking, performance monitoring, alerting | Sentry + Datadog |
| **A/B Testing** | Conversion optimization framework | PostHog |

**Exit Criteria:**
- Sub-2-second page loads
- Mobile experience polished
- Seller can self-onboard and manage subscription
- Production monitoring in place

### Phase 6: Growth Features (Weeks 21-24)

**Milestone: Market Expansion Ready**

| Component | Deliverables | Tech |
|-----------|--------------|------|
| **Advanced Personalization** | ML-based recommendations, preference prediction | Zep + custom models |
| **Seller Tools** | Pricing recommendations, competitive analysis | Groq + analytics |
| **Social Features** | Share vehicles, reviews, community activity | Supabase |
| **Multi-language** | i18n support for Spanish (initial) | next-intl |
| **Advanced Analytics** | Cohort analysis, funnel optimization, attribution | Custom + BI tools |

**Exit Criteria:**
- Advanced personalization improving match rates
- Seller tools providing actionable insights
- Ready for geographic expansion

---

## 14. Success Metrics

### 14.1 North Star Metrics

| Metric | Target (6 months) | Target (12 months) |
|--------|-------------------|---------------------|
| Monthly Active Buyers | 50,000 | 250,000 |
| Monthly Leads Generated | 2,500 | 15,000 |
| Lead-to-Sale Conversion | 12% | 18% |
| Seller Retention | 85% | 90% |

### 14.2 Product Quality Metrics

| Metric | Target |
|--------|--------|
| Buyer NPS | > 60 |
| Seller NPS | > 50 |
| Otto Conversation Completion Rate | > 70% |
| Match Accuracy (post-purchase survey) | > 85% |
| Average Session Duration | > 8 minutes |

### 14.3 Operational Metrics

| Metric | Target |
|--------|--------|
| API Uptime | 99.9% |
| Page Load Time | < 2s |
| Otto Response Time | < 2s |
| Lead Delivery Time | < 1 minute |
| Support Ticket Resolution | < 24 hours |

---

## 15. Appendices

### Appendix A: Conversation Example Scripts

**See attached document**: `Otto_AI_Discovery_Chat_Sessions.md` for complete conversation flows including:
- Pamela: Luxury EV, Range-Focused, Dark Colors
- John: Performance SUV, Budget-Conscious
- Sarah: Ultra-Luxury, Tech-Forward
- Mike: Family SUV, Practical Features
- Lisa: Sports Car, Design-Forward
- Alex: First-Time EV Buyer, Value-Focused

### Appendix B: UI Component Reference

**See attached screenshots**:
- `Otto_Vehicle_Details_With_Carousel.png`: Vehicle detail modal
- `1764256631030.png`: Main search results grid

### Appendix C: Condition Report Sample

**See attached**: `2022LexusES350117484.pdf` for example vehicle condition report showing:
- VIN: 58ADZ1B17NU117484
- Vehicle: 2022 Lexus ES ES 350
- Condition Score: 4.3 (Clean)
- Issues: 3 exterior, 1 mechanical, 1 tires/wheels
- Full inspection breakdown

### Appendix D: Vehicle Features Taxonomy

**Feature Categories**:
- Drivetrain: AWD, FWD, RWD, 4WD
- Fuel: EV, Hybrid, PHEV, Gas, Diesel
- Performance: Sport Mode, Launch Control, Performance Package
- Safety: Premium Safety, ADAS, Blind Spot Monitor, 360 Camera
- Technology: FSD, Super Cruise, Autopilot, Advanced Tech
- Comfort: Premium Comfort, Heated Seats, Ventilated Seats, Massage
- Luxury: Premium Interior, Leather, Wood Trim
- Space: Spacious, Third Row, Panoramic Roof

### Appendix E: Glossary

| Term | Definition |
|------|------------|
| **Otto Concierge** | AI-powered conversational assistant |
| **Match %** | Algorithm-generated preference match score |
| **Lead Package** | Complete buyer intelligence delivered to seller |
| **Reservation Hold** | Temporary lock on vehicle (default 48 hours) |
| **Social Proof** | Real-time activity indicators (viewers, offers) |
| **Condition Report** | Standardized vehicle inspection document |

---

## 16. BMAD Method & Claude Code Integration

### 16.1 Project Structure for BMAD

This PRD is designed to work with the BMAD (Build, Measure, Analyze, Decide) methodology and Claude Code for implementation. The following structure is recommended:

```
otto-ai/
├── .bmad/
│   ├── PRD.md                    # This document
│   ├── architecture.md           # Detailed architecture decisions
│   ├── decisions/                # Architecture Decision Records (ADRs)
│   └── sprints/                  # Sprint planning documents
│
├── apps/
│   ├── web/                      # Next.js frontend
│   │   ├── app/                  # App Router pages
│   │   ├── components/           # React components
│   │   ├── lib/                  # Utilities, API clients
│   │   └── styles/               # Tailwind config, globals
│   │
│   └── seller-dashboard/         # Seller portal (could be same app or separate)
│
├── packages/
│   ├── database/                 # Supabase schema, migrations, types
│   ├── ai/                       # AI service integrations
│   │   ├── groq/                 # Groq client, prompts
│   │   ├── openrouter/           # OpenRouter client
│   │   ├── zep/                  # Zep memory client
│   │   └── rag/                  # RAG pipeline
│   ├── shared/                   # Shared types, utilities
│   └── ui/                       # Shared UI components
│
├── supabase/
│   ├── migrations/               # Database migrations
│   ├── functions/                # Edge functions
│   └── seed.sql                  # Seed data
│
└── docs/
    ├── api/                      # API documentation
    ├── guides/                   # Developer guides
    └── runbooks/                 # Operational runbooks
```

### 16.2 Claude Code Task Breakdown

When using Claude Code, break tasks into focused units:

#### Foundation Tasks (Phase 1)
```
Task: Setup Supabase Project
- Create Supabase project
- Configure environment variables
- Setup RLS policies template
- Test connection from Next.js

Task: Vehicle Schema
- Create vehicles table with all fields
- Add pgvector extension
- Create vehicle_embeddings table
- Add indexes for common queries

Task: PDF Ingestion Pipeline
- Create upload endpoint
- Integrate OpenRouter Vision
- Parse condition report structure
- Store extracted data
- Generate embedding
```

#### AI Integration Tasks (Phase 2)
```
Task: Groq Integration
- Setup Groq client
- Create Otto system prompt
- Implement streaming responses
- Handle function calling for UI updates

Task: Zep Memory Integration
- Setup Zep client
- Define memory schema
- Implement memory retrieval on conversation start
- Implement memory updates after messages

Task: RAG Pipeline
- Create embedding generation function
- Implement hybrid search (semantic + filters)
- Build result ranking logic
- Connect to Groq context
```

### 16.3 Environment Variables Template

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Groq
GROQ_API_KEY=

# OpenRouter
OPENROUTER_API_KEY=

# Zep Cloud
ZEP_API_KEY=
ZEP_PROJECT_ID=

# Cloudflare
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_API_TOKEN=

# Optional: CRM Integrations
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
HUBSPOT_API_KEY=

# Optional: Notifications
RESEND_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
```

### 16.4 Key Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Monorepo** | Yes (Turborepo) | Shared types, easier refactoring |
| **Styling** | Tailwind + shadcn/ui | Rapid development, consistent design |
| **State Management** | Zustand (client) + React Query (server) | Simple, performant |
| **Real-time** | Supabase Realtime + WebSocket | Built-in with Supabase |
| **Auth** | Supabase Auth | Integrated with RLS |
| **Deployment** | Vercel (web) + Supabase (backend) | Optimal for Next.js |
| **Error Tracking** | Sentry | Industry standard |
| **Analytics** | PostHog | Privacy-focused, self-hostable |

### 16.5 Testing Strategy

```
Unit Tests: Vitest
- AI prompt functions
- RAG query building
- Lead scoring algorithm
- Utility functions

Integration Tests: Playwright
- Full conversation flows
- Reservation process
- Lead delivery

E2E Tests: Playwright
- Buyer journey: landing → reservation
- Seller journey: upload → lead received
- Cross-browser testing
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 2025 | Otto.AI Team | Initial PRD |
| 2.0 | Nov 2025 | Otto.AI Team | Updated tech stack (Groq, OpenRouter, Zep, Supabase), dual-customer model, enhanced lead packages |

---

*This document serves as the foundational specification for Otto.AI development. It is designed to work with the BMAD Method for project management and Claude Code for AI-assisted implementation.*