from google import genai
from config.settings import GOOGLE_API_KEY, GEMINI_MODEL

def test_api_key():
    print("KEY FROM ENV:", GOOGLE_API_KEY)

    if not GOOGLE_API_KEY or not GOOGLE_API_KEY.strip():
        raise RuntimeError("GOOGLE_API_KEY missing or empty")

    if not GEMINI_MODEL.startswith("gemini"):
        raise ValueError(f"Invalid model name: {GEMINI_MODEL}")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Reply with: API key is working"
    )

    if not response or not getattr(response, "text", None):
        raise RuntimeError("No response text received")

    print("SUCCESS:", response.text.strip())
    return True


if __name__ == "__main__":
    test_api_key()
