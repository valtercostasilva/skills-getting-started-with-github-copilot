"""
Validation and error handling tests using AAA (Arrange-Act-Assert) pattern.

Tests cover error scenarios and edge cases:
- 404 errors for non-existent activities
- 400 errors for duplicate signups, capacity limits, and invalid unregistrations
- Boundary conditions (exactly at capacity, one spot remaining)
- Activity capacity enforcement
"""

import pytest
from fastapi.testclient import TestClient
from conftest import is_participant_registered, get_participant_count


class TestSignupValidation:
    """Tests for signup endpoint validation and error handling."""
    
    def test_signup_nonexistent_activity_returns_404(self, client: TestClient):
        """
        Arrange: Invalid activity name prepared
        Act: POST signup request with non-existent activity
        Assert: Response is 404 with 'Activity not found' message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email_returns_400(self, client: TestClient):
        """
        Arrange: Student already signed up for activity
        Act: POST signup request with same email
        Assert: Response is 400 with 'already signed up' message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_at_capacity_returns_400(self, client: TestClient):
        """
        Arrange: Create activity with exact capacity (fill it up)
        Act: POST signup request when at maximum
        Assert: Response is 400 with 'at maximum capacity' message
        """
        # Arrange - Use an activity with small capacity and fill it
        # We'll modify Tennis Club which has max_participants=10, currently 1 participant
        from src.app import activities
        activity_name = "Tennis Club"
        # Fill the activity to capacity
        for i in range(9):  # Already has 1 (sophia), add 9 more = 10 total
            activities[activity_name]["participants"].append(f"participant{i}@mergington.edu")
        
        new_email = "attemptfull@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"].lower()
        assert not is_participant_registered(activity_name, new_email)
    
    def test_signup_one_spot_available_succeeds(self, client: TestClient):
        """
        Arrange: Activity with one spot remaining
        Act: POST signup request
        Assert: Response is 200, participant is added
        """
        # Arrange
        from src.app import activities
        activity_name = "Drama Club"
        # Drama Club has max 25, currently 2 participants
        # Fill to 24 (one spot left)
        for i in range(22):
            activities[activity_name]["participants"].append(f"filler{i}@mergington.edu")
        
        new_email = "lastspot@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert is_participant_registered(activity_name, new_email)
        assert get_participant_count(activity_name) == 25


class TestUnregisterValidation:
    """Tests for unregister endpoint validation and error handling."""
    
    def test_unregister_nonexistent_activity_returns_404(self, client: TestClient):
        """
        Arrange: Invalid activity name prepared
        Act: DELETE unregister request with non-existent activity
        Assert: Response is 404 with 'Activity not found' message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_not_signed_up_returns_400(self, client: TestClient):
        """
        Arrange: Email never signed up for activity
        Act: DELETE unregister request with unregistered email
        Assert: Response is 400 with 'not signed up' message
        """
        # Arrange
        activity_name = "Science Club"
        unknown_email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": unknown_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_creates_available_spot(self, client: TestClient):
        """
        Arrange: Activity at capacity with registered participant
        Act: DELETE unregister to free up a spot
        Assert: Spot count increases by 1
        """
        # Arrange
        from src.app import activities
        activity_name = "Basketball Team"
        # Fill Basketball Team to capacity (max=15, currently 1)
        for i in range(14):
            activities[activity_name]["participants"].append(f"player{i}@mergington.edu")
        
        email_to_remove = activities[activity_name]["participants"][0]
        count_before = get_participant_count(activity_name)
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        assert get_participant_count(activity_name) == count_before - 1
        assert not is_participant_registered(activity_name, email_to_remove)


class TestCapacityBoundary:
    """Tests for activity capacity boundary conditions."""
    
    def test_signup_exactly_at_capacity_boundary(self, client: TestClient):
        """
        Arrange: Activity with max_participants=12, currently 11 participants
        Act: Signup first student (fills last spot), then signup another
        Assert: First succeeds (200), second fails (400 at capacity)
        """
        # Arrange
        from src.app import activities
        activity_name = "Chess Club"
        # Chess Club has max 12, currently 2, add 9 more = 11 total
        for i in range(9):
            activities[activity_name]["participants"].append(f"chess{i}@mergington.edu")
        
        last_spot_email = "chessfinale@mergington.edu"
        overflow_email = "chessoverflow@mergington.edu"
        
        # Act - Fill the last spot
        response_fill = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": last_spot_email}
        )
        
        # Act - Try to exceed capacity
        response_overflow = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": overflow_email}
        )
        
        # Assert
        assert response_fill.status_code == 200
        assert get_participant_count(activity_name) == 12  # Now at capacity
        assert response_overflow.status_code == 400
        assert "capacity" in response_overflow.json()["detail"].lower()
        assert not is_participant_registered(activity_name, overflow_email)
    
    def test_signup_after_unregister_fills_spot(self, client: TestClient):
        """
        Arrange: Activity at capacity, then unregister one participant
        Act: Signup a new student after unregister
        Assert: New signup succeeds, can reach capacity again
        """
        # Arrange
        from src.app import activities
        activity_name = "Art Studio"
        # Fill Art Studio to capacity (max=18, currently 1)
        for i in range(17):
            activities[activity_name]["participants"].append(f"artist{i}@mergington.edu")
        
        participant_to_remove = activities[activity_name]["participants"][0]
        new_student = "newartist@mergington.edu"
        
        # Act - Remove one participant
        response_remove = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": participant_to_remove}
        )
        
        count_after_remove = get_participant_count(activity_name)
        
        # Act - Fill the spot with new student
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        
        # Assert
        assert response_remove.status_code == 200
        assert count_after_remove == 17
        assert response_signup.status_code == 200
        assert get_participant_count(activity_name) == 18  # Back at capacity
        assert is_participant_registered(activity_name, new_student)


class TestSignupAndUnregisterSequence:
    """Tests for signup and unregister sequences and interactions."""
    
    def test_signup_then_unregister_same_email(self, client: TestClient):
        """
        Arrange: Email ready, activity ready
        Act: POST signup, then DELETE unregister same email
        Assert: Both succeed, email not in participants after sequence
        """
        # Arrange
        activity_name = "Science Club"
        email = "scientist@mergington.edu"
        
        # Act - Signup
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup succeeded
        assert response_signup.status_code == 200
        assert is_participant_registered(activity_name, email)
        
        # Act - Unregister
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert unregister succeeded
        assert response_unregister.status_code == 200
        assert not is_participant_registered(activity_name, email)
    
    def test_multiple_signups_and_unregisters_independent(self, client: TestClient):
        """
        Arrange: Multiple emails and activities ready
        Act: Signup and unregister multiple participants
        Assert: Each operation is independent and correct
        """
        # Arrange
        activity = "Debate Team"
        emails = ["debater1@mergington.edu", "debater2@mergington.edu", "debater3@mergington.edu"]
        
        # Act - Signup all
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            assert is_participant_registered(activity, email)
        
        # Act - Unregister middle one
        response_middle = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": emails[1]}
        )
        
        # Assert
        assert response_middle.status_code == 200
        assert is_participant_registered(activity, emails[0])
        assert not is_participant_registered(activity, emails[1])
        assert is_participant_registered(activity, emails[2])
