# BMAD Green-Paper Template

**Version**: 1.0
**Purpose**: Greenfield project definition through 6 strategic questions
**Target**: NEW_FEATURE workflow - Constitution generation
**Agent**: Peter (Product Owner) with deepseek-r1:latest

---

## Overview

This template guides the BMAD (Business Model Analysis & Design) green-paper session for greenfield projects. The session uses **6 carefully crafted questions** to extract the essential project information needed to generate a comprehensive **Project Constitution**.

**Green-Paper** = Greenfield project (starting from scratch)
**Brown-Paper** = Brownfield project (modifying existing system) - Different template

---

## The 6 Strategic Questions

### Question 1: Problem Statement (REQUIRED)
**Question**: "What problem does this project solve?"

**Purpose**: Establish clear problem definition and business value

**Guidance for User**:
- Describe the current pain point or opportunity
- Explain why this problem is worth solving
- Quantify the impact if possible (costs, time, user frustration)
- Keep focused on ONE core problem (not a list of many problems)

**Examples**:
- ✅ "Software teams waste 40% of sprint planning time manually breaking down requirements into tasks, leading to inconsistent granularity and missed edge cases."
- ✅ "Freelancers struggle to track billable hours across multiple clients, resulting in 15-20% revenue leakage due to untracked time."
- ❌ "We need a better project management tool" (too vague)
- ❌ "Solve collaboration, time tracking, reporting, and automation" (too many problems)

**Constraints**:
- Type: Text
- Max Length: 500 characters
- Required: YES
- Validation: Must contain at least 50 characters

---

### Question 2: Users & Stakeholders (REQUIRED)
**Question**: "Who are the primary users/stakeholders?"

**Purpose**: Identify target audience and their roles

**Guidance for User**:
- List the PRIMARY user groups (2-4 max)
- For each group, briefly describe their role and what they need
- Distinguish between primary users (daily usage) and stakeholders (decision makers)
- Prioritize: Which user group is most important?

**Examples**:
- ✅ "Primary: Software developers (task execution), Secondary: Project managers (oversight), Stakeholders: CTOs (ROI metrics)"
- ✅ "Solo freelancers billing <10 clients, focusing on designers and consultants who need simple time tracking without complex invoicing"
- ❌ "Everyone" (not specific enough)
- ❌ "Users" (who specifically?)

**Constraints**:
- Type: Text
- Max Length: 300 characters
- Required: YES
- Validation: Must mention at least one specific user role

---

### Question 3: Core Functionalities (REQUIRED)
**Question**: "What are the core functionalities?"

**Purpose**: Define MUST-HAVE features (not nice-to-haves)

**Guidance for User**:
- List 3-7 CORE functionalities only
- Focus on what makes this project VIABLE (not perfect)
- Use active verbs: Create, Track, Generate, Analyze, etc.
- Avoid implementation details (no "using React" or "with PostgreSQL")
- Use MoSCoW: Must-have, Should-have, Could-have, Won't-have (focus on Must-have)

**Examples**:
- ✅ "1) Create and organize tasks in markdown format, 2) AI-powered task breakdown from high-level descriptions, 3) Automated workflow routing based on work type (bug, feature, maintenance), 4) Quality gates validation before deployment, 5) 100% local AI execution for privacy"
- ✅ "1) Start/stop time tracking with one click, 2) Categorize time by project and task, 3) Generate weekly invoice summaries, 4) Export to CSV for accounting software"
- ❌ "A really good user interface" (not specific)
- ❌ "Everything that Jira does but better" (not defined)

**Constraints**:
- Type: Multiline text
- Max Length: 1000 characters
- Required: YES
- Validation: Must contain at least 3 distinct functionalities

---

### Question 4: Success Criteria (REQUIRED)
**Question**: "What are the success criteria?"

**Purpose**: Define measurable outcomes to validate project success

**Guidance for User**:
- Specify 3-5 MEASURABLE criteria
- Use SMART format: Specific, Measurable, Achievable, Relevant, Time-bound
- Mix quantitative (numbers) and qualitative (feedback) measures
- Focus on OUTCOMES not outputs (not "deploy 5 features" but "reduce task creation time by 50%")

**Examples**:
- ✅ "1) 100 active users within 3 months, 2) 95% agent workflow success rate, 3) <2 second API response time, 4) Complete BMAD session in <30 minutes, 5) Zero user data sent to external services"
- ✅ "1) Freelancers track 90%+ of billable hours (vs 70% baseline), 2) Invoice generation takes <5 minutes (vs 60 min baseline), 3) 4.5+ star rating in user feedback, 4) 50 paying customers by month 6"
- ❌ "Users will be happy" (not measurable)
- ❌ "Build 20 features" (output, not outcome)

**Constraints**:
- Type: Multiline text
- Max Length: 500 characters
- Required: YES
- Validation: Must contain at least 2 criteria with numbers/metrics

---

### Question 5: Technical Constraints (OPTIONAL)
**Question**: "What are the technical constraints?"

**Purpose**: Identify technical requirements, limitations, or non-negotiables

