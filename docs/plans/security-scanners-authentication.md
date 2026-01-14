# Security Scanners: Authentication & Authorization

**Phase:** Week 148-150
**Priority:** HIGH
**Target:** Classic ASP, VBScript

---

## Overview

Authentication en authorization vulnerabilities zijn kritiek voor multi-tenant systemen zoals FysioOne waar OmgevingId-based access control cruciaal is.

---

## CWE-306: Missing Authentication Detector

### Doel
Detecteer pagina's die kritieke functies uitvoeren zonder authenticatie check.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Admin page without auth check
<%
' NO session check here!
Set conn = Server.CreateObject("ADODB.Connection")
conn.Execute "DELETE FROM Users WHERE id = " & Request("id")
%>

' SAFE: Authentication check at top
<%
If Session("loggedIn") <> True Then
    Response.Redirect "login.asp"
    Response.End
End If
%>
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| AUTH-001 | Admin/delete/update page zonder `Session(` check | CRITICAL |
| AUTH-002 | Database write zonder authentication | CRITICAL |
| AUTH-003 | `Response.Redirect` zonder `Response.End` | HIGH |

### Classic ASP Auth Patterns

```vbscript
' Pattern 1: Session-based authentication
If Session("UserID") = "" Then Response.Redirect "login.asp"

' Pattern 2: Include file authentication
<!--#include file="checkAuth.asp"-->

' Pattern 3: Cookie-based (risky)
If Request.Cookies("auth") <> "" Then
```

---

## CWE-285: Access Control Detector

### Doel
Detecteer ontbrekende autorisatie checks (je bent ingelogd, maar mag je dit?)

### Patterns te Detecteren

```vbscript
' VULNERABLE: No role/permission check
<%
If Session("loggedIn") = True Then
    ' Missing: Is user allowed to view this record?
    Set rs = conn.Execute("SELECT * FROM PatientData WHERE id = " & Request("id"))
End If
%>

' SAFE: Authorization check
<%
If Session("loggedIn") = True Then
    ' Check if user has access to this patient
    If HasAccessToPatient(Session("UserID"), Request("patientId")) Then
        Set rs = conn.Execute("SELECT * FROM PatientData...")
    End If
End If
%>
```

### FysioOne-Specific Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| AUTHZ-001 | Patient data access zonder OmgevingId check | CRITICAL |
| AUTHZ-002 | Cross-tenant data access mogelijk | CRITICAL |
| AUTHZ-003 | Admin functions zonder role check | HIGH |

---

## CWE-352: CSRF Detector

### Doel
Detecteer forms die state-changing operations uitvoeren zonder CSRF tokens.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Form without CSRF token
<form method="POST" action="delete_user.asp">
    <input type="hidden" name="id" value="<%=userID%>">
    <input type="submit" value="Delete">
</form>

' SAFE: Form with CSRF token
<form method="POST" action="delete_user.asp">
    <input type="hidden" name="csrf_token" value="<%=Session("CSRFToken")%>">
    <input type="hidden" name="id" value="<%=userID%>">
    <input type="submit" value="Delete">
</form>
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| CSRF-001 | POST form zonder token naar write operation | HIGH |
| CSRF-002 | GET request voor state change | CRITICAL |
| CSRF-003 | Token niet gevalideerd server-side | HIGH |

---

## CWE-807: Untrusted Input in Security Decisions

### Doel
Detecteer security decisions gebaseerd op client-side input.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Trust hidden field for authorization
If Request("isAdmin") = "true" Then
    ' Grant admin access
End If

' VULNERABLE: Trust cookie for permissions
If Request.Cookies("role") = "admin" Then
    ' Grant admin access
End If

' SAFE: Server-side session check
If Session("isAdmin") = True Then
    ' Grant admin access
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| TRUST-001 | `Request("isAdmin")` of soortgelijk | CRITICAL |
| TRUST-002 | `Request.Cookies("role")` voor auth | CRITICAL |
| TRUST-003 | Hidden field voor permissions | HIGH |

---

## Implementation Architecture

```python
class AuthenticationScanner(BaseSecurityScanner):
    """Authentication and Authorization scanner suite"""

    def __init__(self, project_path: str):
        self.detectors = [
            MissingAuthenticationDetector(),
            AccessControlDetector(),
            CSRFDetector(),
            UntrustedInputDetector(),
        ]

    async def scan(self) -> SecurityScanResult:
        results = SecurityScanResult()
        for detector in self.detectors:
            findings = await detector.scan(self.project_path)
            results.add_findings(findings)
        return results
```

---

## FysioOne Integration Points

### OmgevingId-specific checks

```python
class FysioOneAuthorizationDetector(AccessControlDetector):
    """FysioOne-specific authorization checks"""

    OMGEVING_PATTERNS = [
        # Check for cross-tenant data access
        r'WHERE.*(?!OmgevingId)',  # Query without OmgevingId filter
        r'SELECT.*FROM\s+Patienten(?!.*ses_omgevingId)',
    ]
```

---

## Effort Estimate

| Task | Days |
|------|------|
| MissingAuthenticationDetector | 3 |
| AccessControlDetector | 3 |
| CSRFDetector | 2 |
| UntrustedInputDetector | 2 |
| FysioOne-specific rules | 2 |
| Integration + Tests | 2 |
| **Total** | **14 days** |

---

*Spec Version: 1.0*
*Target: Week 148-150*
