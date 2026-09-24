def test_swarm_returns_roster_and_persistent_mode(client):
    res = client.get("/api/v1/agents/swarm")
    assert res.status_code == 200
    body = res.json()
    assert len(body["active_agents"]) == 4
    assert body["system_mode"] == "AI-Man"
    assert body["security_gate"] == "Active"


def test_mode_update_is_persisted_across_reads(client):
    res = client.post("/api/v1/agents/mode", json={"mode": "Autonomous"})
    assert res.status_code == 200
    assert res.json()["system_mode"] == "Autonomous"

    res = client.get("/api/v1/agents/swarm")
    assert res.json()["system_mode"] == "Autonomous"


def test_mode_rejects_invalid_value(client):
    res = client.post("/api/v1/agents/mode", json={"mode": "chaotic"})
    assert res.status_code == 422


def test_mode_requires_auth(bare_client, fakes):
    res = bare_client.post("/api/v1/agents/mode", json={"mode": "Manual"})
    assert res.status_code == 401
    assert fakes["modes"].value == "AI-Man"