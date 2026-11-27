"""Route and service coverage for the advanced feature bundles."""

import asyncio

from app.services.notifications import NotificationService


def test_preferences_default_update_and_validation(client):
    res = client.get("/api/v1/preferences/")
    assert res.status_code == 200
    assert res.json() == {
        "theme": "dark",
        "accent": "blue",
        "density": "comfortable",
        "reduced_motion": False,
        "updated_at": None,
    }

    res = client.put(
        "/api/v1/preferences/",
        json={"theme": "light", "accent": "emerald", "reduced_motion": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["theme"] == "light"
    assert body["accent"] == "emerald"
    assert body["reduced_motion"] is True
    assert body["updated_at"] is not None

    assert client.put("/api/v1/preferences/", json={"theme": "neon"}).status_code == 422


def test_preferences_require_auth(bare_client):
    assert bare_client.get("/api/v1/preferences/").status_code == 401
    assert bare_client.put("/api/v1/preferences/", json={"theme": "light"}).status_code == 401


def test_snippet_crud(client):
    res = client.post(
        "/api/v1/terminal/snippets",
        json={"name": "Tail logs", "command": "tail -f app.log", "description": "Follow logfile"},
    )
    assert res.status_code == 201
    snippet = res.json()
    assert snippet["name"] == "Tail logs"

    res = client.get("/api/v1/terminal/snippets")
    assert [item["id"] for item in res.json()["snippets"]] == [snippet["id"]]

    res = client.patch(
        f"/api/v1/terminal/snippets/{snippet['id']}", json={"name": "Log tail"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Log tail"

    assert client.delete(f"/api/v1/terminal/snippets/{snippet['id']}").status_code == 204
    assert client.get("/api/v1/terminal/snippets").json()["snippets"] == []
    assert client.delete(f"/api/v1/terminal/snippets/{snippet['id']}").status_code == 404


def test_command_history(client):
    res = client.post("/api/v1/terminal/history", json={"command": "pytest -q"})
    assert res.status_code == 201
    assert res.json()["saved"] is True

    res = client.get("/api/v1/terminal/history")
    assert [entry["command"] for entry in res.json()["entries"]] == ["pytest -q"]

    assert client.post("/api/v1/terminal/history", json={"command": ""}).status_code == 422
    assert client.delete("/api/v1/terminal/history").status_code == 204
    assert client.get("/api/v1/terminal/history").json()["entries"] == []


def test_command_history_normalizes_string_id(client, fakes):
    asyncio.run(fakes["history"].add("test-user", "id check"))
    fakes["history"].rows[0]["id"] = 42
    res = client.get("/api/v1/terminal/history")
    assert res.status_code == 200
    assert res.json()["entries"][0]["id"] == "42"


def test_log_history_filtering(client, fakes):
    project = asyncio.run(fakes["projects"].create("Logged", owner_id="test-user"))
    asyncio.run(fakes["logs"].add("INFO", "agent-one", "alpha completed", project["id"]))
    asyncio.run(fakes["logs"].add("WARN", "agent-two", "beta warning", project["id"]))

    res = client.get("/api/v1/terminal/logs?search=alpha")
    assert res.status_code == 200
    assert [entry["agent"] for entry in res.json()["entries"]] == ["agent-one"]

    res = client.get("/api/v1/terminal/logs?level=WARN")
    assert [entry["message"] for entry in res.json()["entries"]] == ["beta warning"]


def test_terminal_routes_require_auth(bare_client):
    assert bare_client.get("/api/v1/terminal/snippets").status_code == 401
    assert bare_client.get("/api/v1/terminal/history").status_code == 401
    assert bare_client.get("/api/v1/terminal/logs").status_code == 401


def test_notification_lifecycle(client, fakes):
    service = NotificationService(repo=fakes["notifications"])
    asyncio.run(
        service.notify("test-user", title="Pipeline done", body="All stages complete", type="success")
    )

    res = client.get("/api/v1/notifications/")
    assert res.status_code == 200
    items = res.json()["notifications"]
    assert len(items) == 1
    assert items[0]["title"] == "Pipeline done"

    assert client.get("/api/v1/notifications/counts").json() == {"total": 1, "unread": 1}

    res = client.post(f"/api/v1/notifications/{items[0]['id']}/read")
    assert res.status_code == 200
    assert res.json()["read_at"] is not None
    assert client.get("/api/v1/notifications/counts").json()["unread"] == 0
    assert client.get("/api/v1/notifications/?unread_only=true").json()["notifications"] == []

    assert client.post("/api/v1/notifications/read-all").json() == {"updated": 0}
    assert client.delete(f"/api/v1/notifications/{items[0]['id']}").status_code == 204
    assert client.get("/api/v1/notifications/counts").json() == {"total": 0, "unread": 0}

    assert client.post("/api/v1/notifications/missing/read").status_code == 404
    assert client.delete("/api/v1/notifications/missing").status_code == 404


def test_clear_notifications_and_auth(client, fakes, bare_client):
    service = NotificationService(repo=fakes["notifications"])
    asyncio.run(service.notify("test-user", title="Clear me"))
    assert client.get("/api/v1/notifications/counts").json()["total"] == 1
    assert client.delete("/api/v1/notifications/").status_code == 204
    assert client.get("/api/v1/notifications/counts").json()["total"] == 0
    assert bare_client.get("/api/v1/notifications/").status_code == 401


def test_workspace_search_and_templates(client):
    res = client.get("/api/v1/workspace/search?q=metrics")
    assert res.status_code == 200
    assert any(item["href"] == "/metrics" for item in res.json()["results"])

    res = client.get("/api/v1/workspace/search?q=definitely-not-present-xyz")
    assert res.json()["results"] == []

    res = client.get("/api/v1/workspace/templates")
    assert res.status_code == 200
    assert any(template["id"] == "blank" for template in res.json()["templates"])


def test_project_template_tags_filters_and_meta(client):
    res = client.post(
        "/api/v1/projects/",
        json={"name": "Templated", "template_id": "blank", "tags": ["alpha"]},
    )
    assert res.status_code == 200
    project_id = res.json()["id"]
    assert res.json()["template_id"] == "blank"
    assert res.json()["tags"] == ["alpha"]

    bad = client.post("/api/v1/projects/", json={"name": "Bad", "template_id": "nope"})
    assert bad.status_code == 400

    res = client.patch(
        f"/api/v1/workspace/projects/{project_id}",
        json={"tags": ["beta"], "pinned": True},
    )
    assert res.status_code == 200

    detail = client.get(f"/api/v1/projects/{project_id}").json()
    assert detail["tags"] == ["beta"]
    assert detail["pinned"] is True

    listing = client.get("/api/v1/projects/?tag=beta&status=queued&search=templated")
    assert [p["id"] for p in listing.json()["projects"]] == [project_id]
    assert client.get("/api/v1/projects/?tag=missing").json()["projects"] == []

    assert client.patch(
        f"/api/v1/workspace/projects/{project_id}", json={"template_id": "nope"}
    ).status_code == 400
    assert client.patch(
        "/api/v1/workspace/projects/missing", json={"pinned": True}
    ).status_code == 404


def test_bulk_project_actions(client, fakes):
    first = asyncio.run(fakes["projects"].create("Bulk one", owner_id="test-user"))
    second = asyncio.run(fakes["projects"].create("Bulk two", owner_id="test-user"))
    ids = [first["id"], second["id"]]

    def bulk(action, value=None):
        payload = {"ids": ids, "action": action}
        if value is not None:
            payload["value"] = value
        return client.post("/api/v1/workspace/projects/bulk", json=payload)

    assert bulk("tag", "urgent").json() == {"affected": 2, "action": "tag"}
    assert bulk("pin").json()["affected"] == 2
    assert bulk("status", "delivered").json()["affected"] == 2
    assert bulk("untag", "urgent").json()["affected"] == 2
    assert bulk("unpin").json()["affected"] == 2
    assert bulk("delete").json()["affected"] == 2
    assert client.get("/api/v1/projects/").json()["projects"] == []

    assert bulk("status", "bogus").status_code == 400
    assert bulk("tag").status_code == 400
    assert client.post(
        "/api/v1/workspace/projects/bulk", json={"ids": [], "action": "pin"}
    ).status_code == 422


def test_workspace_metrics_and_audit(client, fakes):
    asyncio.run(fakes["projects"].create("Measured", owner_id="test-user", tags=["x"]))
    service = NotificationService(repo=fakes["notifications"])
    asyncio.run(service.notify("test-user", title="Unread me"))
    asyncio.run(
        fakes["admin"].insert_event(
            {"status": "open", "severity": "warn", "title": "Finding", "owner_id": "test-user"}
        )
    )

    res = client.get("/api/v1/workspace/metrics")
    assert res.status_code == 200
    body = res.json()
    assert body["projects_total"] == 1
    assert body["projects_by_status"]["queued"] == 1
    assert len(body["projects_recent"]) == 7
    assert body["notifications_unread"] == 1
    assert body["sentinel_open"] == 1
    assert body["app_status"] == "running"

    res = client.get("/api/v1/workspace/audit?action=project.bulk.pin")
    assert res.status_code == 200
    assert res.json()["entries"] == []

    # test-user is not an admin under the default settings.
    assert client.get("/api/v1/workspace/audit?all_users=true").status_code == 403
