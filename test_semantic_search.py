"""Quick test for semantic search functionality"""
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_semantic_search():
    """Test that we can generate embeddings and search vehicles"""

    print("=" * 60)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 60)

    query = "reliable pickup truck for work"
    print(f"\nQuery: '{query}'")

    api_key = os.getenv('OPENROUTER_API_KEY')

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/text-embedding-3-small",
                "input": query,
                "dimensions": 1536
            },
            timeout=30
        )

        if response.status_code != 200:
            print(f"ERROR: {response.status_code} - {response.text}")
            return

        result = response.json()
        embedding = result['data'][0]['embedding']
        print(f"Generated embedding: {len(embedding)} dimensions")

    from supabase import create_client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

    supabase = create_client(supabase_url, supabase_key)

    print("\nSearching vehicles...")

    result = supabase.rpc(
        'match_vehicle_listings',
        {
            'query_embedding': embedding,
            'match_count': 5,
            'min_similarity': 0.0
        }
    ).execute()

    if result.data:
        print(f"\nFound {len(result.data)} matching vehicles:\n")
        for i, vehicle in enumerate(result.data, 1):
            similarity = vehicle.get('similarity', 0)
            print(f"  {i}. {vehicle['year']} {vehicle['make']} {vehicle['model']}")
            print(f"     VIN: {vehicle['vin']}")
            print(f"     Similarity: {similarity:.4f}")
            print()
    else:
        print("No vehicles found - checking if embeddings exist...")
        check = supabase.table('vehicle_listings').select('vin, text_embedding').execute()
        for row in check.data:
            has_embedding = row.get('text_embedding') is not None
            print(f"  {row['vin'][:10]}...: has_embedding = {has_embedding}")

if __name__ == "__main__":
    asyncio.run(test_semantic_search())
