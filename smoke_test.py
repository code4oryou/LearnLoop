from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


def main():
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Reply with exactly: LearnLoop Gemini connection successful."
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    print(response.text)
    print(f"Model used: {GEMINI_MODEL}")


if __name__ == "__main__":
    main()