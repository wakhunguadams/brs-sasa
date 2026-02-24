"""
Demo script for Public Participation Agent
Shows the agent in action with real-time interaction
"""
import asyncio
import sys
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def demo_query(query: str, conversation_id: str = "demo"):
    """Run a single query through the workflow"""
    print(f"\n{'='*80}")
    print(f"👤 USER: {query}")
    print(f"{'='*80}\n")
    
    try:
        # Initialize workflow
        await brs_workflow.initialize()
        
        # Create input
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
        
        # Invoke workflow
        result = await brs_workflow.invoke(inputs)
        
        # Display results
        agent = result.get('current_agent', 'unknown')
        response = result.get('response', 'No response')
        confidence = result.get('confidence', 0.0)
        sources = result.get('sources', [])
        
        print(f"🤖 BRS-SASA ({agent}):\n")
        print(response)
        
        if sources:
            print(f"\n📚 Sources: {', '.join(sources)}")
        
        print(f"\n✅ {confidence:.0%} confident")
        print(f"{'='*80}\n")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in demo: {str(e)}")
        print(f"❌ ERROR: {str(e)}\n")
        return None

async def main():
    """Run the demo"""
    print("\n" + "="*80)
    print("🇰🇪 BRS-SASA PUBLIC PARTICIPATION AGENT DEMO")
    print("="*80)
    print("\nThis demo shows the Public Participation Agent helping citizens")
    print("understand and provide feedback on the Trust Administration Bill 2025.")
    print("\n" + "="*80 + "\n")
    
    # Demo scenarios
    scenarios = [
        {
            "title": "SCENARIO 1: Understanding Legislation",
            "query": "What is the Trust Administration Bill 2025 about?"
        },
        {
            "title": "SCENARIO 2: Jurisdiction Comparison",
            "query": "How does Kenya's Trust Administration Bill compare to UK trust laws?"
        },
        {
            "title": "SCENARIO 3: Providing Feedback",
            "query": "I think the Trust Administration Bill should include more protections for beneficiaries"
        },
        {
            "title": "SCENARIO 4: Specific Section Query",
            "query": "What does the bill say about trust registration requirements?"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'#'*80}")
        print(f"# {scenario['title']}")
        print(f"{'#'*80}")
        
        await demo_query(scenario['query'], f"demo_{i}")
        
        if i < len(scenarios):
            print("\nPress Enter to continue to next scenario...")
            input()
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("  ✅ Legislation search and explanation")
    print("  ✅ International jurisdiction comparison")
    print("  ✅ Feedback collection")
    print("  ✅ Intelligent routing to correct agent")
    print("\nTo test the API directly:")
    print("  curl -X POST http://localhost:8000/api/v1/chat/message \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"message\": \"What is the Trust Administration Bill about?\", \"conversation_id\": \"test\"}'")
    print("\nTo view feedback statistics:")
    print("  curl http://localhost:8000/api/v1/feedback/stats")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
        sys.exit(0)
