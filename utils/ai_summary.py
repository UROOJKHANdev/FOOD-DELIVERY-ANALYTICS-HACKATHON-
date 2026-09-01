import os

FALLBACK_NARRATIVE = """In the last period we completed 38,964 orders with an average door-to-door time of about 26.6 minutes. Traffic is the single biggest driver of delay — Jam conditions push delivery time to ~31.4 minutes vs ~21.5 minutes in light traffic, and the worst-case combo of fog + jam pushes the average to ~36.9 minutes. Festival days also run noticeably slower than normal days.

Electric scooters are the fastest fleet segment, while motorcycles run slowest. Since delivery time is negatively correlated with rider ratings (-0.36), slower orders directly hurt customer satisfaction — so re-routing around forecasted jams/fog, prioritizing electric scooters in high-traffic zones, and adding surge staffing on festivals are the top recommended actions."""


def get_api_key(st):
    try:
        return st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except Exception:
        return os.getenv("GROQ_API_KEY")


def generate_summary(st, analysis_summary: str) -> str:
    """Generate on demand; caller handles errors to preserve a reliable dashboard."""
    api_key = get_api_key(st)
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a business data analyst. Explain the given delivery analytics results in simple, clear business language. Focus on what actions the company should take."},
            {"role": "user", "content": f"Here are our calculated food delivery analysis results:\n{analysis_summary}\n\nExplain these findings in 3-4 short paragraphs for a business presentation."},
        ], temperature=0.5, max_tokens=500,
    )
    return response.choices[0].message.content
