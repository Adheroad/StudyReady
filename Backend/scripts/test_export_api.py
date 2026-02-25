"""Comprehensive test for PDF and DOCX export endpoints."""

import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
PAPER_ID = "f0537afc-bf87-4a58-9fcd-4b6b4bb361b6"  # Existing mock paper


def test_pdf_download():
    """Test PDF download endpoint."""
    print("\n" + "=" * 60)
    print("Testing PDF Download Endpoint")
    print("=" * 60)
    
    url = f"{BASE_URL}/papers/{PAPER_ID}/download?format=pdf"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"✗ Failed: Status {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    # Check content type
    content_type = response.headers.get('Content-Type')
    if content_type != 'application/pdf':
        print(f"✗ Wrong content type: {content_type}")
        return False
    
    # Check file size
    size = len(response.content)
    if size < 1000:  # PDF should be at least 1KB
        print(f"✗ PDF too small: {size} bytes")
        return False
    
    # Save to file
    output_path = Path("/tmp/test_api_export.pdf")
    output_path.write_bytes(response.content)
    
    print(f"✓ PDF downloaded successfully")
    print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"  Content-Type: {content_type}")
    print(f"  Saved to: {output_path}")
    
    return True


def test_docx_download():
    """Test DOCX download endpoint."""
    print("\n" + "=" * 60)
    print("Testing DOCX Download Endpoint")
    print("=" * 60)
    
    url = f"{BASE_URL}/papers/{PAPER_ID}/download?format=docx"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"✗ Failed: Status {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    # Check content type
    content_type = response.headers.get('Content-Type')
    expected = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if content_type != expected:
        print(f"✗ Wrong content type: {content_type}")
        return False
    
    # Check file size
    size = len(response.content)
    if size < 5000:  # DOCX should be at least 5KB
        print(f"✗ DOCX too small: {size} bytes")
        return False
    
    # Save to file
    output_path = Path("/tmp/test_api_export.docx")
    output_path.write_bytes(response.content)
    
    print(f"✓ DOCX downloaded successfully")
    print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"  Content-Type: {content_type}")
    print(f"  Saved to: {output_path}")
    
    return True


def test_markdown_download():
    """Test Markdown download endpoint."""
    print("\n" + "=" * 60)
    print("Testing Markdown Download Endpoint")
    print("=" * 60)
    
    url = f"{BASE_URL}/papers/{PAPER_ID}/download?format=markdown"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"✗ Failed: Status {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    # Check content type
    content_type = response.headers.get('Content-Type', '')
    if not content_type.startswith('text/markdown'):
        print(f"✗ Wrong content type: {content_type}")
        return False
    
    # Check content
    content = response.text
    if len(content) < 100:
        print(f"✗ Markdown too short: {len(content)} chars")
        return False
    
    # Save to file
    output_path = Path("/tmp/test_api_export.md")
    output_path.write_text(content)
    
    print(f"✓ Markdown downloaded successfully")
    print(f"  Size: {len(content):,} characters")
    print(f"  Content-Type: {content_type}")
    print(f"  Preview: {content[:200]}...")
    print(f"  Saved to: {output_path}")
    
    return True


def test_invalid_format():
    """Test invalid format handling."""
    print("\n" + "=" * 60)
    print("Testing Invalid Format Handling")
    print("=" * 60)
    
    url = f"{BASE_URL}/papers/{PAPER_ID}/download?format=invalid"
    response = requests.get(url)
    
    if response.status_code != 400:
        print(f"✗ Should return 400, got {response.status_code}")
        return False
    
    print(f"✓ Invalid format correctly rejected")
    print(f"  Status: {response.status_code}")
    print(f"  Message: {response.json().get('detail')}")
    
    return True


def test_invalid_paper_id():
    """Test invalid paper ID handling."""
    print("\n" + "=" * 60)
    print("Testing Invalid Paper ID Handling")
    print("=" * 60)
    
    url = f"{BASE_URL}/papers/invalid-id/download?format=pdf"
    response = requests.get(url)
    
    if response.status_code != 400:
        print(f"✗ Should return 400, got {response.status_code}")
        return False
    
    print(f"✓ Invalid paper ID correctly rejected")
    print(f"  Status: {response.status_code}")
    print(f"  Message: {response.json().get('detail')}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PDF/DOCX Export API Tests")
    print("=" * 60)
    
    tests = [
        ("PDF Download", test_pdf_download),
        ("DOCX Download", test_docx_download),
        ("Markdown Download", test_markdown_download),
        ("Invalid Format", test_invalid_format),
        ("Invalid Paper ID", test_invalid_paper_id),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
