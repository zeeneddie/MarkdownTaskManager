---
id: TASK-002
type: task
parent_id: STORY-001
title: Configure API keys
status: TODO
priority: HIGH
assigned_to: eddie
estimated_hours: 1
created_at: 2025-11-12
tags:
  - config
---

# TASK-002: Configure API keys

**Parent:** [STORY-001](../story.md) - Setup Stripe SDK

## 📋 Description

Configure Stripe API keys in environment variables.

## ✅ Checklist

- [ ] Add STRIPE_SECRET_KEY to .env
- [ ] Add STRIPE_PUBLISHABLE_KEY to .env
- [ ] Update config.py to read keys
- [ ] Add validation on startup

## 💻 Implementation

```python
# backend/app/config.py
class Settings(BaseSettings):
    # ... existing settings

    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str

    @validator('STRIPE_SECRET_KEY')
    def validate_stripe_key(cls, v):
        if not v.startswith('sk_'):
            raise ValueError('Invalid Stripe secret key')
        return v
```

---

**Created:** 2025-11-12 15:55:00
