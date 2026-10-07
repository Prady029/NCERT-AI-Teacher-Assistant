"""
Prompt templates for NCERT AI Teacher Assistant.
All prompts are curriculum-aligned and follow NCERT/CBSE guidelines.
"""

from typing import Dict, List

# =============================================================================
# LESSON PLAN PROMPTS
# =============================================================================

LESSON_PLAN_SYSTEM_PROMPT = """You are an expert NCERT curriculum designer and master teacher with 20+ years of experience creating lesson plans for Indian classrooms (Classes 6-12). You deeply understand:

1. NCERT textbooks and their pedagogical approach (constructivist, activity-based)
2. CBSE examination patterns and assessment guidelines
3. NCF 2005 principles: connecting knowledge to life outside school, shifting away from rote learning
4. NEP 2020 vision: competency-based education, multidisciplinary approach, critical thinking
5. Bloom's Taxonomy for writing measurable learning objectives
6. 5E Instructional Model (Engage, Explore, Explain, Elaborate, Evaluate)
7. Inclusive education strategies for diverse learners
7. Indian classroom realities: large class sizes, limited resources, multilingual contexts

Your lesson plans are practical, time-bound, and directly implementable by teachers."""

LESSON_PLAN_5E_TEMPLATE = """Create a detailed {duration}-period lesson plan for:

**Subject:** {subject}
**Class:** {class_level}
**Chapter:** {chapter}
**Pedagogical Model:** 5E (Engage, Explore, Explain, Elaborate, Evaluate)
**Student Profile:** {student_profile}
**Language:** {language}

## Required Structure:

### 1. LESSON METADATA
- Lesson Title
- Duration: {duration} periods ({total_minutes} minutes total)
- NCERT Textbook Reference (page numbers)
- CBSE Learning Outcomes mapped
- Prerequisites

### 2. LEARNING OBJECTIVES (Bloom's Taxonomy Aligned)
Write 4-6 measurable objectives using Bloom's action verbs:
- Remember: list, define, identify, recall
- Understand: explain, describe, summarize, interpret
- Apply: solve, demonstrate, use, illustrate
- Analyze: compare, contrast, categorize, examine
- Evaluate: judge, justify, critique, defend
- Create: design, construct, formulate, propose

Format each as: "Students will be able to [Bloom verb] [content] [context]"

### 3. 5E LESSON FLOW (with exact timings)

#### ENGAGE ({engage_time} minutes)
- Hook/Provocation: [Specific activity, question, demo, or real-world connection]
- Prior Knowledge Activation: [Specific questions to assess readiness]
- Learning Objective Sharing: [How objectives communicated to students]

#### EXPLORE ({explore_time} minutes)
- Hands-on Activity/Investigation: [Detailed step-by-step student activity]
- Grouping Strategy: [Individual/Pairs/Groups of 4 with rationale]
- Materials Needed: [Specific, locally available materials]
- Guiding Questions: [3-5 open-ended questions for teacher circulation]
- Data Collection/Recording: [How students document findings]

#### EXPLAIN ({explain_time} minutes)
- Student-Led Sharing: [Structure for groups presenting findings]
- Teacher Facilitation: [Key concepts to formalize, vocabulary to introduce]
- Addressing Misconceptions: [Specific common errors and corrections]
- Connecting to Textbook: [Specific NCERT sections, diagrams, examples]

#### ELABORATE ({elaborate_time} minutes)
- Extension Activity: [Application to new context or deeper investigation]
- Differentiation:
  * For Advanced Learners: [Extension challenge]
  * For Struggling Learners: [Scaffolded support]
  * For ELL Students: [Language supports]
- Cross-Curricular Connections: [Links to other subjects]

#### EVALUATE ({evaluate_time} minutes)
- Formative Assessment: [Specific check-for-understanding strategy]
- Exit Ticket: [3 targeted questions aligned to objectives]
- Homework/Extension: [Meaningful practice, not busy work]

### 4. ASSESSMENT CHECKPOINTS (throughout lesson)
| Checkpoint | Method | Objective Assessed | Success Criteria |

### 5. DIFFERENTIATION STRATEGIES
- Content: [How content is adapted]
- Process: [How activities are modified]
- Product: [How students demonstrate learning]
- Environment: [Classroom arrangement, grouping]

### 6. REQUIRED MATERIALS & RESOURCES
- Physical Materials: [Specific quantities]
- Digital Resources: [Links to simulations, videos, PhET, DIKSHA]
- Textbook References: [Exact NCERT pages, figures, activities]

### 7. TEACHER REFLECTION NOTES
- Anticipated Challenges: [3 specific challenges with mitigation]
- Timing Adjustments: [If running short/long]
- Key Questions to Ask: [Higher-order questions for deep thinking]

### 8. CURRICULUM ALIGNMENT
Map each objective to:
- NCERT Learning Outcome Code
- CBSE Competency
- NEP 2020 Skill (Critical Thinking, Creativity, Collaboration, Communication)

---

Generate the complete lesson plan as a structured JSON object matching the LessonPlanResponse schema. Be specific - use actual NCERT content, real activities, and practical Indian classroom strategies."""


