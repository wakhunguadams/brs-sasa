"""
Verification test for Application Assistant Agent
Tests the end-to-end lookup of business registration numbers
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger("test_application_assistant")

async def test_lookup(reg_number: str):
    logger.info(f"\n{'='*60}\nTESTING LOOKUP: {reg_number}\n{'='*60}")
    
    inputs = {
        "user_input": f"Check status for {reg_number}",
        "conversation_id": f"test_reg_{reg_number}"
    }
    
    try:
        result = await brs_workflow.invoke(inputs)
        print(f"\nResponse for {reg_number}:")
        print("-" * 40)
        print(result.get("response", "No response found"))
        print("-" * 40)
        
        # Validation checks
        response = result.get("response", "").lower()
        has_reg_num = reg_number.lower() in response
        has_status = any(s in response for s in ["registered", "status", "stage", "found", "not found"])
        
        print(f"✅ Reg number found in response: {has_reg_num}")
        print(f"✅ Status info present: {has_status}")
        
    except Exception as e:
        logger.error(f"Test failed for {reg_number}: {str(e)}")

async def main():
    # Initialize workflow
    await brs_workflow.initialize()
    
    # Test cases from user
    test_numbers = [
        "PVT-A71M2E5B",  # Provided by user
        "BN-KDS3P7Q5",   # Provided by user
        "BN-YZC6PY7",    # Provided by user
        "PVT-JZUA5QB",   # Provided by user
    ]
    
    for num in test_numbers:
        await test_lookup(num)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
