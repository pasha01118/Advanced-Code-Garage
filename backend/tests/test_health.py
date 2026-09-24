def test_health(bare_client):
    res = bare_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root(bare_client):
    res = bare_client.get("/")
    assert res.status_code == 200
    assert res.json()["system"] == "Advanced Code Garage"