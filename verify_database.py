"""
Quick database verification script
Confirms feedback and conversation data is stored correctly
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from core.models import FeedbackModel, ConversationModel, MessageModel
from sqlalchemy import func

def verify_database():
    """Verify database contents"""
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("BRS SASA DATABASE VERIFICATION")
    print("="*80 + "\n")
    
    try:
        # Check feedback
        print("📋 FEEDBACK ENTRIES")
        print("-" * 80)
        total_feedback = db.query(FeedbackModel).count()
        print(f"Total feedback entries: {total_feedback}")
        
        if total_feedback > 0:
            # Count by sentiment
            positive = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "positive").count()
            negative = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "negative").count()
            neutral = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "neutral").count()
            suggestion = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "suggestion").count()
            
            print(f"  - Positive: {positive}")
            print(f"  - Negative: {negative}")
            print(f"  - Neutral: {neutral}")
            print(f"  - Suggestions: {suggestion}")
            
            # Show recent feedback
            print("\nRecent feedback (last 5):")
            recent = db.query(FeedbackModel).order_by(FeedbackModel.created_at.desc()).limit(5).all()
            for fb in recent:
                print(f"  • [{fb.sentiment}] {fb.feedback_text[:60]}...")
                print(f"    ID: {fb.id}")
                print(f"    Created: {fb.created_at}")
        else:
            print("  No feedback entries found")
        
        print("\n" + "-" * 80)
        
        # Check conversations
        print("\n💬 CONVERSATIONS")
        print("-" * 80)
        total_conversations = db.query(ConversationModel).count()
        print(f"Total conversations: {total_conversations}")
        
        if total_conversations > 0:
            # Count messages
            total_messages = db.query(MessageModel).count()
            print(f"Total messages: {total_messages}")
            
            # Show recent conversations
            print("\nRecent conversations (last 3):")
            recent_convs = db.query(ConversationModel).order_by(ConversationModel.created_at.desc()).limit(3).all()
            for conv in recent_convs:
                msg_count = len(conv.messages)
                print(f"  • Conversation ID: {conv.id}")
                print(f"    Title: {conv.title or 'Untitled'}")
                print(f"    Messages: {msg_count}")
                print(f"    Status: {conv.status}")
                print(f"    Created: {conv.created_at}")
        else:
            print("  No conversations found")
        
        print("\n" + "-" * 80)
        
        # Database health check
        print("\n✅ DATABASE HEALTH CHECK")
        print("-" * 80)
        print("✅ Database connection: OK")
        print("✅ Feedback table: OK")
        print("✅ Conversations table: OK")
        print("✅ Messages table: OK")
        
        if total_feedback > 0:
            print("✅ Feedback collection: WORKING")
        else:
            print("⚠️  Feedback collection: No entries (run tests to populate)")
        
        if total_conversations > 0:
            print("✅ Conversation storage: WORKING")
        else:
            print("⚠️  Conversation storage: No entries (run tests to populate)")
        
        print("\n" + "="*80)
        print("DATABASE VERIFICATION COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_database()
