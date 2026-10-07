# NCERT AI Teacher Assistant 🏫🤖

**An AI-powered assistant that helps teachers create lesson plans, draft question sets, and automate classroom paperwork — so they can focus on teaching.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![LLM](https://img.shields.io/badge/LLM-Gemini%20%7C%20GPT-purple.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

---

## 🎯 The Problem

> **Teachers spend 40%+ of their time on paperwork** — lesson plans, question papers, assessment rubrics, administrative reports — instead of actual teaching.

This project was born from my background in **education (B.Sc.B.Ed from NCERT's RIE Bhubaneswar)** combined with my career in **Data Science/GenAI**. The goal: *help teachers teach, not draft papers.*

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| **📝 Lesson Plan Generator** | Creates structured lesson plans aligned with NCERT curriculum | 🔄 In Progress |
| **📋 Question Paper Generator** | Drafts unit tests, exam papers with varying difficulty levels | 🔄 In Progress |
| **🎯 Learning Objectives** | Auto-generates Bloom's Taxonomy aligned objectives | 📋 Planned |
| **📊 Assessment Rubrics** | Creates marking schemes and evaluation criteria | 📋 Planned |
| **📚 Chapter Summaries** | Concise summaries for quick teacher reference | 📋 Planned |
| **🔄 Differentiation Support** | Adapts content for different learning levels | 📋 Planned |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NCERT AI Teacher Assistant                │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Next.js + TypeScript + Tailwind)                 │
│  ├── Teacher Dashboard          ├── Lesson Plan Builder      │
│  ├── Question Paper Wizard      ├── Class Management         │
│  └── Resource Library           └── Export (PDF/Word/Google) │
├─────────────────────────────────────────────────────────────┤
│  Backend (Python FastAPI / Next.js API Routes)               │
│  ├── LLM Orchestration (LangChain/LangGraph)                │
│  ├── Prompt Templates (Curriculum-Aware)                    │
│  ├── RAG Pipeline (NCERT Textbooks + Syllabus)              │
│  ├── Output Validation & Formatting                         │
│  └── Teacher Feedback Loop (RLHF-style)                     │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Base                                               │
│  ├── NCERT Textbooks (PDF/EPUB → Vector Store)              │
│  ├── CBSE Syllabus & Curriculum Maps                        │
│  ├── Question Banks (Previous Years, Exemplars)             │
│  └── Pedagogical Frameworks (Bloom's, NCF 2005, NEP 2020)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS, Framer Motion |
| **Backend** | Next.js API Routes / Python FastAPI |
| **LLM** | Google Gemini / OpenAI GPT-4 / Local LLMs (Ollama) |
| **RAG** | LangChain, LangGraph, Qdrant / LanceDB |
| **Document Processing** | PyMuPDF, python-docx, unstructured |
| **Vector Search** | Qdrant, LanceDB, or pgvector |
| **Auth** | NextAuth.js (Google, Email) |
| **Deployment** | Vercel (Frontend) + Railway/Render (Backend) |
| **Export** | PDF (ReportLab/WeasyPrint), DOCX (python-docx), Google Docs API |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+ (for backend services)
- LLM API Key (Google AI Studio / OpenAI / Anthropic)

### Frontend Setup
```bash
cd prady029.github.io  # This is the Next.js frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Backend Setup (Python)
```bash
cd backend  # To be created
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

### Environment Variables
```bash
# .env
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000
```

---

## 📚 Curriculum Alignment

The assistant is designed around **Indian education standards**:

| Framework | Integration |
|-----------|-------------|
| **NCERT Textbooks** | Primary knowledge source (Classes 6-12) |
| **CBSE Syllabus** | Chapter-wise mapping, weightage |
| **NCF 2005** | Pedagogical principles, constructivist approach |
| **NEP 2020** | Competency-based education, multidisciplinary |
| **Bloom's Taxonomy** | Objective classification (Remember → Create) |
| **Learning Outcomes** | NCERT-defined outcomes per class/subject |

### Supported Subjects (Planned)
- **Science** (Physics, Chemistry, Biology) — Classes 9-12
- **Mathematics** — Classes 9-12
- **Social Science** (History, Geography, Civics, Economics) — Classes 9-10
- **English/Hindi** — Language and literature

---

## 💡 Example Use Cases

### 1. Lesson Plan Generation
```
Input:  Class 10 Science, Chapter "Light - Reflection and Refraction", 
        2 periods, mixed-ability class

Output: Structured lesson plan with:
  • Learning objectives (Bloom's aligned)
  • Prerequisites & misconceptions
  • Activity timeline (5E model: Engage, Explore, Explain, Elaborate, Evaluate)
  • Differentiation strategies
  • Assessment checkpoints
  • Required materials & digital resources
```

### 2. Question Paper Creation
```
Input:  Class 12 Physics, Unit "Electrostatics", 
        30 marks, 1 hour, CBSE pattern

Output: Question paper with:
  • Section A: MCQs (1 mark × 5)
  • Section B: Short Answer (2 marks × 5) 
  • Section C: Long Answer (3 marks × 4)
  • Section D: Case-based (5 marks × 1)
  • Marking scheme & blueprint
  • Difficulty distribution (Easy 30%, Medium 50%, Hard 20%)
```

---

## 🔒 Privacy & Ethics

| Principle | Implementation |
|-----------|----------------|
| **Data Privacy** | No student PII stored; teacher data encrypted at rest |
| **Content Safety** | LLM guardrails for educational appropriateness |
| **Bias Mitigation** | Regular audits for gender/cultural bias in generated content |
| **Human-in-Loop** | Teacher *must* review before classroom use |
| **Offline Option** | Local LLM support (Ollama) for air-gapped schools |

> ⚠️ **Important**: This tool is **experimental**. Always review generated content before use. AI can hallucinate facts, misalign with curriculum, or produce inappropriate difficulty levels.

---

## 🗺️ Roadmap

### Phase 1: Core MVP (Current)
- [ ] Lesson plan generator (single chapter)
- [ ] Question paper generator (single unit)
- [ ] Basic NCERT textbook RAG
- [ ] PDF/Word export

### Phase 2: Classroom Integration
- [ ] Multi-chapter unit plans
- [ ] Assessment rubric generator
- [ ] Student-facing practice questions
- [ ] Teacher dashboard with class management

### Phase 3: Intelligence & Personalization
- [ ] Adaptive difficulty based on class performance
- [ ] Learning gap analysis from assessments
- [ ] Multi-language support (Hindi, regional)
- [ ] Voice input for teachers

### Phase 4: Ecosystem
- [ ] Collaborative lesson planning
- [ ] Integration with DIKSHA, Google Classroom
- [ ] Analytics for school administrators
- [ ] Community-contributed templates

---

## 🤝 Contributing

We welcome contributions from **educators, developers, and researchers**!

### Ways to Contribute
1. **🧪 Test & Report** — Try the tool, report bugs, suggest improvements
2. **📚 Curriculum Mapping** — Help map NCERT chapters to learning objectives
3. **💬 Prompt Engineering** — Refine prompts for better outputs
4. **🌐 Localization** — Add Hindi/regional language support
5. **💻 Code** — Frontend, backend, RAG pipeline improvements

### Development Setup
```bash
# Fork & clone
git clone https://github.com/Prady029/NCERT-AI-Teacher-Assistant
cd NCERT-AI-Teacher-Assistant

# Create feature branch
git checkout -b feature/lesson-plan-v2

# Make changes, test, commit
git commit -m "feat: add 5E model template for science lessons"

# Push & create PR
git push origin feature/lesson-plan-v2
```

---

## 📖 Documentation

| Document | Link |
|----------|------|
| **User Guide** | [USAGE_GUIDE.md](docs/USAGE_GUIDE.md) *(coming soon)* |
| **Prompt Templates** | [PROMPTS.md](docs/PROMPTS.md) *(coming soon)* |
| **API Reference** | [API.md](docs/API.md) *(coming soon)* |
| **Curriculum Maps** | [CURRICULUM.md](docs/CURRICULUM.md) *(coming soon)* |

---

## 📜 License

MIT License — Free for educational and research use.

---

## 🙏 Acknowledgments

- **NCERT** — For open-access textbooks and curriculum frameworks
- **CBSE** — For syllabus and examination patterns
- **Teachers** — Whose daily challenges inspired this project
- **Open Source LLM Community** — HuggingFace, LangChain, Ollama teams

---

## 👤 Author

**Pradyumna Kumar Sahoo**  
*Data Scientist • B.Sc.B.Ed (NCERT RIE Bhubaneswar) • M.Sc. Big Data Analytics (CURAJ)*

- 🌐 Portfolio: [prady029.github.io](https://prady029.github.io)
- 💼 LinkedIn: [prady029](https://linkedin.com/in/prady029)
- 🐙 GitHub: [@Prady029](https://github.com/Prady029)
- ✉️ Email: [pradyumna.sahoo@outlook.in](mailto:pradyumna.sahoo@outlook.in)

---

> *"Technology will not replace great teachers, but technology in the hands of great teachers can be transformational."* — George Couros

*Last updated: October 2024*