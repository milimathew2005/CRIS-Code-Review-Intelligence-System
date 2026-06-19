def test_health_check(client):
    """
    Verifies that the /health endpoint executes successfully.
    Note: Database status check will execute sqlite check in mock.
    """
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "database" in response.json()

def test_reviews_skeleton_endpoint(client):
    """
    Verifies the code review routing endpoint behaves as expected in skeleton mode.
    """
    payload = {
        "file_content": "def main():\n    print('Hello World')",
        "diff_content": None
    }
    response = client.post("/api/v1/reviews/review", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "backend setup verified" in data["summary"].lower()
    assert len(data["issues"]) > 0
    assert data["issues"][0]["file_path"] == "main.py"
