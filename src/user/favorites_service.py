"""
Otto.AI Favorites Service

Implements Story 1.6: Vehicle Favorites and Notifications
Manages user favorites with Supabase integration

Features:
- Add/remove vehicles from user favorites
- List user favorites with pagination
- Check if vehicle is favorited
- Duplicate prevention
- Comprehensive error handling
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import psycopg
from psycopg.rows import dict_row
import uuid

logger = logging.getLogger(__name__)

@dataclass
class FavoriteItem:
    """Favorite vehicle data model"""
    id: str
    user_id: str
    vehicle_id: str
    created_at: datetime
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    price: Optional[float] = None
    vehicle_image: Optional[str] = None
    vehicle_url: Optional[str] = None

class FavoritesService:
    """
    Service for managing user vehicle favorites

    Provides CRUD operations for user favorites with Supabase integration
    """

    def __init__(self):
        """Initialize favorites service"""
        self.db_conn = None

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

            logger.info("✅ Favorites Service connected to Supabase")

            # Create favorites table if it doesn't exist
            await self._create_favorites_table()

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Favorites Service: {e}")
            return False

    async def _create_favorites_table(self) -> None:
        """Create user_favorites table if it doesn't exist"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_favorites (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        vehicle_id VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(user_id, vehicle_id)
                    );
                """)

                # Create indexes for optimal query performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON user_favorites(user_id);
                    CREATE INDEX IF NOT EXISTS idx_favorites_vehicle_id ON user_favorites(vehicle_id);
                    CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON user_favorites(created_at);
                """)

                # Create trigger for updated_at
                cur.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """)

                cur.execute("""
                    DROP TRIGGER IF EXISTS update_user_favorites_updated_at ON user_favorites;
                    CREATE TRIGGER update_user_favorites_updated_at
                        BEFORE UPDATE ON user_favorites
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """)

                self.db_conn.commit()
                logger.info("✅ Favorites table created/verified successfully")

        except Exception as e:
            logger.error(f"❌ Failed to create favorites table: {e}")
            raise

    async def add_to_favorites(self, user_id: str, vehicle_id: str) -> bool:
        """
        Add vehicle to user favorites with duplicate checking

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier

        Returns:
            True if successfully added, False if already exists or error
        """
        try:
            # Check if already favorited
            if await self.favorite_exists(user_id, vehicle_id):
                logger.info(f"Vehicle {vehicle_id} already in favorites for user {user_id}")
                return False

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_favorites (user_id, vehicle_id)
                    VALUES (%s, %s)
                    RETURNING id, created_at;
                """, (user_id, vehicle_id))

                result = cur.fetchone()
                self.db_conn.commit()

                logger.info(f"✅ Added vehicle {vehicle_id} to favorites for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to add to favorites: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def remove_from_favorites(self, user_id: str, vehicle_id: str) -> bool:
        """
        Remove vehicle from user favorites

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier

        Returns:
            True if successfully removed, False if not found or error
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM user_favorites
                    WHERE user_id = %s AND vehicle_id = %s
                    RETURNING id;
                """, (user_id, vehicle_id))

                result = cur.fetchone()
                self.db_conn.commit()

                if result:
                    logger.info(f"✅ Removed vehicle {vehicle_id} from favorites for user {user_id}")
                    return True
                else:
                    logger.info(f"Vehicle {vehicle_id} not in favorites for user {user_id}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to remove from favorites: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    async def get_user_favorites(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[FavoriteItem], int]:
        """
        Get paginated list of user's favorite vehicles

        Args:
            user_id: User identifier
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            Tuple of (favorites list, total count)
        """
        try:
            with self.db_conn.cursor(row_factory=dict_row) as cur:
                # Get total count
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM user_favorites
                    WHERE user_id = %s;
                """, (user_id,))

                total = cur.fetchone()['total']

                # Get paginated favorites with vehicle details
                cur.execute("""
                    SELECT
                        f.id,
                        f.user_id,
                        f.vehicle_id,
                        f.created_at,
                        v.make as vehicle_make,
                        v.model as vehicle_model,
                        v.year as vehicle_year,
                        v.price,
                        v.image_urls[1] as vehicle_image,
                        v.url as vehicle_url
                    FROM user_favorites f
                    LEFT JOIN vehicles v ON f.vehicle_id = v.id
                    WHERE f.user_id = %s
                    ORDER BY f.created_at DESC
                    LIMIT %s OFFSET %s;
                """, (user_id, limit, offset))

                rows = cur.fetchall()

                favorites = [
                    FavoriteItem(
                        id=str(row['id']),
                        user_id=row['user_id'],
                        vehicle_id=row['vehicle_id'],
                        created_at=row['created_at'],
                        vehicle_make=row.get('vehicle_make'),
                        vehicle_model=row.get('vehicle_model'),
                        vehicle_year=row.get('vehicle_year'),
                        price=row.get('price'),
                        vehicle_image=row.get('vehicle_image'),
                        vehicle_url=row.get('vehicle_url')
                    )
                    for row in rows
                ]

                logger.info(f"✅ Retrieved {len(favorites)} favorites for user {user_id}")
                return favorites, total

        except Exception as e:
            logger.error(f"❌ Failed to get user favorites: {e}")
            return [], 0

    async def favorite_exists(self, user_id: str, vehicle_id: str) -> bool:
        """
        Check if vehicle is in user's favorites

        Args:
            user_id: User identifier
            vehicle_id: Vehicle identifier

        Returns:
            True if favorited, False otherwise
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM user_favorites
                        WHERE user_id = %s AND vehicle_id = %s
                    );
                """, (user_id, vehicle_id))

                result = cur.fetchone()
                return result[0] if result else False

        except Exception as e:
            logger.error(f"❌ Failed to check favorite exists: {e}")
            return False

    async def get_favorite_count(self, user_id: str) -> int:
        """
        Get total number of favorites for a user

        Args:
            user_id: User identifier

        Returns:
            Number of favorite vehicles
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM user_favorites WHERE user_id = %s;
                """, (user_id,))

                result = cur.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"❌ Failed to get favorite count: {e}")
            return 0

    async def close(self) -> None:
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Favorites Service connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'db_conn') and self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass