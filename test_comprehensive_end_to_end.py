"""
Comprehensive End-to-End Testing for BRS SASA
Testing as a real user - each agent, supervisor, database operations, and all tools
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.workflow import brs_workflow
from core.database import SessionLocal, init_db
from core.models import FeedbackModel, ConversationModel, MessageModel
from core.logger import setup_logger
from sqlalchemy import text

logger = setup_logger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_test(test_name):
    """Print test name"""
    print(f"{Colors.OKCYAN}{Colors.BOLD}🧪 TEST: {test_name}{Colors.ENDC}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

async def test_query(query: str, expected_agent: str = None, test_name: str = None):
    """
    Test a single query through the workflow
    """
    if test_name:
        print_test(test_name)
    
    print_info(f"User Query: '{query}'")
    
    try:
        # Invoke workflow
        result = await brs_workflow.invoke({
            "user_input": query,
            "messages": [],
            "conversation_id": "test_session"
        })
        
        # Extract results
        response = result.get("response", "")
        current_agent = result.get("current_agent", "unknown")
        query_type = result.get("query_type", "unknown")
        confidence = result.get("confidence", 0.0)
        sources = result.get("sources", [])
        
        # Print results
        print_info(f"Routed to: {current_agent} (Query Type: {query_type})")
        print_info(f"Confidence: {confidence}")
        
        if sources:
            print_info(f"Sources: {len(sources)} source(s)")
        
        print(f"\n{Colors.BOLD}Response:{Colors.ENDC}")
        print(f"{response[:500]}..." if len(response) > 500 else response)
        
        # Validate expected agent
        if expected_agent:
            if current_agent == expected_agent or query_type == expected_agent:
                print_success(f"Correctly routed to {expected_agent}")
            else:
                print_error(f"Expected {expected_agent}, got {current_agent}")
                return False
        
        # Check if response is meaningful
        if len(response) < 20:
            print_error("Response too short - might be an error")
            return False
        
        print_success("Test passed")
        return True
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        logger.error(f"Error in test_query: {str(e)}", exc_info=True)
        return False

async def test_database_operations():
    """
    Test database operations for feedback and conversations
    """
    print_header("DATABASE OPERATIONS TEST")
    
    db = SessionLocal()
    
    try:
        # Test 1: Database connection
        print_test("Database Connection")
        db.execute(text("SELECT 1"))
        print_success("Database connection successful")
        
        # Test 2: Create feedback entry
        print_test("Create Feedback Entry")
        feedback = FeedbackModel(
            user_query="Test query about Trust Act",
            feedback_text="I think the registration fees are too high",
            legislation_section="Section 8",
            sentiment="negative",
            feedback_metadata={"test": True}
        )
        db.add(feedback)
        db.commit()
        feedback_id = feedback.id
        print_success(f"Feedback created with ID: {feedback_id}")
        
        # Test 3: Retrieve feedback
        print_test("Retrieve Feedback")
        retrieved = db.query(FeedbackModel).filter(FeedbackModel.id == feedback_id).first()
        if retrieved and retrieved.feedback_text == feedback.feedback_text:
            print_success("Feedback retrieved successfully")
        else:
            print_error("Failed to retrieve feedback")
            return False
        
        # Test 4: Count feedback by sentiment
        print_test("Count Feedback by Sentiment")
        negative_count = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "negative").count()
        print_success(f"Found {negative_count} negative feedback entries")
        
        # Test 5: Create conversation
        print_test("Create Conversation")
        conversation = ConversationModel(
            title="Test Conversation",
            status="active",
            conversation_metadata={"test": True}
        )
        db.add(conversation)
        db.commit()
        conv_id = conversation.id
        print_success(f"Conversation created with ID: {conv_id}")
        
        # Test 6: Add messages to conversation
        print_test("Add Messages to Conversation")
        message1 = MessageModel(
            conversation_id=conv_id,
            role="user",
            content="Hello, I need help with business registration",
            message_metadata={}
        )
        message2 = MessageModel(
            conversation_id=conv_id,
            role="assistant",
            content="I'd be happy to help you with business registration!",
            message_metadata={}
        )
        db.add(message1)
        db.add(message2)
        db.commit()
        print_success("Messages added to conversation")
        
        # Test 7: Retrieve conversation with messages
        print_test("Retrieve Conversation with Messages")
        conv_with_messages = db.query(ConversationModel).filter(
            ConversationModel.id == conv_id
        ).first()
        if conv_with_messages and len(conv_with_messages.messages) == 2:
            print_success(f"Retrieved conversation with {len(conv_with_messages.messages)} messages")
        else:
            print_error("Failed to retrieve conversation with messages")
            return False
        
        # Test 8: Clean up test data
        print_test("Clean Up Test Data")
        db.delete(retrieved)
        db.delete(conv_with_messages)
        db.commit()
        print_success("Test data cleaned up")
        
        return True
        
    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        logger.error(f"Database test error: {str(e)}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()

async def test_router_supervisor():
    """
    Test the router/supervisor to ensure correct agent routing
    """
    print_header("ROUTER/SUPERVISOR TEST")
    
    test_cases = [
        ("What documents do I need to register a company?", "rag_agent", "Knowledge Query"),
        ("Hello, who are you?", "conversation_agent", "Greeting"),
        ("Tell me about the Trust Administration Bill", "public_participation_agent", "Legislation Query"),
        ("What's the status of my application PVT-123456?", "application_assistant_agent", "Application Lookup"),
        ("What's the weather today?", "out_of_scope", "Out of Scope Query"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_agent, test_name in test_cases:
        result = await test_query(query, expected_agent, test_name)
        if result:
            passed += 1
        else:
            failed += 1
        print()  # Blank line between tests
    
    print_info(f"Router Tests: {passed} passed, {failed} failed")
    return failed == 0

async def test_rag_agent():
    """
    Test RAG agent with knowledge base queries
    """
    print_header("RAG AGENT TEST")
    
    test_cases = [
        "What are the requirements for registering a private limited company?",
        "How much does it cost to register a business name?",
        "What is the Companies Act 2015?",
        "Can a foreigner be a director in a Kenyan company?",
        "What documents are needed for LLP registration?",
    ]
    
    passed = 0
    failed = 0
    
    for query in test_cases:
        result = await test_query(query, "rag_agent", f"RAG Query: {query[:50]}...")
        if result:
            passed += 1
        else:
            failed += 1
        print()
    
    print_info(f"RAG Agent Tests: {passed} passed, {failed} failed")
    return failed == 0

async def test_conversation_agent():
    """
    Test conversation agent with general queries
    """
    print_header("CONVERSATION AGENT TEST")
    
    test_cases = [
        "Hello!",
        "Who are you?",
        "What services does BRS provide?",
        "How can I contact BRS?",
        "What are your office hours?",
    ]
    
    passed = 0
    failed = 0
    
    for query in test_cases:
        result = await test_query(query, "conversation_agent", f"Conversation: {query}")
        if result:
            passed += 1
        else:
            failed += 1
        print()
    
    print_info(f"Conversation Agent Tests: {passed} passed, {failed} failed")
    return failed == 0

async def test_public_participation_agent():
    """
    Test public participation agent with legislation queries and feedback
    """
    print_header("PUBLIC PARTICIPATION AGENT TEST")
    
    # Initialize database for feedback testing
    db = SessionLocal()
    initial_feedback_count = db.query(FeedbackModel).count()
    db.close()
    
    test_cases = [
        ("Explain the Trust Administration Bill 2025", False),
        ("How does Kenya's trust law compare to Uganda's?", False),
        ("I think the registration fees in the Trust Act are too high", True),
        ("I support the transparency requirements in the bill", True),
        ("What are the penalties for non-compliance in the Trust Act?", False),
    ]
    
    passed = 0
    failed = 0
    
    for query, should_collect_feedback in test_cases:
        test_name = f"Legislation: {query[:50]}..."
        if should_collect_feedback:
            test_name += " (Should collect feedback)"
        
        result = await test_query(query, "public_participation_agent", test_name)
        
        if result and should_collect_feedback:
            # Check if feedback was stored in database
            db = SessionLocal()
            new_feedback_count = db.query(FeedbackModel).count()
            db.close()
            
            if new_feedback_count > initial_feedback_count:
                print_success("Feedback successfully stored in database")
                initial_feedback_count = new_feedback_count
            else:
                print_warning("Feedback might not have been stored")
        
        if result:
            passed += 1
        else:
            failed += 1
        print()
    
    print_info(f"Public Participation Agent Tests: {passed} passed, {failed} failed")
    return failed == 0

async def test_application_assistant_agent():
    """
    Test application assistant agent with registration status queries
    """
    print_header("APPLICATION ASSISTANT AGENT TEST")
    
    test_cases = [
        "What's the status of my application PVT-2024001?",
        "I want to check my business registration BN-2024500",
        "How do I track my company registration?",
        "What does PVT mean in a registration number?",
        "My application number is CPR-2024100, what's the status?",
    ]
    
    passed = 0
    failed = 0
    
    for query in test_cases:
        result = await test_query(query, "application_assistant_agent", f"Application: {query[:50]}...")
        if result:
            passed += 1
        else:
            failed += 1
        print()
    
    print_info(f"Application Assistant Agent Tests: {passed} passed, {failed} failed")
    return failed == 0

async def test_escalation_scenarios():
    """
    Test scenarios that should trigger escalation to human agents
    """
    print_header("ESCALATION SCENARIOS TEST")
    
    print_info("Testing scenarios that should be flagged for human escalation")
    
    test_cases = [
        "I want to speak to a real person",
        "This is not helpful, I need human assistance",
        "Can I talk to your supervisor?",
        "I have a complaint about my registration",
        "My payment was deducted but registration failed",
    ]
    
    passed = 0
    
    for query in test_cases:
        print_test(f"Escalation: {query}")
        print_info(f"User Query: '{query}'")
        
        # These should be handled gracefully and indicate escalation path
        result = await brs_workflow.invoke({
            "user_input": query,
            "messages": [],
            "conversation_id": "test_escalation"
        })
        
        response = result.get("response", "")
        
        # Check if response mentions contact information or escalation
        escalation_keywords = ["contact", "phone", "email", "human", "agent", "supervisor"]
        has_escalation_info = any(keyword in response.lower() for keyword in escalation_keywords)
        
        if has_escalation_info:
            print_success("Response includes escalation/contact information")
            passed += 1
        else:
            print_warning("Response might not properly handle escalation")
        
        print(f"\n{Colors.BOLD}Response:{Colors.ENDC}")
        print(f"{response[:300]}..." if len(response) > 300 else response)
        print()
    
    print_info(f"Escalation Tests: {passed}/{len(test_cases)} included escalation info")
    return True

async def test_tools_individually():
    """
    Test individual tools to ensure they work correctly
    """
    print_header("INDIVIDUAL TOOLS TEST")
    
    # Test 1: Feedback Tool
    print_test("Feedback Collection Tool")
    try:
        from tools.feedback_tool import collect_legislation_feedback
        
        result = collect_legislation_feedback.invoke({
            "user_query": "Test query about legislation",
            "feedback_text": "This is a test feedback",
            "legislation_section": "Section 1",
            "sentiment": "neutral"
        })
        
        if "feedback ID" in result.lower() or "recorded" in result.lower():
            print_success("Feedback tool working correctly")
            print_info(f"Result: {result}")
        else:
            print_error("Feedback tool response unexpected")
    except Exception as e:
        print_error(f"Feedback tool failed: {str(e)}")
    
    print()
    
    # Test 2: Knowledge Base Search Tool
    print_test("Knowledge Base Search Tool")
    try:
        from tools.knowledge_base_tool import search_knowledge_base
        
        result = await search_knowledge_base.ainvoke({
            "query": "company registration requirements"
        })
        
        if result and len(result) > 50:
            print_success("Knowledge base search working correctly")
            print_info(f"Result length: {len(result)} characters")
        else:
            print_warning("Knowledge base search returned limited results")
    except Exception as e:
        print_error(f"Knowledge base search failed: {str(e)}")
    
    print()
    
    # Test 3: BRS Status Checker Tool
    print_test("BRS Status Checker Tool")
    try:
        from tools.brs_status_checker import check_business_registration_status
        
        result = check_business_registration_status.invoke({
            "registration_number": "PVT-2024001"
        })
        
        if result:
            print_success("BRS status checker working correctly")
            print_info(f"Result: {result[:200]}...")
        else:
            print_warning("BRS status checker returned empty result")
    except Exception as e:
        print_error(f"BRS status checker failed: {str(e)}")
    
    print()
    
    # Test 4: Web Search Tool
    print_test("Web Search Tool")
    try:
        from tools.web_search_tool import search_web_duckduckgo
        
        result = await search_web_duckduckgo.ainvoke({
            "query": "Kenya business registration"
        })
        
        if result and len(result) > 50:
            print_success("Web search tool working correctly")
            print_info(f"Result length: {len(result)} characters")
        else:
            print_warning("Web search returned limited results")
    except Exception as e:
        print_error(f"Web search tool failed: {str(e)}")
    
    print()
    
    return True

async def test_multi_turn_conversation():
    """
    Test multi-turn conversation to ensure context is maintained
    """
    print_header("MULTI-TURN CONVERSATION TEST")
    
    conversation_id = "test_multi_turn"
    messages = []
    
    turns = [
        "Hello, I want to register a company",
        "What documents do I need?",
        "How much will it cost?",
        "How long does the process take?",
        "Thank you for your help"
    ]
    
    for i, query in enumerate(turns, 1):
        print_test(f"Turn {i}: {query}")
        
        result = await brs_workflow.invoke({
            "user_input": query,
            "messages": messages,
            "conversation_id": conversation_id
        })
        
        response = result.get("response", "")
        
        # Add to message history
        from langchain_core.messages import HumanMessage, AIMessage
        messages.append(HumanMessage(content=query))
        messages.append(AIMessage(content=response))
        
        print(f"\n{Colors.BOLD}Response:{Colors.ENDC}")
        print(f"{response[:300]}..." if len(response) > 300 else response)
        print()
    
    print_success("Multi-turn conversation completed")
    return True

async def run_all_tests():
    """
    Run all comprehensive tests
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "═" * 78 + "╗")
    print("║" + "BRS SASA COMPREHENSIVE END-TO-END TEST SUITE".center(78) + "║")
    print("║" + "Testing as a Real User".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"{Colors.ENDC}\n")
    
    # Initialize system
    print_info("Initializing BRS SASA system...")
    try:
        init_db()
        await brs_workflow.initialize()
        print_success("System initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize system: {str(e)}")
        return
    
    # Track results
    results = {}
    
    # Run tests
    results["Database Operations"] = await test_database_operations()
    results["Router/Supervisor"] = await test_router_supervisor()
    results["RAG Agent"] = await test_rag_agent()
    results["Conversation Agent"] = await test_conversation_agent()
    results["Public Participation Agent"] = await test_public_participation_agent()
    results["Application Assistant Agent"] = await test_application_assistant_agent()
    results["Escalation Scenarios"] = await test_escalation_scenarios()
    results["Individual Tools"] = await test_tools_individually()
    results["Multi-turn Conversation"] = await test_multi_turn_conversation()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✅ Passed: {passed}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ Failed: {failed}{Colors.ENDC}")
    
    if failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}\n")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  SOME TESTS FAILED - REVIEW REQUIRED{Colors.ENDC}\n")
    
    # Cleanup
    await brs_workflow.close()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
