"""
Tests for the Mergington High School extracurricular activities API
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have all activities
        assert "Baseball Team" in data
        assert "Soccer Club" in data
        assert "Music Band" in data
        assert "Drama Club" in data
        assert "Debate Team" in data
        assert "Science Club" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_contains_activity_details(self, client):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Baseball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_contains_participants(self, client):
        """Test that activities include participant information"""
        response = client.get("/activities")
        data = response.json()
        
        # Baseball Team should have alex@mergington.edu
        assert "alex@mergington.edu" in data["Baseball Team"]["participants"]
        # Music Band should have two participants
        assert len(data["Music Band"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Baseball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        # Signup for activity
        client.post("/activities/Soccer Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Soccer Club"]["participants"]

    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test that signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up twice with same email fails"""
        email = "duplicate@mergington.edu"
        activity = "Drama Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_existing_participant_fails(self, client):
        """Test that signup with an already registered participant fails"""
        response = client.post(
            "/activities/Baseball Team/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from activity"""
        response = client.delete(
            "/activities/Baseball Team/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alex@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # Unregister
        client.delete(
            "/activities/Music Band/unregister?email=maya@mergington.edu"
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert "maya@mergington.edu" not in activities["Music Band"]["participants"]
        # But lucas should still be there
        assert "lucas@mergington.edu" in activities["Music Band"]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-participant fails"""
        response = client.delete(
            "/activities/Baseball Team/unregister?email=nosuchstudent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_twice_fails(self, client):
        """Test that unregistering twice fails on second attempt"""
        email = "student@mergington.edu"
        activity = "Soccer Club"
        
        # First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # First unregister should succeed
        response1 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"]


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        activity = "Science Club"
        
        # Verify student not in activity
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify student is now in activity
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify student is removed from activity
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple students signing up and unregistering"""
        activity = "Chess Club"
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # All students signup
        for email in students:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are signed up
        response = client.get("/activities")
        for email in students:
            assert email in response.json()[activity]["participants"]
        
        # Unregister student2
        response = client.delete(f"/activities/{activity}/unregister?email={students[1]}")
        assert response.status_code == 200
        
        # Verify student2 is removed but others remain
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert students[0] in participants
        assert students[1] not in participants
        assert students[2] in participants
