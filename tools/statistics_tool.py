"""
Statistics & Analytics Tools for BRS-SASA
Provides real-time statistics on company registrations, trends, and metrics
"""
from langchain_core.tools import tool
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Database path
DB_PATH = "brs_sasa.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@tool
async def get_registration_statistics(month: Optional[int] = None, year: Optional[int] = None) -> str:
    """
    Get company registration statistics for a specific month/year or current month.
    
    Use this tool when users ask about:
    - How many companies registered last month?
    - Registration counts for a specific period
    - Monthly/annual registration trends
    
    Args:
        month: Month (1-12), defaults to current month
        year: Year, defaults to current year
        
    Returns:
        Registration statistics for the specified period
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # If no month/year specified, use current month
        if not month or not year:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        # Query registration statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registrations,
                COUNT(DISTINCT company_type) as company_types,
                COUNT(DISTINCT county) as counties
            FROM companies 
            WHERE strftime('%m', registration_date) = ?
            AND strftime('%Y', registration_date) = ?
        """, (f"{month:02d}", str(year)))
        
        result = cursor.fetchone()
        
        if not result or result['total_registrations'] == 0:
            # Try previous month if no data for current month
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            
            cursor.execute("""
                SELECT COUNT(*) as total_registrations
                FROM companies 
                WHERE strftime('%m', registration_date) = ?
                AND strftime('%Y', registration_date) = ?
            """, (f"{prev_month:02d}", str(prev_year)))
            
            result = cursor.fetchone()
            
            if not result or result['total_registrations'] == 0:
                conn.close()
                return (
                    f"No registration data available for {year}-{month:02d}. "
                    f"Please try a different month or contact BRS for current statistics."
                )
        
        # Get breakdown by company type
        cursor.execute("""
            SELECT 
                company_type,
                COUNT(*) as count
            FROM companies 
            WHERE strftime('%m', registration_date) = ?
            AND strftime('%Y', registration_date) = ?
            GROUP BY company_type
            ORDER BY count DESC
        """, (f"{month:02d}", str(year)))
        
        type_breakdown = cursor.fetchall()
        
        # Get breakdown by county
        cursor.execute("""
            SELECT 
                county,
                COUNT(*) as count
            FROM companies 
            WHERE strftime('%m', registration_date) = ?
            AND strftime('%Y', registration_date) = ?
            GROUP BY county
            ORDER BY count DESC
            LIMIT 10
        """, (f"{month:02d}", str(year)))
        
        county_breakdown = cursor.fetchall()
        
        conn.close()
        
        # Format response
        response = []
        response.append(f"Company Registration Statistics for {year}-{month:02d}")
        response.append("=" * 60)
        response.append(f"\nTotal Registrations: {result['total_registrations']}")
        
        if type_breakdown:
            response.append("\nBreakdown by Company Type:")
            for row in type_breakdown:
                response.append(f"  - {row['company_type']}: {row['count']}")
        
        if county_breakdown:
            response.append("\nTop 10 Counties by Registrations:")
            for row in county_breakdown:
                response.append(f"  - {row['county']}: {row['count']}")
        
        response.append("\n" + "=" * 60)
        response.append("Source: BRS Registration Database")
        response.append("Note: Data may be delayed by 1-2 days for processing.")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Error getting registration statistics: {str(e)}")
        return (
            f"Error retrieving registration statistics: {str(e)}\n\n"
            f"Please try:\n"
            f"- Contacting BRS directly at +254 11 112 7000\n"
            f"- Visiting https://brs.go.ke/ for official statistics\n"
            f"- Trying a different query"
        )

@tool
async def get_sector_statistics() -> str:
    """
    Get company registration statistics broken down by sector/industry.
    
    Use this tool when users ask about:
    - Which sector has the most registrations?
    - Sector-wise registration breakdown
    - Industry trends
    
    Returns:
        Sector-wise registration statistics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query sector statistics
        cursor.execute("""
            SELECT 
                sector,
                COUNT(*) as count,
                ROUND(AVG(julianday('now') - julianday(registration_date)), 1) as avg_age_days
            FROM companies 
            WHERE sector IS NOT NULL
            GROUP BY sector
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        conn.close()
        
        if not results:
            return (
                "No sector data available in the database.\n\n"
                "Common sectors in Kenya include:\n"
                "- Technology & IT Services\n"
                "- Agriculture & Food Processing\n"
                "- Manufacturing\n"
                "- Construction\n"
                "- Financial Services\n"
                "- Retail & Trade\n"
                "- Tourism & Hospitality\n"
                "- Education & Training\n"
                "- Healthcare\n"
                "- Transportation & Logistics\n\n"
                "For detailed sector statistics, contact BRS or visit https://brs.go.ke/"
            )
        
        # Format response
        response = []
        response.append("Company Registration Statistics by Sector")
        response.append("=" * 60)
        
        for idx, row in enumerate(results, 1):
            response.append(f"\n{idx}. {row['sector']}")
            response.append(f"   Registrations: {row['count']}")
            response.append(f"   Average Company Age: {row['avg_age_days']:.0f} days")
        
        response.append("\n" + "=" * 60)
        response.append("Source: BRS Registration Database")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Error getting sector statistics: {str(e)}")
        return (
            f"Error retrieving sector statistics: {str(e)}\n\n"
            f"Please contact BRS at +254 11 112 7000 for sector-specific data."
        )

