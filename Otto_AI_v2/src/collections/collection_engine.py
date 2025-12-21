"""
Otto.AI Collection Engine

Implements Story 1.7: Add Curated Vehicle Collections and Categories
Core engine for dynamic collection generation and vehicle ranking

Features:
- Rule-based collection generation from templates
- Multi-factor vehicle scoring and ranking
- Automatic collection refresh on inventory changes
- Template management for different use cases
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import uuid
import psycopg
from psycopg.rows import dict_row
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class CollectionType(Enum):
    """Collection types"""
    CURATED = "curated"
    TRENDING = "trending"
    DYNAMIC = "dynamic"
    TEMPLATE = "template"

class ScoringFactor(Enum):
    """Scoring factors for vehicle ranking"""
    RELEVANCE = "relevance"
    PRICE = "price"
    POPULARITY = "popularity"
    MILEAGE = "mileage"
    YEAR = "year"
    LOCATION = "location"

@dataclass
class CollectionCriteria:
    """Collection criteria data model"""
    vehicle_type: Optional[str] = None
    fuel_type: Optional[Union[str, List[str]]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    mileage_max: Optional[int] = None
    make: Optional[Union[str, List[str]]] = None
    model: Optional[str] = None
    features: Optional[List[str]] = None
    location: Optional[str] = None
    seats_min: Optional[int] = None
    safety_rating_min: Optional[int] = None
    fuel_efficiency_min: Optional[float] = None
    horsepower_min: Optional[int] = None
    drive_type: Optional[str] = None
    custom_rules: Optional[Dict[str, Any]] = field(default_factory=dict)

@dataclass
class Collection:
    """Collection data model"""
    id: str
    name: str
    description: Optional[str]
    type: CollectionType
    criteria: CollectionCriteria
    vehicle_ids: List[str]
    scores: Dict[str, float]  # vehicle_id -> score
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

@dataclass
class CollectionTemplate:
    """Collection template data model"""
    id: str
    name: str
    description: Optional[str]
    template_type: str
    criteria_template: Dict[str, Any]
    is_active: bool = True

class CollectionEngine:
    """
    Core engine for managing vehicle collections
    """

    def __init__(self):
        """Initialize collection engine"""
        self.db_conn = None
        self._templates_cache: Dict[str, CollectionTemplate] = {}
        self._cache_ttl = 300  # 5 minutes

    async def initialize(self, supabase_url: str, supabase_key: str) -> bool:
        """
        Initialize database connection

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anonymous key

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to Supabase
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string, autocommit=True)

            # Initialize database schema
            await self._initialize_schema()

            # Load templates into cache
            await self._refresh_templates_cache()

            logger.info("CollectionEngine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CollectionEngine: {e}")
            return False

    async def _initialize_schema(self):
        """Initialize database schema if not exists"""
        try:
            # Read and execute schema file
            schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute schema
            with self.db_conn.cursor() as cur:
                cur.execute(schema_sql)

            logger.info("Database schema initialized")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    async def _refresh_templates_cache(self):
        """Refresh templates cache from database"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT id, name, description, template_type, criteria_template, is_active
                    FROM collection_templates
                    WHERE is_active = TRUE
                """)

                self._templates_cache = {}
                for row in cur.fetchall():
                    template = CollectionTemplate(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        template_type=row['template_type'],
                        criteria_template=row['criteria_template'],
                        is_active=row['is_active']
                    )
                    self._templates_cache[row['name']] = template

            logger.info(f"Loaded {len(self._templates_cache)} templates into cache")

        except Exception as e:
            logger.error(f"Failed to refresh templates cache: {e}")

    async def create_collection(
        self,
        name: str,
        description: Optional[str],
        collection_type: CollectionType,
        criteria: CollectionCriteria,
        created_by: Optional[str] = None
    ) -> str:
        """
        Create a new collection

        Args:
            name: Collection name
            description: Collection description
            collection_type: Type of collection
            criteria: Collection criteria
            created_by: Admin user ID

        Returns:
            Collection ID
        """
        try:
            collection_id = str(uuid.uuid4())
            criteria_json = json.dumps(criteria.__dict__, default=str)

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vehicle_collections
                    (id, name, description, type, criteria, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (collection_id, name, description, collection_type.value, criteria_json, created_by))

            # Generate collection with vehicles
            await self._generate_collection_vehicles(collection_id, criteria)

            logger.info(f"Created collection: {collection_id}")
            return collection_id

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def _generate_collection_vehicles(self, collection_id: str, criteria: CollectionCriteria):
        """Generate vehicle mappings for a collection based on criteria"""
        try:
            # Build query based on criteria
            query, params = self._build_vehicle_query(criteria)

            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get matching vehicles
                cur.execute(query, params)
                vehicles = cur.fetchall()

                # Score and rank vehicles
                scored_vehicles = await self._score_vehicles(vehicles, criteria)

                # Insert into mapping table
                for i, (vehicle_id, score) in enumerate(scored_vehicles):
                    cur.execute("""
                        INSERT INTO collection_vehicle_mappings
                        (collection_id, vehicle_id, score, rank_position)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (collection_id, vehicle_id) DO UPDATE
                        SET score = EXCLUDED.score, rank_position = EXCLUDED.rank_position
                    """, (collection_id, vehicle_id, score, i + 1))

            logger.info(f"Added {len(scored_vehicles)} vehicles to collection {collection_id}")

        except Exception as e:
            logger.error(f"Failed to generate collection vehicles: {e}")
            raise

    def _build_vehicle_query(self, criteria: CollectionCriteria) -> Tuple[str, List]:
        """Build SQL query based on collection criteria"""
        query_parts = ["SELECT id FROM vehicles WHERE 1=1"]
        params = []

        # Add filters
        if criteria.vehicle_type:
            query_parts.append("AND vehicle_type = %s")
            params.append(criteria.vehicle_type)

        if criteria.fuel_type:
            if isinstance(criteria.fuel_type, list):
                placeholders = ','.join(['%s'] * len(criteria.fuel_type))
                query_parts.append(f"AND fuel_type = ANY(ARRAY[{placeholders}])")
                params.extend(criteria.fuel_type)
            else:
                query_parts.append("AND fuel_type = %s")
                params.append(criteria.fuel_type)

        if criteria.price_min:
            query_parts.append("AND price >= %s")
            params.append(criteria.price_min)

        if criteria.price_max:
            query_parts.append("AND price <= %s")
            params.append(criteria.price_max)

        if criteria.year_min:
            query_parts.append("AND year >= %s")
            params.append(criteria.year_min)

        if criteria.year_max:
            query_parts.append("AND year <= %s")
            params.append(criteria.year_max)

        if criteria.mileage_max:
            query_parts.append("AND mileage <= %s")
            params.append(criteria.mileage_max)

        if criteria.make:
            if isinstance(criteria.make, list):
                placeholders = ','.join(['%s'] * len(criteria.make))
                query_parts.append(f"AND make = ANY(ARRAY[{placeholders}])")
                params.extend(criteria.make)
            else:
                query_parts.append("AND make = %s")
                params.append(criteria.make)

        # Add ordering
        query_parts.append("ORDER BY created_at DESC LIMIT 1000")  # Limit for performance

        return ' '.join(query_parts), params

    async def _score_vehicles(
        self,
        vehicles: List[Dict[str, Any]],
        criteria: CollectionCriteria
    ) -> List[Tuple[str, float]]:
        """Score vehicles based on multiple factors"""
        scored_vehicles = []

        for vehicle in vehicles:
            score = 0.0
            factors = {}

            # Price scoring (lower is better for budget collections)
            if criteria.price_max and vehicle.get('price'):
                price_score = 1.0 - (vehicle['price'] / criteria.price_max)
                factors['price'] = price_score
                score += price_score * 0.3

            # Year scoring (newer is better)
            if vehicle.get('year'):
                current_year = datetime.now().year
                year_score = min(1.0, vehicle['year'] / current_year)
                factors['year'] = year_score
                score += year_score * 0.2

            # Mileage scoring (lower is better)
            if criteria.mileage_max and vehicle.get('mileage'):
                mileage_score = 1.0 - (vehicle['mileage'] / criteria.mileage_max)
                factors['mileage'] = mileage_score
                score += mileage_score * 0.2

            # Default scoring
            if not factors:
                score = 0.5  # Neutral score

            scored_vehicles.append((vehicle['id'], score))

        # Sort by score (descending)
        scored_vehicles.sort(key=lambda x: x[1], reverse=True)

        return scored_vehicles

    async def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID"""
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get collection details
                cur.execute("""
                    SELECT id, name, description, type, criteria, created_at, updated_at
                    FROM vehicle_collections
                    WHERE id = %s AND is_active = TRUE
                """, (collection_id,))

                collection_row = cur.fetchone()
                if not collection_row:
                    return None

                # Get vehicles in collection
                cur.execute("""
                    SELECT vehicle_id, score, rank_position
                    FROM collection_vehicle_mappings
                    WHERE collection_id = %s
                    ORDER BY rank_position
                """, (collection_id,))

                mappings = cur.fetchall()

                # Build collection object
                criteria_dict = json.loads(collection_row['criteria'])
                criteria = CollectionCriteria(**criteria_dict)

                collection = Collection(
                    id=collection_row['id'],
                    name=collection_row['name'],
                    description=collection_row['description'],
                    type=CollectionType(collection_row['type']),
                    criteria=criteria,
                    vehicle_ids=[m['vehicle_id'] for m in mappings],
                    scores={m['vehicle_id']: m['score'] for m in mappings},
                    metadata={'vehicle_count': len(mappings)},
                    created_at=collection_row['created_at'],
                    updated_at=collection_row['updated_at']
                )

                return collection

        except Exception as e:
            logger.error(f"Failed to get collection {collection_id}: {e}")
            return None

    async def get_collections(
        self,
        collection_type: Optional[CollectionType] = None,
        featured_only: bool = False,
        limit: int = 50
    ) -> List[Collection]:
        """Get collections with optional filtering"""
        try:
            query_parts = ["SELECT id FROM vehicle_collections WHERE is_active = TRUE"]
            params = []

            if collection_type:
                query_parts.append("AND type = %s")
                params.append(collection_type.value)

            if featured_only:
                query_parts.append("AND is_featured = TRUE")
                params.append(True)

            query_parts.append("ORDER BY sort_order, created_at DESC LIMIT %s")
            params.append(limit)

            with self.db_conn.cursor() as cur:
                cur.execute(' '.join(query_parts), params)
                collection_ids = [row[0] for row in cur.fetchall()]

            # Get full collection objects
            collections = []
            for collection_id in collection_ids:
                collection = await self.get_collection(collection_id)
                if collection:
                    collections.append(collection)

            return collections

        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []

    async def get_trending_collections(self, limit: int = 10) -> List[Collection]:
        """Get trending collections based on engagement"""
        try:
            # Get collections with highest engagement in last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, COUNT(ca.id) as engagement_count
                    FROM vehicle_collections c
                    LEFT JOIN collection_analytics ca ON c.id = ca.collection_id
                    WHERE c.is_active = TRUE
                    AND c.type = 'trending'
                    AND (ca.created_at >= %s OR ca.created_at IS NULL)
                    GROUP BY c.id
                    ORDER BY engagement_count DESC, c.created_at DESC
                    LIMIT %s
                """, (week_ago, limit))

                collection_ids = [row[0] for row in cur.fetchall()]

            # Get full collection objects
            collections = []
            for collection_id in collection_ids:
                collection = await self.get_collection(collection_id)
                if collection:
                    collections.append(collection)

            return collections

        except Exception as e:
            logger.error(f"Failed to get trending collections: {e}")
            return []

    async def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        criteria: Optional[CollectionCriteria] = None,
        sort_order: Optional[int] = None,
        is_featured: Optional[bool] = None
    ) -> bool:
        """Update collection details"""
        try:
            update_parts = []
            params = []

            if name:
                update_parts.append("name = %s")
                params.append(name)

            if description is not None:
                update_parts.append("description = %s")
                params.append(description)

            if criteria:
                criteria_json = json.dumps(criteria.__dict__, default=str)
                update_parts.append("criteria = %s")
                params.append(criteria_json)

            if sort_order is not None:
                update_parts.append("sort_order = %s")
                params.append(sort_order)

            if is_featured is not None:
                update_parts.append("is_featured = %s")
                params.append(is_featured)

            if not update_parts:
                return True  # No updates needed

            update_parts.append("updated_at = NOW()")
            params.append(collection_id)

            with self.db_conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE vehicle_collections
                    SET {', '.join(update_parts)}
                    WHERE id = %s
                """, params)

            # Regenerate vehicles if criteria changed
            if criteria:
                # Clear existing mappings
                cur.execute("""
                    DELETE FROM collection_vehicle_mappings
                    WHERE collection_id = %s
                """, (collection_id,))

                # Generate new mappings
                await self._generate_collection_vehicles(collection_id, criteria)

            logger.info(f"Updated collection {collection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update collection {collection_id}: {e}")
            return False

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection (soft delete by setting is_active = False)"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE vehicle_collections
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE id = %s
                """, (collection_id,))

            logger.info(f"Deleted collection {collection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection {collection_id}: {e}")
            return False

    async def refresh_all_dynamic_collections(self):
        """Refresh all dynamic and template-based collections"""
        try:
            with self.db_conn.cursor() as cur:
                # Get all dynamic and template collections
                cur.execute("""
                    SELECT id, criteria, type
                    FROM vehicle_collections
                    WHERE is_active = TRUE
                    AND type IN ('dynamic', 'template')
                """)

                collections = cur.fetchall()

            for collection_id, criteria_json, collection_type in collections:
                criteria_dict = json.loads(criteria_json)
                criteria = CollectionCriteria(**criteria_dict)

                # Clear existing mappings
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM collection_vehicle_mappings
                        WHERE collection_id = %s
                    """, (collection_id,))

                # Generate new mappings
                await self._generate_collection_vehicles(collection_id, criteria)

                # Update last refreshed timestamp
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        UPDATE vehicle_collections
                        SET last_refreshed_at = NOW()
                        WHERE id = %s
                    """, (collection_id,))

            logger.info(f"Refreshed {len(collections)} dynamic collections")

        except Exception as e:
            logger.error(f"Failed to refresh dynamic collections: {e}")

    async def generate_collection_from_template(
        self,
        template_name: str,
        collection_name: str,
        description: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate a collection from a template"""
        try:
            # Get template
            template = self._templates_cache.get(template_name)
            if not template:
                # Try loading from database
                await self._refresh_templates_cache()
                template = self._templates_cache.get(template_name)

            if not template:
                logger.error(f"Template not found: {template_name}")
                return None

            # Process template variables
            criteria_dict = template.criteria_template.copy()
            if template_variables:
                for key, value in template_variables.items():
                    if f"${{{key}}}" in str(criteria_dict):
                        # Simple string replacement
                        criteria_str = json.dumps(criteria_dict)
                        criteria_str = criteria_str.replace(f"${{{key}}}", str(value))
                        criteria_dict = json.loads(criteria_str)

            # Create criteria object
            criteria = CollectionCriteria(**criteria_dict)

            # Create collection
            collection_id = await self.create_collection(
                name=collection_name,
                description=description or template.description,
                collection_type=CollectionType.TEMPLATE,
                criteria=criteria
            )

            logger.info(f"Generated collection {collection_id} from template {template_name}")
            return collection_id

        except Exception as e:
            logger.error(f"Failed to generate collection from template: {e}")
            return None