# Security Scanners: Data Protection

**Phase:** Week 151-153
**Priority:** HIGH
**Target:** Classic ASP, VBScript, Database

---

## Overview

Data protection vulnerabilities zijn cruciaal voor healthcare systemen zoals FysioOne waar patiëntgegevens worden verwerkt (AVG/GDPR compliance).

---

## CWE-311: Missing Encryption Detector

### Doel
Detecteer gevoelige data die onversleuteld wordt opgeslagen of verzonden.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Password in plain text
Session("password") = Request("password")
conn.Execute "INSERT INTO Users (password) VALUES ('" & password & "')"

' VULNERABLE: Sensitive data in cookies without encryption
Response.Cookies("ssn") = patientSSN

' SAFE: Hashed password
hashedPwd = HashPassword(Request("password"))
conn.Execute "INSERT INTO Users (password) VALUES ('" & hashedPwd & "')"
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| CRYPT-001 | Password stored in Session/Cookie plain | CRITICAL |
| CRYPT-002 | BSN/SSN zonder encryption | CRITICAL |
| CRYPT-003 | Credit card numbers plain text | CRITICAL |
| CRYPT-004 | Medical data zonder encryption | HIGH |

### Sensitive Data Patterns

```python
SENSITIVE_DATA_PATTERNS = [
    r'password',
    r'wachtwoord',
    r'bsn',
    r'sofi',
    r'creditcard',
    r'iban',
    r'pin',
    r'secret',
    r'token',
    r'apikey',
]
```

---

## CWE-327: Weak Cryptography Detector

### Doel
Detecteer gebruik van verouderde of onveilige cryptografische algoritmes.

### Patterns te Detecteren

```vbscript
' VULNERABLE: MD5 for password hashing
hash = MD5(password)

' VULNERABLE: DES encryption
Set cipher = Server.CreateObject("CAPICOM.EncryptedData")
cipher.Algorithm.Name = CAPICOM_ENCRYPTION_ALGORITHM_DES

' SAFE: SHA-256 or bcrypt
hash = SHA256(password & salt)
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| WEAK-001 | MD5 voor passwords | HIGH |
| WEAK-002 | SHA1 voor passwords | MEDIUM |
| WEAK-003 | DES/3DES encryption | HIGH |
| WEAK-004 | RC4 encryption | HIGH |
| WEAK-005 | Hardcoded encryption keys | CRITICAL |

---

## CWE-798: Hardcoded Credentials Detector

### Doel
Detecteer hardcoded wachtwoorden, API keys, en andere credentials.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Hardcoded database credentials
conn.Open "Provider=SQLOLEDB;Data Source=server;User ID=sa;Password=P@ssw0rd123"

' VULNERABLE: Hardcoded API key
apiKey = "sk_live_abc123xyz789"

' VULNERABLE: Hardcoded encryption key
encryptionKey = "MySecretKey123"

' SAFE: External configuration
conn.Open Application("ConnectionString")
apiKey = Application("APIKey")
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| CRED-001 | `Password=` in connection string | CRITICAL |
| CRED-002 | `pwd=` of `p=` in connection string | CRITICAL |
| CRED-003 | API key patterns (sk_, pk_, api_) | HIGH |
| CRED-004 | `secret`, `key`, `token` assignments | MEDIUM |

### Entropy-based Detection

```python
def detect_high_entropy_strings(content: str) -> List[Finding]:
    """Detect strings with high entropy (likely secrets)"""
    pattern = r'["\'][A-Za-z0-9+/=]{20,}["\']'
    for match in re.finditer(pattern, content):
        entropy = calculate_entropy(match.group())
        if entropy > 4.5:  # High entropy threshold
            yield Finding(
                cwe="CWE-798",
                message=f"Possible hardcoded secret (entropy: {entropy:.2f})"
            )
```

---

## CWE-209: Error Message Exposure Detector

### Doel
Detecteer foutmeldingen die gevoelige informatie lekken.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Full error details exposed
On Error Resume Next
conn.Execute sql
If Err.Number <> 0 Then
    Response.Write "Error: " & Err.Description & "<br>"
    Response.Write "SQL: " & sql
End If

' SAFE: Generic error message
On Error Resume Next
conn.Execute sql
If Err.Number <> 0 Then
    Response.Write "Er is een fout opgetreden. Probeer het later opnieuw."
    LogError Err.Description, sql  ' Log details server-side
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| ERR-001 | `Response.Write Err.Description` | HIGH |
| ERR-002 | SQL query in error output | CRITICAL |
| ERR-003 | Stack trace in output | HIGH |
| ERR-004 | Connection string in error | CRITICAL |

---

## Healthcare-Specific Rules (AVG/GDPR)

### Patient Data Protection

```python
class HealthcareDataProtectionDetector(BaseSecurityScanner):
    """GDPR/AVG compliance checks for healthcare data"""

    PATIENT_DATA_FIELDS = [
        'bsn', 'geboortedatum', 'diagnose', 'behandeling',
        'medicatie', 'allergien', 'verzekering'
    ]

    def check_data_minimization(self):
        """Check if only necessary data is collected"""

    def check_consent_tracking(self):
        """Verify consent is recorded for data processing"""

    def check_data_retention(self):
        """Check for data retention policy compliance"""
```

---

## Implementation

```python
# backend/app/scanners/security/data_protection.py
from .base import BaseSecurityScanner

class MissingEncryptionDetector(BaseSecurityScanner):
    """CWE-311: Missing Encryption of Sensitive Data"""
    cwe_id = "CWE-311"

class WeakCryptoDetector(BaseSecurityScanner):
    """CWE-327: Use of a Broken or Risky Cryptographic Algorithm"""
    cwe_id = "CWE-327"

class HardcodedCredentialsDetector(BaseSecurityScanner):
    """CWE-798: Use of Hard-coded Credentials"""
    cwe_id = "CWE-798"

class ErrorMessageExposureDetector(BaseSecurityScanner):
    """CWE-209: Information Exposure Through an Error Message"""
    cwe_id = "CWE-209"
```

---

## Effort Estimate

| Task | Days |
|------|------|
| MissingEncryptionDetector | 2 |
| WeakCryptoDetector | 2 |
| HardcodedCredentialsDetector | 2 |
| ErrorMessageExposureDetector | 1 |
| Healthcare-specific rules | 2 |
| Integration + Tests | 2 |
| **Total** | **11 days** |

---

*Spec Version: 1.0*
*Target: Week 151-153*
