# AttendIQ COA AI Learning Assistant

## End-to-End README for Smart Attendance, COA Learning Intelligence, AI Training, Monitoring, Recommendations, and Metric Tradeoffs

**Version:** 1.0  
**Project:** AttendIQ COA Smart Attendance + AI Learning Assistant  
**Domain:** Computer Organization and Architecture  
**Primary Users:** Students, Faculty, Academic Administrators  
**Core Stack:** PWA + FastAPI + PostgreSQL + PaddleOCR + Flan-T5 LoRA + Knowledge Graph + Prometheus/Grafana + MLflow  

---

## 1. Executive Summary

AttendIQ COA is a privacy-first classroom attendance and learning intelligence platform for Computer Organization and Architecture. The original product requirement was to design a system that motivates students to attend COA classes and participate meaningfully. The proposed solution converts attendance from a rule-based compliance activity into a learning-value mechanism.

The platform verifies whether students are present in the correct classroom, checks whether students participated during the class, unlocks academic resources based on attendance and engagement, and later introduces an AI assistant that can read handwritten answers or notes, identify concept coverage, detect missing concepts, generate feedback, and recommend personalized resources.

The overall design philosophy is:

```text
Attendance should unlock better learning, not merely enforce physical presence.
```

The AI assistant follows this engineering principle:

```text
Knowledge Base First → Dataset Second → Fine-Tuning Third → Recommendations Fourth → Monitoring Everywhere
```

---

## 2. Problem Statement

Computer Organization and Architecture is difficult for many students because it contains abstract hardware-level concepts such as:

- CPU functional blocks
- Instruction set architecture
- Registers
- Instruction execution cycle
- RTL interpretation
- Addressing modes
- Data representation
- Integer and floating point arithmetic
- Adders and multipliers
- Restoring and non-restoring division
- Control unit design
- Memory hierarchy
- Cache mapping
- Replacement algorithms
- DMA
- Interrupts
- Pipelining
- Pipeline hazards

Students often skip classes when topics feel theoretical or when classroom attendance does not provide immediate value. Faculty may manually track attendance, but this does not reliably measure engagement or learning. Institutions receive attendance data, but not concept-level understanding.

### Design Challenge

```text
How might we increase genuine student attendance and active engagement in COA classes while preserving privacy and using free/open-source-first development resources?
```

---

## 3. Product Vision

AttendIQ COA should become a classroom engagement platform with four major layers:

1. **Presence Verification**  
   Verify whether student check-in occurred during a valid class session.

2. **Participation Verification**  
   Use micro-quizzes and concept checks to measure active engagement.

3. **Reward-Based Resource Access**  
   Unlock academic resources based on attendance and participation progress.

4. **AI Learning Feedback**  
   Use OCR + concept extraction + LoRA fine-tuned model + recommendation graph to guide student learning.

---

## 4. Key Product Features

### Student Features

- Login using institutional credentials.
- View active COA class sessions.
- Scan rotating QR code for attendance.
- Complete in-class concept checks.
- View attendance percentage.
- View participation score.
- Track reward tier progress.
- Access unlocked notes, PYQs, lab solutions, quizzes, and revision resources.
- Upload handwritten answers or notes in Phase 2.
- Receive AI-generated concept feedback.
- Receive personalized resource recommendations.

### Faculty Features

- Create class sessions.
- Start and close class sessions.
- Display rotating QR code.
- Monitor live attendance.
- Launch micro-quizzes.
- View topic-level quiz analytics.
- Upload and map learning resources.
- Review weak topics.
- Export attendance and participation reports.
- Override attendance with audit trail when needed.

### Admin Features

- Manage users.
- Manage departments, courses, sections, and classrooms.
- Enroll students.
- Configure reward policies.
- Review logs and audit records.
- Manage privacy and retention rules.

---

## 5. High-Level Architecture

