"""
Otto.AI Embedding Service
Handles embedding generation using OpenRouter API and RAG-Anything integration
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
import json

import requests
import numpy as np
from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import EmbeddingFunc

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingRequest:
    """Embedding request structure"""
    text: Optional[str] = None
    images: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class EmbeddingResponse:
    """Embedding response structure"""
    embedding: List[float]
    embedding_dim: int
    processing_time: float

class OttoAIEmbeddingService:
    """
    Otto.AI Embedding Service
    Integrates OpenRouter API with RAG-Anything for multimodal processing
    """

    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_model = os.getenv('OPENROUTER_EMBEDDING_MODEL', 'openai/text-embedding-3-small')
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small outputs 1536 dimensions natively

        # RAG-Anything configuration
        self.rag_config = RAGAnythingConfig(
            parser="mineru",  # Default parser for multimodal documents
            parse_method="auto",  # Auto-detect parsing method
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            context_window=1,
            max_concurrent_files=4
        )

        # Initialize RAGAnything (will be set up lazily)
        self.rag: Optional[RAGAnything] = None
        self.lightrag: Optional[LightRAG] = None

        # Database connection
        self.db_conn: Optional[psycopg.extensions.connection] = None

    async def initialize(self, supabase_url: str, supabase_key: str):
        """Initialize the service with database connection"""
        try:
            # Connect to Supabase using proper connection string format
            # Supabase URL needs to be converted to PostgreSQL connection string
            # Format: postgresql://postgres:[password]@db.[project_ref].supabase.co:5432/postgres
            project_ref = supabase_url.split('//')[1].split('.')[0]
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if not db_password:
                raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

            connection_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
            self.db_conn = psycopg.connect(connection_string)
            register_vector(self.db_conn)
            logger.info("✅ Connected to Supabase database")

            # Initialize LightRAG (for RAGAnything integration)
            await self._initialize_lightrag()

            # Initialize RAGAnything with OpenRouter integration
            await self._initialize_rag_anything()

            logger.info("✅ Embedding service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding service: {e}")
            return False

    async def _initialize_lightrag(self):
        """Initialize LightRAG instance for RAG-Anything integration"""
        try:
            working_dir = "./rag_storage"

            # Create working directory if it doesn't exist
            os.makedirs(working_dir, exist_ok=True)

            # Initialize LightRAG with OpenRouter embeddings
            self.lightrag = LightRAG(
                working_dir=working_dir,
                llm_model_func=self._llm_model_func,
                embedding_func=self._embedding_func
            )

            # Initialize storage
            await self.lightrag.initialize_storages()
            await initialize_pipeline_status()

            logger.info(f"✅ LightRAG initialized in {working_dir}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize LightRAG: {e}")
            raise

    async def _initialize_rag_anything(self):
        """Initialize RAGAnything with OpenRouter integration"""
        try:
            # Use existing LightRAG instance
            self.rag = RAGAnything(
                lightrag=self.lightrag,
                vision_model_func=self._vision_model_func
            )

            logger.info("✅ RAGAnything initialized with OpenRouter integration")

        except Exception as e:
            logger.error(f"❌ Failed to initialize RAGAnything: {e}")
            raise

    def _llm_model_func(self, prompt: str, system_prompt: Optional[str] = None,
                           history_messages: Optional[List] = None, **kwargs) -> str:
        """LLM model function for RAG-Anything using OpenRouter"""
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto-ai.com",
                    "X-Title": "Otto.AI LLM Processing",
                },
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [
                        {"role": "system", "content": system_prompt if system_prompt else "You are a helpful AI assistant for vehicle search and analysis."},
                        *(history_messages or []),
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter API request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ OpenRouter LLM request failed: {e}")
            raise

    def _vision_model_func(self, prompt: str, system_prompt: Optional[str] = None,
                            history_messages: Optional[List] = None, image_data: Optional[str] = None,
                            messages: Optional[List] = None, **kwargs) -> str:
        """Vision model function for RAGAnything using OpenRouter"""
        try:
            # Use messages format if provided (for multimodal VLM)
            if messages:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://otto-ai.com",
                        "X-Title": "Otto.AI Vision Processing",
                    },
                    json={
                        "model": "google/gemini-2.5-flash-image",
                        "messages": messages
                    },
                    timeout=60
                )
            else:
                # Traditional format
                messages_list = []
                if system_prompt:
                    messages_list.append({"role": "system", "content": system_prompt})

                if image_data:
                    messages_list.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                        ]
                    })
                else:
                    messages_list.append({"role": "user", "content": prompt})

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://otto-ai.com",
                        "X-Title": "Otto.AI Vision Processing",
                    },
                    json={
                        "model": "google/gemini-2.5-flash-image",
                        "messages": messages_list
                    },
                    timeout=60
                )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter Vision API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter Vision API request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ OpenRouter Vision request failed: {e}")
            raise

    def _embedding_func(self) -> EmbeddingFunc:
        """Create embedding function for LightRAG using OpenRouter"""
        async def openrouter_embedding_func(texts: Union[str, List[str]]) -> List[float]:
            """Generate embeddings using OpenRouter API"""
            if isinstance(texts, str):
                texts = [texts]

            all_embeddings = []

            for text in texts:
                try:
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.openrouter_api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://otto-ai.com",
                            "X-Title": "Otto.AI Embedding Generation",
                        },
                        json={
                            "model": self.openrouter_model,
                            "input": text,
                            "encoding_format": "float",
                            "dimensions": self.embedding_dim  # Request reduced dimensions for HNSW compatibility
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        embedding = result['data'][0]['embedding']
                        if len(embedding) == self.embedding_dim:
                            all_embeddings.extend(embedding)
                        else:
                            logger.warning(f"⚠️ Unexpected embedding dimension: {len(embedding)} (expected {self.embedding_dim})")
                            # Pad or truncate to expected dimension
                            if len(embedding) < self.embedding_dim:
                                embedding.extend([0.0] * (self.embedding_dim - len(embedding)))
                            else:
                                embedding = embedding[:self.embedding_dim]
                            all_embeddings.extend(embedding)
                    else:
                        logger.error(f"OpenRouter Embedding API error: {response.status_code}")
                        # Fallback to zero vector
                        all_embeddings.extend([0.0] * self.embedding_dim)

                except Exception as e:
                    logger.error(f"❌ OpenRouter embedding request failed for text: {str(text)[:50]}...: {e}")
                    # Fallback to zero vector
                    all_embeddings.extend([0.0] * self.embedding_dim)

            return all_embeddings

        return EmbeddingFunc(
            embedding_dim=self.embedding_dim,
            max_token_size=8192,
            func=openrouter_embedding_func
        )

    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embedding for text, images, or multimodal content

        Args:
            request: EmbeddingRequest containing text, images, or context

        Returns:
            EmbeddingResponse with generated embedding and metadata
        """
        try:
            import time
            start_time = time.time()

            if self.rag is None:
                logger.error("❌ RAG-Anything not initialized. Call initialize() first.")
                raise Exception("Service not initialized")

            # For text-only requests, use direct OpenRouter API for better performance
            if request.text and not request.images and not request.context:
                embedding = await self._generate_text_embedding_direct(request.text)
            else:
                # Use RAG-Anything for multimodal processing
                embedding = await self._generate_rag_embedding(request)

            processing_time = time.time() - start_time

            return EmbeddingResponse(
                embedding=embedding,
                embedding_dim=len(embedding),
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return fallback embedding
            return EmbeddingResponse(
                embedding=[0.0] * self.embedding_dim,
                embedding_dim=self.embedding_dim,
                processing_time=0.0
            )

    async def _generate_text_embedding_direct(self, text: str) -> List[float]:
        """Generate text embedding directly via OpenRouter API (faster for text-only)"""
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto-ai.com",
                    "X-Title": "Otto.AI Text Embedding",
                },
                json={
                    "model": self.openrouter_model,
                    "input": text,
                    "encoding_format": "float",
                    "dimensions": self.embedding_dim  # Request reduced dimensions for HNSW compatibility
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                embedding = result['data'][0]['embedding']

                if len(embedding) == self.embedding_dim:
                    return embedding
                else:
                    logger.warning(f"⚠️ Unexpected embedding dimension: {len(embedding)} (expected {self.embedding_dim})")
                    return self._normalize_embedding(embedding)
            else:
                logger.error(f"❌ OpenRouter embedding error: {response.status_code}")
                return [0.0] * self.embedding_dim

        except Exception as e:
            logger.error(f"❌ Direct embedding generation failed: {e}")
            return [0.0] * self.embedding_dim

    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to expected dimension"""
        if len(embedding) == self.embedding_dim:
            return embedding
        elif len(embedding) < self.embedding_dim:
            # Pad with zeros
            return embedding + [0.0] * (self.embedding_dim - len(embedding))
        else:
            # Truncate
            return embedding[:self.embedding_dim]

    async def _generate_rag_embedding(self, request: EmbeddingRequest) -> List[float]:
        """Generate embedding using RAG-Anything for multimodal processing"""
        try:
            # Create multimodal content for RAG-Anything
            if request.text or request.images:
                # For simplicity, we'll process text content through RAG-Anything
                # In a full implementation, we might pass image data through the image modal processor
                content = request.text or ""

                # Use RAG-Anything to process the content
                # This is a simplified approach - full implementation would use RAG-Anything's document processing
                return await self._generate_text_embedding_direct(content)

            # Return zero embedding if no content
            return [0.0] * self.embedding_dim

        except Exception as e:
            logger.error(f"❌ RAG embedding generation failed: {e}")
            return [0.0] * self.embedding_dim

    async def store_vehicle_embedding(self, vehicle_data: Dict[str, Any]) -> bool:
        """
        Store vehicle data with embeddings in the database

        Args:
            vehicle_data: Dictionary containing vehicle information

        Returns:
            Boolean indicating success
        """
        try:
            if not self.db_conn:
                logger.error("❌ Database not connected. Call initialize() first.")
                return False

            cursor = self.db_conn.cursor()

            # Generate embeddings for title, description, and features
            title_embedding = []
            description_embedding = []
            features_embedding = []

            # Generate title embedding
            if vehicle_data.get('title'):
                title_response = await self.generate_embedding(
                    EmbeddingRequest(text=vehicle_data['title'])
                )
                title_embedding = title_response.embedding

            # Generate description embedding
            if vehicle_data.get('description'):
                desc_response = await self.generate_embedding(
                    EmbeddingRequest(text=vehicle_data['description'])
                )
                description_embedding = desc_response.embedding

            # Generate features embedding
            if vehicle_data.get('features') and len(vehicle_data['features']) > 0:
                features_text = " ".join(vehicle_data['features'])
                features_response = await self.generate_embedding(
                    EmbeddingRequest(text=features_text)
                )
                features_embedding = features_response.embedding

            # Prepare fields for database insertion
            fields = [
                'vin', 'make', 'model', 'year', 'trim', 'vehicle_type', 'fuel_type',
                'transmission', 'drivetrain', 'engine_displacement', 'horsepower', 'torque',
                'exterior_color', 'interior_color', 'num_doors', 'price', 'msrp',
                'mileage', 'condition', 'city', 'state', 'country', 'description',
                'features', 'images', 'title_embedding', 'description_embedding', 'features_embedding',
                'is_active', 'is_available'
            ]

            # Prepare values
            values = [
                vehicle_data.get('vin'),
                vehicle_data.get('make'),
                vehicle_data.get('model'),
                vehicle_data.get('year'),
                vehicle_data.get('trim'),
                vehicle_data.get('vehicle_type'),
                vehicle_data.get('fuel_type'),
                vehicle_data.get('transmission'),
                vehicle_data.get('drivetrain'),
                vehicle_data.get('engine_displacement'),
                vehicle_data.get('horsepower'),
                vehicle_data.get('torque'),
                vehicle_data.get('exterior_color'),
                vehicle_data.get('interior_color'),
                vehicle_data.get('num_doors'),
                vehicle_data.get('price'),
                vehicle_data.get('msrp'),
                vehicle_data.get('mileage'),
                vehicle_data.get('condition'),
                vehicle_data.get('city'),
                vehicle_data.get('state'),
                vehicle_data.get('country', 'USA'),
                vehicle_data.get('description'),
                vehicle_data.get('features', []),
                vehicle_data.get('images', []),
                title_embedding,
                description_embedding,
                features_embedding,
                vehicle_data.get('is_active', True),
                vehicle_data.get('is_available', True)
            ]

            # Build INSERT query
            placeholders = ', '.join(['%s'] * len(fields))
            update_fields = ', '.join([f'"{field}" = EXCLUDED.%s' for field in fields])
            query = f"""
                INSERT INTO vehicles ({', '.join(fields)})
                VALUES ({placeholders})
                ON CONFLICT (vin) DO UPDATE SET
                    {update_fields};
            """.strip()

            cursor.execute(query, values)
            cursor.close()

            logger.info(f"✅ Stored vehicle embedding for: {vehicle_data.get('make')} {vehicle_data.get('model')} ({vehicle_data.get('year')})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to store vehicle embedding: {e}")
            return False

    async def generate_vehicle_image(
        self,
        vehicle_description: str,
        aspect_ratio: str = "16:9",
        style_hint: Optional[str] = "professional automotive photography"
    ) -> Dict[str, Any]:
        """
        Generate vehicle listing image using Gemini 2.5 Flash Image capabilities

        Args:
            vehicle_description: Detailed description of the vehicle
            aspect_ratio: Image aspect ratio (16:9, 4:3, 1:1, etc.)
            style_hint: Optional style guidance for the image

        Returns:
            Dictionary with generated image data
        """
        try:
            # Enhanced prompt for vehicle image generation
            prompt = f"""
            Generate a professional automotive photograph of: {vehicle_description}

            Style: {style_hint}
            Requirements:
            - High quality, realistic vehicle photography
            - Professional lighting and composition
            - Appropriate background (showroom, road, or lifestyle setting)
            - Vehicle should be the main focus
            - {aspect_ratio} aspect ratio for optimal listing display
            """

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto-ai.com",
                    "X-Title": "Otto.AI Vehicle Image Generation",
                },
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "modalities": ["image", "text"],
                    "image_config": {
                        "aspect_ratio": aspect_ratio
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("choices", [{}])[0].get("message", {})

                # Extract image and text response
                images = message.get("images", [])
                text_response = message.get("content", "")

                if images:
                    image_data = images[0].get("image_url", {}).get("url", "")
                    return {
                        "success": True,
                        "image_data": image_data,  # Base64 encoded
                        "text_description": text_response,
                        "aspect_ratio": aspect_ratio,
                        "model": "google/gemini-2.5-flash-image"
                    }
                else:
                    logger.warning("No images generated in response")
                    return {
                        "success": False,
                        "error": "No images generated",
                        "text_response": text_response
                    }
            else:
                logger.error(f"Image generation error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}"
                }

        except Exception as e:
            logger.error(f"❌ Vehicle image generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analyze_vehicle_image(
        self,
        image_base64: str,
        analysis_prompt: str = "Analyze this vehicle image and extract key features, condition, and characteristics."
    ) -> Dict[str, Any]:
        """
        Analyze uploaded vehicle image using Gemini 2.5 Flash Image capabilities

        Args:
            image_base64: Base64 encoded image data
            analysis_prompt: Specific analysis request

        Returns:
            Dictionary with image analysis results
        """
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto-ai.com",
                    "X-Title": "Otto.AI Vehicle Image Analysis",
                },
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": analysis_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }
                    ]
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                return {
                    "success": True,
                    "analysis": analysis,
                    "model": "google/gemini-2.5-flash-image"
                }
            else:
                logger.error(f"Image analysis error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}"
                }

        except Exception as e:
            logger.error(f"❌ Vehicle image analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def close(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("✅ Database connection closed")

        if self.rag:
            await self.rag.finalize_storages()
            logger.info("✅ RAG-Anything storages finalized")

# Global service instance
_embedding_service: Optional[OttoAIEmbeddingService] = None

async def get_embedding_service() -> OttoAIEmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = OttoAIEmbeddingService()
    return _embedding_service