@tool
async def get_regional_statistics() -> str:
    """
    Get company registration statistics broken down by county/region.
    
    Use this tool when users ask about:
    - Which county has the most registrations?
    - Regional registration breakdown
    - County-wise trends
    
    Returns:
        County-wise registration statistics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query regional statistics
        cursor.execute("""
            SELECT 
                county,
                COUNT(*) as count,
                ROUND(AVG(julianday('now') - julianday(registration_date)), 1) as avg_age_days
            FROM companies 
            WHERE county IS NOT NULL
            GROUP BY county
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        conn.close()
        
        if not results:
            return (
                "No regional data available in the database.\n\n"
                "Kenya has 47 counties. Nairobi, Mombasa, and Kiambu typically have "
                "the highest registration numbers due to higher business activity.\n\n"
                "For detailed county statistics, contact BRS or visit https://brs.go.ke/"
            )
        
        # Format response
        response = []
        response.append("Company Registration Statistics by County")
        response.append("=" * 60)
        
        for idx, row in enumerate(results, 1):
            response.append(f"\n{idx}. {row['county']}")
            response.append(f"   Registrations: {row['count']}")
            response.append(f"   Average Company Age: {row['avg_age_days']:.0f} days")
        
        response.append("\n" + "=" * 60)
        response.append("Source: BRS Registration Database")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Error getting regional statistics: {str(e)}")
        return (
            f"Error retrieving regional statistics: {str(e)}\n\n"
            f"Please contact BRS at +254 11 112 7000 for county-specific data."
        )

@tool
async def get_trend_analysis(period: str = "6_months") -> str:
    """
    Get registration trend analysis for a specified period.
    
    Use this tool when users ask about:
    - Registration trends for the past 6 months
    - Monthly trends and patterns
    - Growth rates
    
    Args:
        period: Time period - "1_month", "3_months", "6_months", "12_months"
        
    Returns:
        Trend analysis for the specified period
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate date range based on period
        now = datetime.now()
        if period == "1_month":
            start_date = now - timedelta(days=30)
        elif period == "3_months":
            start_date = now - timedelta(days=90)
        elif period == "12_months":
            start_date = now - timedelta(days=365)
        else:  # 6_months default
            start_date = now - timedelta(days=180)
        
        # Query monthly trends
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', registration_date) as month,
                COUNT(*) as registrations,
                COUNT(DISTINCT company_type) as company_types
            FROM companies 
            WHERE registration_date >= ?
            GROUP BY strftime('%Y-%m', registration_date)
            ORDER BY month DESC
        """, (start_date.strftime('%Y-%m-%d'),))
        
        results = cursor.fetchall()
        
        conn.close()
        
        if not results:
            return (
                f"No registration data available for the last {period}.\n\n"
                f"Please contact BRS for historical trend data."
            )
        
        # Calculate growth rate
        if len(results) >= 2:
            current = results[0]['registrations']
            previous = results[1]['registrations']
            if previous > 0:
                growth_rate = ((current - previous) / previous) * 100
            else:
                growth_rate = 0
        else:
            growth_rate = 0
        
        # Format response
        response = []
        response.append(f"Registration Trend Analysis - Last {period.replace('_', ' ').title()}")
        response.append("=" * 60)
        response.append(f"\nTotal Registrations: {sum(r['registrations'] for r in results)}")
        response.append(f"Average per Month: {sum(r['registrations'] for r in results) / len(results):.0f}")
        response.append(f"Current Month Growth: {growth_rate:+.1f}%")
        
        response.append("\nMonthly Breakdown:")
        for row in results:
            response.append(f"  {row['month']}: {row['registrations']} registrations")
        
        response.append("\n" + "=" * 60)
        response.append("Source: BRS Registration Database")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Error getting trend analysis: {str(e)}")
        return (
            f"Error retrieving trend analysis: {str(e)}\n\n"
            f"Please contact BRS at +254 11 112 7000 for trend data."
        )

