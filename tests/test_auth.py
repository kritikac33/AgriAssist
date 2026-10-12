import pytest
from fastapi import status


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_user(self, client, test_user_data):
        """Test user registration."""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email fails."""
        # First registration
        client.post("/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpass123"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_invalid_password(self, client, test_user_data):
        """Test login with invalid password."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client, test_user_data):
        """Test getting current user info with valid token."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token fails."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, test_user_data):
        """Test token refresh."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token fails."""
        response = client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRBAC:
    """Test role-based access control."""
    
    def test_admin_access(self, client, admin_user_data):
        """Test admin can access admin-only endpoints (when implemented)."""
        # Register admin
        client.post("/auth/register", json=admin_user_data)
        login_response = client.post("/auth/login", json={
            "email": admin_user_data["email"],
            "password": admin_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Verify user has admin role
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "admin"
    
    def test_officer_access(self, client, officer_user_data):
        """Test officer role is correctly assigned."""
        # Register officer
        client.post("/auth/register", json=officer_user_data)
        login_response = client.post("/auth/login", json={
            "email": officer_user_data["email"],
            "password": officer_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Verify user has officer role
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "officer"
    
    def test_farmer_access(self, client, test_user_data):
        """Test farmer role is correctly assigned."""
        # Register farmer
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Verify user has farmer role
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "farmer"
    
    def test_cross_role_access_blocked(self, client, test_user_data, admin_user_data):
        """Test that users cannot access endpoints for other roles.
        
        Note: This test will be more meaningful when role-specific endpoints
        are implemented in later parts. For now, it verifies that the
        authentication system correctly assigns and verifies roles.
        """
        # Register farmer and admin
        client.post("/auth/register", json=test_user_data)
        client.post("/auth/register", json=admin_user_data)
        
        # Login as farmer
        farmer_login = client.post("/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        farmer_token = farmer_login.json()["access_token"]
        
        # Login as admin
        admin_login = client.post("/auth/login", json={
            "email": admin_user_data["email"],
            "password": admin_user_data["password"]
        })
        admin_token = admin_login.json()["access_token"]
        
        # Verify roles are different
        farmer_me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
        admin_me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert farmer_me.json()["role"] == "farmer"
        assert admin_me.json()["role"] == "admin"
        assert farmer_me.json()["id"] != admin_me.json()["id"]
