"""
Vehicle Database Service
Handles vehicle embedding storage, retrieval, and semantic tag management
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import os
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

logger = logging.getLogger(__name__)

class VehicleDatabaseService:
    """
    Service for managing vehicle embeddings and semantic tags in Supabase PostgreSQL
    Provides optimized storage, retrieval, and similarity search for vehicle data
    """

    def __init__(self, embedding_dim: int = 1536):
        """
        Initialize vehicle database service

        Args:
            embedding_dim: Dimension of embedding vectors (default 1536 for HNSW compatibility)
        """
        self.db_conn = None
        self.embedding_dim = embedding_dim

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
            # Connect to Supabase using proper connection string format
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)
            register_vector(self.db_conn)

            logger.info("✅ Vehicle Database Service connected to Supabase")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Vehicle Database Service: {e}")
            return False

    async def store_vehicle_embedding(
        self,
        vehicle_id: str,
        embedding: List[float],
        semantic_tags: List[str],
        vehicle_make: Optional[str] = None,
        vehicle_model: Optional[str] = None,
        vehicle_year: Optional[int] = None,
        price_range: Optional[str] = None,
        text_embedding: Optional[List[float]] = None,
        image_count: int = 0,
        metadata_processed: bool = False
    ) -> bool:
        """
        Store vehicle embedding with comprehensive error handling and retry logic

        Args:
            vehicle_id: Unique vehicle identifier
            embedding: Combined vehicle embedding vector
            semantic_tags: List of semantic tags for the vehicle
            vehicle_make: Vehicle manufacturer
            vehicle_model: Vehicle model
            vehicle_year: Vehicle year
            price_range: Price range category
            text_embedding: Text-only embedding (optional)
            image_count: Number of images processed
            metadata_processed: Whether metadata was successfully processed

        Returns:
            True if storage successful, False otherwise
        """
        max_retries = 3
        retry_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                # Validate inputs
                if not vehicle_id or not isinstance(vehicle_id, str):
                    raise ValueError("vehicle_id must be a non-empty string")

                if not embedding or len(embedding) != self.embedding_dim:
                    raise ValueError(f"Embedding must be a list of {self.embedding_dim} floats")

                if not isinstance(semantic_tags, list):
                    raise ValueError("semantic_tags must be a list")

                # Convert embedding to PostgreSQL vector format
                embedding_str = f"[{','.join(map(str, embedding))}]"
                text_embedding_str = None
                if text_embedding and len(text_embedding) == self.embedding_dim:
                    text_embedding_str = f"[{','.join(map(str, text_embedding))}]"

                with self.db_conn.cursor() as cursor:
                    # Check if vehicle already exists
                    cursor.execute(
                        "SELECT id FROM vehicle_embeddings WHERE vehicle_id = %s",
                        (vehicle_id,)
                    )
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing record
                        update_query = """
                            UPDATE vehicle_embeddings
                            SET embedding = %s::vector,
                                semantic_tags = %s,
                                text_embedding = %s::vector,
                                image_count = %s,
                                metadata_processed = %s,
                                updated_at = NOW()
                            WHERE vehicle_id = %s
                        """
                        cursor.execute(update_query, (
                            embedding_str,
                            semantic_tags,
                            text_embedding_str,
                            image_count,
                            metadata_processed,
                            vehicle_id
                        ))
                        logger.info(f"✅ Updated embedding for vehicle: {vehicle_id}")
                    else:
                        # Insert new record
                        insert_query = """
                            INSERT INTO vehicle_embeddings
                            (vehicle_id, embedding, semantic_tags, vehicle_make, vehicle_model,
                             vehicle_year, price_range, text_embedding, image_count, metadata_processed)
                            VALUES (%s::vector, %s::vector, %s, %s, %s, %s, %s, %s::vector, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            vehicle_id,
                            embedding_str,
                            semantic_tags,
                            vehicle_make,
                            vehicle_model,
                            vehicle_year,
                            price_range,
                            text_embedding_str,
                            image_count,
                            metadata_processed
                        ))
                        logger.info(f"✅ Stored new embedding for vehicle: {vehicle_id}")

                    self.db_conn.commit()
                    return True

            except psycopg2.Error as e:
                self.db_conn.rollback()
                logger.error(f"❌ Database error storing embedding for {vehicle_id} (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to store embedding for {vehicle_id} after {max_retries} attempts")
                    return False

            except ValueError as e:
                logger.error(f"❌ Validation error for {vehicle_id}: {e}")
                return False

            except Exception as e:
                logger.error(f"❌ Unexpected error storing embedding for {vehicle_id}: {e}")
                return False

        return False

    async def get_vehicle_embedding(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve vehicle embedding and metadata

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            Dictionary with vehicle data or None if not found
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, vehicle_id, embedding, semantic_tags, vehicle_make, vehicle_model,
                           vehicle_year, price_range, text_embedding, image_count, metadata_processed,
                           created_at, updated_at
                    FROM vehicle_embeddings
                    WHERE vehicle_id = %s
                """
                cursor.execute(query, (vehicle_id,))
                result = cursor.fetchone()

                if result:
                    # Convert RealDictRow to regular dict
                    vehicle_data = dict(result)
                    logger.debug(f"✅ Retrieved embedding for vehicle: {vehicle_id}")
                    return vehicle_data
                else:
                    logger.info(f"ℹ️ No embedding found for vehicle: {vehicle_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error retrieving embedding for {vehicle_id}: {e}")
            return None

    async def search_similar_vehicles(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        vehicle_make: Optional[str] = None,
        vehicle_year_range: Optional[Tuple[int, int]] = None,
        price_range: Optional[str] = None,
        required_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vehicles using vector similarity with optional filters

        Args:
            query_embedding: Embedding vector to search against
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            vehicle_make: Filter by vehicle make
            vehicle_year_range: Filter by year range (min_year, max_year)
            price_range: Filter by price range
            required_tags: Vehicles must have all these semantic tags

        Returns:
            List of similar vehicles with similarity scores
        """
        try:
            if not query_embedding or len(query_embedding) != self.embedding_dim:
                raise ValueError(f"Query embedding must have {self.embedding_dim} dimensions")

            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build dynamic query with filters
                base_query = """
                    SELECT
                        id, vehicle_id, vehicle_make, vehicle_model, vehicle_year,
                        price_range, semantic_tags, image_count, metadata_processed,
                        1 - (embedding <=> %s::vector) as similarity_score
                    FROM vehicle_embeddings
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                """

                params = [embedding_str, embedding_str, similarity_threshold]
                param_count = 3

                # Add optional filters
                if vehicle_make:
                    base_query += f" AND vehicle_make = ${param_count + 1}"
                    params.append(vehicle_make)
                    param_count += 1

                if vehicle_year_range:
                    base_query += f" AND vehicle_year BETWEEN ${param_count + 1} AND ${param_count + 2}"
                    params.extend(vehicle_year_range)
                    param_count += 2

                if price_range:
                    base_query += f" AND price_range = ${param_count + 1}"
                    params.append(price_range)
                    param_count += 1

                if required_tags:
                    # Use GIN index for efficient tag filtering
                    for i, tag in enumerate(required_tags):
                        base_query += f" AND ${param_count + 1} = ANY(semantic_tags)"
                        params.append(tag)
                        param_count += 1

                # Order by similarity and limit results
                base_query += f" ORDER BY similarity_score DESC LIMIT ${param_count + 1}"
                params.append(limit)

                cursor.execute(base_query, params)
                results = cursor.fetchall()

                # Convert to list of dicts
                similar_vehicles = [dict(row) for row in results]

                logger.info(f"✅ Found {len(similar_vehicles)} similar vehicles with threshold {similarity_threshold}")
                return similar_vehicles

        except Exception as e:
            logger.error(f"❌ Error searching similar vehicles: {e}")
            return []

    async def search_by_semantic_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search vehicles by semantic tags

        Args:
            tags: List of tags to search for
            match_all: If True, vehicles must have all tags. If False, any tag match
            limit: Maximum number of results

        Returns:
            List of vehicles matching the semantic tags
        """
        try:
            if not tags:
                return []

            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if match_all:
                    # Vehicles must have all specified tags
                    query = """
                        SELECT vehicle_id, vehicle_make, vehicle_model, vehicle_year,
                               price_range, semantic_tags, image_count
                        FROM vehicle_embeddings
                        WHERE %s = ALL(semantic_tags)
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (tags, limit))
                else:
                    # Vehicles can have any of the specified tags
                    query = """
                        SELECT vehicle_id, vehicle_make, vehicle_model, vehicle_year,
                               price_range, semantic_tags, image_count
                        FROM vehicle_embeddings
                        WHERE semantic_tags && %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (tags, limit))

                results = cursor.fetchall()
                vehicles = [dict(row) for row in results]

                logger.info(f"✅ Found {len(vehicles)} vehicles matching tags {tags} (match_all={match_all})")
                return vehicles

        except Exception as e:
            logger.error(f"❌ Error searching by semantic tags: {e}")
            return []

    async def get_popular_semantic_tags(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get most popular semantic tags across all vehicles

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of tags with usage counts
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT tag, COUNT(*) as vehicle_count
                    FROM (
                        SELECT unnest(semantic_tags) as tag
                        FROM vehicle_embeddings
                    ) tag_counts
                    GROUP BY tag
                    ORDER BY vehicle_count DESC, tag ASC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                results = cursor.fetchall()

                popular_tags = [dict(row) for row in results]
                logger.info(f"✅ Retrieved {len(popular_tags)} popular semantic tags")
                return popular_tags

        except Exception as e:
            logger.error(f"❌ Error getting popular semantic tags: {e}")
            return []

    async def update_vehicle_tags(
        self,
        vehicle_id: str,
        new_tags: List[str],
        merge_with_existing: bool = True
    ) -> bool:
        """
        Update semantic tags for a vehicle

        Args:
            vehicle_id: Vehicle identifier
            new_tags: New tags to add or set
            merge_with_existing: If True, merge with existing tags. If False, replace all tags

        Returns:
            True if update successful, False otherwise
        """
        try:
            with self.db_conn.cursor() as cursor:
                if merge_with_existing:
                    # Merge with existing tags
                    query = """
                        UPDATE vehicle_embeddings
                        SET semantic_tags = array_cat(
                            array_remove(semantic_tags, %s), %s
                        ),
                        updated_at = NOW()
                        WHERE vehicle_id = %s
                    """
                    cursor.execute(query, (new_tags[0] if new_tags else '', new_tags, vehicle_id))
                else:
                    # Replace all tags
                    query = """
                        UPDATE vehicle_embeddings
                        SET semantic_tags = %s, updated_at = NOW()
                        WHERE vehicle_id = %s
                    """
                    cursor.execute(query, (new_tags, vehicle_id))

                self.db_conn.commit()
                affected_rows = cursor.rowcount

                if affected_rows > 0:
                    logger.info(f"✅ Updated tags for vehicle {vehicle_id} (merge={merge_with_existing})")
                    return True
                else:
                    logger.info(f"ℹ️ Vehicle {vehicle_id} not found for tag update")
                    return False

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"❌ Error updating tags for vehicle {vehicle_id}: {e}")
            return False

    async def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                stats = {}

                # Total vehicles
                cursor.execute("SELECT COUNT(*) as total_vehicles FROM vehicle_embeddings")
                stats['total_vehicles'] = cursor.fetchone()['total_vehicles']

                # Vehicles with images
                cursor.execute("SELECT COUNT(*) as vehicles_with_images FROM vehicle_embeddings WHERE image_count > 0")
                stats['vehicles_with_images'] = cursor.fetchone()['vehicles_with_images']

                # Average image count
                cursor.execute("SELECT AVG(image_count) as avg_image_count FROM vehicle_embeddings WHERE image_count > 0")
                result = cursor.fetchone()
                stats['avg_image_count'] = float(result['avg_image_count']) if result['avg_image_count'] else 0

                # Popular makes
                cursor.execute("""
                    SELECT vehicle_make, COUNT(*) as count
                    FROM vehicle_embeddings
                    WHERE vehicle_make IS NOT NULL
                    GROUP BY vehicle_make
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats['popular_makes'] = [dict(row) for row in cursor.fetchall()]

                # Year distribution
                cursor.execute("""
                    SELECT vehicle_year, COUNT(*) as count
                    FROM vehicle_embeddings
                    WHERE vehicle_year IS NOT NULL
                    GROUP BY vehicle_year
                    ORDER BY vehicle_year DESC
                """)
                stats['year_distribution'] = [dict(row) for row in cursor.fetchall()]

                # Tag statistics
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT vehicle_id) as vehicles_with_tags,
                        COUNT(DISTINCT unnest(semantic_tags)) as unique_tags,
                        AVG(array_length(semantic_tags, 1)) as avg_tags_per_vehicle
                    FROM vehicle_embeddings
                    WHERE semantic_tags IS NOT NULL AND array_length(semantic_tags, 1) > 0
                """)
                result = cursor.fetchone()
                if result:
                    stats['vehicles_with_tags'] = result['vehicles_with_tags']
                    stats['unique_tags'] = result['unique_tags']
                    stats['avg_tags_per_vehicle'] = float(result['avg_tags_per_vehicle']) if result['avg_tags_per_vehicle'] else 0

                logger.info("✅ Database statistics retrieved successfully")
                return stats

        except Exception as e:
            logger.error(f"❌ Error getting database statistics: {e}")
            return {}

    async def delete_vehicle_embedding(self, vehicle_id: str) -> bool:
        """
        Delete vehicle embedding from database

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM vehicle_embeddings WHERE vehicle_id = %s",
                    (vehicle_id,)
                )
                affected_rows = cursor.rowcount
                self.db_conn.commit()

                if affected_rows > 0:
                    logger.info(f"✅ Deleted embedding for vehicle: {vehicle_id}")
                    return True
                else:
                    logger.info(f"ℹ️ Vehicle {vehicle_id} not found for deletion")
                    return False

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"❌ Error deleting embedding for vehicle {vehicle_id}: {e}")
            return False

    async def hybrid_search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector similarity with traditional filters

        Story 3-7 Updates:
        - Added multi-select support for makes and vehicle_types arrays
        - Uses effective_price (asking > auction > estimated) for price filtering
        - Handles NULL prices correctly (excludes from price ranges, sorts last)

        Args:
            query_embedding: Query embedding vector for similarity search
            filters: Dictionary of traditional filters including:
                - make (str): Single make filter (backward compatibility)
                - makes (List[str]): Multi-select makes filter
                - vehicle_type (str): Single vehicle type filter (backward compatibility)
                - vehicle_types (List[str]): Multi-select vehicle types filter
                - model, year_min, year_max, price_min, price_max, mileage_max
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            sort_by: Sort field ('relevance', 'price', 'year', 'mileage')
            sort_order: Sort order ('asc', 'desc')

        Returns:
            Dictionary with search results and metadata
        """
        try:
            if not self.db_conn:
                raise RuntimeError("Database connection not initialized")

            if not query_embedding or len(query_embedding) != self.embedding_dim:
                raise ValueError(f"Query embedding must have {self.embedding_dim} dimensions")

            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Build the hybrid search query
            base_query = """
                WITH similarity_results AS (
                    SELECT
                        ve.id,
                        ve.vehicle_id,
                        ve.vehicle_make,
                        ve.vehicle_model,
                        ve.vehicle_year,
                        ve.price_range,
                        ve.semantic_tags,
                        ve.image_count,
                        1 - (ve.embedding <=> %s::vector) as similarity_score,
                        -- Join with actual vehicle data if available
                        COALESCE(v.vin, ve.vehicle_id) as vin,
                        COALESCE(v.trim, '') as trim,
                        COALESCE(v.vehicle_type, 'unknown') as vehicle_type,
                        COALESCE(v.price, 0) as price,
                        COALESCE(v.mileage, 0) as mileage,
                        COALESCE(v.description, '') as description,
                        COALESCE(v.features, ARRAY[]::text[]) as features,
                        COALESCE(v.exterior_color, 'unknown') as exterior_color,
                        COALESCE(v.interior_color, 'unknown') as interior_color,
                        COALESCE(v.city, 'unknown') as city,
                        COALESCE(v.state, 'unknown') as state,
                        COALESCE(v.condition, 'unknown') as condition,
                        COALESCE(v.images, ARRAY[]::text[]) as images
                    FROM vehicle_embeddings ve
                    LEFT JOIN vehicles v ON ve.vehicle_id = v.id
                    WHERE 1 - (ve.embedding <=> %s::vector) > 0.1  -- Minimum similarity threshold
            """

            params = [embedding_str, embedding_str]
            param_count = 2

            # Apply traditional filters (Story 3-7: Added multi-select support)
            if filters:
                # Multi-select makes (NEW - Story 3-7)
                if filters.get('makes') and isinstance(filters['makes'], list):
                    makes_list = filters['makes']
                    if makes_list:
                        # Use ANY clause for array matching
                        base_query += f" AND ve.vehicle_make = ANY(${param_count + 1}::text[])"
                        params.append(makes_list)
                        param_count += 1
                # Fallback to single-select make for backward compatibility
                elif filters.get('make'):
                    base_query += f" AND ve.vehicle_make ILIKE ${param_count + 1}"
                    params.append(f"%{filters['make']}%")
                    param_count += 1

                # Multi-select vehicle_types (NEW - Story 3-7)
                if filters.get('vehicle_types') and isinstance(filters['vehicle_types'], list):
                    types_list = filters['vehicle_types']
                    if types_list:
                        # Use ANY clause for array matching
                        base_query += f" AND v.vehicle_type = ANY(${param_count + 1}::text[])"
                        params.append(types_list)
                        param_count += 1
                # Fallback to single-select vehicle_type for backward compatibility
                elif filters.get('vehicle_type'):
                    base_query += f" AND v.vehicle_type ILIKE ${param_count + 1}"
                    params.append(f"%{filters['vehicle_type']}%")
                    param_count += 1

                if filters.get('model'):
                    base_query += f" AND ve.vehicle_model ILIKE ${param_count + 1}"
                    params.append(f"%{filters['model']}%")
                    param_count += 1

                if filters.get('year_min'):
                    base_query += f" AND (ve.vehicle_year >= ${param_count + 1} OR v.year >= ${param_count + 1})"
                    params.append(filters['year_min'])
                    param_count += 1

                if filters.get('year_max'):
                    base_query += f" AND (ve.vehicle_year <= ${param_count + 1} OR v.year <= ${param_count + 1})"
                    params.append(filters['year_max'])
                    param_count += 1

                # Price filtering using effective_price (Story 3-7: handles NULL prices)
                if filters.get('price_min'):
                    base_query += f" AND COALESCE(v.asking_price, v.estimated_price, v.auction_forecast) >= ${param_count + 1}"
                    params.append(filters['price_min'])
                    param_count += 1

                if filters.get('price_max'):
                    base_query += f" AND COALESCE(v.asking_price, v.estimated_price, v.auction_forecast) <= ${param_count + 1}"
                    params.append(filters['price_max'])
                    param_count += 1

                if filters.get('mileage_max'):
                    base_query += f" AND COALESCE(v.mileage, 999999) <= ${param_count + 1}"
                    params.append(filters['mileage_max'])
                    param_count += 1

                if filters.get('fuel_type'):
                    base_query += f" AND v.fuel_type ILIKE ${param_count + 1}"
                    params.append(f"%{filters['fuel_type']}%")
                    param_count += 1

                if filters.get('city'):
                    base_query += f" AND v.city ILIKE ${param_count + 1}"
                    params.append(f"%{filters['city']}%")
                    param_count += 1

                if filters.get('state'):
                    base_query += f" AND v.state ILIKE ${param_count + 1}"
                    params.append(f"%{filters['state']}%")
                    param_count += 1

            # Add sorting (Story 3-7: Use effective_price for price sorting, NULLs last)
            if sort_by == "relevance":
                order_clause = "similarity_score"
            elif sort_by == "price":
                # Use effective_price with COALESCE to handle NULL prices
                # Put NULL prices at the end (high value for ASC, low/negative for DESC)
                null_value = 999999999 if sort_order.lower() == "asc" else -1
                order_clause = f"COALESCE(v.asking_price, v.estimated_price, v.auction_forecast, {null_value})"
            elif sort_by == "year":
                order_clause = "COALESCE(ve.vehicle_year, v.year)"
            elif sort_by == "mileage":
                # Put NULL mileage at the end for ASC sort (treat as very high mileage)
                null_value = 999999 if sort_order.lower() == "asc" else -1
                order_clause = f"COALESCE(v.mileage, {null_value})"
            else:
                order_clause = "similarity_score"  # Default

            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            base_query += f"), filtered_results AS (SELECT *, ROW_NUMBER() OVER (ORDER BY {order_clause} {sort_direction}) as row_num FROM similarity_results) SELECT * FROM filtered_results ORDER BY {order_clause} {sort_direction} LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])

            # Execute the query
            with self.db_conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(base_query, params)
                results = cursor.fetchall()

                # Get total count for pagination
                count_query = base_query.split("LIMIT")[0]  # Remove LIMIT and OFFSET
                count_query = count_query.replace(
                    f"SELECT *, ROW_NUMBER() OVER (ORDER BY {order_clause} {sort_direction}) as row_num FROM similarity_results) SELECT * FROM filtered_results",
                    "SELECT COUNT(*) as total_count FROM similarity_results"
                )
                count_query = count_query.split("OFFSET")[0]  # Remove OFFSET if present

                cursor.execute(count_query, params[:-2])  # Use same params but without LIMIT/OFFSET
                count_result = cursor.fetchone()
                total_count = count_result['total_count'] if count_result else 0

                # Process results and add match explanations
                processed_results = []
                for result in results:
                    # Generate match explanation based on similarity and filters
                    explanation = self._generate_match_explanation(
                        result,
                        query_embedding,
                        filters
                    )

                    processed_result = {
                        "vehicle": {
                            "id": result['vehicle_id'],
                            "vin": result['vin'],
                            "year": result['vehicle_year'] or 0,
                            "make": result['vehicle_make'] or '',
                            "model": result['vehicle_model'] or '',
                            "trim": result['trim'] or None,
                            "vehicle_type": result['vehicle_type'],
                            "price": float(result['price']),
                            "mileage": result['mileage'] if result['mileage'] else None,
                            "description": result['description'],
                            "features": result['features'] or [],
                            "exterior_color": result['exterior_color'],
                            "interior_color": result['interior_color'],
                            "city": result['city'],
                            "state": result['state'],
                            "condition": result['condition'],
                            "images": result['images'] or []
                        },
                        "similarity_score": float(result['similarity_score']),
                        "match_explanation": explanation,
                        "preference_score": self._calculate_preference_score(result, filters)
                    }
                    processed_results.append(processed_result)

                logger.info(f"✅ Hybrid search completed: {len(processed_results)} results from {total_count} total vehicles")

                return {
                    "results": processed_results,
                    "total_count": total_count,
                    "filters_applied": filters or {},
                    "search_metadata": {
                        "query_embedding_dim": len(query_embedding),
                        "similarity_threshold": 0.1,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "limit": limit,
                        "offset": offset
                    }
                }

        except Exception as e:
            logger.error(f"❌ Error in hybrid search: {e}")
            return {
                "results": [],
                "total_count": 0,
                "error": str(e)
            }

    def _generate_match_explanation(
        self,
        result: Dict[str, Any],
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable explanation for why this vehicle matches the search

        Args:
            result: Database result row
            query_embedding: Query embedding vector
            filters: Applied filters

        Returns:
            Explanation string
        """
        try:
            similarity_score = float(result.get('similarity_score', 0))
            make = result.get('vehicle_make', 'Unknown')
            model = result.get('vehicle_model', 'Unknown')
            year = result.get('vehicle_year', 'Unknown')
            vehicle_type = result.get('vehicle_type', 'vehicle')

            # Base explanation
            if similarity_score > 0.8:
                match_quality = "excellent match"
            elif similarity_score > 0.6:
                match_quality = "good match"
            elif similarity_score > 0.4:
                match_quality = "moderate match"
            else:
                match_quality = "basic match"

            explanation = f"{match_quality} for {year} {make} {model}"

            # Add type-specific context
            if vehicle_type != 'unknown':
                explanation += f" ({vehicle_type})"

            # Add filter context
            filter_matches = []
            if filters:
                if filters.get('make') and make and filters['make'].lower() in make.lower():
                    filter_matches.append("make matches your filter")
                if filters.get('model') and model and filters['model'].lower() in model.lower():
                    filter_matches.append("model matches your filter")
                if filters.get('year_min') and year and year >= filters['year_min']:
                    filter_matches.append("meets your year requirements")
                if filters.get('year_max') and year and year <= filters['year_max']:
                    filter_matches.append("within your year range")

            if filter_matches:
                explanation += f" - {', '.join(filter_matches)}"

            return explanation

        except Exception as e:
            logger.warning(f"Error generating match explanation: {e}")
            return f"Similar vehicle match found (confidence: {result.get('similarity_score', 0):.2f})"

    def _calculate_preference_score(
        self,
        result: Dict[str, Any],
        filters: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate preference score based on how well vehicle matches user filters

        Args:
            result: Database result row
            filters: Applied filters

        Returns:
            Preference score between 0.0 and 1.0
        """
        try:
            if not filters:
                return float(result.get('similarity_score', 0))  # Default to similarity score

            score = 0.0
            total_criteria = 0

            # Make filter matching
            if filters.get('make'):
                total_criteria += 1
                make = result.get('vehicle_make', '')
                if make and filters['make'].lower() in make.lower():
                    score += 0.3

            # Model filter matching
            if filters.get('model'):
                total_criteria += 1
                model = result.get('vehicle_model', '')
                if model and filters['model'].lower() in model.lower():
                    score += 0.3

            # Year range matching
            if filters.get('year_min') or filters.get('year_max'):
                total_criteria += 1
                year = result.get('vehicle_year') or result.get('year', 0)
                year_min = filters.get('year_min', 0)
                year_max = filters.get('year_max', 9999)
                if year_min <= year <= year_max:
                    score += 0.2

            # Price range matching
            if filters.get('price_min') or filters.get('price_max'):
                total_criteria += 1
                price = float(result.get('price', 0))
                price_min = filters.get('price_min', 0)
                price_max = filters.get('price_max', float('inf'))
                if price_min <= price <= price_max:
                    score += 0.2

            # Normalize and combine with similarity
            if total_criteria > 0:
                filter_score = score / total_criteria
                similarity_score = float(result.get('similarity_score', 0))
                # Weight more towards semantic similarity but include filter preferences
                return (similarity_score * 0.7) + (filter_score * 0.3)
            else:
                return float(result.get('similarity_score', 0))

        except Exception as e:
            logger.warning(f"Error calculating preference score: {e}")
            return float(result.get('similarity_score', 0))

    async def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific vehicle by ID with comprehensive error handling

        Args:
            vehicle_id: Unique vehicle identifier

        Returns:
            Vehicle data dictionary or None if not found
        """
        if not self.db_conn:
            logger.error("Database connection not initialized")
            return None

        try:
            with self.db_conn.cursor(row_factory=dict_row) as cursor:
                query = """
                SELECT
                    v.id as vehicle_id,
                    v.vin,
                    v.year as vehicle_year,
                    v.make as vehicle_make,
                    v.model as vehicle_model,
                    v.trim,
                    v.vehicle_type,
                    v.price,
                    v.mileage,
                    v.description,
                    v.features,
                    v.exterior_color,
                    v.interior_color,
                    v.city,
                    v.state,
                    v.condition,
                    v.images,
                    v.created_at,
                    v.updated_at,
                    ve.semantic_tags,
                    ve.embedding,
                    ve.text_embedding,
                    ve.metadata_processed
                FROM vehicles v
                LEFT JOIN vehicle_embeddings ve ON v.id = ve.vehicle_id
                WHERE v.id = %s
                """

                cursor.execute(query, (vehicle_id,))
                result = cursor.fetchone()

                if result:
                    # Convert to expected format
                    vehicle_data = {
                        'id': result['vehicle_id'],
                        'vin': result['vin'],
                        'year': result['vehicle_year'] or 0,
                        'make': result['vehicle_make'] or '',
                        'model': result['vehicle_model'] or '',
                        'trim': result['trim'],
                        'vehicle_type': result['vehicle_type'] or 'unknown',
                        'price': float(result['price']) if result['price'] else 0.0,
                        'mileage': result['mileage'],
                        'description': result['description'] or '',
                        'features': result['features'] or [],
                        'exterior_color': result['exterior_color'] or '',
                        'interior_color': result['interior_color'] or '',
                        'city': result['city'] or '',
                        'state': result['state'] or '',
                        'condition': result['condition'] or 'unknown',
                        'images': result['images'] or [],
                        'created_at': result['created_at'],
                        'updated_at': result['updated_at'],
                        'semantic_tags': result['semantic_tags'] or [],
                        'embedding': result['embedding'],
                        'text_embedding': result['text_embedding'],
                        'metadata_processed': result['metadata_processed'] or False
                    }

                    logger.info(f"✅ Retrieved vehicle {vehicle_id}")
                    return vehicle_data
                else:
                    logger.warning(f"Vehicle {vehicle_id} not found")
                    return None

        except Exception as e:
            logger.error(f"❌ Error retrieving vehicle {vehicle_id}: {e}")
            return None

    async def get_vehicles_by_ids(self, vehicle_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple vehicles by their IDs with efficient batch query

        Args:
            vehicle_ids: List of vehicle IDs to retrieve

        Returns:
            List of vehicle data dictionaries
        """
        if not self.db_conn:
            logger.error("Database connection not initialized")
            return []

        if not vehicle_ids:
            return []

        try:
            with self.db_conn.cursor(row_factory=dict_row) as cursor:
                # Use IN clause for efficient batch retrieval
                placeholders = ','.join(['%s'] * len(vehicle_ids))
                query = f"""
                SELECT
                    v.id as vehicle_id,
                    v.vin,
                    v.year as vehicle_year,
                    v.make as vehicle_make,
                    v.model as vehicle_model,
                    v.trim,
                    v.vehicle_type,
                    v.price,
                    v.mileage,
                    v.description,
                    v.features,
                    v.exterior_color,
                    v.interior_color,
                    v.city,
                    v.state,
                    v.condition,
                    v.images,
                    v.created_at,
                    v.updated_at,
                    ve.semantic_tags,
                    ve.embedding,
                    ve.text_embedding,
                    ve.metadata_processed
                FROM vehicles v
                LEFT JOIN vehicle_embeddings ve ON v.id = ve.vehicle_id
                WHERE v.id IN ({placeholders})
                ORDER BY v.created_at DESC
                """

                cursor.execute(query, vehicle_ids)
                results = cursor.fetchall()

                vehicles = []
                for result in results:
                    vehicle_data = {
                        'id': result['vehicle_id'],
                        'vin': result['vin'],
                        'year': result['vehicle_year'] or 0,
                        'make': result['vehicle_make'] or '',
                        'model': result['vehicle_model'] or '',
                        'trim': result['trim'],
                        'vehicle_type': result['vehicle_type'] or 'unknown',
                        'price': float(result['price']) if result['price'] else 0.0,
                        'mileage': result['mileage'],
                        'description': result['description'] or '',
                        'features': result['features'] or [],
                        'exterior_color': result['exterior_color'] or '',
                        'interior_color': result['interior_color'] or '',
                        'city': result['city'] or '',
                        'state': result['state'] or '',
                        'condition': result['condition'] or 'unknown',
                        'images': result['images'] or [],
                        'created_at': result['created_at'],
                        'updated_at': result['updated_at'],
                        'semantic_tags': result['semantic_tags'] or [],
                        'embedding': result['embedding'],
                        'text_embedding': result['text_embedding'],
                        'metadata_processed': result['metadata_processed'] or False
                    }
                    vehicles.append(vehicle_data)

                logger.info(f"✅ Retrieved {len(vehicles)} vehicles from {len(vehicle_ids)} requested IDs")
                return vehicles

        except Exception as e:
            logger.error(f"❌ Error retrieving vehicles by IDs: {e}")
            return []