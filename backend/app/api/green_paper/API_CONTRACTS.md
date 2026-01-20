# Week 10 API Contracts - Green-Paper Workflow

**Version**: 1.0
**Date**: 2025-11-18
**Status**: Draft

---

## Overview

API contracts for the MarQed Green-Paper Workflow implementation. This workflow enables greenfield project creation through a 6-question MarQed session interface, following the Spec-Kit pipeline: **Constitution → Specification → Tasks**.

---

## Endpoints

### 1. Start Green-Paper Session

**POST** `/api/projects/{project_id}/green-paper/start`

Initializes a new MarQed green-paper session for a project.

#### Request

**Path Parameters**:
- `project_id` (UUID, required) - The project identifier

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {token}
```

**Body**:
```json
{
  "session_type": "green-paper",
  "metadata": {
    "initiated_by": "user_id",
    "context": "New greenfield project setup"
  }
}
```

#### Response

**Success (201 Created)**:
```json
{
  "session_id": "uuid",
  "project_id": "uuid",
  "session_type": "green-paper",
  "status": "in_progress",
  "current_question": 1,
  "total_questions": 6,
  "created_at": "2025-11-18T10:00:00Z",
  "questions": [
    {
      "question_number": 1,
      "question_text": "What problem does this project solve?",
      "question_type": "text",
      "required": true,
      "max_length": 500
    },
    {
      "question_number": 2,
      "question_text": "Who are the primary users/stakeholders?",
      "question_type": "text",
      "required": true,
      "max_length": 300
    },
    {
      "question_number": 3,
      "question_text": "What are the core functionalities?",
      "question_type": "multiline",
      "required": true,
      "max_length": 1000
    },
    {
      "question_number": 4,
      "question_text": "What are the success criteria?",
      "question_type": "multiline",
      "required": true,
      "max_length": 500
    },
    {
      "question_number": 5,
      "question_text": "What are the technical constraints?",
      "question_type": "multiline",
      "required": false,
      "max_length": 500
    },
    {
      "question_number": 6,
      "question_text": "What is the expected timeline?",
      "question_type": "text",
      "required": false,
      "max_length": 200
    }
  ]
}
```

**Error (400 Bad Request)**:
```json
{
  "error": "validation_error",
  "message": "Project must be in draft status to start green-paper session",
  "details": {
    "current_status": "active",
    "required_status": "draft"
  }
}
```

**Error (404 Not Found)**:
```json
{
  "error": "not_found",
  "message": "Project not found",
  "project_id": "uuid"
}
```

---

### 2. Submit Answer

**POST** `/api/projects/{project_id}/green-paper/{session_id}/answer`

Submits an answer to a specific MarQed question.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)
- `session_id` (UUID, required)

**Body**:
```json
{
  "question_number": 1,
  "answer": "This project solves the problem of inefficient task management by providing a markdown-based system with AI agent integration.",
  "metadata": {
    "time_spent_seconds": 120,
    "revision_count": 2
  }
}
```

#### Response

**Success (200 OK)**:
```json
{
  "session_id": "uuid",
  "question_number": 1,
  "status": "accepted",
  "next_question": 2,
  "progress": {
    "answered": 1,
    "remaining": 5,
    "percentage": 16.67
  },
  "validation": {
    "is_valid": true,
    "word_count": 23,
    "character_count": 142
  }
}
```

**Error (422 Unprocessable Entity)**:
```json
{
  "error": "validation_error",
  "message": "Answer exceeds maximum length",
  "details": {
    "max_length": 500,
    "actual_length": 623,
    "question_number": 1
  }
}
```

---

### 3. Get Session Status

**GET** `/api/projects/{project_id}/green-paper/{session_id}`

Retrieves current status of a green-paper session.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)
- `session_id` (UUID, required)

#### Response

**Success (200 OK)**:
```json
{
  "session_id": "uuid",
  "project_id": "uuid",
  "status": "in_progress",
  "current_question": 3,
  "total_questions": 6,
  "answers": [
    {
      "question_number": 1,
      "answer": "This project solves...",
      "answered_at": "2025-11-18T10:05:00Z"
    },
    {
      "question_number": 2,
      "answer": "Primary users are...",
      "answered_at": "2025-11-18T10:08:00Z"
    }
  ],
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:08:00Z"
}
```

---

### 4. Generate Constitution

**POST** `/api/projects/{project_id}/green-paper/{session_id}/generate-constitution`

Triggers AI agents to generate project constitution from MarQed answers.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)
- `session_id` (UUID, required)

**Body**:
```json
{
  "options": {
    "include_technical_details": true,
    "generate_epics": true,
    "validation_mode": "strict"
  }
}
```

#### Response

**Success (202 Accepted)**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "estimated_completion": "2025-11-18T10:20:00Z",
  "message": "Peter (Product Owner) is analyzing MarQed answers and generating constitution",
  "workflow": {
    "workflow_id": "uuid",
    "workflow_type": "NEW_FEATURE",
    "agents_assigned": ["Peter", "Felix", "Diana"]
  }
}
```