```text
Student Mobile PWA
        |
        v
Authentication Service
        |
        v
Attendance API ------------------------+
        |                              |
        v                              |
Verification Engine                    |
        |                              |
        +--> QR Token Service          |
        +--> Device Session Validator  |
        +--> Optional Proximity Check   |
        |                              |
        v                              |
PostgreSQL Database <------------------+

Faculty Dashboard
        |
        +--> Session Management API
        +--> Quiz API
        +--> Resource API
        +--> Analytics API

Phase 2 AI Service
        |
        +--> OCR Engine
        +--> COA Concept Extractor
        +--> T5 LoRA Feedback Model
        +--> Recommendation Engine
```

---

## 6. Recommended Technology Stack

| Layer | Recommended Option | Reason |
|---|---|---|
| Frontend | React / Next.js / PWA | Works well for phone-first web apps. |
| Backend | FastAPI | Python-native, lightweight, good for AI integration. |
| Database | PostgreSQL | Strong relational model for users, sessions, attendance, quizzes, resources, and analytics. |
| Storage | Supabase Storage / S3-compatible storage | Stores notes, PDFs, quiz files, and AI uploads. |
| Authentication | Supabase Auth / Firebase Auth / Custom JWT | Good for MVP authentication. |
| OCR | PaddleOCR | Suitable for scanned/handwritten educational content. |
| Model | Flan-T5 Large + LoRA | Good balance of cost, quality, and domain adaptation. |
| Monitoring | Prometheus + Grafana | Runtime metrics and dashboards. |
| Experiment Tracking | MLflow | Tracks model training runs, metrics, parameters, artifacts, and versions. |
| Batch Quality Monitoring | Evidently-style reports | Data drift, AI quality, and batch evaluation reporting. |

---

## 7. Production Repository Structure

```text
attendiq-coa/
├── frontend/
│   ├── student-app/
│   ├── faculty-dashboard/
│   └── admin-dashboard/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── courses/
│   │   ├── enrollments/
│   │   ├── classrooms/
│   │   ├── sessions/
│   │   ├── attendance/
│   │   ├── verification/
│   │   ├── quizzes/
│   │   ├── rewards/
│   │   ├── resources/
│   │   ├── analytics/
│   │   ├── audits/
│   │   └── ai/
│   ├── config/
│   ├── middleware/
│   ├── db/
│   ├── tests/
│   └── main.py
│
├── ai-services/
│   ├── ocr-service/
│   ├── t5-lora-service/
│   ├── recommendation-engine/
│   └── weak-topic-detector/
│
├── database/
│   ├── schema/
│   ├── migrations/
│   ├── seed/
│   └── views/
│
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   ├── ERD.md
│   ├── API_SPEC.md
│   ├── UML.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   ├── AI_ARCHITECTURE.md
│   ├── COST_ESTIMATION.md
│   └── SRS.md
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   ├── terraform/
│   ├── kubernetes/
│   └── monitoring/
│
├── scripts/
├── .github/
│   └── workflows/
├── README.md
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## 8. Core Database Tables

| Table | Purpose |
|---|---|
| users | Stores students, faculty, and admins. |
| departments | Stores academic departments. |
| courses | Stores COA course metadata. |
| course_sections | Maps course to faculty and batch/section. |
| enrollments | Maps students to course sections. |
| classrooms | Stores classroom metadata and optional proximity information. |
| class_sessions | Stores lecture/session details. |
| qr_tokens | Stores short-lived QR token metadata. |
| attendance_records | Stores attendance event and verification status. |
| device_sessions | Stores hashed device/session signals. |
| quiz_questions | Stores concept-check questions. |
| session_quizzes | Maps questions to active sessions. |
| quiz_responses | Stores student answers. |
| resources | Stores notes, quizzes, PYQs, and unlockable materials. |
| reward_policies | Stores bronze/silver/gold/platinum thresholds. |
| student_reward_status | Stores current student reward progress. |
| resource_access_logs | Tracks resource usage. |
| ai_submissions | Stores OCR and AI feedback workflow outputs. |
| audit_logs | Tracks sensitive actions and overrides. |

---

## 9. Core API Groups

### Authentication

```text
POST /auth/register
POST /auth/login
POST /auth/logout
```

### Course and Enrollment

```text
GET  /courses
POST /admin/courses
POST /admin/enrollments
```

### Sessions

```text
POST /faculty/sessions
POST /faculty/sessions/{sessionId}/start
POST /faculty/sessions/{sessionId}/close
GET  /faculty/sessions/{sessionId}/live
GET  /faculty/sessions/{sessionId}/qr
```

### Attendance

```text
POST /student/attendance/check-in
GET  /student/attendance/summary?courseId={courseId}
POST /faculty/attendance/{attendanceId}/override
```

### Quizzes

```text
POST /faculty/sessions/{sessionId}/quizzes
GET  /student/sessions/{sessionId}/active-quiz
POST /student/quizzes/{sessionQuizId}/responses
GET  /faculty/sessions/{sessionId}/quiz-analytics
```

### Resources and Rewards

```text
POST /faculty/resources
GET  /student/resources?courseId={courseId}
GET  /student/rewards?courseId={courseId}
```

### Analytics

```text
GET /faculty/analytics/course/{courseId}
GET /admin/audit-logs
```

### AI Phase 2

```text
POST /student/ai/submissions
GET  /student/ai/submissions/{submissionId}
```

---

## 10. AI Learning Assistant Objective

The AI learning assistant should help students understand and improve their COA answers. It should not replace faculty grading. It should provide support, feedback, and recommendations.

### AI Capabilities

- Extract text from handwritten notes and answers.
- Identify covered COA concepts.
- Identify missing concepts.
- Detect misconceptions.
- Generate constructive feedback.
- Recommend learning resources.
- Aggregate weak-topic analytics for faculty.

---

## 11. Data Collection Strategy

The model should not be trained directly on raw PDFs. Raw notes are noisy and not task-aligned. The correct approach is to use source material to build structured datasets.

```text
PDFs / Notes / Questions / Answers
        |
        v
