# BRS-SASA CRM Dashboard Guide

## Overview

The CRM Dashboard is an administrative interface that provides real-time monitoring and management of all data logged by the BRS-SASA system. It's designed to demonstrate to stakeholders how the system captures and stores user interactions, feedback, and issues.

## Access

- **URL**: http://localhost:8502
- **Purpose**: Admin/CRM monitoring and management
- **Audience**: BRS staff, administrators, stakeholders

## Features

### 1. Real-Time Statistics Dashboard

The main dashboard displays key metrics:

- **Total Feedback**: Count of all public participation feedback entries
- **Issue Reports**: Count of screenshot-based issue reports
- **Open Issues**: Number of unresolved issues (with escalation count)
- **Conversations**: Total conversations with message counts

All metrics show today's activity as a delta indicator.

### 2. Feedback Management Tab 💬

**Purpose**: Monitor and analyze public participation feedback on legislation

**Features**:
- Filter by sentiment (Positive, Negative, Neutral, Suggestion)
- Sort by date (newest/oldest first)
- View feedback distribution by sentiment
- Visual bar chart of sentiment breakdown
- Detailed feedback entries with:
  - User query
  - Feedback text
  - Legislation section
  - Sentiment analysis
  - Timestamp

**Use Case**: Track public opinion on proposed legislation, identify concerns, measure engagement

### 3. Issue Reports Tab 🐛

**Purpose**: Manage screenshot-based issue reports from users

**Features**:
- Filter by status (Open, Resolved, Escalated)
- Filter by issue type (Error, Form, Payment, Navigation, Other)
- View issue statistics by status and type
- Detailed issue information:
  - User query
  - Screenshot path
  - Extracted text (OCR)
  - AI analysis results
  - Issue type and status
  - Creation and resolution timestamps

**Actions**:
- ✅ **Resolve**: Mark issue as resolved
- ⚠️ **Escalate**: Flag issue for higher-level attention

**Use Case**: Track technical issues users face, prioritize fixes, measure resolution time

### 4. Conversations Tab 💭

**Purpose**: View conversation history and user interactions

**Features**:
- Recent conversations (last 10)
- Conversation metadata:
  - Title
  - Status
  - Message count
  - Creation and update timestamps
- Last 5 messages preview per conversation

**Use Case**: Understand user journeys, identify common questions, quality assurance

### 5. Analytics Tab 📈

**Purpose**: Visualize trends over time

**Features**:
- Feedback over time (last 7 days) - line chart
- Issues over time (last 7 days) - line chart
- Time-based trend analysis

**Use Case**: Identify patterns, measure system usage, track issue frequency

## How Data Gets Logged

### Feedback Logging Flow

```
User asks about legislation
    ↓
Public Participation Agent responds
    ↓
User provides feedback
    ↓
Feedback Tool saves to database
    ↓
Appears in CRM Dashboard (Feedback Tab)
```

**Database Table**: `feedback`
**Fields**: user_query, legislation_section, feedback_text, sentiment, created_at

### Issue Report Logging Flow

```
User uploads screenshot of issue
    ↓
Application Assistant Agent receives it
    ↓
Screenshot Analysis Tool processes image
    ↓
Issue Report saved to database
    ↓
Appears in CRM Dashboard (Issues Tab)
```

**Database Table**: `issue_reports`
**Fields**: user_query, screenshot_path, extracted_text, analysis_result, issue_type, status, created_at

### Conversation Logging Flow

```
User starts conversation
    ↓
Conversation created in database
    ↓
Each message saved to messages table
    ↓
Appears in CRM Dashboard (Conversations Tab)
```

**Database Tables**: `conversations`, `messages`
**Fields**: 
- Conversations: title, status, created_at, updated_at
- Messages: conversation_id, role, content, created_at

## Starting the Dashboard

### Option 1: Start All Services (Recommended)

```bash
python start_all_services.py
```

This starts:
- API Server (port 8000)
- User Interface (port 8501)
- CRM Dashboard (port 8502)

### Option 2: Start CRM Dashboard Only

```bash
streamlit run crm_dashboard.py --server.port 8502
```

### Option 3: Start Specific Service

```bash
# API only
python start_all_services.py --mode api

# User UI only
python start_all_services.py --mode ui

# CRM Dashboard only
python start_all_services.py --mode crm
```

