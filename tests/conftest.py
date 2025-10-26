"""
Fixtures and configuration for pytest tests
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the src directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Sample activities data for testing"""
    return {
        "Test Activity": {
            "description": "A test activity for testing purposes",
            "schedule": "Test Schedule",
            "max_participants": 5,
            "participants": ["test1@mergington.edu", "test2@mergington.edu"]
        },
        "Empty Activity": {
            "description": "An activity with no participants",
            "schedule": "Whenever",
            "max_participants": 10,
            "participants": []
        }
    }


@pytest.fixture
def reset_activities():
    """Fixture to reset activities to original state after each test"""
    # Import the activities from the app module
    from app import activities
    
    # Store original activities
    original_activities = activities.copy()
    
    yield
    
    # Reset activities to original state
    activities.clear()
    activities.update(original_activities)