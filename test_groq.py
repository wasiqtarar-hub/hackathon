import os

from dotenv import load_dotenv

from logger import configure_logger

try:
    from groq import Groq
except ImportError as exc:  # pragma: no cover - runtime guidance
    raise SystemExit(
        "The groq package is not installed. Run pip install -r requirements.txt first."
    ) from exc


load_dotenv()
logger = configure_logger("debug.log", name="groq_test")


def main():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    if not api_key or "your_" in api_key.lower():
        raise SystemExit("Set a valid GROQ_API_KEY in .env before running test_groq.py.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a connectivity test for a car comparison app.",
            },
            {
                "role": "user",
                "content": "Reply with a short confirmation that the Groq connection is working.",
            },
        ],
        temperature=0.1,
        max_tokens=60,
    )

    message = response.choices[0].message.content.strip()
    logger.info("Successfully connected to Groq using model %s", model)
    print("Groq connection successful.")
    print(f"Model: {model}")
    print(f"Response: {message}")


if __name__ == "__main__":
    main()
