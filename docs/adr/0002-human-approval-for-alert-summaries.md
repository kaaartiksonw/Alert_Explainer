## Title

0002: Human approval for alert summaries

## Status

Accepted

## Context

An incorrect or misleading automated summary in the on-call channel could cause
the on-call engineer to under-react or over-react to a real incident. A few
minutes of approval delay costs much less than a bad summary during an active
incident.

## Decision

The n8n alert-summary workflow routes each generated summary to a human for
approval before it is sent to the on-call channel instead of sending it
automatically.

## Consequences

- Human approval addresses the risk that an incorrect or misleading summary
  causes the on-call engineer to under-react or over-react to a real incident.
- Summary delivery is slower.
- Delivery depends on someone being available to approve.