**Guidance for User**:
- List hard technical constraints (requirements, not preferences)
- Examples: Privacy requirements, platform compatibility, performance needs, compliance
- Avoid over-constraining (don't specify implementation if flexibility is okay)
- Explain WHY each constraint exists (business reason)

**Examples**:
- ✅ "1) 100% local AI execution (GDPR privacy requirement - no cloud APIs), 2) Works offline (field workers have spotty connectivity), 3) Supports PostgreSQL only (enterprise IT standard), 4) Mobile-first responsive design (80% users on mobile)"
- ✅ "1) Must integrate with QuickBooks API (existing accounting system), 2) SOC 2 compliant data handling (client requirement), 3) <1MB bundle size (targeting emerging markets with slow connections)"
- ✅ "None - we're flexible on technical implementation" (valid answer!)
- ❌ "Must use React because I like React" (preference, not constraint)

**Constraints**:
- Type: Multiline text
- Max Length: 500 characters
- Required: NO (optional)
- Validation: None (can be skipped)

---

### Question 6: Expected Timeline (OPTIONAL)
**Question**: "What is the expected timeline?"

**Purpose**: Set realistic timeframe expectations

**Guidance for User**:
- Provide rough timeframe (weeks or months, not exact dates)
- Consider: MVP timeline vs Full project timeline
- Be realistic about team size and availability
- Mention any hard deadlines if they exist

**Examples**:
- ✅ "40 weeks total (MVP in 12 weeks, full release in 40 weeks), 2-week sprints, 1 full-time developer + part-time support"
- ✅ "Need MVP in 8 weeks for investor demo, full product in 6 months for conference launch"
- ✅ "Flexible timeline - prioritize quality over speed" (valid answer!)
- ❌ "As fast as possible" (not helpful)

**Constraints**:
- Type: Text
- Max Length: 200 characters
- Required: NO (optional)
- Validation: None (can be skipped)

---

## Peter's Constitution Generation Prompt

**Context**: Peter receives all 6 answered questions and must generate a comprehensive Project Constitution.

### Prompt Template for Peter

```markdown
You are Peter, the Product Owner agent using deepseek-r1:latest model.

You have received a completed BMAD Green-Paper session for a new greenfield project.
Your task is to analyze these 6 answers and generate a comprehensive PROJECT CONSTITUTION.

## Input: BMAD Answers

**Q1 - Problem Statement**: {{answer_1}}
**Q2 - Users & Stakeholders**: {{answer_2}}
**Q3 - Core Functionalities**: {{answer_3}}
**Q4 - Success Criteria**: {{answer_4}}
**Q5 - Technical Constraints**: {{answer_5 | default: "None specified"}}
**Q6 - Expected Timeline**: {{answer_6 | default: "Flexible"}}

## Your Task

Generate a PROJECT CONSTITUTION with the following structure:

### 1. Problem Statement (150-250 words)
- Expand on Q1 answer
- Add context about WHY this problem matters
- Quantify impact if possible
- Identify root causes

### 2. Stakeholders Analysis (100-200 words)
- Parse Q2 answer into structured stakeholder list
- For EACH stakeholder group:
  * Role/Title
  * Primary needs
  * Priority level (Primary/Secondary/Tertiary)
  * Success definition from their perspective

### 3. Core Functionalities Breakdown (200-400 words)
- Parse Q3 answer into structured functionality list
- For EACH functionality:
  * Name (concise, 2-4 words)
  * Description (what it does)
  * Priority (Must-have / Should-have / Could-have)
  * Related stakeholder (who needs this most)
- Identify dependencies between functionalities

### 4. Success Criteria (150-250 words)
- Parse Q4 answer into structured criteria list
- For EACH criterion:
  * Metric name
  * Target value (with number)
  * Measurement method (how to track)
  * Timeframe (when to measure)
- Ensure SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)

### 5. Technical Constraints (100-150 words)
- Parse Q5 answer (or note "None specified")
- For EACH constraint:
  * Constraint description
  * Business reason (why it exists)
  * Impact on implementation (high/medium/low)

### 6. Timeline & Milestones (150-200 words)
- Parse Q6 answer (or propose reasonable timeline based on scope)
- Break into phases:
  * Discovery & Planning (weeks)
  * MVP Development (weeks)
  * Beta Testing (weeks)
  * Full Release (weeks)
- Define 3-5 major milestones with deliverables
- Calculate total duration in weeks

### 7. Risks & Assumptions (100-150 words)
- Identify 3-5 key risks based on the answers
- State assumptions made during constitution creation
- Suggest mitigation strategies

## Output Requirements

- Total word count: 1000-1500 words
- Format: Structured JSON matching Constitution data model
- Tone: Professional, clear, actionable
- Avoid: Jargon, vague statements, implementation details

## Validation Checklist

Before returning the constitution, verify:
- [ ] All 7 sections completed
- [ ] All stakeholders from Q2 included
- [ ] All functionalities from Q3 categorized by priority
- [ ] All success criteria from Q4 are measurable
- [ ] Timeline is realistic given scope
- [ ] No contradictions between sections

Generate the PROJECT CONSTITUTION now.
```

---

## Constitution Template Structure

```json
{
  "constitution_id": "uuid",
  "project_id": "uuid",
  "version": 1,
  "status": "draft",
  "content": {
    "problem_statement": "Detailed problem statement with context...",
    "stakeholders": [
      {
        "role": "Software Developer",
        "description": "Daily users who execute tasks...",
        "priority": "primary",
        "needs": ["Fast task creation", "Clear priorities"],
        "success_definition": "Spend <10% of time on task management"
      }
    ],
    "core_functionalities": [
      {
        "name": "AI Task Breakdown",
        "description": "Automatically break high-level requirements into granular tasks",
        "priority": "must_have",
        "stakeholder": "Software Developer",
        "dependencies": ["Task Management"]
      }
    ],
    "success_criteria": [
      {
        "metric": "User Adoption",
        "target": "100 active users",
        "measurement": "Analytics dashboard - weekly active users",
        "timeframe": "3 months post-launch"
      }
    ],
    "technical_constraints": [
      {
        "constraint": "100% local AI execution",
        "reason": "GDPR compliance and user privacy",
        "impact": "high"
      }
    ],
    "timeline": {
      "start_date": "2025-11-18",
      "phases": [
        {
          "name": "Discovery & Planning",
          "duration_weeks": 2,
          "deliverables": ["Project charter", "Technical architecture"]
        },
        {
          "name": "MVP Development",
          "duration_weeks": 12,
          "deliverables": ["Core features", "Basic UI", "Local AI integration"]
        }
      ],
      "total_duration_weeks": 40,
      "milestones": [
        {
          "name": "Week 10: BMAD Green-Paper Workflow",
          "target_date": "2025-12-23",
          "deliverables": ["6-question interface", "Constitution pipeline"]
        }
      ]
    },
    "risks_and_assumptions": {
      "risks": [
        {
          "risk": "Local AI models may not match cloud API quality",
          "likelihood": "medium",
          "impact": "medium",
          "mitigation": "Extensive testing, model selection, fallback options"
        }
      ],
      "assumptions": [
        "Users have hardware capable of running Ollama models",
        "PostgreSQL database available in target environments"
      ]
    }
  },
  "metadata": {
    "generated_by": "Peter",
    "generation_method": "BMAD_green_paper",
    "llm_model": "deepseek-r1:latest",
    "generated_at": "2025-11-18T10:15:00Z",
    "word_count": 1250,
    "bmad_session_id": "uuid"
  }
}
```

---

## User Review Guidance

After Peter generates the constitution, the user reviews it using this guidance:

### Approval Checklist
- [ ] Problem statement accurately reflects the actual problem
- [ ] All key stakeholders are identified
- [ ] Core functionalities cover the MVP scope
- [ ] Success criteria are realistic and measurable
- [ ] Technical constraints are correct and complete
- [ ] Timeline is achievable with available resources
- [ ] No major risks overlooked

### Common Rejection Reasons
1. **Timeline too aggressive**: "40 weeks is unrealistic for our team size"
2. **Missing stakeholder**: "You forgot about the compliance team"
3. **Wrong priority**: "Feature X should be must-have, not should-have"
4. **Unclear success criteria**: "How exactly do we measure 'user satisfaction'?"
5. **Missing constraint**: "We forgot to mention the API rate limit constraint"

### Feedback Format
```json
{
  "action": "reject",
  "feedback": "Timeline is too aggressive for our team size",
  "requested_changes": [
    {
      "section": "timeline",
      "field": "total_duration_weeks",
      "current_value": "40",
      "suggested_value": "52",
      "reason": "We only have 1 full-time developer, need more buffer"
    }
  ]
}
```

---

## Progressive Validation Checkpoint

After constitution approval, the workflow proceeds to Felix for Specification generation.

**Validation Question**: "The constitution has been approved. Ready to proceed to High-Level Design (HLD) specification generation?"
- YES → Trigger Felix (Feature Architect)
- NO → Pause workflow, wait for user

---

## Best Practices

### For Users Answering Questions
1. **Be specific**: Vague answers produce vague constitutions
2. **Quantify when possible**: "50% faster" > "much faster"
3. **Think MVP**: What's the MINIMUM to validate the idea?
4. **Consider constraints early**: Privacy, compliance, integrations
5. **Be realistic**: Overpromising leads to failed projects

### For Peter Generating Constitutions
1. **Stay faithful to answers**: Don't invent requirements
2. **Ask for clarification**: Better to pause than assume
3. **Identify contradictions**: Flag conflicts in answers
4. **Be realistic about timeline**: Factor in testing, deployment
5. **Consider risks**: Every project has risks - identify them

---

## Next Steps After Constitution

1. **User reviews constitution** (API endpoint: `/api/projects/{id}/constitution/{id}/review`)
2. **If approved** → Felix generates HLD Specification
3. **If rejected** → Peter regenerates with feedback (max 3 iterations)
4. **After specification approved** → Felix generates Tasks (Epics/Features/Stories)
5. **After tasks generated** → Paul creates Sprint Plan

---

**Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Ready for implementation
**Next Review**: After first pilot session
