"""Generate embeddings for existing vehicles"""
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def generate_embeddings():
    from supabase import create_client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    api_key = os.getenv('OPENROUTER_API_KEY')

    supabase = create_client(supabase_url, supabase_key)

    # Get all vehicles
    result = supabase.table('vehicle_listings').select('id, vin, year, make, model, trim, description_text').execute()

    print(f"Found {len(result.data)} vehicles to embed\n")

    async with httpx.AsyncClient() as client:
        for vehicle in result.data:
            # Create searchable text
            text = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
            if vehicle.get('trim'):
                text += f" {vehicle['trim']}"
            if vehicle.get('description_text'):
                text += f" {vehicle['description_text']}"

            print(f"Generating embedding for: {text[:50]}...")

            # Generate embedding
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": text,
                    "dimensions": 1536
                },
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ERROR: {response.status_code}")
                continue

            embedding = response.json()['data'][0]['embedding']

            # Update vehicle with embedding
            update_result = supabase.table('vehicle_listings').update({
                'text_embedding': embedding,
                'description_text': text
            }).eq('id', vehicle['id']).execute()

            print(f"  Updated {vehicle['vin'][:10]}... with {len(embedding)} dim embedding")

    print("\nDone! Embeddings generated for all vehicles.")

if __name__ == "__main__":
    asyncio.run(generate_embeddings())