Text Extraction / OCR
        |
        v
Cleaning and Chunking
        |
        v
Concept Tagging
        |
        v
Knowledge Base and Resource Graph
        |
        v
Instruction Dataset Generation
        |
        v
LoRA Fine-Tuning
```

### Resources to Collect

| Resource Type | Examples | Usage |
|---|---|---|
| University notes | COA lecture notes, digital notes, tutorials | Foundational knowledge base. |
| Faculty resources | PPTs, annotations, class notes, rubrics | Highest-quality local ground truth. |
| Question papers | Mid-sem, end-sem, quizzes, PYQs | Evaluation and answer dataset generation. |
| Student answers | Excellent, good, average, weak, misconception answers | Train concept coverage and feedback quality. |
| Lab material | ISA examples, CPU design labs, memory experiments | Practical examples and resource recommendation. |
| Open educational material | Licensed public notes/books | Fill gaps in concept coverage. |

### Data Governance

- Use only legally reusable or institution-approved content.
- Anonymize student submissions.
- Do not train on identifiable student data without consent.
- Track source metadata and license metadata.
- Keep faculty review for generated datasets.

---

## 12. COA Concept Taxonomy

```text
COA
├── Functional Blocks
│   ├── CPU
│   ├── Memory
│   ├── Input-Output Subsystems
│   └── Control Unit
│
├── Instruction Set Architecture
│   ├── Registers
│   ├── Instruction Execution Cycle
│   ├── RTL Interpretation
│   ├── Addressing Modes
│   └── Instruction Sets
│
├── Data Representation
│   ├── Signed Number Representation
│   ├── Fixed Point Representation
│   ├── Floating Point Representation
│   └── Character Representation
│
├── Computer Arithmetic
│   ├── Integer Addition and Subtraction
│   ├── Ripple Carry Adder
│   ├── Carry Look Ahead Adder
│   ├── Shift-and-Add Multiplication
│   ├── Booth Multiplier
│   ├── Carry Save Multiplier
│   ├── Restoring Division
│   ├── Non-Restoring Division
│   └── Floating Point Arithmetic
│
├── CPU Control Unit
│   ├── Hardwired Control
│   ├── Microprogrammed Control
│   └── Hypothetical CPU Design
│
├── Memory System
│   ├── Semiconductor Memory
│   ├── Memory Organization
│   ├── Memory Interleaving
│   ├── Hierarchical Memory
│   ├── Cache Memory
│   ├── Cache Size vs Block Size
│   ├── Mapping Functions
│   ├── Replacement Algorithms
│   └── Write Policies
│
├── I/O Subsystems
│   ├── Program Controlled I/O
│   ├── Interrupt Driven I/O
│   ├── DMA
│   ├── Privileged Instructions
│   ├── Non-Privileged Instructions
│   ├── Software Interrupts
│   └── Exceptions
│
└── Performance Enhancement
    ├── Pipelining
    ├── Throughput
    ├── Speedup
    └── Pipeline Hazards
