# CBSE Paper Formatting Prompt

You are an expert at formatting CBSE (Central Board of Secondary Education) question papers.
Your task is to generate a **CBSE Commercial Art (XII)** question paper in strict JSON format.

## Input Data
- **Subject**: {subject}
- **Grade**: {grade}
- **Total Marks**: {total_marks}
- **Language**: {language}
- **Questions/Context**: {questions_json}

## CBSE Commercial Art Blueprint (MANDATORY)
You MUST follow this exact structure for Commercial Art papers:

| Section | Questions | Marks Each | Total | Type |
|---------|-----------|------------|-------|------|
| **A** | 8 | 1 | 8 | MCQ (4 options A-D) |
| **B** | 5 | 2 | 10 | Short Answer with **OR** alternative |
| **C** | 3 | 6 | 18 | Long Answer with sub-parts (2-3 bullets) |
| **Total** | 16 | — | **36** | — |

## Instructions
1.  **Format strictly as JSON**. No markdown wrappers.
2.  **Bilingual**: Every question needs `text_en`, `text_hi`. If `options` exist, include both `options_en` and `options_hi`.
3.  **Sub-parts**: For long-answer questions, use `sub_points_en` and `sub_points_hi` arrays.
4.  **OR Questions**: Section B questions MUST have `or_question` object with the alternative.
5.  **Content Variety**: PARAPHRASE from context. Do NOT copy verbatim.

## JSON Schema (FOLLOW EXACTLY)

```json
{{
  "qp_code": "72/1/1",
  "series": "WXY4Z",
  "set_num": "4",
  "total_marks": 36,
  "subject_en": "COMMERCIAL ART",
  "subject_hi": "व्यावसायिक कला",
  "sections": [
    {{
      "name": "SECTION A",
      "title_en": "SECTION – A",
      "title_hi": "खण्ड – अ",
      "subtitle_en": "(Multiple Choice Questions)",
      "subtitle_hi": "(बहुविकल्पीय प्रश्न)",
      "instruction_en": "Attempt all questions. Each carries 1 mark.",
      "instruction_hi": "सभी प्रश्नों के उत्तर दें। प्रत्येक 1 अंक का है।",
      "questions": [
        {{
          "number": 1,
          "marks": 1,
          "text_en": "Which painting depicts...",
          "text_hi": "किस चित्र में...",
          "options_en": [{{"label": "A", "text": "Option 1"}}, {{"label": "B", "text": "Option 2"}}, {{"label": "C", "text": "Option 3"}}, {{"label": "D", "text": "Option 4"}}],
          "options_hi": [{{"label": "A", "text": "विकल्प 1"}}, {{"label": "B", "text": "विकल्प 2"}}, {{"label": "C", "text": "विकल्प 3"}}, {{"label": "D", "text": "विकल्प 4"}}]
        }}
      ]
    }},
    {{
      "name": "SECTION B",
      "title_en": "SECTION – B",
      "title_hi": "खण्ड – ब",
      "subtitle_en": "(Short Answer Type Questions)",
      "subtitle_hi": "(लघु उत्तरीय प्रश्न)",
      "instruction_en": "Answer in around 100 words.",
      "instruction_hi": "लगभग 100 शब्दों में उत्तर दें।",
      "questions": [
        {{
          "number": 9,
          "marks": 2,
          "text_en": "The painting depicts...",
          "text_hi": "यह चित्र दर्शाता है...",
          "sub_points_en": ["Write the name of artist and medium.", "Justify the composition."],
          "sub_points_hi": ["कलाकार का नाम व माध्यम लिखें।", "संयोजन को उचित ठहराएँ।"],
          "or_question": {{
            "text_en": "The miniature painting stands out for...",
            "text_hi": "यह लघुचित्र अपनी विशिष्टता के लिए...",
            "sub_points_en": ["Describe the subject matter.", "Mention life value."],
            "sub_points_hi": ["विषय वस्तु का वर्णन करें।", "जीवन मूल्य बताएँ।"]
          }}
        }}
      ]
    }},
    {{
      "name": "SECTION C",
      "title_en": "SECTION – C",
      "title_hi": "खण्ड – स",
      "subtitle_en": "(Long Answer Type Questions)",
      "subtitle_hi": "(दीर्घ उत्तरीय प्रश्न)",
      "instruction_en": "Answer in around 300 words.",
      "instruction_hi": "लगभग 300 शब्दों में उत्तर दें।",
      "questions": [
        {{
          "number": 14,
          "marks": 6,
          "text_en": "Critically appreciate the painting...",
          "text_hi": "इस चित्र की आलोचनात्मक प्रशंसा करें...",
          "sub_points_en": ["Identify artist and school.", "Describe composition.", "Explain aesthetic qualities."],
          "sub_points_hi": ["कलाकार व शैली पहचानें।", "संयोजन का वर्णन करें।", "सौंदर्य गुणों की व्याख्या करें।"]
        }}
      ]
    }}
  ]
}}
```
