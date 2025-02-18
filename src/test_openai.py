import asyncio
from openai import AsyncAzureOpenAI
from utils.config import settings


async def test_openai_connection():
    """Azure OpenAI APIの接続テスト"""
    try:
        client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

        print("API設定:")
        print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"API Version: {settings.AZURE_OPENAI_API_VERSION}")
        print(f"Deployment Name: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")

        # 簡単なテストメッセージを送信
        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            max_tokens=50,
        )
        print("\nAPIテスト結果:")
        print(f"Response: {response.choices[0].message.content}")

    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        if hasattr(e, "response"):
            print(
                f"Response: {e.response.text if hasattr(e.response, 'text') else str(e.response)}"
            )


if __name__ == "__main__":
    asyncio.run(test_openai_connection())
