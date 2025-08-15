#!/usr/bin/env python3
"""
Test script for draft document upload endpoints
"""

import asyncio
import aiohttp
import tempfile
import os
from pathlib import Path

async def test_draft_endpoints():
    """Test the new draft document upload endpoints"""
    
    print("Testing draft document upload endpoints...")
    
    # Create test files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
        STATEMENT OF FACTS
        
        On January 1, 2024, plaintiff John Doe entered into a contract with defendant MegaCorp Inc.
        The contract required MegaCorp to deliver widgets by February 15, 2024.
        MegaCorp failed to deliver the widgets on time, causing damages to plaintiff.
        
        Key Facts:
        1. Contract execution date: January 1, 2024
        2. Delivery deadline: February 15, 2024  
        3. Actual delivery: Never occurred
        4. Damages: $50,000 in lost revenue
        """)
        fact_draft_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
        COMPLAINT FOR BREACH OF CONTRACT
        
        PARTIES:
        Plaintiff: John Doe, an individual
        Defendant: MegaCorp Inc., a Delaware corporation
        
        JURISDICTION AND VENUE:
        This court has jurisdiction over this matter pursuant to 28 U.S.C. § 1332.
        Venue is proper in this district under 28 U.S.C. § 1391.
        
        CAUSES OF ACTION:
        Count I: Breach of Contract
        Count II: Unjust Enrichment
        Count III: Negligent Misrepresentation
        
        PRAYER FOR RELIEF:
        Plaintiff seeks damages in excess of $50,000, plus costs and attorney fees.
        """)
        case_draft_path = f.name
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test fact draft upload
            print("\n1. Testing fact draft upload endpoint...")
            with open(fact_draft_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_fact_statement.txt')
                
                async with session.post('http://localhost:8000/api/upload-fact-draft', data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"✓ Fact draft upload successful: {result.get('upload_id')}")
                        print(f"  - Document type: {result.get('document_type')}")
                        print(f"  - Processing priority: {result.get('processing_priority')}")
                    else:
                        print(f"✗ Fact draft upload failed: {resp.status}")
                        print(await resp.text())
            
            # Test case draft upload  
            print("\n2. Testing case draft upload endpoint...")
            with open(case_draft_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test_complaint.txt')
                
                async with session.post('http://localhost:8000/api/upload-case-draft', data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"✓ Case draft upload successful: {result.get('upload_id')}")
                        print(f"  - Document type: {result.get('document_type')}")
                        print(f"  - Processing priority: {result.get('processing_priority')}")
                    else:
                        print(f"✗ Case draft upload failed: {resp.status}")
                        print(await resp.text())
            
            # Test evidence table to see if drafts are included
            print("\n3. Testing evidence table integration...")
            async with session.get('http://localhost:8000/api/evidence') as resp:
                if resp.status == 200:
                    evidence_data = await resp.json()
                    rows = evidence_data.get('rows', [])
                    draft_rows = [row for row in rows if 'draft' in row.get('document_type', '')]
                    print(f"✓ Evidence table contains {len(draft_rows)} draft documents")
                    
                    for row in draft_rows[-2:]:  # Show last 2 draft entries
                        print(f"  - {row.get('document_type')}: {row.get('title')}")
                else:
                    print(f"✗ Evidence table request failed: {resp.status}")
                        
    except aiohttp.ClientConnectorError:
        print("✗ Could not connect to server. Make sure the ingest server is running on port 8000.")
        print("  Start it with: python maestro/bots/ingest-server.py")
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
    finally:
        # Clean up test files
        try:
            os.unlink(fact_draft_path)
            os.unlink(case_draft_path)
        except:
            pass
    
    print("\nTest completed!")

if __name__ == '__main__':
    asyncio.run(test_draft_endpoints())