## Demo Workflow for Stakeholders

### 1. Show Real-Time Feedback Logging

1. Open User UI: http://localhost:8501
2. Open CRM Dashboard: http://localhost:8502 (Feedback Tab)
3. In User UI, ask: "What is the Trust Act about?"
4. Provide feedback: "This is very helpful, thank you!"
5. Watch it appear in CRM Dashboard in real-time
6. Click refresh to see the new entry

### 2. Show Issue Report Logging

1. Open User UI: http://localhost:8501
2. Open CRM Dashboard: http://localhost:8502 (Issues Tab)
3. In User UI, upload a screenshot of an error
4. Watch the issue appear in CRM Dashboard
5. Show the extracted text and AI analysis
6. Demonstrate resolving or escalating the issue

### 3. Show Conversation Tracking

1. Open User UI: http://localhost:8501
2. Open CRM Dashboard: http://localhost:8502 (Conversations Tab)
3. Have a multi-turn conversation in User UI
4. Show how each message is logged
5. Demonstrate conversation history and metadata

### 4. Show Analytics

1. Open CRM Dashboard: http://localhost:8502 (Analytics Tab)
2. Show feedback trends over the last 7 days
3. Show issue report trends
4. Explain how this helps identify patterns

## Database Schema

### Feedback Table
```sql
CREATE TABLE feedback (
    id VARCHAR PRIMARY KEY,
    user_query TEXT NOT NULL,
    legislation_section VARCHAR,
    feedback_text TEXT NOT NULL,
    sentiment VARCHAR,  -- positive, negative, neutral, suggestion
    feedback_metadata JSON,
    created_at TIMESTAMP
);
```

### Issue Reports Table
```sql
CREATE TABLE issue_reports (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR,
    user_query TEXT NOT NULL,
    screenshot_path VARCHAR,
    screenshot_url VARCHAR,
    extracted_text TEXT,
    analysis_result JSON,
    issue_type VARCHAR,  -- error, navigation, form, payment, other
    status VARCHAR DEFAULT 'open',  -- open, resolved, escalated
    resolution TEXT,
    escalated_to VARCHAR,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY,
    title VARCHAR,
    status VARCHAR DEFAULT 'active',
    conversation_metadata JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR FOREIGN KEY,
    role VARCHAR NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    message_metadata JSON,
    created_at TIMESTAMP
);
```

## Current Database Status

As of the last check:
- **Feedback entries**: 66
- **Issue reports**: 0 (will increase as users upload screenshots)
- **Conversations**: 145
- **Messages**: 278

## Troubleshooting

### Dashboard won't start
```bash
# Check if port 8502 is already in use
lsof -i :8502

# Kill existing process if needed
kill -9 <PID>

# Restart dashboard
streamlit run crm_dashboard.py --server.port 8502
```

### No data showing
```bash
# Verify database has data
python -c "
from core.database import SessionLocal
from core.models import FeedbackModel, IssueReportModel

db = SessionLocal()
print(f'Feedback: {db.query(FeedbackModel).count()}')
print(f'Issues: {db.query(IssueReportModel).count()}')
db.close()
"
```

### Can't connect to database
- Ensure `.env` file has correct `DATABASE_URL`
- Check database file exists: `ls -la brs_sasa.db`
- Verify database migrations are up to date

## Future Enhancements

Potential additions to the CRM dashboard:

1. **Export functionality**: Export data to CSV/Excel
2. **Advanced filtering**: Date ranges, keyword search
3. **User management**: Track individual users
4. **Email notifications**: Alert on escalated issues
5. **Performance metrics**: Response times, resolution rates
6. **Sentiment analysis trends**: Track sentiment over time
7. **Issue categorization**: Auto-categorize common issues
8. **Integration with ticketing**: Export to Jira/ServiceNow

## Security Considerations

- Dashboard should be behind authentication in production
- Implement role-based access control (RBAC)
- Audit log for admin actions
- Secure database connections
- Rate limiting on API endpoints
- Data retention policies

## Support

For questions or issues with the CRM Dashboard:
- Check logs in `logs/` directory
- Review database schema in `core/models.py`
- Consult API documentation at http://localhost:8000/docs