```

---

## 13. Preprocessing Pipeline

### Step 1: File Collection

Store raw data in a structured folder:

```text
data/raw/
├── notes/
├── slides/
├── question_papers/
├── lab_manuals/
├── student_answers/
└── faculty_rubrics/
```

### Step 2: Text Extraction

Use text extraction for digital PDFs:

```text
PyMuPDF
pdfplumber
Apache Tika
```

Use OCR for scanned PDFs and handwritten notes:

```text
PaddleOCR
Tesseract fallback
```

### Step 3: Cleaning

Remove:

- Headers
- Footers
- Page numbers
- Watermarks
- Duplicated lines
- Broken hyphenation
- References not useful for training
- Navigation text

### Step 4: Chunking

Chunk by:

- Chapter
- Topic
- Subtopic
- Concept
- Definition
- Formula
- Example
- Question-answer pair

### Step 5: Concept Tagging

Each chunk should be tagged with:

```json
{
  "topic": "Cache Memory",
  "subtopic": "Direct Mapping",
  "concepts": ["cache line", "block", "mapping function"],
  "difficulty": "medium",
  "source_type": "faculty_notes",
  "license_status": "approved"
}
```

---

## 14. OCR Pipeline

```text
Image Upload
        |
        v
File Validation
        |
        v
Image Resize
        |
        v
Noise Removal
        |
        v
Deskew
        |
        v
Contrast Enhancement
        |
        v
PaddleOCR
        |
        v
OCR Confidence Scoring
        |
        v
Text Cleanup
        |
        v
Concept Extraction
```

### OCR Metrics

| Metric | Meaning | Decision |
|---|---|---|
| OCR Confidence | Confidence score from OCR engine | Ask re-upload if too low. |
| CER | Character Error Rate | Improve preprocessing if high. |
| WER | Word Error Rate | Improve OCR model or image quality guidance if high. |
| OCR Latency | Processing time | Resize images or use async processing if high. |
| OCR Failure Rate | No text or pipeline crash | Add validation and fallback OCR. |

---

## 15. Knowledge Graph Strategy

A knowledge graph makes recommendations explainable and reduces hallucination.

```text
Concept
   ├── Definition
   ├── Formula
   ├── Example
   ├── Related Concepts
   ├── Resources
   ├── Quiz Questions
   ├── Common Misconceptions
   └── Difficulty Level
```

Example:

```text
Pipeline Hazard
   ├── Data Hazard
   ├── Structural Hazard
   ├── Control Hazard
   ├── Forwarding
   ├── Stalling
   ├── Branch Prediction
   ├── Pipeline Notes
   ├── Hazard Quiz
   └── Faculty Revision Sheet
