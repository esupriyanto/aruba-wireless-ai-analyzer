"""Stub Hermes Agent server for Docker deployment."""

from fastapi import FastAPI

app = FastAPI(title="Hermes Agent", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "hermes-agent"}


@app.post("/diagnose")
def diagnose(issue: dict, context: dict | None = None):
    """Stub diagnosis endpoint."""
    return {
        "analysis": f"Diagnosis for: {issue.get('title', 'unknown')}",
        "root_cause": "Stub analysis",
        "impact": "Stub impact",
        "recommendation": "Stub recommendation",
    }


@app.post("/execute")
def execute(actions: list[str], target: str | None = None):
    """Stub remediation endpoint."""
    return {
        "status": "accepted",
        "message": f"Actions queued for {target}: {', '.join(actions)}",
    }
