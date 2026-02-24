"""Demo script showing web search capability in action"""
import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/chat/completions"

def chat(message):
    """Send a chat message and get response"""
    print(f"\n{'='*70}")
    print(f"USER: {message}")
    print(f"{'='*70}")
    
    response = requests.post(
        API_URL,
        json={"messages": [{"role": "user", "content": message}]},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assistant_message = data['choices'][0]['message']['content']
        sources = data.get('sources', [])
        confidence = data.get('confidence', 0)
        
        print(f"\nASSISTANT:\n{assistant_message}")
        print(f"\n{'─'*70}")
        print(f"Sources: {', '.join(sources) if sources else 'None'}")
        print(f"Confidence: {confidence}")
        print(f"{'='*70}\n")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    print("\n" + "="*70)
    print("BRS-SASA Web Search Demo")
    print("="*70)
    print("\nThis demo shows the agent using web search for current information")
    print("and knowledge base for laws/regulations.\n")
    
    # Test 1: Knowledge base query (should use local KB)
    print("\n📚 TEST 1: Knowledge Base Query (Laws & Regulations)")
    chat("What are the fees for registering a private company in Kenya?")
    time.sleep(2)
    
    # Test 2: Current information query (should use web search)
    print("\n🌐 TEST 2: Web Search Query (Current Information)")
    chat("Who is the current director of the Business Registration Service in Kenya?")
    time.sleep(2)
    
    # Test 3: News query (should use news search)
    print("\n📰 TEST 3: News Search Query (Recent Updates)")
    chat("What's the latest news about BRS Kenya?")
    time.sleep(2)
    
    # Test 4: Mixed query (might use both)
    print("\n🔄 TEST 4: Mixed Query (Knowledge Base + Web)")
    chat("How do I register a company and who should I contact at BRS?")
    
    print("\n" + "="*70)
    print("Demo completed!")
    print("="*70)

if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python start_server.py")
    input("Press Enter to start the demo...")
    main()