# =============================================================================
# QUESTION PAPER PROMPTS
# =============================================================================

QUESTION_PAPER_SYSTEM_PROMPT = """You are an expert CBSE examination paper setter with deep knowledge of:
1. CBSE question paper design and blueprint principles
2. NCERT textbook content and exemplar problems
3. Competency-based assessment (NEP 2020)
3. Bloom's Taxonomy distribution in exam papers
4. Question typology: MCQ, VSA, SA, LA, Case-based, Assertion-Reason
5. Marking scheme design with step-wise marking
6. Difficulty calibration: Easy (30%), Medium (50%), Hard (20%)
7. Time management: 1 mark = 1.5-2 minutes

Create papers that are fair, valid, reliable, and aligned to curriculum."""

QUESTION_PAPER_TEMPLATE = """Design a CBSE-pattern question paper for:

**Subject:** {subject}
**Class:** {class_level}
**Units/Chapters:** {chapters}
**Total Marks:** {total_marks}
**Duration:** {duration} minutes
**Difficulty Distribution:** Easy {easy_pct}%, Medium {medium_pct}%, Hard {hard_pct}%

## Question Type Distribution:
{type_distribution}

## Required Output Structure:

### 1. BLUEPRINT (Design Matrix)
| Unit/Chapter | MCQ (1M) | VSA (1M) | SA (2M) | LA (3M) | Case (5M) | Total Marks | Weightage% |
|--------------|----------|----------|---------|---------|-----------|-------------|------------|

### 2. SECTION-WISE QUESTIONS

#### SECTION A: Multiple Choice Questions (1 Mark Each)
For each MCQ provide:
- Question stem (clear, unambiguous)
- 4 options (1 correct, 3 plausible distractors)
- Correct answer with justification
- Cognitive level (Bloom's)
- NCERT reference (page/example)

#### SECTION B: Very Short Answer (1 Mark Each)
- Concise questions requiring 1-2 sentence answers
- Specific NCERT-based answers
- Marking: 1 mark for correct answer

#### SECTION C: Short Answer (2 Marks Each)
- Questions requiring 3-4 step solutions/explanations
- Step-wise marking scheme (1+1 or 0.5+0.5+1)
- NCERT exemplar-style problems

#### SECTION D: Long Answer (3 Marks Each)
- Multi-step problems requiring 5-7 steps
- Detailed marking scheme with partial credit
- Application/Analysis level (Bloom's)

#### SECTION E: Case-Based/Source-Based (4-5 Marks)
- Real-world scenario/data from NCERT context
- 3-4 sub-questions of varying cognitive levels
- Integrates multiple concepts from chapter

### 3. MARKING SCHEME
Detailed step-wise marking for each question with:
- Key steps/keywords for credit
- Common errors and deductions
- Alternative method credit

### 4. DIFFICULTY ANALYSIS
| Question | Type | Difficulty | Bloom Level | Time (min) |
|----------|------|------------|-------------|------------|

### 5. TIME MANAGEMENT GUIDE
- Section-wise time allocation
- Buffer time for review

---

Generate as structured JSON matching QuestionPaperResponse schema. Questions must be directly from or inspired by NCERT textbook content, exemplar problems, and previous CBSE papers. Ensure linguistic accessibility for Indian students."""


# =============================================================================
# CHAPTER SUMMARY PROMPTS
# =============================================================================

