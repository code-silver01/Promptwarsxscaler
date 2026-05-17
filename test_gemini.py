import os
from google import genai
from google.genai import types

def test():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="say hi",
        )
        print("gemini-2.5-flash worked:", response.text)
    except Exception as e:
        print("gemini-2.5-flash error:", e)

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="say hi",
        )
        print("gemini-1.5-flash worked:", response.text)
    except Exception as e:
        print("gemini-1.5-flash error:", e)

if __name__ == "__main__":
    test()