```

---

## 16. Dataset Generation Strategy

Do not fine-tune on raw chapters. Generate educational task datasets.

### Dataset A: Concept Explanation

```json
{
  "instruction": "Explain cache mapping in COA.",
  "output": "Cache mapping defines how memory blocks are placed into cache lines..."
}
```

### Dataset B: Concept Coverage

```json
{
  "question": "Explain DMA.",
  "expected_concepts": ["direct memory transfer", "CPU bypass", "interrupt", "DMA controller"],
  "student_answer": "DMA transfers data between memory and device without CPU involvement.",
  "covered_concepts": ["direct memory transfer", "CPU bypass"],
  "missing_concepts": ["interrupt", "DMA controller"]
}
```

### Dataset C: Feedback Generation

```json
{
  "student_answer": "Pipeline hazards occur when instructions conflict.",
  "topic": "Pipeline Hazards",
  "feedback": "The answer is partially correct but should explain structural, data, and control hazards separately."
}
```

### Dataset D: Recommendation Mapping

```json
{
  "missing_concepts": ["branch prediction", "pipeline stall"],
  "recommended_resources": ["Pipeline Hazard Notes", "Branch Prediction Quiz"]
}
```

---

## 17. Synthetic Dataset Strategy

Real student answers may be limited. Generate synthetic training examples for each topic:

```text
Excellent Answer
Good Answer
Average Answer
Weak Answer
Incomplete Answer
Misconception Answer
```

For every topic, create:

```text
100+ answer variations
```

Synthetic data must be sampled and reviewed before being trusted for training.

---

## 18. Model Selection Strategy

| Model | Pros | Cons | Decision |
|---|---|---|---|
| Flan-T5 Base | Fast, cheap, easy to train | Lower reasoning and feedback quality | Good baseline |
| Flan-T5 Large | Better feedback quality, manageable cost | Higher latency and compute than Base | Recommended MVP model |
| Llama-class models | Strong generation | Higher cost, latency, and hallucination risk | Use only if T5 is insufficient |

### Recommendation

```text
Flan-T5 Large + LoRA
```

This provides a good balance between:

- Educational feedback quality
- Training cost
- Inference latency
- Deployment simplicity
- Fine-tuning feasibility

---

## 19. LoRA Training Strategy

### Recommended Configuration

```yaml
base_model: flan-t5-large
fine_tuning_method: LoRA
rank: 16
alpha: 32
dropout: 0.05
learning_rate: 2e-5
batch_size: 8
epochs: 3
train_split: 80
validation_split: 10
test_split: 10
```

### Training Steps

```text
1. Build concept taxonomy.
2. Build knowledge base.
3. Generate instruction dataset.
4. Split train/validation/test.
5. Train LoRA adapter.
6. Track experiments using MLflow.
7. Evaluate on unseen test data.
8. Run faculty review.
9. Register accepted model version.
10. Deploy inference service.
```

---

## 20. Evaluation Metrics

### OCR Metrics

| Metric | Target |
|---|---|
| OCR Confidence | > 90% average for accepted uploads |
| Character Error Rate | Lower is better |
| Word Error Rate | Lower is better |
| OCR Failure Rate | < 5% |

### Model Metrics

| Metric | Target |
|---|---|
| Concept Coverage Accuracy | > 85% |
| Missing Concept Precision | > 80% |
| Missing Concept Recall | > 80% |
| Hallucination Rate | < 5% |
| JSON Validity Rate | > 98% |
| Faculty Feedback Rating | > 4/5 |

### Recommendation Metrics

| Metric | Meaning |
|---|---|
| CTR | Did student open recommended resource? |
| Completion Rate | Did student complete resource/quiz? |
| Post-Resource Quiz Improvement | Did learning improve after recommendation? |
| Faculty Override Rate | Did faculty reject/change recommendation? |
| Recommendation Coverage | Do all concepts have resources? |

---

## 21. Recommendation Engine

The recommendation engine should be hybrid, not LLM-only.

```text
Missing Concepts
        |
        v
Knowledge Graph Lookup
        |
        v
Resource Ranking
        |
        v
