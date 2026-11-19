from models import Alert

NEXT_STEPS = {
    "critical": "Investigate immediately and take corrective action.",
    "warning": "Review the affected system and monitor the metric closely.",
    "info": "Review the metric and confirm whether any action is needed.",
}


def generate_explanation(alert: Alert) -> str:
    """Build an explanation from the alert's own fields using fixed rules.

    Args:
        alert: Alert whose severity selects a recommended next step and whose
            metric value is compared with its threshold. Its title, source,
            and metric name are included in the explanation.

    Returns:
        A rule-based explanation with a recommended next step and acknowledgement
        text. A truthy optional resolved_by value is uppercased; otherwise the
        acknowledgement is "Not yet acknowledged". No external AI or LLM
        service is called.

    Raises:
        KeyError: If the severity is not present in NEXT_STEPS.
        AttributeError: If a truthy resolved_by value has no upper method.
    """
    if alert.metric_value > alert.threshold:
        comparison = "exceeded"
    elif alert.metric_value < alert.threshold:
        comparison = "fell below"
    else:
        comparison = "reached"

    next_step = NEXT_STEPS[alert.severity]
    explanation = (
        f'This {alert.severity} alert from {alert.source} is titled "{alert.title}". '
        f"The {alert.metric_name} metric {comparison} its threshold: the current value is "
        f"{alert.metric_value}, compared with a threshold of {alert.threshold}. "
        f"Recommended next step: {next_step}"
    )
    resolved_by = getattr(alert, "resolved_by", None)
    acknowledgement = resolved_by.upper() if resolved_by else "Not yet acknowledged"
    return explanation + f" Acknowledged by: {acknowledgement}."