**Error (400 Bad Request)**:
```json
{
  "error": "incomplete_session",
  "message": "All 6 questions must be answered before generating constitution",
  "details": {
    "answered": 4,
    "required": 6,
    "missing_questions": [5, 6]
  }
}
```

---

### 5. Get Constitution

**GET** `/api/projects/{project_id}/constitution`

Retrieves the generated project constitution.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)

**Query Parameters**:
- `version` (integer, optional) - Specific version number (default: latest)
- `format` (string, optional) - Response format: `json` or `markdown` (default: `json`)

#### Response

**Success (200 OK)** - JSON format:
```json
{
  "constitution_id": "uuid",
  "project_id": "uuid",
  "version": 1,
  "status": "approved",
  "content": {
    "problem_statement": "Detailed problem statement...",
    "stakeholders": [
      {
        "role": "End User",
        "description": "Task managers who need...",
        "priority": "primary"
      }
    ],
    "core_functionalities": [
      {
        "name": "Task Management",
        "description": "Create, update, delete tasks...",
        "priority": "must_have"
      }
    ],
    "success_criteria": [
      {
        "metric": "User Adoption",
        "target": "100 active users in 3 months",
        "measurement": "Analytics dashboard"
      }
    ],
    "technical_constraints": [
      {
        "constraint": "100% local AI execution",
        "reason": "Privacy requirements",
        "impact": "high"
      }
    ],
    "timeline": {
      "start_date": "2025-11-18",
      "target_completion": "2026-07-30",
      "duration_weeks": 40,
      "milestones": [
        {
          "name": "Week 10: MarQed Green-Paper",
          "target_date": "2025-12-23",
          "deliverables": ["6-question interface", "Constitution pipeline"]
        }
      ]
    }
  },
  "metadata": {
    "generated_by": "Peter",
    "generation_method": "MarQed_green_paper",
    "llm_model": "deepseek-r1:latest",
    "generated_at": "2025-11-18T10:15:00Z",
    "word_count": 1250
  },
  "created_at": "2025-11-18T10:15:00Z",
  "approved_at": "2025-11-18T10:30:00Z"
}
```

**Success (200 OK)** - Markdown format:
```
Content-Type: text/markdown

# Project Constitution

## Problem Statement
[Content...]

## Stakeholders
[Content...]

[etc.]
```

---

### 6. Approve/Reject Constitution

**POST** `/api/projects/{project_id}/constitution/{constitution_id}/review`

User reviews and approves/rejects the generated constitution.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)
- `constitution_id` (UUID, required)

**Body**:
```json
{
  "action": "approve",
  "feedback": "Constitution accurately reflects our vision. Ready to proceed to specification.",
  "requested_changes": []
}
```

OR for rejection:

```json
{
  "action": "reject",
  "feedback": "Timeline is too aggressive for our team size.",
  "requested_changes": [
    {
      "section": "timeline",
      "field": "duration_weeks",
      "current_value": "40",
      "suggested_value": "52",
      "reason": "Need more time for thorough testing"
    }
  ]
}
```

#### Response

**Success (200 OK)** - Approved:
```json
{
  "constitution_id": "uuid",
  "status": "approved",
  "approved_at": "2025-11-18T10:30:00Z",
  "next_step": {
    "action": "generate_specification",
    "endpoint": "/api/projects/{project_id}/specification/generate",
    "description": "Proceed to specification generation (Felix - Feature Architect)"
  }
}
```

**Success (200 OK)** - Rejected:
```json
{
  "constitution_id": "uuid",
  "status": "revision_required",
  "revision_id": "uuid",
  "feedback_recorded": true,
  "next_step": {
    "action": "regenerate_constitution",
    "endpoint": "/api/projects/{project_id}/green-paper/{session_id}/regenerate-constitution",
    "description": "Peter will regenerate constitution with requested changes"
  }
}
```

---

### 7. Generate Specification

**POST** `/api/projects/{project_id}/specification/generate`

Generates High-Level Design (HLD) specification from approved constitution.

#### Request

**Path Parameters**:
- `project_id` (UUID, required)

**Body**:
```json
{
  "constitution_id": "uuid",
  "options": {
    "detail_level": "high",
    "include_api_contracts": true,
    "include_data_models": true,
    "include_architecture_diagrams": false
  }
}
```

#### Response