Recommendation List
```

### Ranking Formula

```text
resource_score =
0.40 × concept_match_score
+ 0.25 × difficulty_match_score
+ 0.20 × historical_success_score
+ 0.10 × faculty_priority_score
+ 0.05 × freshness_score
```

### Recommendation Decision Rules

| Signal | Action |
|---|---|
| Low CTR | Improve titles, previews, and ranking relevance. |
| Low completion rate | Recommend shorter or easier resources first. |
| Low quiz improvement | Faculty should review resource mapping. |
| High faculty override rate | Fix knowledge graph and resource tags. |
| Low recommendation coverage | Collect more resources for missing concepts. |

---

## 22. Monitoring Architecture

```text
FastAPI AI Service
    |
    | /metrics
    v
Prometheus
    |
    v
Grafana Dashboards

Training Scripts
    |
    v
MLflow Tracking

AI Prediction Events
    |
    v
PostgreSQL Analytics Tables

Batch Evaluation Jobs
    |
    v
AI Quality Reports
```

### Dashboard 1: AI Service Health

Track:

- Requests per minute
- Error rate
- P50/P95/P99 latency
- OCR latency
- Model inference latency
- Queue depth
- CPU/GPU usage
- Timeout count

### Dashboard 2: OCR Quality

Track:

- OCR confidence trend
- CER
- WER
- OCR failure rate
- Low-confidence upload rate
- Reupload rate

### Dashboard 3: Model Quality

Track:

- Concept coverage accuracy
- Missing concept precision
- Missing concept recall
- Hallucination rate
- JSON validity rate
- Faculty rating
- Student helpfulness rating

### Dashboard 4: Recommendation Quality

Track:

- Recommendation CTR
- Completion rate
- Quiz improvement
- Faculty override rate
- Recommendation coverage by topic

### Dashboard 5: Faculty Learning Analytics

Track:

- Weakest topics
- Concept mastery heatmap
- Topic improvement over time
- Resource usage by topic
- AI feedback volume by topic

---

## 23. Example Prometheus Metrics

```python
ai_requests_total
ai_request_latency_seconds
ocr_confidence_score
ocr_processing_time_seconds
model_inference_latency_seconds
hallucination_rate
json_validity_rate
recommendation_ctr
post_resource_quiz_improvement
```

---

## 24. MLflow Tracking

Track every training run with:

```python
mlflow.log_param("base_model", "flan-t5-large")
mlflow.log_param("lora_rank", 16)
mlflow.log_param("lora_alpha", 32)
mlflow.log_param("learning_rate", 2e-5)
mlflow.log_param("epochs", 3)

mlflow.log_metric("train_loss", train_loss)
mlflow.log_metric("val_loss", val_loss)
mlflow.log_metric("concept_coverage_accuracy", coverage_acc)
mlflow.log_metric("missing_concept_precision", missing_precision)
mlflow.log_metric("missing_concept_recall", missing_recall)
mlflow.log_metric("hallucination_rate", hallucination_rate)
mlflow.log_metric("json_validity_rate", json_validity_rate)
```

---

## 25. Drift Detection

Monitor these drift types:

| Drift Type | What It Means | Action |
|---|---|---|
| OCR Drift | OCR confidence decreases over time | Improve preprocessing or capture guidance. |
| Topic Drift | Some topics dominate recent requests | Rebalance dataset or teaching resources. |
| Concept Drift | Student answers change style or syllabus changes | Update taxonomy and retrain. |
| Recommendation Drift | Previously useful resources stop helping | Re-rank or replace resources. |
| Feedback Drift | Faculty ratings drop | Fine-tune feedback examples. |

---

## 26. AI Metric Tradeoff Framework

Never optimize one metric alone. Optimize the portfolio.

### Priority Order

```text
Safety
  ↓
Accuracy
  ↓
Educational Value
  ↓
Latency
  ↓
