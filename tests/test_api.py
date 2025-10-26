"""
Test the main API endpoints
"""

import pytest
from fastapi.testclient import TestClient
import json


def test_root_redirect(client):
    """Test that root path redirects to static files"""
    response = client.get("/")
    assert response.status_code == 200


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    
    # Check that we have some default activities
    assert len(activities) > 0
    
    # Check structure of activities
    for activity_name, details in activities.items():
        assert isinstance(activity_name, str)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)
        assert isinstance(details["max_participants"], int)


def test_get_specific_activity(client):
    """Test getting a specific activity"""
    # First get all activities to find one that exists
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    
    # Test getting the specific activity
    response = client.get(f"/activities/{activity_name}")
    assert response.status_code == 200
    
    activity = response.json()
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


def test_get_nonexistent_activity(client):
    """Test getting a non-existent activity returns 404"""
    response = client.get("/activities/NonExistentActivity")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_for_activity_success(client, reset_activities):
    """Test successful signup for an activity"""
    # Get an activity with available spots
    response = client.get("/activities")
    activities = response.json()
    
    # Find an activity with available spots
    activity_name = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            break
    
    assert activity_name is not None, "No activities with available spots found"
    
    # Sign up for the activity
    test_email = "newstudent@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "successfully" in result["message"].lower()
    
    # Verify the participant was added
    response = client.get(f"/activities/{activity_name}")
    activity = response.json()
    assert test_email in activity["participants"]


def test_signup_duplicate_participant(client, reset_activities):
    """Test that signing up twice with same email fails"""
    # Get an activity and find an existing participant
    response = client.get("/activities")
    activities = response.json()
    
    activity_name = None
    existing_email = None
    for name, details in activities.items():
        if details["participants"]:
            activity_name = name
            existing_email = details["participants"][0]
            break
    
    assert activity_name is not None, "No activities with participants found"
    
    # Try to sign up with existing email
    response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_activity_full(client, reset_activities):
    """Test signup when activity is full"""
    # First, let's create a scenario where an activity becomes full
    response = client.get("/activities")
    activities = response.json()
    
    # Find an activity we can fill up
    activity_name = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            break
    
    assert activity_name is not None
    
    # Get the activity details to find spots left
    activity_response = client.get("/activities")
    all_activities = activity_response.json()
    activity = all_activities[activity_name]
    spots_left = activity["max_participants"] - len(activity["participants"])
    
    # Add participants until full
    for i in range(spots_left):
        test_email = f"student{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        assert response.status_code == 200
    
    # Now try to add one more participant
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_signup_nonexistent_activity(client):
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistentActivity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_invalid_email(client):
    """Test signup with invalid email format"""
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    
    # Test with invalid email
    response = client.post(f"/activities/{activity_name}/signup?email=invalid-email")
    assert response.status_code == 400
    assert "invalid email" in response.json()["detail"].lower()


def test_unregister_participant_success(client, reset_activities):
    """Test successful unregistration of a participant"""
    # First get an activity with participants
    response = client.get("/activities")
    activities = response.json()
    
    activity_name = None
    existing_email = None
    for name, details in activities.items():
        if details["participants"]:
            activity_name = name
            existing_email = details["participants"][0]
            break
    
    assert activity_name is not None, "No activities with participants found"
    
    # Unregister the participant
    response = client.delete(f"/activities/{activity_name}/unregister?email={existing_email}")
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "unregistered" in result["message"].lower()
    
    # Verify the participant was removed
    response = client.get(f"/activities/{activity_name}")
    activity = response.json()
    assert existing_email not in activity["participants"]


def test_unregister_nonexistent_participant(client):
    """Test unregistering a participant who isn't registered"""
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    
    response = client.delete(f"/activities/{activity_name}/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_nonexistent_activity(client):
    """Test unregistering from non-existent activity"""
    response = client.delete("/activities/NonExistentActivity/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()