@tool
async def get_process_metrics(company_type: Optional[str] = None) -> str:
    """
    Get process efficiency metrics including average registration times.
    
    Use this tool when users ask about:
    - Average registration time for a specific company type
    - Process efficiency metrics
    - Registration timelines
    
    Args:
        company_type: Optional company type filter (e.g., "private", "public", "llp")
        
    Returns:
        Process efficiency metrics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query process metrics
        if company_type:
            cursor.execute("""
                SELECT 
                    company_type,
                    COUNT(*) as count,
                    ROUND(AVG(julianday(completed_date) - julianday(submission_date)), 1) as avg_days,
                    MIN(julianday(completed_date) - julianday(submission_date)) as min_days,
                    MAX(julianday(completed_date) - julianday(submission_date)) as max_days
                FROM companies 
                WHERE company_type LIKE ?
                AND completed_date IS NOT NULL
                GROUP BY company_type
            """, (f"%{company_type}%",))
        else:
            cursor.execute("""
                SELECT 
                    company_type,
                    COUNT(*) as count,
                    ROUND(AVG(julianday(completed_date) - julianday(submission_date)), 1) as avg_days,
                    MIN(julianday(completed_date) - julianday(submission_date)) as min_days,
                    MAX(julianday(completed_date) - julianday(submission_date)) as max_days
                FROM companies 
                WHERE completed_date IS NOT NULL
                GROUP BY company_type
                ORDER BY count DESC
            """)
        
        results = cursor.fetchall()
        
        conn.close()
        
        if not results:
            return (
                "No process metrics data available.\n\n"
                "Typical registration timelines in Kenya:\n"
                "- Private Limited Company: 3-5 business days\n"
                "- Public Limited Company: 5-7 business days\n"
                "- Business Name: 1-2 business days\n"
                "- LLP: 3-5 business days\n"
                "- Partnership: 2-3 business days\n\n"
                "For detailed process metrics, contact BRS."
            )
        
        # Format response
        response = []
        response.append("Company Registration Process Metrics")
        response.append("=" * 60)
        
        for row in results:
            response.append(f"\n{row['company_type']}")
            response.append(f"  Total Registrations: {row['count']}")
            response.append(f"  Average Processing Time: {row['avg_days']:.1f} days")
            response.append(f"  Fastest: {row['min_days']:.0f} days")
            response.append(f"  Slowest: {row['max_days']:.0f} days")
        
        response.append("\n" + "=" * 60)
        response.append("Source: BRS Registration Database")
        
        return "\n".join(response)
        
    except Exception as e:
        logger.error(f"Error getting process metrics: {str(e)}")
        return (
            f"Error retrieving process metrics: {str(e)}\n\n"
            f"Typical registration timelines:\n"
            f"- Private Limited Company: 3-5 business days\n"
            f"- Public Limited Company: 5-7 business days\n"
            f"- Business Name: 1-2 business days\n\n"
            f"Contact BRS at +254 11 112 7000 for detailed metrics."
        )

@tool
async def get_registration_number_format() -> str:
    """
    Get information about BRS registration number formats.
    
    Use this tool when users ask about:
    - Registration number format
    - How registration numbers look
    - What format to use for registration numbers
    
    Returns:
        Information about different registration number formats in Kenya.
    """
    return """
Business Registration Number Formats in Kenya:

1. Private Companies (Limited by Shares):
   Format: PVT-XXXXXXXXX/XXXX
   Example: PVT-ABCD1234/2024
   
2. Public Companies:
   Format: CPR-XXXXXXXXX/XXXX
   Example: CPR-WXYZ5678/2024

3. Business Names:
   Format: BN-XXXXXXXXX/XXXX
   Example: BN-SHOP1234/2024

4. Limited Liability Partnerships (LLP):
   Format: LLP-XXXXXXXXX/XXXX
   Example: LLP-PART5678/2024

5. Partnerships:
   Format: GP-XXXXXXXXX/XXXX (General Partnership)
   Example: GP-FIRM9012/2024

6. Foreign Companies:
   Format: FC-XXXXXXXXX/XXXX
   Example: FC-INTL3456/2024

Note: 
- The format may vary depending on when the business was registered
- Older registrations may have different formats
- The year (XXXX) represents the registration year

To check your registration status, provide your registration number to the 
check_business_registration_status tool.

For more information, visit: https://brs.go.ke/ or call +254 11 112 7000
"""
