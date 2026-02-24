"""
Test BRS API accessibility and authentication
Based on official API documentation
"""
import asyncio
import httpx
import json
import base64

# BRS Test API Configuration
BRS_API_BASE_URL = "https://brs.pesaflow.com"
BRS_API_SECRET = "VcJRykqeGNmOZzB2Rx2i6RrdtSgPH66+"
BRS_API_KEY = "C54b_uUW-Bi1nrTfPl"

# Create Basic Auth header
def create_basic_auth_header(username: str, password: str) -> str:
    """Create Basic Auth header value"""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"

async def test_brs_api():
    """Test BRS API with correct authentication method"""
    
    print("=" * 80)
    print("BRS API ACCESSIBILITY TEST")
    print("=" * 80)
    print(f"\nAPI Base URL: {BRS_API_BASE_URL}")
    print(f"Endpoint: /api/businesses")
    print(f"Auth Method: Basic Auth")
    print("=" * 80)
    
    # Test registration numbers from documentation
    test_cases = [
        {
            "name": "Non-existent business (from docs)",
            "registration_number": "CPR/2001/0000000001",
            "expected": "empty records"
        },
        {
            "name": "Existing business (from docs)",
            "registration_number": "BN/2001/00002",
            "expected": "Acme Name."
        },
        {
            "name": "Test private company",
            "registration_number": "PVT/2020/123456",
            "expected": "unknown"
        }
    ]
    
    # Create Basic Auth header
    auth_header = create_basic_auth_header(BRS_API_KEY, BRS_API_SECRET)
    
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"\nAuth Header: {auth_header[:20]}... (truncated)")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        
        for idx, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"TEST {idx}: {test_case['name']}")
            print(f"{'='*80}")
            print(f"Registration Number: {test_case['registration_number']}")
            print(f"Expected: {test_case['expected']}")
            print("-" * 80)
            
            url = f"{BRS_API_BASE_URL}/api/businesses"
            params = {"registration_number": test_case['registration_number']}
            
            try:
                response = await client.get(url, params=params, headers=headers)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response Length: {len(response.text)} bytes")
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS - API is accessible!")
                    
                    try:
                        data = response.json()
                        print(f"\nResponse Structure:")
                        print(f"  - Count: {data.get('count', 0)}")
                        print(f"  - Records: {len(data.get('records', []))}")
                        
                        if data.get('records'):
                            print(f"\nBusiness Details:")
                            for record in data['records']:
                                print(f"  - Business Name: {record.get('business_name', 'N/A')}")
                                print(f"  - Registration Number: {record.get('registration_number', 'N/A')}")
                                print(f"  - Status: {record.get('status', 'N/A')}")
                                print(f"  - Registration Date: {record.get('registration_date', 'N/A')}")
                                print(f"  - Email: {record.get('email', 'N/A')}")
                                print(f"  - Phone: {record.get('phone_number', 'N/A')}")
                                
                                if record.get('partners'):
                                    print(f"  - Partners: {len(record['partners'])}")
                                    for partner in record['partners']:
                                        print(f"    • {partner.get('name', 'N/A')} ({partner.get('id_type', 'N/A')}: {partner.get('id_number', 'N/A')})")
                        else:
                            print(f"\n⚠️  No records found for this registration number")
                        
                        print(f"\nFull Response:")
                        print(json.dumps(data, indent=2))
                        
                    except json.JSONDecodeError:
                        print(f"Response Text: {response.text[:500]}")
                
                elif response.status_code == 401:
                    print(f"❌ UNAUTHORIZED - Check credentials")
                    print(f"Response: {response.text}")
                elif response.status_code == 403:
                    print(f"❌ FORBIDDEN - Access denied")
                    print(f"Response: {response.text[:200]}")
                elif response.status_code == 404:
                    print(f"⚠️  NOT FOUND - Endpoint doesn't exist")
                else:
                    print(f"⚠️  Unexpected status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                
            except httpx.TimeoutException:
                print(f"❌ TIMEOUT - Request took too long")
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("\nAPI Details:")
    print(f"  Base URL: {BRS_API_BASE_URL}")
    print(f"  Endpoint: /api/businesses")
    print(f"  Auth: Basic Auth")
    print(f"  Format: ?registration_number=<number>")
    print("\nNext Steps:")
    print("  1. If tests pass → Create BRS Status Checker tool")
    print("  2. If tests fail → Request correct credentials from BRS")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_brs_api())