**Success (202 Accepted)**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "estimated_completion": "2025-11-18T11:00:00Z",
  "message": "Felix (Feature Architect) is generating HLD specification from constitution",
  "workflow": {
    "workflow_id": "uuid",
    "workflow_type": "NEW_FEATURE",
    "current_stage": "specification_generation",
    "agents_assigned": ["Felix", "Diana"]
  }
}
```

**Error (400 Bad Request)**:
```json
{
  "error": "constitution_not_approved",
  "message": "Constitution must be approved before generating specification",
  "details": {
    "constitution_status": "draft",
    "required_status": "approved"
  }
}
```

---

## Data Models

### GreenPaperSession

```typescript
interface GreenPaperSession {
  session_id: string;
  project_id: string;
  session_type: "green-paper";
  status: "in_progress" | "completed" | "cancelled";
  current_question: number;
  total_questions: 6;
  answers: Answer[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}
```

### Answer

```typescript
interface Answer {
  question_number: number;
  question_text: string;
  answer: string;
  answered_at: string;
  metadata?: {
    time_spent_seconds?: number;
    revision_count?: number;
  };
}
```

### Constitution

```typescript
interface Constitution {
  constitution_id: string;
  project_id: string;
  version: number;
  status: "draft" | "approved" | "revision_required" | "archived";
  content: {
    problem_statement: string;
    stakeholders: Stakeholder[];
    core_functionalities: Functionality[];
    success_criteria: Criterion[];
    technical_constraints: Constraint[];
    timeline: Timeline;
  };
  metadata: {
    generated_by: string;
    generation_method: string;
    llm_model: string;
    generated_at: string;
    word_count: number;
  };
  created_at: string;
  approved_at?: string;
}
```

### ConstitutionReview

```typescript
interface ConstitutionReview {
  action: "approve" | "reject";
  feedback: string;
  requested_changes: Change[];
}

interface Change {
  section: string;
  field: string;
  current_value: string;
  suggested_value: string;
  reason: string;
}
```

---

## Validation Rules

### Green-Paper Session

1. **Project Status**: Project must be in `draft` status to start green-paper session
2. **Single Active Session**: Only one active green-paper session per project
3. **Sequential Answers**: Questions must be answered sequentially (1 → 2 → 3 → 4 → 5 → 6)
4. **Required Questions**: Questions 1-4 are required; 5-6 are optional
5. **Answer Length**: Each answer must respect `max_length` constraint

### Constitution Generation

1. **Complete Session**: All required questions (1-4) must be answered
2. **Session Status**: Session must have status `completed`
3. **No Active Constitution**: No pending constitution generation for same project
4. **Project Active**: Project must exist and not be archived

### Constitution Approval

1. **Single Approval**: Each constitution version can only be approved once
2. **Valid Feedback**: Rejection requires feedback and at least one requested change
3. **No Specification**: Cannot approve if specification already generated

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Request validation failed |
| `not_found` | 404 | Resource not found |
| `incomplete_session` | 400 | MarQed session incomplete |
| `constitution_not_approved` | 400 | Constitution not approved |
| `duplicate_session` | 409 | Active session already exists |
| `invalid_status` | 400 | Invalid resource status |
| `unauthorized` | 401 | Authentication required |
| `forbidden` | 403 | Insufficient permissions |
| `processing_error` | 500 | Agent workflow error |
| `timeout` | 504 | Agent processing timeout |

---

## Workflow Integration

### Agent Workflow Sequence

```
User → Green-Paper Session → MarQed Answers
  ↓
Peter (Product Owner) → Generate Constitution
  ↓
User → Review & Approve
  ↓
Felix (Feature Architect) → Generate Specification (HLD)
  ↓
User → Review & Approve
  ↓
Felix → Generate Tasks (Epics/Features/Stories)
  ↓
Paul (Project Lead) → Create Sprint Plan
```

### Status Transitions

```
Green-Paper Session:
  draft → in_progress → completed → [constitution_generated]

Constitution:
  draft → [user_review] → approved | revision_required
                           ↓           ↓
                     [spec_gen]   [regenerate]

Specification:
  draft → [user_review] → approved | revision_required
                           ↓           ↓
                     [task_gen]   [regenerate]
```

---

## Rate Limits

- **Session Creation**: 5 per project per hour
- **Answer Submission**: 20 per session per minute
- **Constitution Generation**: 2 per project per hour
- **Specification Generation**: 2 per project per hour

---

## Webhooks (Future)

Optional webhook notifications for async events:

```json
{
  "event": "constitution.generated",
  "project_id": "uuid",
  "constitution_id": "uuid",
  "timestamp": "2025-11-18T10:15:00Z",
  "data": {
    "status": "ready_for_review",
    "url": "/api/projects/{project_id}/constitution"
  }
}
```

---

**Last Updated**: 2025-11-18
**Next Review**: Before implementation start
**Status**: Ready for review
