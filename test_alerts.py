from datetime import datetime
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


def _create_alert(client: TestClient, **overrides: str | float) -> dict[str, Any]:
    payload: dict[str, str | float] = {
        "title": "Test alert",
        "severity": "warning",
        "source": "test-source",
        "metric_name": "test_metric",
        "metric_value": 50.0,
        "threshold": 40.0,
    }
    payload.update(overrides)
    response = client.post("/alerts/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_alert(client: TestClient) -> None:
    response = client.post(
        "/alerts/",
        json={
            "title": "CPU usage high",
            "severity": "critical",
            "source": "monitoring",
            "metric_name": "cpu_usage",
            "metric_value": 95.0,
            "threshold": 80.0,
        },
    )

    assert response.status_code == 201
    alert = response.json()
    assert alert["id"] == 1
    assert alert["title"] == "CPU usage high"
    assert alert["severity"] == "critical"
    assert alert["metric_name"] == "cpu_usage"


def test_list_alerts(client: TestClient) -> None:
    _create_alert(client, title="First alert")
    _create_alert(client, title="Second alert")

    response = client.get("/alerts/")

    assert response.status_code == 200
    assert [alert["title"] for alert in response.json()] == [
        "First alert",
        "Second alert",
    ]


def test_get_alert_by_id(client: TestClient) -> None:
    alert = _create_alert(client)

    response = client.get(f"/alerts/{alert['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == alert["id"]
    assert response.json()["title"] == "Test alert"


def test_explain_alert(client: TestClient) -> None:
    alert = _create_alert(client)

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    explanation = response.json()
    assert explanation["alert_id"] == alert["id"]
    assert "warning" in explanation["explanation"]
    assert "test_metric" in explanation["explanation"]
    assert datetime.fromisoformat(
        explanation["generated_at"].replace("Z", "+00:00")
    )


def test_explain_alert_for_nonexistent_id_returns_404(
    client: TestClient,
) -> None:
    response = client.post("/alerts/999/explain")

    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"


def test_explain_alert_when_metric_is_below_threshold(
    client: TestClient,
) -> None:
    alert = _create_alert(
        client,
        title="Connection pool below minimum",
        severity="warning",
        source="db-pool",
        metric_name="active_connections",
        metric_value=2,
        threshold=10,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "fell below its threshold" in response.json()["explanation"]


def test_explain_alert_with_zero_threshold_does_not_crash(
    client: TestClient,
) -> None:
    alert = _create_alert(
        client,
        title="Unexpected traffic on idle endpoint",
        severity="info",
        source="edge-cache",
        metric_name="request_count",
        metric_value=5,
        threshold=0,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "threshold of 0.0" in response.json()["explanation"]


@pytest.fixture
def client() -> Iterator[TestClient]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db() -> Iterator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()
