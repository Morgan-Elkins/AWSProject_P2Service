import pytest
from app import create_app, send_jira_message


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture()
def client(app):
    with app.app_context():
        return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_get_health(client):
    response = client.get("/health")
    assert b"Healthy" in response.data

def test_sending_jira_message(client):
    data = {"title": "pytest", "desc": "pytest desc", "prio": 0}
    response = send_jira_message(data)
    assert response == "Issue created successfully!"