---
assigned_to: eddie
created_at: '2025-11-12'
estimated_hours: 8
id: STORY-004
parent_id: FEATURE-004
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

# STORY-004: Implement login endpoint

**Parent:** [FEATURE-004](../../feature.md)

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

- [TASK-004](tasks/TASK-004.md) - Create login endpoint (📝 4h)

## 📊 Metrics

- **Estimated:** 5 SP (8 hours)
- **Confidence:** ±10%

---

**Last Sync:** 2025-11-12 16:01:57
