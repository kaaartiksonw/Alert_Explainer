# Alert Explainer API

The capstone's AI intelligence layer is a FastAPI service that stores monitoring
alerts in SQLite and returns rule-based explanations. It does not call an
external AI or LLM service.

Explanations include the alert's title, source, severity, metric value and
threshold comparison, a fixed severity-specific recommended next step, and
acknowledgement text. Comparisons are "exceeded", "fell below", or "reached".
If an optional `resolved_by` attribute is truthy, its value is uppercased;
otherwise the text is `Not yet acknowledged`. The current model and API have
no `resolved_by` field or acknowledgement endpoint, so alerts created through
this API use the default acknowledgement text.

## Project Structure

```text
alert_explainer_api/
|-- database.py             # SQLite engine, sessions, and declarative base
|-- main.py                 # Table creation, FastAPI app, and root endpoint
|-- models.py               # SQLAlchemy Alert model
|-- schemas.py              # Pydantic request and response schemas
|-- requirements.txt        # Runtime dependencies
|-- routers/
|   |-- __init__.py
|   `-- alerts.py           # Alert creation, listing, retrieval, and explanation
|-- services/
|   |-- __init__.py
|   `-- explainer.py        # Fixed explanation rules
|-- test_alerts.py          # API tests using an in-memory SQLite database
|-- docs/adr/
|   |-- 0001-rule-based-explanations.md
|   `-- 0002-human-approval-for-alert-summaries.md
`-- README.md
```

The application creates `alerts.db` in the current working directory and creates
missing tables when `main` is imported. Run commands from the project root.

## Alert Fields

All six input fields are required for `POST /alerts/`. Responses include those
fields plus the generated `id` and `created_at` fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | integer | Database-generated primary key; response only. |
| `title` | string | Alert title. |
| `severity` | string | Must be `critical`, `warning`, or `info`. |
| `source` | string | Origin of the alert. |
| `metric_name` | string | Name of the monitored metric. |
| `metric_value` | float | Current metric value. |
| `threshold` | float | Value against which the metric is compared. |
| `created_at` | datetime | Creation timestamp; response only, defaults to the current UTC time. |

Pydantic restricts severity to the three listed values. The SQLAlchemy model
stores severity as a string and does not enforce that enumeration in the
database. SQLite does not preserve timezone information for the stored datetime;
`created_at` responses may therefore omit a timezone offset.

## Endpoints

| Method | Path | Returns | Status Codes |
| --- | --- | --- | --- |
| GET | `/` | `{"status":"Alert Explainer API is running"}` | `200` |
| POST | `/alerts/` | Created alert, including ID and creation timestamp | `201`; `422` for invalid input |
| GET | `/alerts/` | All alerts ordered by ascending ID; `[]` if empty | `200` |
| GET | `/alerts/{alert_id}` | One alert | `200`; `404` if absent; `422` for an invalid integer ID |
| POST | `/alerts/{alert_id}/explain` | `alert_id`, `explanation`, and `generated_at` | `200`; `404` if absent; `422` for an invalid integer ID |

Both alert-specific endpoints return `{"detail":"Alert not found"}` for an
unknown integer ID. The explain endpoint takes no request body and returns a
UTC generation timestamp. Its explanation text is deterministic for the same
alert fields, but `generated_at` changes on each call. There are no update,
delete, summary-delivery, or approval endpoints. Use the trailing slashes shown
for collection routes; `/alerts` redirects to `/alerts/` with `307`.

FastAPI also provides `GET /docs` (Swagger UI), `GET /redoc` (ReDoc),
`GET /openapi.json` (OpenAPI schema), and `GET /docs/oauth2-redirect` (Swagger
OAuth2 redirect helper), each returning `200`.

## Install And Run

Python 3.12 is the verified runtime. The runtime dependencies are FastAPI,
Uvicorn, SQLAlchemy, and Pydantic. Tests additionally require pytest and httpx.

### Windows PowerShell

Open PowerShell in the project folder. Create the virtual environment only if
it does not already exist:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pytest httpx
uvicorn main:app --reload
```

### Linux Or macOS

Open a terminal in the project folder. Create the virtual environment only if
it does not already exist:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest httpx
uvicorn main:app --reload
```

The server runs at http://127.0.0.1:8000. Open the Swagger UI at
http://127.0.0.1:8000/docs and expand `POST /alerts/{alert_id}/explain` to see the
route description, including its 404 case. Stop the server with Ctrl+C.

No LLM API key or external database is needed. Installing dependencies requires
package access; the explanation rules themselves run offline.

## Tests

With the virtual environment activated, run from the project root:

```text
python -m pytest test_alerts.py -v
```

Expected result: **8 passed**. The tests override the database dependency with
an in-memory SQLite database. Importing the application still initializes the
local database tables. Tests cover creation, listing, retrieval, explanation,
missing alerts for explanation, below-threshold values, a zero threshold, and
the default acknowledgement text.

## Architecture Decisions

- [ADR 0001: Rule-based explanations](docs/adr/0001-rule-based-explanations.md)
  records speed and cost, offline CI, determinism, and the generic-explanation
  trade-off.
- [ADR 0002: Human approval for alert summaries](docs/adr/0002-human-approval-for-alert-summaries.md)
  records the capstone's n8n workflow decision to require approval before sending
  summaries to the on-call channel, for incident safety. That external workflow
  is not included or enforced by this API repository.