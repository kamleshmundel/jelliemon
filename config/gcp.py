from google.cloud import storage
from django.conf import settings
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def delete_audio_from_gcp(audio_path):
    """Delete the audio file from the GCP bucket based on the URL."""
    if not audio_path:
        return
    
    # Set up Google Cloud credentials if not already set
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "service-account-key.json")

    try:
        # Initialize GCP storage client
        client = storage.Client()
        bucket = client.bucket(settings.GS_BUCKET_NAME)  # Ensure this is your bucket's name
        print(f"Connected to bucket: {bucket.name}")

        # Create a blob reference to the audio file
        blob = bucket.blob(audio_path)
        
        # Delete the file from the bucket
        blob.delete()
        print(f"Audio file {audio_path} deleted from the bucket.")
    
    except Exception as e:
        print(f"Failed to delete audio file {audio_path}: {e}")
