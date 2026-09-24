def test_create_project_requires_auth(bare_client):
    res = bare_client.post("/api/v1/projects/", json={"name": "Secret"})
    assert res.status_code == 401


def test_create_and_fetch_project(client, fakes):
    res = client.post("/api/v1/projects/", json={"name": "Demo Project", "repo_url": "https://github.com/x/y"})
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Demo Project"
    assert body["status"] == "analyzing"
    assert body["progress"] >= 10

    res = client.get(f"/api/v1/projects/{body['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "Demo Project"


def test_missing_project_returns_404(client):
    res = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_audit_trails_are_recorded(client, fakes):
    client.post("/api/v1/projects/", json={"name": "Audited"})
    actions = [e["action"] for e in fakes["audit"].entries]
    assert "project.create" in actions