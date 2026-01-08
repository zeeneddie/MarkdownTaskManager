---
assigned_to: eddie
created_at: '2025-11-12'
estimated_hours: 8
id: STORY-003
parent_id: FEATURE-003
priority: HIGH
sp: 5
sprint: Sprint 16
status: PLANNED
tags:
- backend
- api
title: Implement login endpoint
type: story
---

# STORY-003: Implement login endpoint

**Parent:** [FEATURE-003](../../feature.md)

## 📋 User Story

**As a** user
**I want to** login with email and password
**So that** I can access my account

## ✅ Acceptance Criteria

- [ ] API endpoint POST /api/auth/login exists
- [ ] Returns JWT access token on success
- [ ] Returns refresh token in httpOnly cookie
- [ ] Returns 401 on invalid credentials

## 🔧 Tasks

- [TASK-003](tasks/TASK-003.md) - Create login endpoint (📝 4h)

## 📊 Metrics

- **Estimated:** 5 SP (8 hours)
- **Confidence:** ±10%

---

**Last Sync:** 2025-11-12 16:00:03