Cost
```

### Tradeoff: Accuracy vs Hallucination

If Model A has slightly higher accuracy but much higher hallucination, choose Model B.

```text
Educational systems require trustworthiness more than marginal accuracy gain.
```

### Tradeoff: Precision vs Recall

- High precision avoids false missing-concept claims.
- High recall catches more learning gaps.

Recommended MVP balance:

```text
Precision: 80–85%
Recall: 80–85%
```

### Tradeoff: OCR Accuracy vs Speed

If OCR is poor, downstream feedback becomes poor. Prefer better OCR unless latency becomes unacceptable.

### Tradeoff: Latency vs Quality

```text
If accuracy gain is less than 2% and latency doubles, do not use the larger model.
```

### Tradeoff: Cost vs Quality

Start with Flan-T5 Large + LoRA. Move to larger models only if evaluation metrics show meaningful educational improvement.

### Tradeoff: Recommendation Precision vs Diversity

Use mostly precision with some controlled diversity:

```text
70% relevance / precision
30% diversity / exploration
```

---

## 27. Release Gate

Release a model only if:

```text
Concept Coverage Accuracy >= 85%
Missing Concept Precision >= 80%
Missing Concept Recall >= 80%
Hallucination Rate <= 5%
JSON Validity Rate >= 98%
Faculty Feedback Rating >= 4/5
OCR Confidence >= 90% average for accepted uploads
P95 Latency <= 5 seconds for synchronous feedback
```

If a release gate fails, block deployment and improve the relevant part of the pipeline.

---

## 28. MLOps Pipeline

```text
Data Collection
        |
        v
Preprocessing
        |
        v
Knowledge Base
        |
        v
Dataset Generator
        |
        v
Train / Validation / Test Split
        |
        v
LoRA Training
        |
        v
MLflow Tracking
        |
        v
Evaluation and Faculty Review
        |
        v
Model Registry
        |
        v
Inference API
        |
        v
Monitoring Dashboards
        |
        v
Feedback Loop and Retraining
```

---

## 29. Security and Privacy Principles

The system should not collect:

- Continuous location
- Camera recordings
- Audio recordings
- Biometrics
- Face recognition
- Background tracking

The system may collect:

- Attendance event timestamp
- Session ID
- QR validation status
- Device hash
- Optional proximity signal during check-in
- Quiz participation
- Resource access events
- AI submission metadata

### AI Privacy

- Anonymize student answer data.
- Do not train on identifiable data without consent.
- Store only required uploads.
- Allow deletion under retention policy.
- Keep final grading under faculty control.

---

## 30. Final Engineering Recommendation

Build AttendIQ COA in phases:

### Phase 1: Attendance + Engagement MVP

- QR-based attendance
- Session management
- Micro-quizzes
- Reward tiers
- Resource unlocking

### Phase 2: AI Feedback Assistant

- OCR pipeline
- Concept extraction
- Knowledge graph
- Flan-T5 LoRA feedback model
- Recommendation engine

### Phase 3: Monitoring + Quality System

- Prometheus metrics
- Grafana dashboards
- MLflow tracking
- Batch quality evaluation
- Faculty review loop

### Phase 4: Adaptive Learning Platform

- Personalized revision plans
- Weak-topic prediction
- Multi-subject support
- Institution-wide learning analytics

Final guiding principle:

```text
Start simple, prove classroom value, measure everything, and only then scale AI complexity.
```

---

## 31. Final Summary

AttendIQ COA is not just an attendance product. It is a learning intelligence platform that connects classroom presence, participation, resources, feedback, and analytics.

The strongest design decision is to keep the AI assistant grounded in a COA knowledge base and concept taxonomy. This reduces hallucination, improves recommendation quality, and gives faculty a transparent way to validate outputs.

The best AI engineering strategy is:

```text
Collect approved resources
→ Build concept taxonomy
→ Build knowledge graph
→ Generate structured datasets
→ Fine-tune Flan-T5 Large with LoRA
→ Evaluate with strict metrics
→ Deploy with monitoring dashboards
→ Improve continuously using feedback
```

This creates a strong, explainable, privacy-conscious, and scalable AI learning assistant for Computer Organization and Architecture.
