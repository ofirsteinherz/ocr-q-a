import os
from dotenv import load_dotenv

from gpt_client import GPTClient, Message, MessageRole, GPTResponseError

# Load environment variables from .env file
load_dotenv(verbose=True)

def main():
    # Initialize client with your credentials
    client = GPTClient(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    # Example: Chat conversation
    try:
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant specialized in Python programming."
            ),
            Message(
                role=MessageRole.USER,
                content="What are some best practices for error handling in Python?"
            )
        ]
        
        response = client.chat(messages)
        print("\nChat Response:")
        print(response)
        
    except GPTResponseError as e:
        print(f"GPT Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Example: Image analysis
    try:
        image_response = client.analyze_image(
            image_source="https://www.wikihow.com/images/a/ab/Start-a-Wiki-Step-33-Version-3.jpg",
            prompt="What's in this image?",
            system_prompt="You are an expert image analyzer. Please provide a detailed analysis."
        )
        print("\nImage Analysis:")
        print(image_response)
    except GPTResponseError as e:
        print(f"Image analysis error: {e}")
    except Exception as e:
        print(f"Unexpected error during image analysis: {e}")

if __name__ == "__main__":
    main()