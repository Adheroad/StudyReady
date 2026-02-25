"""Test script for PDF/DOCX export with mock paper."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.export import generate_pdf, generate_docx

# Mock CBSE paper content
MOCK_PAPER = """# CENTRAL BOARD OF SECONDARY EDUCATION

Class XII - Commercial Art
Time: 3 Hours                                Maximum Marks: 70

## GENERAL INSTRUCTIONS:
1. This question paper contains 12 questions divided into sections A, B, C.
2. Section A contains 2 MCQs of 1 mark each.
3. Section B contains 3 short answer questions of 2 marks each.
4. Section C contains 1 long answer question of 6 marks.
5. All questions are compulsory.

## SECTION A (2 × 1 = 2 marks)

1. In which painting Lord Krishna is painted in Veerat (Large) Rupa?
   (A) Krishna with Gopis
   (B) Krishna lifting Mount Govardhana
   (C) Nand, Yashoda and Krishna going to Vrindavan
   (D) Krishna on Swing

2. Which technique was typically used in Pahari painting?
   (A) Fresco
   (B) Tempera
   (C) Watercolor
   (D) Oil painting

## SECTION B (3 × 2 = 6 marks)

3. Describe the significance of color symbolism in Mughal miniature paintings. [2 marks]

4. Explain the role of patronage in the development of Rajasthani painting schools. [2 marks]

5. Compare and contrast the Kangra and Basohli styles of Pahari painting. [2 marks]

## SECTION C (1 × 6 = 6 marks)

6. Analyze the painting "Radha and Krishna in the Grove" from the Kangra school. Discuss:
   • The composition and use of space
   • Color palette and its emotional impact
   • Symbolic elements and their meanings
   • The influence of Bhakti movement on the artwork
   
   OR
   
   Examine the evolution of portrait painting in the Mughal school from Akbar to Jahangir's reign. [6 marks]
"""


def test_pdf_export():
    """Test PDF generation."""
    print("Testing PDF export...")
    
    pdf_bytes = generate_pdf(
        paper_content=MOCK_PAPER,
        subject="Commercial Art",
        grade="XII",
        total_marks=70,
        output_path="test_paper.pdf",
    )
    
    print(f"✓ PDF generated: {len(pdf_bytes)} bytes")
    print(f"✓ Saved to: test_paper.pdf")


def test_docx_export():
    """Test DOCX generation."""
    print("\nTesting DOCX export...")
    
    docx_bytes = generate_docx(
        paper_content=MOCK_PAPER,
        subject="Commercial Art",
        grade="XII",
        total_marks=70,
        output_path="test_paper.docx",
    )
    
    print(f"✓ DOCX generated: {len(docx_bytes)} bytes")
    print(f"✓ Saved to: test_paper.docx")


if __name__ == "__main__":
    print("=" * 60)
    print("PDF/DOCX Export Test")
    print("=" * 60)
    
    try:
        test_pdf_export()
        test_docx_export()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
