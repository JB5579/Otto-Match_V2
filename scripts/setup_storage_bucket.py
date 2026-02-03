"""
Setup Supabase Storage bucket for vehicle images.

This script verifies and creates the 'vehicle-images' storage bucket
if it doesn't exist.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
import httpx

# Get environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
STORAGE_BUCKET = os.getenv('SUPABASE_STORAGE_BUCKET', 'vehicle-images')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
    sys.exit(1)

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Storage Bucket: {STORAGE_BUCKET}")

# Create Supabase client
client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Create HTTP client for storage operations
http_client = httpx.Client(
    base_url=SUPABASE_URL,
    headers={
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    },
    timeout=30.0
)

# Step 1: Check if bucket exists
print("\n📋 Step 1: Checking if storage bucket exists...")
try:
    response = http_client.get(
        f"/storage/v1/bucket/{STORAGE_BUCKET}"
    )

    if response.status_code == 200:
        print(f"✅ Storage bucket '{STORAGE_BUCKET}' already exists")
    elif response.status_code == 404:
        print(f"⚠️  Storage bucket '{STORAGE_BUCKET}' does not exist")
        bucket_exists = False
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        print(f"Response: {response.text}")
        bucket_exists = False
except Exception as e:
    print(f"❌ Error checking bucket: {e}")
    bucket_exists = False

# Step 2: Create bucket if it doesn't exist
if response.status_code != 200:
    print(f"\n📦 Step 2: Creating storage bucket '{STORAGE_BUCKET}'...")
    try:
        create_response = http_client.post(
            "/storage/v1/bucket",
            json={
                "id": STORAGE_BUCKET,
                "name": STORAGE_BUCKET,
                "public": True,  # Make bucket public for frontend access
                "file_size_limit": 10485760,  # 10MB limit per file
                "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"]
            }
        )

        if create_response.status_code in (200, 201):
            print(f"✅ Storage bucket '{STORAGE_BUCKET}' created successfully")
        else:
            print(f"⚠️  Failed to create bucket: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            print("\n💡 You may need to create the bucket manually in Supabase Dashboard:")
            print(f"   https://supabase.com/dashboard/project/{os.getenv('SUPABASE_PROJECT_ID')}/storage")
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        print("\n💡 You may need to create the bucket manually in Supabase Dashboard:")
        print(f"   https://supabase.com/dashboard/project/{os.getenv('SUPABASE_PROJECT_ID')}/storage")

# Step 3: Set bucket policy to public
print(f"\n🔓 Step 3: Ensuring bucket '{STORAGE_BUCKET}' is public...")
try:
    policy_response = http_client.post(
        f"/storage/v1/bucket/{STORAGE_BUCKET}",
        json={
            "public": True
        }
    )

    if policy_response.status_code in (200, 201):
        print(f"✅ Bucket '{STORAGE_BUCKET}' is now public")
    else:
        print(f"⚠️  Could not update bucket policy: {policy_response.status_code}")
        print(f"Response: {policy_response.text}")
except Exception as e:
    print(f"⚠️  Error updating bucket policy: {e}")

# Step 4: Create storage path test
print(f"\n🧪 Step 4: Testing storage upload...")
try:
    # Create a small test image (1x1 pixel JPEG)
    test_image_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x03\x02\x02\x03\x03\x03\x03\x04\x03\x03\x04\x05\x08\x05\x05\x04\x04\x05\n\x05\x07\x07\x06\x08\x0c\n\x0c\x0c\x0b\n\x0b\x0b\r\x0e\x12\x10\r\x0e\x11\x0e\x0b\x0b\x10\x16\x10\x11\x13\x14\x15\x15\x15\x0c\x0f\x17\x18\x16\x14\x18\x12\x14\x15\x14\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\xff\xda\x00\x08\x01\x01\x00\x00?\x00T_\xff\xd9'

    test_response = http_client.post(
        f"/storage/v1/object/{STORAGE_BUCKET}/test/test_image.jpg",
        headers={"Content-Type": "image/jpeg"},
        content=test_image_bytes
    )

    if test_response.status_code in (200, 201):
        test_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/test/test_image.jpg"
        print(f"✅ Test upload successful!")
        print(f"   Public URL: {test_url}")

        # Clean up test file
        delete_response = http_client.delete(
            f"/storage/v1/object/{STORAGE_BUCKET}/test/test_image.jpg"
        )
        if delete_response.status_code in (200, 204):
            print(f"✅ Test file cleaned up")
    else:
        print(f"⚠️  Test upload failed: {test_response.status_code}")
        print(f"Response: {test_response.text}")
except Exception as e:
    print(f"❌ Error testing upload: {e}")

print("\n" + "="*60)
print("Storage bucket setup complete!")
print("="*60)
print(f"\nBucket: {STORAGE_BUCKET}")
print(f"Public URL format: {SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/<path>")
print("\nNext steps:")
print("1. Re-process PDFs to upload images to the storage bucket")
print("2. Images should now appear in the frontend vehicle grid")

http_client.close()