CHAPTER_SUMMARY_TEMPLATE = """Create a comprehensive chapter summary for:

**Subject:** {subject}
**Class:** {class_level}
**Chapter:** {chapter}
**Detail Level:** {detail_level}
**Language:** {language}

## Required Structure:

### 1. CHAPTER OVERVIEW
- Chapter theme/big idea (2-3 sentences)
- Real-world relevance/hook
- Prerequisites from previous classes

### 2. KEY CONCEPTS (Hierarchical)
Organize as: Main Concept → Sub-concepts → Key Points
- Use NCERT terminology exactly
- Highlight definitional vs. conceptual understanding

### 3. IMPORTANT DEFINITIONS
| Term | NCERT Definition | Simplified Explanation | Example |

### 4. FORMULAS & LAWS (if applicable)
| Formula/Law | Variables | Conditions | NCERT Derivation Reference |

### 5. DIAGRAMS & TABLES (descriptive)
List important diagrams with labels and what they illustrate

### 6. COMMON MISCONCEPTIONS
| Misconception | Correct Concept | Classroom Strategy to Address |

### 7. REAL-WORLD APPLICATIONS
Connect to: Daily life, Technology, Environment, Career paths

### 8. NCERT EXEMPLAR PROBLEMS (Representative)
3-5 solved examples showing different question types

### 9. PRACTICE QUESTIONS (with answers)
- 5 MCQs with explanations
- 3 Short Answer
- 2 Long Answer/Application
- 1 Case-based

### 10. EXAM FOCUS AREAS (CBSE Perspective)
- Must-know definitions
- Frequently asked numerical types
- Diagram-based questions from this chapter
- Previous year question trends

### 11. QUICK REVISION CARD (One-page summary)
Condensed version for last-minute revision

---

Generate as structured JSON matching ChapterSummaryResponse schema. Use exact NCERT language, include page references, and ensure accessibility for diverse learners."""


# =============================================================================
# EVALUATION PROMPTS
# =============================================================================

EVALUATION_TEMPLATE = """Evaluate the student's response against the model answer.

**Question:** {question}
**Marks Allocated:** {marks}
**Model Answer:** {model_answer}
**Student Answer:** {student_answer}
**Marking Criteria:** {criteria}

## Evaluation Guidelines:
1. **Content Accuracy** (60%): Correct concepts, facts, formulas
2. **Completeness** (20%): All required steps/points addressed
3. **Clarity & Structure** (10%): Logical flow, proper terminology
4. **NCERT Alignment** (10%): Uses textbook language/approach

## Step-wise Marking:
- Break model answer into markable points
- Award partial credit for partially correct steps
- Deduct for major errors, not minor notation issues
- Credit alternative valid methods

## Output JSON:
{{
  "score": <float>,
  "max_score": <int>,
  "feedback": "<constructive, specific feedback>",
  "criteria_met": ["<criterion1>", "<criterion2>"],
  "criteria_missed": ["<criterion1>", "<criterion2>"],
  "suggestions": ["<specific improvement>", "<next step>"]
}}

Be encouraging but rigorous. Focus on learning, not just scoring."""


# =============================================================================
# PROMPT REGISTRY
# =============================================================================

PROMPT_REGISTRY = {
    "lesson_plan_5e": {
        "system": LESSON_PLAN_SYSTEM_PROMPT,
        "template": LESSON_PLAN_5E_TEMPLATE,
        "variables": ["subject", "class_level", "chapter", "duration", "total_minutes", "student_profile", "language", "engage_time", "explore_time", "explain_time", "elaborate_time", "evaluate_time"]
    },
    "question_paper": {
        "system": QUESTION_PAPER_SYSTEM_PROMPT,
        "template": QUESTION_PAPER_TEMPLATE,
        "variables": ["subject", "class_level", "chapters", "total_marks", "duration", "easy_pct", "medium_pct", "hard_pct", "type_distribution"]
    },
    "chapter_summary": {
        "system": "You are an expert NCERT content creator making chapter summaries for teachers and students.",
        "template": CHAPTER_SUMMARY_TEMPLATE,
        "variables": ["subject", "class_level", "chapter", "detail_level", "language"]
    },
    "evaluation": {
        "system": "You are a fair, expert CBSE examiner evaluating student responses.",
        "template": EVALUATION_TEMPLATE,
        "variables": ["question", "marks", "model_answer", "student_answer", "criteria"]
    }
}


def get_prompt(prompt_name: str, **kwargs) -> Dict[str, str]:
    """Get formatted prompt by name with variables."""
    if prompt_name not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt: {prompt_name}")
    
    prompt_info = PROMPT_REGISTRY[prompt_name]
    template = prompt_info["template"]
    
    # Format template with provided variables
    try:
        formatted = template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required variable for {prompt_name}: {e}")
    
    return {
        "system": prompt_info["system"],
        "user": formatted
    }


def get_prompt_variables(prompt_name: str) -> List[str]:
    """Get required variables for a prompt."""
    if prompt_name not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt: {prompt_name}")
    return PROMPT_REGISTRY[prompt_name]["variables"]