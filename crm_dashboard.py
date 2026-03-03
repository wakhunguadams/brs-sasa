"""
BRS-SASA CRM Dashboard
Admin interface to view feedback, issue reports, conversations, and analytics
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from core.models import FeedbackModel, IssueReportModel, ConversationModel, MessageModel
from sqlalchemy import func, desc

# Page configuration
st.set_page_config(
    page_title="BRS-SASA CRM Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .feedback-positive { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    .feedback-negative { background-color: #f8d7da; padding: 10px; border-radius: 5px; }
    .feedback-neutral { background-color: #d1ecf1; padding: 10px; border-radius: 5px; }
    .feedback-suggestion { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .issue-open { color: #dc3545; font-weight: bold; }
    .issue-resolved { color: #28a745; font-weight: bold; }
    .issue-escalated { color: #ffc107; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 30

def get_db():
    """Get database session"""
    return SessionLocal()

def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("📊 BRS-SASA CRM Dashboard")
        st.caption("Real-time monitoring of feedback, issues, and conversations")
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col3:
        st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

def render_statistics():
    """Render key statistics"""
    db = get_db()
    
    try:
        # Get counts
        total_feedback = db.query(FeedbackModel).count()
        total_issues = db.query(IssueReportModel).count()
        total_conversations = db.query(ConversationModel).count()
        total_messages = db.query(MessageModel).count()
        
        # Get today's counts
        today = datetime.now().date()
        feedback_today = db.query(FeedbackModel).filter(
            func.date(FeedbackModel.created_at) == today
        ).count()
        issues_today = db.query(IssueReportModel).filter(
            func.date(IssueReportModel.created_at) == today
        ).count()
        
        # Open issues
        open_issues = db.query(IssueReportModel).filter(
            IssueReportModel.status == "open"
        ).count()
        
        # Escalated issues
        escalated_issues = db.query(IssueReportModel).filter(
            IssueReportModel.status == "escalated"
        ).count()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Feedback",
                total_feedback,
                f"+{feedback_today} today",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Issue Reports",
                total_issues,
                f"+{issues_today} today",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                "Open Issues",
                open_issues,
                f"{escalated_issues} escalated",
                delta_color="inverse" if open_issues > 10 else "normal"
            )
        
        with col4:
            st.metric(
                "Conversations",
                total_conversations,
                f"{total_messages} messages",
                delta_color="normal"
            )
        
    finally:
        db.close()

def render_feedback_section():
    """Render feedback management section"""
    st.header("💬 Public Participation Feedback")
    
    db = get_db()
    
    try:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sentiment_filter = st.selectbox(
                "Filter by Sentiment",
                ["All", "Positive", "Negative", "Neutral", "Suggestion"]
            )
        
        with col2:
            limit = st.number_input("Show entries", min_value=10, max_value=100, value=20)
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First"])
        
        # Query feedback
        query = db.query(FeedbackModel)
        
        if sentiment_filter != "All":
            query = query.filter(FeedbackModel.sentiment == sentiment_filter.lower())
        
        if sort_by == "Newest First":
            query = query.order_by(desc(FeedbackModel.created_at))
        else:
            query = query.order_by(FeedbackModel.created_at)
        
        feedback_list = query.limit(limit).all()
        
        # Display feedback count by sentiment
        st.subheader("Feedback Distribution")
        sentiment_counts = db.query(
            FeedbackModel.sentiment,
            func.count(FeedbackModel.id)
        ).group_by(FeedbackModel.sentiment).all()
        
        sentiment_df = pd.DataFrame(sentiment_counts, columns=["Sentiment", "Count"])
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(sentiment_df, use_container_width=True, hide_index=True)
        with col2:
            st.bar_chart(sentiment_df.set_index("Sentiment"))
        
        # Display feedback entries
        st.subheader(f"Recent Feedback ({len(feedback_list)} entries)")
        
        for feedback in feedback_list:
            sentiment_class = f"feedback-{feedback.sentiment}"
            
            with st.expander(
                f"{'🟢' if feedback.sentiment == 'positive' else '🔴' if feedback.sentiment == 'negative' else '🟡' if feedback.sentiment == 'suggestion' else '⚪'} "
                f"{feedback.feedback_text[:80]}... - {feedback.created_at.strftime('%Y-%m-%d %H:%M')}"
            ):
                st.markdown(f'<div class="{sentiment_class}">', unsafe_allow_html=True)
                st.write(f"**Feedback ID:** `{feedback.id}`")
                st.write(f"**User Query:** {feedback.user_query}")
                st.write(f"**Feedback:** {feedback.feedback_text}")
                if feedback.legislation_section:
                    st.write(f"**Section:** {feedback.legislation_section}")
                st.write(f"**Sentiment:** {feedback.sentiment.upper()}")
                st.write(f"**Created:** {feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown('</div>', unsafe_allow_html=True)
        
    finally:
        db.close()

def render_issues_section():
    """Render issue reports section"""
    st.header("🐛 Issue Reports (Screenshots)")
    
    db = get_db()
    
    try:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Open", "Resolved", "Escalated"]
            )
        
        with col2:
            issue_type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Error", "Form", "Payment", "Navigation", "Other"]
            )
        
        with col3:
            limit_issues = st.number_input("Show issues", min_value=10, max_value=50, value=20)
        
        # Query issues
        query = db.query(IssueReportModel)
        
        if status_filter != "All":
            query = query.filter(IssueReportModel.status == status_filter.lower())
        
        if issue_type_filter != "All":
            query = query.filter(IssueReportModel.issue_type == issue_type_filter.lower())
        
        issues = query.order_by(desc(IssueReportModel.created_at)).limit(limit_issues).all()
        
        # Display issue statistics
        st.subheader("Issue Statistics")
        
        status_counts = db.query(
            IssueReportModel.status,
            func.count(IssueReportModel.id)
        ).group_by(IssueReportModel.status).all()
        
        type_counts = db.query(
            IssueReportModel.issue_type,
            func.count(IssueReportModel.id)
        ).group_by(IssueReportModel.issue_type).all()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**By Status:**")
            if status_counts:
                status_df = pd.DataFrame(status_counts, columns=["Status", "Count"])
                st.dataframe(status_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**By Type:**")
            if type_counts:
                type_df = pd.DataFrame(type_counts, columns=["Type", "Count"])
                st.dataframe(type_df, use_container_width=True, hide_index=True)
        
        # Display issues
        st.subheader(f"Recent Issues ({len(issues)} entries)")
        
        if not issues:
            st.info("No issue reports yet. Issues will appear here when users upload screenshots.")
        
        for issue in issues:
            status_class = f"issue-{issue.status}"
            status_icon = "🔴" if issue.status == "open" else "🟢" if issue.status == "resolved" else "🟡"
            
            with st.expander(
                f"{status_icon} {issue.user_query[:60]}... - {issue.created_at.strftime('%Y-%m-%d %H:%M')}"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Issue ID:** `{issue.id}`")
                    st.write(f"**User Query:** {issue.user_query}")
                    st.write(f"**Status:** {issue.status.upper()}")
                    if issue.issue_type:
                        st.write(f"**Type:** {issue.issue_type.upper()}")
                    if issue.screenshot_path:
                        st.write(f"**Screenshot:** `{issue.screenshot_path}`")
                    if issue.extracted_text:
                        st.write(f"**Extracted Text:** {issue.extracted_text[:200]}...")
                    st.write(f"**Created:** {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if issue.resolved_at:
                        st.write(f"**Resolved:** {issue.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                with col2:
                    st.write("**Actions:**")
                    if issue.status == "open":
                        if st.button(f"✅ Resolve", key=f"resolve_{issue.id}"):
                            issue.status = "resolved"
                            issue.resolved_at = datetime.utcnow()
                            db.commit()
                            st.success("Issue marked as resolved!")
                            st.rerun()
                        
                        if st.button(f"⚠️ Escalate", key=f"escalate_{issue.id}"):
                            issue.status = "escalated"
                            db.commit()
                            st.warning("Issue escalated!")
                            st.rerun()
                
                if issue.analysis_result:
                    with st.expander("View Analysis"):
                        st.json(issue.analysis_result)
        
    finally:
        db.close()

def render_conversations_section():
    """Render conversations section"""
    st.header("💭 Conversations")
    
    db = get_db()
    
    try:
        # Get recent conversations
        conversations = db.query(ConversationModel).order_by(
            desc(ConversationModel.updated_at)
        ).limit(10).all()
        
        st.subheader(f"Recent Conversations ({len(conversations)})")
        
        for conv in conversations:
            message_count = len(conv.messages)
            
            with st.expander(
                f"💬 {conv.title or 'Untitled'} - {message_count} messages - {conv.updated_at.strftime('%Y-%m-%d %H:%M')}"
            ):
                st.write(f"**Conversation ID:** `{conv.id}`")
                st.write(f"**Status:** {conv.status}")
                st.write(f"**Created:** {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Last Updated:** {conv.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if conv.messages:
                    st.write(f"**Messages ({len(conv.messages)}):**")
                    for msg in conv.messages[-5:]:  # Show last 5 messages
                        role_icon = "👤" if msg.role == "user" else "🤖"
                        st.text(f"{role_icon} {msg.role}: {msg.content[:100]}...")
        
    finally:
        db.close()

def render_analytics_section():
    """Render analytics section"""
    st.header("📈 Analytics")
    
    db = get_db()
    
    try:
        # Time-based analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Feedback Over Time (Last 7 Days)")
            
            # Get feedback for last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            daily_feedback = db.query(
                func.date(FeedbackModel.created_at).label('date'),
                func.count(FeedbackModel.id).label('count')
            ).filter(
                FeedbackModel.created_at >= seven_days_ago
            ).group_by(
                func.date(FeedbackModel.created_at)
            ).all()
            
            if daily_feedback:
                df = pd.DataFrame(daily_feedback, columns=['Date', 'Count'])
                st.line_chart(df.set_index('Date'))
            else:
                st.info("No feedback data for the last 7 days")
        
        with col2:
            st.subheader("Issues Over Time (Last 7 Days)")
            
            daily_issues = db.query(
                func.date(IssueReportModel.created_at).label('date'),
                func.count(IssueReportModel.id).label('count')
            ).filter(
                IssueReportModel.created_at >= seven_days_ago
            ).group_by(
                func.date(IssueReportModel.created_at)
            ).all()
            
            if daily_issues:
                df = pd.DataFrame(daily_issues, columns=['Date', 'Count'])
                st.line_chart(df.set_index('Date'))
            else:
                st.info("No issue data for the last 7 days")
        
    finally:
        db.close()

def main():
    """Main dashboard"""
    
    # Header
    render_header()
    
    st.divider()
    
    # Statistics
    render_statistics()
    
    st.divider()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Feedback",
        "🐛 Issues",
        "💭 Conversations",
        "📈 Analytics"
    ])
    
    with tab1:
        render_feedback_section()
    
    with tab2:
        render_issues_section()
    
    with tab3:
        render_conversations_section()
    
    with tab4:
        render_analytics_section()
    
    # Footer
    st.divider()
    st.caption("BRS-SASA CRM Dashboard - Real-time monitoring and management")

if __name__ == "__main__":
    main()
