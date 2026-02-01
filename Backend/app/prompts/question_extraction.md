# Question Extraction Prompt

Extract ALL questions from this exam paper image. Return a JSON array.

## For EACH question, extract:
1. question_number: The question number as shown (e.g., "1", "2a", "13")
2. question_text: Full question text, preserving formatting and mathematical notation (LaTeX)
3. marks: Integer marks for the question
4. section: Section identifier (A, B, C, D, अ, ब, स, द)
5. question_type: "mcq", "short", "long", or "practical"
6. chapter: Inferred chapter/unit name
7. topic: Specific topic within the chapter
8. difficulty: "easy", "medium", or "hard"
9. language: "en" or "hi" (detect from text)
10. has_diagram: true if the question includes/references a diagram or image
11. image_description: If has_diagram is true, describe the image in detail for regeneration
12. bounding_box: [ymin, xmin, ymax, xmax] (0-1000 scale) if has_diagram is true

## CRITICAL RULES:

### Section Handling
- **Section Persistence**: If a section identifier (A, B, C, अ, ब, etc.) is found on a page, apply it to ALL subsequent questions on that page until a new section identifier appears.
- Example: If "Section A" appears before Q1, then Q1-Q5 all belong to Section A unless "Section B" appears mid-page.
- If no section is found on a page, leave `section` as empty string.

### Bilingual Extraction
- If questions appear in BOTH English AND Hindi, extract EACH as a SEPARATE entry.
- Treat English and Hindi versions as independent questions with the same question_number.

### OR / ATHVA Questions (VERY IMPORTANT)
- Questions with **"OR"**, **"अथवा"** (Athva), **"या"**, or similar alternatives are **SINGLE questions**.
- Do NOT split them into separate entries.
- Include the FULL text with both options in one `question_text` field.
- Example: A question like "Q13: ... OR Q13 alternative..." should be ONE entry.

### Formatting
- Preserve mathematical notation as LaTeX (e.g., $\frac{a}{b}$)
- Preserve bullet points and sub-parts
- Include all MCQ options (A, B, C, D) in the question_text

## Output Format:
```json
{
  "questions": [
    {
      "question_number": "1",
      "question_text": "Full question text here...",
      "marks": 1,
      "section": "A",
      "question_type": "mcq",
      "chapter": "Chapter Name",
      "topic": "Topic Name",
      "difficulty": "medium",
      "language": "en",
      "has_diagram": false,
      "image_description": null,
      "bounding_box": null
    }
  ]
}
```

Return ONLY the JSON object. No explanations or markdown.
