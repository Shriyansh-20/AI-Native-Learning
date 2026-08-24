import json
import os
import requests


STATES = [
    "S1_HEALTHY",
    "S2_BENIGN_DRIFT",
    "S3_FORMAT_GLITCH",
    "S4_CORRUPTED",
]

BASE_URL = "https://grid.ai.juspay.net"


def _extract_text_from_response(data: dict) -> str:
    """
    Extract the final text response from an Anthropic-compatible response.

    Some models may return thinking blocks before the final text block,
    so we explicitly search for content items with type == "text".
    """
    text_blocks = [
        item.get("text", "")
        for item in data.get("content", [])
        if item.get("type") == "text"
    ]

    text = "".join(text_blocks).strip()

    if not text:
        raise ValueError(
            "LLM returned no text output. "
            f"stop_reason={data.get('stop_reason')}"
        )

    return text


def _clean_json_text(text: str) -> str:
    """
    Remove simple markdown code fences if the model adds them.
    """
    text = text.strip()

    if text.startswith("```"):
        text = (
            text.replace("```json", "")
            .replace("```JSON", "")
            .replace("```", "")
            .strip()
        )

    return text


def estimate_likelihoods_with_llm(evidence: dict) -> dict:
    """
    Ask the LLM to estimate P(Evidence | State) for every hidden state.

    These likelihood values are NOT posterior probabilities and therefore
    do not need to sum to 1.

    The Bayesian posterior is computed later in Python using:

        posterior ∝ prior × likelihood
    """

    api_key = os.environ.get("JUSPAY_API_KEY")
    model = os.environ.get(
        "JUSPAY_LLM_MODEL",
        "kimi-latest",
    )

    if not api_key:
        raise RuntimeError(
            "JUSPAY_API_KEY is not set in the current terminal environment."
        )

    prompt = f"""
Estimate P(Evidence | State) for each hidden state of a payment data batch.

States:

S1_HEALTHY
Fundamentally valid and safe. Small harmless inconsistencies may exist.

S2_BENIGN_DRIFT
Valid data with a legitimate statistical or representation shift.

S3_FORMAT_GLITCH
Recoverable formatting, serialization, or representation problems.

S4_CORRUPTED
Unsafe semantic corruption or invalid transaction behaviour.

Evidence can overlap across states. Consider all evidence together.

Evidence:
{json.dumps(evidence, separators=(",", ":"))}

Return ONLY valid JSON in exactly this shape:

{{
  "S1_HEALTHY": 0.0,
  "S2_BENIGN_DRIFT": 0.0,
  "S3_FORMAT_GLITCH": 0.0,
  "S4_CORRUPTED": 0.0
}}

Each number is P(Evidence | State), must be between 0 and 1,
and the four values do NOT need to sum to 1.

No explanation. No markdown. Do not return posterior probabilities.
Do not choose an action.
""".strip()

    response = requests.post(
        f"{BASE_URL}/v1/messages",
        headers={
            "Authorization": f"Bearer {api_key}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 2000,
            "temperature": 0,
            "system": (
                "Answer directly and concisely. "
                "Do not reason aloud. "
                "Return only the requested JSON object."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(
            f"LLM request failed with HTTP {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()
    text = _extract_text_from_response(data)
    text = _clean_json_text(text)

    try:
        likelihoods = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM did not return valid JSON. "
            f"Raw text was: {text}"
        ) from exc

    for state in STATES:
        if state not in likelihoods:
            raise ValueError(
                f"LLM response missing state: {state}"
            )

        try:
            likelihoods[state] = float(likelihoods[state])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Likelihood for {state} is not numeric: "
                f"{likelihoods[state]}"
            ) from exc

        if not 0 <= likelihoods[state] <= 1:
            raise ValueError(
                f"Likelihood for {state} must be between 0 and 1. "
                f"Received: {likelihoods[state]}"
            )

    return {
        state: likelihoods[state]
        for state in STATES
    }
