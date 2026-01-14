# Security Scanners: File & Resource Security

**Phase:** Week 154-156
**Priority:** HIGH
**Target:** Classic ASP, File System, URLs

---

## Overview

File en resource security vulnerabilities zijn relevant voor Classic ASP vanwege de directe file system toegang via FSO en de dynamische URL handling.

---

## CWE-434: Unrestricted File Upload Detector

### Doel
Detecteer file upload functionaliteit zonder adequate validatie.

### Patterns te Detecteren

```vbscript
' VULNERABLE: No file type validation
Set upload = Server.CreateObject("Persits.Upload")
upload.Save Server.MapPath("/uploads/")

' VULNERABLE: Only client-side validation
If objFile.ContentType = "image/jpeg" Then
    objFile.SaveAs Server.MapPath("/uploads/" & objFile.FileName)
End If

' SAFE: Server-side validation with whitelist
allowedTypes = Array("jpg", "jpeg", "png", "gif")
ext = LCase(Right(fileName, 4))
If InArray(ext, allowedTypes) And ValidateMagicBytes(fileContent) Then
    objFile.SaveAs Server.MapPath("/uploads/" & SafeFileName(fileName))
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| UPLOAD-001 | `.Save` zonder extension check | CRITICAL |
| UPLOAD-002 | `.SaveAs` met originele filename | HIGH |
| UPLOAD-003 | Alleen ContentType validatie | HIGH |
| UPLOAD-004 | Upload naar web-accessible folder | CRITICAL |

### Dangerous Extensions

```python
DANGEROUS_EXTENSIONS = [
    '.asp', '.aspx', '.asa', '.asax', '.ascx',
    '.ashx', '.asmx', '.cer', '.cdx', '.config',
    '.exe', '.dll', '.bat', '.cmd', '.com',
    '.hta', '.htaccess', '.htpasswd', '.ini',
    '.php', '.php3', '.php4', '.php5', '.phtml',
    '.pl', '.cgi', '.jsp', '.jspx', '.war',
]
```

---

## CWE-732: Permission Assignment Detector

### Doel
Detecteer incorrect ingestelde bestandspermissies.

### Patterns te Detecteren

```vbscript
' VULNERABLE: World-writable files
Set fso = CreateObject("Scripting.FileSystemObject")
Set file = fso.CreateTextFile(Server.MapPath("/public/data.txt"))

' VULNERABLE: Sensitive files in web root
configPath = Server.MapPath("/config.ini")

' SAFE: Outside web root
configPath = Server.MapPath("../private/config.ini")
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| PERM-001 | Config files in web root | HIGH |
| PERM-002 | Log files in public folder | MEDIUM |
| PERM-003 | Database files in web root | CRITICAL |
| PERM-004 | Backup files accessible | HIGH |

---

## CWE-601: Open Redirect Detector

### Doel
Detecteer redirects naar user-controlled URLs.

### Patterns te Detecteren

```vbscript
' VULNERABLE: Direct redirect to user input
Response.Redirect Request("returnUrl")
Response.Redirect Request.QueryString("next")

' VULNERABLE: Partial validation
If Left(redirectUrl, 1) = "/" Then
    Response.Redirect redirectUrl  ' Still vulnerable to //evil.com
End If

' SAFE: Whitelist validation
allowedUrls = Array("/home.asp", "/profile.asp", "/dashboard.asp")
If InArray(Request("returnUrl"), allowedUrls) Then
    Response.Redirect Request("returnUrl")
End If
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| REDIR-001 | `Response.Redirect Request(` | HIGH |
| REDIR-002 | `Response.Redirect` met variabele | MEDIUM |
| REDIR-003 | Partial URL validation | HIGH |

---

## CWE-494: Code Download Integrity Detector

### Doel
Detecteer download van externe code zonder integriteitscontrole.

### Patterns te Detecteren

```vbscript
' VULNERABLE: External script without integrity check
<script src="http://external.com/jquery.js"></script>

' VULNERABLE: Dynamic include from external source
Set xmlhttp = CreateObject("MSXML2.XMLHTTP")
xmlhttp.Open "GET", externalUrl, False
xmlhttp.Send
Execute xmlhttp.responseText

' SAFE: Subresource integrity
<script src="https://cdn.com/jquery.js"
        integrity="sha384-abc123..."
        crossorigin="anonymous"></script>
```

### Detection Rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| INTEG-001 | External script zonder SRI | MEDIUM |
| INTEG-002 | Dynamic code execution from URL | CRITICAL |
| INTEG-003 | HTTP (non-HTTPS) external resources | HIGH |

---

## Implementation

```python
# backend/app/scanners/security/resources.py

class FileUploadDetector(BaseSecurityScanner):
    """CWE-434: Unrestricted Upload of File with Dangerous Type"""

    UPLOAD_COMPONENTS = [
        'Persits.Upload',
        'ASPUpload',
        'ABCUpload',
        'SA-FileUp',
    ]

    async def scan(self) -> List[Finding]:
        findings = []
        for file in self.asp_files:
            if self._has_upload_component(file):
                if not self._has_extension_check(file):
                    findings.append(self._create_critical_finding(file))
        return findings


class PermissionDetector(BaseSecurityScanner):
    """CWE-732: Incorrect Permission Assignment for Critical Resource"""

    SENSITIVE_PATTERNS = [
        r'\.ini$', r'\.config$', r'\.bak$', r'\.sql$',
        r'web\.config', r'global\.asa', r'\.mdb$',
    ]


class OpenRedirectDetector(BaseSecurityScanner):
    """CWE-601: URL Redirection to Untrusted Site"""

    REDIRECT_PATTERNS = [
        r'Response\.Redirect\s+Request\s*\(',
        r'Response\.Redirect\s+\w+(?:Url|URL|Path)',
    ]


class CodeIntegrityDetector(BaseSecurityScanner):
    """CWE-494: Download of Code Without Integrity Check"""

    EXTERNAL_SCRIPT_PATTERN = r'<script[^>]+src=["\']https?://'
```

---

## FysioOne Specific Checks

### Upload Locations

```python
FYSIOONE_UPLOAD_PATHS = [
    '/bijlagen/',
    '/documenten/',
    '/uploads/',
    '/fotos/',
]

def check_upload_security(project_path):
    """Check FysioOne upload folders for security issues"""
    for upload_path in FYSIOONE_UPLOAD_PATHS:
        check_web_config_exists(upload_path)
        check_execution_disabled(upload_path)
        check_mime_type_restrictions(upload_path)
```

---

## Effort Estimate

| Task | Days |
|------|------|
| FileUploadDetector | 3 |
| PermissionDetector | 2 |
| OpenRedirectDetector | 1 |
| CodeIntegrityDetector | 1 |
| FysioOne-specific checks | 1 |
| Integration + Tests | 2 |
| **Total** | **10 days** |

---

*Spec Version: 1.0*
*Target: Week 154-156*
