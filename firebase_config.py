"""
Firebase configuration and initialization module.
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

# Global Firestore client instance
_db: Optional[firestore.Client] = None


def initialize_firebase(credential_path: Optional[str] = None) -> firestore.Client:
    """
    Initialize Firebase Admin SDK and return Firestore client.
    
    Args:
        credential_path: Path to Firebase service account JSON file.
                        If None, will try to use environment variable or default path.
    
    Returns:
        Firestore client instance
    """
    global _db
    
    if _db is not None:
        return _db
    
    # Check if Firebase is already initialized
    try:
        _db = firestore.client()
        return _db
    except ValueError:
        # Not initialized yet, proceed with initialization
        pass
    
    # Determine credential path
    if credential_path is None:
        credential_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
    
    if not os.path.exists(credential_path):
        raise FileNotFoundError(
            f"Firebase credentials file not found at {credential_path}. "
            "Please provide the path to your Firebase service account JSON file."
        )
    
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate(credential_path)
    firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    _db = firestore.client()
    return _db


def get_db() -> firestore.Client:
    """
    Get the Firestore client instance.
    Ensures Firebase is initialized first.
    
    Returns:
        Firestore client instance
    """
    if _db is None:
        raise RuntimeError("Firebase not initialized. Call initialize_firebase() first.")
    return _db

