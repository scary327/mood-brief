import asyncio
import os
import base64
import httpx

async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY", "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")
    model = "google/gemini-2.0-flash-lite-preview-02-05:free"
    
    # create dummy 1x1 png image
    b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        print(resp.status_code)
        print(resp.text)

asyncio.run(main())
