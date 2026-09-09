"""
Integration tests for FastAPI endpoints using AAA (Arrange-Act-Assert) pattern.

Tests cover:
- GET /activities — Retrieve all available activities
- GET / — Root redirect endpoint
- POST /activities/{activity_name}/signup — Register a student for an activity
- DELETE /activities/{activity_name}/unregister — Unregister a student from an activity
"""

import pytest
from fastapi.testclient import TestClient
from conftest import is_participant_registered, get_participant_count


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_all_activities_returns_200(self, client: TestClient):
        """
        Arrange: Client ready
        Act: Send GET request to /activities
        Assert: Response status is 200 OK
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
    
    def test_get_all_activities_returns_all_activities(self, client: TestClient):
        """
        Arrange: Client ready
        Act: Send GET request to /activities
        Assert: Response contains all 9 activities with correct structure
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_response_has_correct_schema(self, client: TestClient):
        """
        Arrange: Client ready
        Act: Send GET request to /activities
        Assert: Each activity has required fields (description, schedule, max_participants, participants)
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_participant_counts_are_correct(self, client: TestClient):
        """
        Arrange: Client ready
        Act: Send GET request to /activities
        Assert: Participant count matches actual participants list length
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            max_participants = activity_details["max_participants"]
            participant_list = activity_details["participants"]
            assert len(participant_list) <= max_participants


class TestRootEndpoint:
    """Tests for GET / (root) endpoint."""
    
    def test_root_redirects_to_static_index(self, client: TestClient):
        """
        Arrange: Client ready
        Act: Send GET request to /
        Assert: Response is a redirect (307) to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful_adds_participant(self, client: TestClient):
        """
        Arrange: Client ready, valid activity exists
        Act: POST request with new student email
        Assert: Response is 200, participant is added to activity
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        initial_count = get_participant_count(activity_name)
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert is_participant_registered(activity_name, new_email)
        assert get_participant_count(activity_name) == initial_count + 1
    
    def test_signup_returns_success_message(self, client: TestClient):
        """
        Arrange: Client ready, valid activity exists
        Act: POST request with new student email
        Assert: Response message is correctly formatted
        """
        # Arrange
        activity_name = "Programming Class"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
    
    def test_signup_for_different_activities_independently(self, client: TestClient):
        """
        Arrange: Client ready, two different activities exist
        Act: Sign up for Activity A, then Activity B
        Assert: Signup for A doesn't affect B, and vice versa
        """
        # Arrange
        email = "student@mergington.edu"
        activity_a = "Chess Club"
        activity_b = "Drama Club"
        
        # Act
        response_a = client.post(
            f"/activities/{activity_a}/signup",
            params={"email": email}
        )
        response_b = client.post(
            f"/activities/{activity_b}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response_a.status_code == 200
        assert response_b.status_code == 200
        assert is_participant_registered(activity_a, email)
        assert is_participant_registered(activity_b, email)


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_successful_removes_participant(self, client: TestClient):
        """
        Arrange: Client ready, participant is registered
        Act: DELETE request with registered email
        Assert: Response is 200, participant is removed from activity
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Known participant
        initial_count = get_participant_count(activity_name)
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert not is_participant_registered(activity_name, email)
        assert get_participant_count(activity_name) == initial_count - 1
    
    def test_unregister_returns_success_message(self, client: TestClient):
        """
        Arrange: Client ready, participant is registered
        Act: DELETE request with registered email
        Assert: Response message is correctly formatted
        """
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # Known participant
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
    
    def test_unregister_from_different_activities_independently(self, client: TestClient):
        """
        Arrange: Client ready, participant in two activities
        Act: Unregister from Activity A only
        Assert: Participant is removed from A but still in B
        """
        # Arrange
        email = "sophia@mergington.edu"  # Participant in Tennis Club and Programming Class
        activity_keep = "Programming Class"
        activity_remove = "Tennis Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_remove}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert not is_participant_registered(activity_remove, email)
        assert is_participant_registered(activity_keep, email)
