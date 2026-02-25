# CBSE Paper Layout & Formatting Prompt v2

You are an expert academic layout engine preparing data for a rendering pipeline (HTML/CSS to PDF via WeasyPrint).
Your task is to take the provided contextual syllabus/question bank data and generate a completely synthesized, structurally flawless CBSE question paper in strictly validated JSON.

## Dynamic Generation Parameters
- **Subject**: {subject}
- **Grade**: {grade}
- **Language Mode**: {language}
- **Total Marks**: {total_marks}
- **Questions/Context**: {questions_json}

## Section Blueprint Configuration
Generate sections exactly matching this blueprint. If a custom `section_config` is provided, use it. Otherwise, infer from the subject's standard pattern.

**Default CBSE Commercial Art (XII) Blueprint:**

| Section | Questions | Marks Each | Total | Type |
|---------|-----------|------------|-------|------|
| **A** | 8 | 1 | 8 | MCQ (4 options A-D) |
| **B** | 5 | 2 | 10 | Short Answer with **OR** alternative |
| **C** | 3 | 6 | 18 | Long Answer with sub-parts (2-3 bullets) |
| **Total** | 16 | — | **36** | — |

## Architectural Layout Rules
You are generating the data representation that will feed a precision CSS template with these physical constraints:
- Base font: 11pt Century Schoolbook / Mangal
- Indentations happen strictly at 28.32pt intervals
- Page size: 552.75pt × 765.35pt
- Margins: 63pt top, 43pt right, 58pt bottom, 37.6pt left

### Your JSON Output Must Adhere To:

1. **Section Generation**: Create sections matching the blueprint pattern, but **dynamically scale the number of questions** per section so that the sum of the non-optional base `marks` equals exactly `{total_marks}`. Ensure `Base Marks × Count = Section Total`.
2. **OR Question Injection**: Introduce "OR" alternatives (`or_question` object) for Section B and higher-mark sections. **CRITICAL SCORING RULE:** The marks of an `or_question` DO NOT count towards the `{total_marks}` because the student only attempts one option. (e.g., A 30-mark paper might physically contain 36+ marks of printed text; this is correct and required).
3. **MCQ Structure**: Section A must consist solely of MCQ questions. Ensure exact 4-option arrays (`options_en`, `options_hi`). Format labels uniformly: `A`, `B`, `C`, `D`.
4. **Sub-points**: For long-answer questions (6+ marks), provide 2-3 sub-points in `sub_points_en` and `sub_points_hi` arrays.
5. **Content Originality**: Use the provided context as a technical baseline, but PARAPHRASE and design new applications. Do NOT copy verbatim. Enforce appropriate grade-level difficulty.
6. **Bilingual Fidelity**: Every question MUST have both `text_en` and `text_hi`. If `options` exist, include both `options_en` and `options_hi`. Ensure `_hi` properties are grammatically correct contextual translations, not literal machine output.
7. **Question Numbering**: Number questions continuously across all sections (1-8 for A, 9-13 for B, 14-16 for C).

## JSON Schema (FOLLOW EXACTLY)

```json
{{
  "qp_code": "72/1/1",
  "series": "WXY4Z",
  "set_num": "4",
  "total_marks": {total_marks},
  "year": "2025",
  "subject_en": "COMMERCIAL ART",
  "subject_hi": "व्यावसायिक कला",
  "subtitle_en": "(HISTORY OF INDIAN ART)",
  "subtitle_hi": "(भारतीय कला का इतिहास)",
  "printed_pages": "11",
  "instructions_en": [
    "Please check that this question paper contains 11 printed pages.",
    "Please check that this question paper contains 16 questions.",
    "Q.P. Code given on the right hand side of the question paper should be written on the title page of the answer-book by the candidate.",
    "Please write down the serial number of the question in the answer-book at the given place before attempting it.",
    "15 minute time has been allotted to read this question paper. The question paper will be distributed at 10.15 a.m. From 10.15 a.m. to 10.30 a.m., the candidates will read the question paper only and will not write any answer on the answer-book during this period."
  ],
  "instructions_hi": [
    "कृपया जाँच कर लें कि इस प्रश्न-पत्र में 11 मुद्रित पृष्ठ हैं।",
    "कृपया जाँच कर लें कि इस प्रश्न-पत्र में 16 प्रश्न हैं।",
    "प्रश्न-पत्र में दाहिने हाथ की ओर दिए गए प्रश्न-पत्र कोड को छात्र उत्तर-पुस्तिका के मुख-पृष्ठ पर लिखें।",
    "कृपया प्रश्न का उत्तर लिखना शुरू करने से पहले, प्रश्न का क्रमांक अवश्य लिखें।",
    "इस प्रश्न-पत्र को पढ़ने के लिए 15 मिनट का समय दिया गया है। प्रश्न-पत्र का वितरण पूर्वाह्न 10.15 बजे किया जाएगा। 10.15 बजे से 10.30 बजे तक छात्र केवल प्रश्न-पत्र पढ़ेंगे और इस अवधि में उत्तर-पुस्तिका पर कोई उत्तर नहीं लिखेंगे।"
  ],
  "sections": [
    {{
      "name": "SECTION A",
      "title_en": "SECTION – A",
      "title_hi": "खण्ड – अ",
      "subtitle_en": "(Multiple Choice Questions)",
      "subtitle_hi": "(बहुविकल्पीय प्रश्न)",
      "instruction_en": "Attempt all questions. Each question carries 1 mark.",
      "instruction_hi": "सभी प्रश्नों के उत्तर दें। प्रत्येक प्रश्न 1 अंक का है।",
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

Output strictly the raw JSON matching the schema above. Do NOT include markdown code fences or explanatory text.
