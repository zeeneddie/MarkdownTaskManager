# GDPR Compliance Checklist

## Overview
General Data Protection Regulation (EU) for personal data protection.

## Key Requirements

### 1. Lawful Basis for Processing
- [ ] Consent mechanism implemented
- [ ] Consent records maintained
- [ ] Easy consent withdrawal
- [ ] Legitimate interest documented

### 2. Data Subject Rights
- [ ] Right to access (SAR)
- [ ] Right to rectification
- [ ] Right to erasure (RTBF)
- [ ] Right to data portability
- [ ] Right to object

### 3. Data Protection Principles
- [ ] Data minimization
- [ ] Purpose limitation
- [ ] Storage limitation
- [ ] Accuracy maintenance

### 4. Security Measures
- [ ] Appropriate technical measures
- [ ] Organizational measures
- [ ] Breach notification (72 hours)
- [ ] Data protection by design

## Code Indicators

```python
INDICATORS = [
    "consent",
    "gdpr",
    "privacy",
    "data_request",
    "anonymize",
    "pseudonymize",
    "data_export",
    "delete_user_data"
]
```

## Data Subject Request Endpoints

| Right | Endpoint Pattern |
|-------|-----------------|
| Access | `GET /api/users/{id}/data` |
| Rectification | `PUT /api/users/{id}` |
| Erasure | `DELETE /api/users/{id}` |
| Portability | `GET /api/users/{id}/export` |
| Objection | `POST /api/users/{id}/opt-out` |

## Consent Management

```python
# Required consent fields
class Consent:
    user_id: str
    purpose: str
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    source: str  # Where consent was obtained
    version: str  # Terms version
```
