"""
Interactive chat with BRS-SASA for different scenarios
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger
import sys

logger = setup_logger(__name__)

# Test scenarios
SCENARIOS = {
    "1": {
        "name": "Business Registration Query",
        "query": "How do I register a private limited company in Kenya?",
        "description": "Tests RAG agent with knowledge base search"
    },
    "2": {
        "name": "Current Information Query",
        "query": "Who is the current Director General of BRS?",
        "description": "Tests conversation agent with web scraping"
    },
    "3": {
        "name": "Legislation Explanation",
        "query": "What is the Trust Administration Bill 2025 about?",
        "description": "Tests public participation agent with legislation search"
    },
    "4": {
        "name": "Jurisdiction Comparison",
        "query": "How does Kenya's Trust Administration Bill compare to Uganda's trust laws?",
        "description": "Tests public participation agent with web search"
    },
    "5": {
        "name": "Feedback Collection",
        "query": "I think the Trust Administration Bill should include more protections for beneficiaries",
        "description": "Tests public participation agent with feedback collection"
    },
    "6": {
        "name": "Fee Information",
        "query": "What are the fees for registering a business name?",
        "description": "Tests RAG agent with fee information"
    },
    "7": {
        "name": "Contact Information",
        "query": "How can I contact BRS?",
        "description": "Tests conversation agent with contact info tool"
    },
    "8": {
        "name": "General Greeting",
        "query": "Hello, what can you help me with?",
        "description": "Tests conversation agent with general chat"
    },
    "9": {
        "name": "Regional Comparison",
        "query": "Compare trust laws in Kenya, Uganda, and Tanzania",
        "description": "Tests public participation agent with multiple countries"
    },
    "10": {
        "name": "Custom Query",
        "query": None,
        "description": "Enter your own question"
    }
}

async def chat_with_brs_sasa(query: str, conversation_id: str = "demo"):
    """Send a query to BRS-SASA and get response"""
    try:
        await brs_workflow.initialize()
        
        inputs = {
            "user_input": query,
            "messages": [],
            "conversation_id": conversation_id,
            "query_type": "",
            "response": "",
            "context": {},
            "retrieved_docs": [],
            "sources": [],
            "confidence": 0.0,
            "current_agent": "",
            "agent_feedback": {},
            "error_count": 0,
            "max_steps": 10
        }
        
        result = await brs_workflow.invoke(inputs)
        
        return {
            "response": result.get('response', 'No response'),
            "agent": result.get('current_agent', 'unknown'),
            "sources": result.get('sources', []),
            "confidence": result.get('confidence', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return {
            "response": f"Error: {str(e)}",
            "agent": "error",
            "sources": [],
            "confidence": 0.0
        }

def display_menu():
    """Display scenario menu"""
    print("\n" + "="*80)
    print("🇰🇪 BRS-SASA INTERACTIVE CHAT - SCENARIO MENU")
    print("="*80)
    print("\nChoose a scenario to test:\n")
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
        print(f"   Query: {scenario['query'] if scenario['query'] else 'Custom'}")
        print(f"   Tests: {scenario['description']}\n")
    
    print("0. Exit")
    print("="*80)

async def main():
    """Main interactive loop"""
    print("\n" + "="*80)
    print("🇰🇪 WELCOME TO BRS-SASA INTERACTIVE CHAT")
    print("="*80)
    print("\nBRS-SASA is your AI assistant for:")
    print("  • Business registration in Kenya")
    print("  • Trust Administration Bill 2025")
    print("  • Public participation in legislation")
    print("  • Jurisdiction comparisons")
    print("="*80)
    
    conversation_count = 0
    
    while True:
        display_menu()
        
        choice = input("\nEnter your choice (0-10): ").strip()
        
        if choice == "0":
            print("\n👋 Thank you for using BRS-SASA! Goodbye!\n")
            break
        
        if choice not in SCENARIOS:
            print("\n❌ Invalid choice. Please try again.")
            continue
        
        scenario = SCENARIOS[choice]
        conversation_count += 1
        
        # Get query
        if scenario['query'] is None:
            query = input("\n💬 Enter your question: ").strip()
            if not query:
                print("❌ Query cannot be empty.")
                continue
        else:
            query = scenario['query']
        
        print(f"\n{'='*80}")
        print(f"📋 SCENARIO: {scenario['name']}")
        print(f"{'='*80}")
        print(f"👤 YOU: {query}")
        print(f"{'='*80}\n")
        print("⏳ Processing... (this may take 5-15 seconds)\n")
        
        # Get response
        result = await chat_with_brs_sasa(query, f"demo_{conversation_count}")
        
        # Display response
        print(f"{'='*80}")
        print(f"🤖 BRS-SASA ({result['agent']}):")
        print(f"{'='*80}\n")
        print(result['response'])
        
        if result['sources']:
            print(f"\n📚 Sources: {', '.join(result['sources'])}")
        
        print(f"\n✅ Confidence: {result['confidence']:.0%}")
        print(f"{'='*80}\n")
        
        # Ask if user wants to continue
        continue_chat = input("Press Enter to continue, or 'q' to quit: ").strip().lower()
        if continue_chat == 'q':
            print("\n👋 Thank you for using BRS-SASA! Goodbye!\n")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted. Goodbye!")
        sys.exit(0)
