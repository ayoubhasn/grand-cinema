"""Tests d'authentification : inscription, connexion, profil."""

from tests.conftest import login


def test_register_creates_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "nouveau@exemple.fr",
            "password": "Secret123!",
            "full_name": "Nouveau",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "nouveau@exemple.fr"
    assert response.json()["role"] == "user"


def test_register_duplicate_email_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@grandcinema.fr", "password": "Secret123!"},
    )
    assert response.status_code == 400


def test_login_success_sets_cookie_and_me_works(client):
    response = login(client, "user@grandcinema.fr", "User123!")
    assert response.status_code == 200
    assert response.json()["email"] == "user@grandcinema.fr"
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["role"] == "user"


def test_login_wrong_password_rejected(client):
    response = login(client, "user@grandcinema.fr", "MauvaisMotDePasse")
    assert response.status_code == 401


def test_me_without_auth_rejected(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout_clears_session(client):
    login(client, "user@grandcinema.fr", "User123!")
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
