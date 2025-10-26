"""
Integration tests for the complete application workflow
"""

import pytest
from fastapi.testclient import TestClient


def test_complete_signup_flow(client, reset_activities):
    """Test the complete flow of viewing activities and signing up"""
    # 1. Get all activities
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # 2. Pick an activity with available spots
    activity_name = None
    original_count = 0
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            original_count = len(details["participants"])
            break
    
    assert activity_name is not None
    
    # 3. Sign up for the activity
    test_email = "integration@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 200
    
    # 4. Verify the signup worked
    response = client.get(f"/activities/{activity_name}")
    assert response.status_code == 200
    activity = response.json()
    assert len(activity["participants"]) == original_count + 1
    assert test_email in activity["participants"]
    
    # 5. Test unregistering
    response = client.delete(f"/activities/{activity_name}/unregister?email={test_email}")
    assert response.status_code == 200
    
    # 6. Verify unregistration worked
    response = client.get(f"/activities/{activity_name}")
    assert response.status_code == 200
    activity = response.json()
    assert len(activity["participants"]) == original_count
    assert test_email not in activity["participants"]


def test_multiple_activities_signup(client, reset_activities):
    """Test signing up for multiple activities with the same email"""
    response = client.get("/activities")
    activities = response.json()
    
    # Find at least 2 activities with available spots
    available_activities = []
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            available_activities.append(name)
        if len(available_activities) >= 2:
            break
    
    assert len(available_activities) >= 2, "Need at least 2 activities with available spots"
    
    test_email = "multisignup@mergington.edu"
    
    # Sign up for both activities
    for activity_name in available_activities[:2]:
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        assert response.status_code == 200
    
    # Verify participation in both
    for activity_name in available_activities[:2]:
        response = client.get("/activities")
        all_activities = response.json()
        activity = all_activities[activity_name]
        assert test_email in activity["participants"]


def test_activity_capacity_management(client, reset_activities):
    """Test that activity capacity is properly managed"""
    response = client.get("/activities")
    activities = response.json()
    
    # Find an activity with at least 2 spots available
    activity_name = None
    available_spots = 0
    for name, details in activities.items():
        spots = details["max_participants"] - len(details["participants"])
        if spots >= 2:
            activity_name = name
            available_spots = spots
            break
    
    assert activity_name is not None, "Need an activity with at least 2 available spots"
    
    # Fill up all but one spot
    for i in range(available_spots - 1):
        test_email = f"capacity{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        assert response.status_code == 200
    
    # Add the last participant
    response = client.post(f"/activities/{activity_name}/signup?email=lastone@mergington.edu")
    assert response.status_code == 200
    
    # Try to add one more (should fail)
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_error_handling_chain(client):
    """Test a chain of error conditions"""
    # Test 404 for non-existent activity
    response = client.get("/activities/DoesNotExist")
    assert response.status_code == 404
    
    # Test 404 for signup to non-existent activity
    response = client.post("/activities/DoesNotExist/signup?email=test@mergington.edu")
    assert response.status_code == 404
    
    # Test 404 for unregister from non-existent activity
    response = client.delete("/activities/DoesNotExist/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    
    # Test invalid email format
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    
    response = client.post(f"/activities/{activity_name}/signup?email=invalid")
    assert response.status_code == 400
    assert "invalid email" in response.json()["detail"].lower()