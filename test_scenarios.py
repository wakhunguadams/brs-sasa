import httpx
import json
import uuid
import asyncio

BASE_URL = "http://localhost:8000/api/v1/chat"

async def run_scenario(name, payload, conversation_id=None):
    print(f"\n>>> SCENARIO: {name}")
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            content = data['choices'][0]['message']['content']
            sources = data.get('sources', [])
            conf = data.get('confidence', 0.0)
            new_conv_id = data.get('conversation_id')
            
            print(f"USER: {payload['messages'][-1]['content']}")
            print(f"ASSISTANT: {content[:200]}..." if len(content) > 200 else f"ASSISTANT: {content}")
            print(f"SOURCES: {sources}")
            print(f"CONFIDENCE: {conf}")
            return new_conv_id
        except Exception as e:
            print(f"ERROR: {e}")
            return None

async def main():
    # 1. General Conversation
    conv_id = await run_scenario("General Conversation", {
        "messages": [{"role": "user", "content": "Hello BRS-SASA, how are you today?"}],
        "stream": False
    })
    
    # 2. Specific Legal Query (Companies Act)
    await run_scenario("Legal Query (Companies Act)", {
        "messages": [{"role": "user", "content": "What does the Companies Act 2015 say about private companies?"}],
        "stream": False
    }, conv_id)
    
    # 3. Fee Query
    await run_scenario("Fee Query", {
        "messages": [{"role": "user", "content": "How much is the registration fee for a foreign company?"}],
        "stream": False
    }, conv_id)
    
    # 4. Multi-turn (Context Check)
    await run_scenario("Multi-turn Context", {
        "messages": [
            {"role": "user", "content": "What are the requirements for an LLP?"},
            {"role": "assistant", "content": "To register a Limited Liability Partnership (LLP) in Kenya, you need..."},
            {"role": "user", "content": "And what are the fees for that?"}
        ],
        "stream": False
    }, conv_id)
    
    # 5. Error Handling / Nonsense
    await run_scenario("Error Handling", {
        "messages": [{"role": "user", "content": "asdfghjkl;12345"}],
        "stream": False
    })

if __name__ == "__main__":
    asyncio.run(main())
