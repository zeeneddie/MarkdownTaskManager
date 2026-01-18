# CWE Implementation Evaluation Report for SAST Scanner

**Date:** 2026-01-17
**Evaluator:** Security Scanner Architecture Team
**Scope:** Evaluation of missing CWEs from CWE Top 25 (2024) and SAST-relevant lists

---

## Executive Summary

This report evaluates which missing CWEs should be added to our regex/pattern-based SAST tool. We currently cover 71 CWEs across our security scanners. This evaluation identifies **16 critical gaps** from the CWE Top 25 (2024) and **7 additional SAST-relevant CWEs** that should be considered for implementation.

### Current CWE Coverage (71 CWEs)

Our existing scanners cover:
- **Memory Safety Detector:** CWE-787, CWE-416, CWE-125, CWE-119, CWE-122, CWE-124, CWE-126, CWE-127, CWE-134, CWE-190, CWE-195, CWE-401, CWE-415, CWE-457, CWE-562, CWE-590, CWE-697, CWE-770, CWE-824
- **Concurrency Detector:** CWE-362, CWE-366, CWE-367, CWE-479, CWE-764, CWE-765, CWE-820, CWE-821, CWE-833
- **Crypto Error Detector:** CWE-208, CWE-295, CWE-296, CWE-321, CWE-326, CWE-327, CWE-328, CWE-330, CWE-798
- **Web Security Detector:** CWE-129, CWE-606, CWE-789, CWE-1236, CWE-1284, CWE-1321
- **Path Security Detector:** CWE-185, CWE-400, CWE-426, CWE-427, CWE-428, CWE-1333
- **Generic Security Scanner:** CWE-200, CWE-259, CWE-337, CWE-521, CWE-522, CWE-601, CWE-602, CWE-841
- **Secret Scanner:** CWE-798 (comprehensive patterns)

---

## Tier 1: Must Implement (Critical Priority)

These CWEs are in the CWE Top 25, have high SAST detectability, and represent critical security gaps.

### 1. CWE-79: Cross-site Scripting (XSS)

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #1 (Score: 56.92) |
| **SAST Detectability** | **High** - Regex can detect many common patterns |
| **Implementation Complexity** | **Medium** - Multiple patterns, multi-language |
| **Security Impact** | **Critical** - Most exploited web vulnerability |
| **Recommendation** | **MUST IMPLEMENT** |

**Detection Approach:**
```
Pattern Types:
1. Direct output of user input (reflected XSS)
2. innerHTML/outerHTML assignments with user data
3. document.write() with tainted data
4. Template interpolation without escaping
5. Server-side rendering without encoding
```

**Example Detection Patterns:**
```python
# JavaScript/TypeScript
r'\.innerHTML\s*=\s*(?:req\.|params\.|query\.|body\.|input)'
r'document\.write\s*\(\s*(?:req\.|params\.|input|user)'
r'\$\([^)]+\)\.html\s*\(\s*(?:req\.|data\.|input)'  # jQuery

# Python (Flask/Django)
r'return\s+.*(?:request\.args|request\.form).*(?:render_template_string|Markup)'
r'render_template_string\s*\(\s*(?:request|input|user)'

# PHP
r'echo\s+\$_(?:GET|POST|REQUEST)\s*\['
r'print\s+\$_(?:GET|POST|REQUEST)'

# Java
r'out\.(?:print|println)\s*\(\s*request\.getParameter'
r'response\.getWriter\s*\(\s*\)\.(?:print|write)\s*\(\s*(?:request|input)'
```

**False Positive Mitigation:**
- Check for escaping functions nearby: `htmlspecialchars`, `escape`, `sanitize`, `encodeHtml`
- Look for Content Security Policy headers
- Detect framework auto-escaping (React JSX, Angular bindings)

**Expected FP Rate:** 15-25% (Medium)

**Recommended Scanner:** New `InjectionDetector` or extend `WebSecurityDetector`

---

### 2. CWE-89: SQL Injection

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #3 (Score: 35.88) |
| **SAST Detectability** | **High** - String concatenation patterns detectable |
| **Implementation Complexity** | **Medium** - 15-20 patterns per language |
| **Security Impact** | **Critical** - Data breach, full DB compromise |
| **Recommendation** | **MUST IMPLEMENT** |

**Detection Approach:**
```
Pattern Types:
1. String concatenation in SQL queries
2. f-strings/template strings with SQL
3. .format() with SQL and user input
4. Raw SQL with direct variable insertion
5. ORM raw query methods with user input
```

**Example Detection Patterns:**
```python
# Python
r'(?:cursor\.execute|db\.execute|engine\.execute)\s*\(\s*(?:f["\']|["\'].*%s|["\'].*\.format\(|["\'].*\+)'
r'(?:execute|raw_sql|text)\s*\(\s*["\'].*\+.*(?:request|input|user)'

# JavaScript
r'(?:query|execute)\s*\(\s*[`"\'].*\$\{(?:req\.|params\.|body\.)'
r'(?:knex|sequelize)\.raw\s*\(\s*[`"\'].*\$\{'

# Java
r'(?:Statement|PreparedStatement).*(?:executeQuery|executeUpdate)\s*\(\s*["\'].*\+'
r'createQuery\s*\(\s*["\'].*\+.*(?:request|input|getParameter)'

# PHP
r'(?:mysql_query|mysqli_query|pg_query)\s*\(\s*["\'].*\.\s*\$_(?:GET|POST|REQUEST)'
r'\$(?:pdo|db|conn)->query\s*\(\s*["\'].*\$_(?:GET|POST)'

# C#
r'(?:SqlCommand|OleDbCommand)\s*\(\s*["\'].*\+'
r'(?:ExecuteReader|ExecuteNonQuery|ExecuteScalar).*["\'].*\+.*(?:Request|input)'
```

**False Positive Mitigation:**
- Detect parameterized queries: `?`, `:param`, `@param`, `$1`
- Look for prepared statement patterns
- Check for ORM safe methods (`.filter()`, `.where()` with params)

**Expected FP Rate:** 10-20% (Low-Medium)

**Recommended Scanner:** New `InjectionDetector`

---

### 3. CWE-78: OS Command Injection

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #7 (Score: 11.30) |
| **SAST Detectability** | **High** - Shell execution patterns detectable |
| **Implementation Complexity** | **Simple** - 10-15 patterns per language |
| **Security Impact** | **Critical** - RCE, full system compromise |
| **Recommendation** | **MUST IMPLEMENT** |

**Example Detection Patterns:**
```python
# Python
r'(?:os\.system|os\.popen|subprocess\.(?:call|run|Popen)|commands\.getoutput)\s*\(\s*(?:f["\']|["\'].*%|.*\+.*(?:request|input|user))'

# JavaScript
r'(?:exec|execSync|spawn|spawnSync)\s*\(\s*(?:`.*\$\{|["\'].*\+.*(?:req\.|input))'
r'child_process\.(?:exec|spawn)\s*\(\s*.*\+.*(?:req\.|params)'

# PHP
r'(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\(\s*["\']?.*\$_(?:GET|POST|REQUEST)'

# Java
r'Runtime\.getRuntime\s*\(\s*\)\.exec\s*\(\s*.*\+.*(?:request|input|getParameter)'

# Ruby
r'(?:system|exec|`|%x\{)\s*.*\#\{(?:params|request)'
```

**Expected FP Rate:** 10-15% (Low)

---

### 4. CWE-22: Path Traversal

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #5 (Score: 12.74) |
| **SAST Detectability** | **High** - File path + user input patterns |
| **Implementation Complexity** | **Simple** - 10-12 patterns per language |
| **Security Impact** | **High** - File disclosure, potential RCE |
| **Recommendation** | **MUST IMPLEMENT** |

**Example Detection Patterns:**
```python
# Python
r'open\s*\(\s*(?:os\.path\.join\s*\([^)]*(?:request|input|user)|f["\'][^"\']*\{.*(?:request|input))'
r'(?:send_file|send_from_directory)\s*\(\s*(?:request|input|user)'

# JavaScript
r'(?:fs\.readFile|fs\.writeFile|fs\.createReadStream)\s*\(\s*(?:path\.join\s*\([^)]*(?:req\.|params)|.*\+.*(?:req\.|params))'

# Java
r'new\s+File\s*\(\s*.*\+.*(?:request\.getParameter|input)'
r'Paths\.get\s*\(\s*.*(?:request|input|getParameter)'

# PHP
r'(?:file_get_contents|fopen|include|require)\s*\(\s*.*\$_(?:GET|POST|REQUEST)'
```

**False Positive Mitigation:**
- Check for path sanitization: `realpath`, `basename`, `Path.normalize`
- Detect allowlist checks on filenames
- Look for `..` filtering patterns

**Expected FP Rate:** 15-20% (Medium)

---

### 5. CWE-502: Deserialization of Untrusted Data

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #16 (Score: 5.07) |
| **SAST Detectability** | **High** - Deserialization APIs are distinct |
| **Implementation Complexity** | **Simple** - 8-10 patterns per language |
| **Security Impact** | **Critical** - RCE in most cases |
| **Recommendation** | **MUST IMPLEMENT** |

**Example Detection Patterns:**
```python
# Python
r'(?:pickle\.loads?|cPickle\.loads?|marshal\.loads?|shelve\.open)\s*\(\s*(?:request|input|user|data)'
r'yaml\.(?:load|unsafe_load)\s*\(\s*(?:request|input|data)'  # PyYAML

# Java
r'(?:ObjectInputStream|XMLDecoder).*\.read(?:Object|)\s*\('
r'(?:fromXML|deserialize)\s*\(\s*(?:request|input|data)'

# PHP
r'unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)'
r'unserialize\s*\(\s*(?:\$input|\$data|\$user)'

# JavaScript
r'eval\s*\(\s*JSON\.parse'  # Dangerous pattern
r'node-serialize|serialize-javascript.*unserialize'

# C#
r'(?:BinaryFormatter|SoapFormatter|NetDataContractSerializer)\.Deserialize'
r'(?:XmlSerializer|DataContractSerializer)\.Deserialize\s*\(\s*(?:request|input)'
```

**Expected FP Rate:** 5-10% (Low)

---

### 6. CWE-918: Server-Side Request Forgery (SSRF)

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #19 (Score: 4.05) |
| **SAST Detectability** | **Medium-High** - URL + request patterns |
| **Implementation Complexity** | **Medium** - Need context awareness |
| **Security Impact** | **High** - Internal network access, cloud metadata |
| **Recommendation** | **MUST IMPLEMENT** |

**Example Detection Patterns:**
```python
# Python
r'(?:requests\.(?:get|post|put|delete|head)|urllib\.request\.urlopen|httpx\.(?:get|post))\s*\(\s*(?:request|input|user|url|f["\'])'

# JavaScript
r'(?:fetch|axios\.(?:get|post)|http\.request|got)\s*\(\s*(?:req\.|params\.|input|user)'

# Java
r'new\s+URL\s*\(\s*(?:request\.getParameter|input|user)'
r'(?:HttpURLConnection|HttpClient).*(?:openConnection|send)\s*\(.*(?:request|input)'

# PHP
r'(?:file_get_contents|curl_init|fopen)\s*\(\s*\$_(?:GET|POST|REQUEST)'
```

**Expected FP Rate:** 20-30% (Medium-High)

---

## Tier 2: Should Implement (High Priority)

These CWEs are important but may have moderate SAST detectability or require more context.

### 7. CWE-352: Cross-Site Request Forgery (CSRF)

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #4 (Score: 19.57) |
| **SAST Detectability** | **Medium** - Absence of CSRF tokens detectable |
| **Implementation Complexity** | **Medium** - Framework-specific patterns |
| **Security Impact** | **High** - Unauthorized actions |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Detection Approach:**
- Detect forms without CSRF tokens
- Detect state-changing endpoints without CSRF validation
- Check for SameSite cookie attribute absence

**Example Patterns:**
```python
# Missing CSRF token in forms
r'<form[^>]*method\s*=\s*["\']post["\'][^>]*>(?:(?!csrf|_token|authenticity_token).)*</form>'

# Python Flask without CSRF
r'@app\.route\s*\([^)]*methods\s*=\s*\[[^\]]*(?:POST|PUT|DELETE)[^\]]*\]'  # Context: no csrf_protect

# Java Spring without CSRF
r'@(?:Post|Put|Delete)Mapping(?:(?!CsrfToken|@CrossOrigin).)*'
```

**Expected FP Rate:** 30-40% (High) - Framework auto-protection causes many FPs

---

### 8. CWE-434: Unrestricted File Upload

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #10 (Score: 10.03) |
| **SAST Detectability** | **Medium** - File upload without validation |
| **Implementation Complexity** | **Medium** - Need to detect missing validation |
| **Security Impact** | **Critical** - RCE via webshell upload |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python
r'(?:save|write)\s*\(\s*(?:request\.files|upload|file).*(?:filename|\.name)'

# PHP (very common vulnerability)
r'move_uploaded_file\s*\(\s*\$_FILES'
r'copy\s*\(\s*\$_FILES\[[^\]]+\]\[["\']tmp_name["\']\]'

# JavaScript
r'(?:multer|formidable|busboy).*(?:destination|filename)\s*:'

# Java
r'(?:transferTo|write)\s*\(\s*(?:file|path|new\s+File)'
```

**Expected FP Rate:** 25-35% (Medium-High)

---

### 9. CWE-94: Code Injection

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #11 (Score: 7.13) |
| **SAST Detectability** | **High** - eval/exec patterns |
| **Implementation Complexity** | **Simple** - Distinct APIs |
| **Security Impact** | **Critical** - RCE |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python
r'(?:eval|exec|compile)\s*\(\s*(?:request|input|user|f["\'])'

# JavaScript
r'eval\s*\(\s*(?:req\.|params\.|input|user)'
r'new\s+Function\s*\(\s*(?:req\.|params\.|input)'
r'setTimeout\s*\(\s*(?:req\.|input|user)'  # When string argument

# PHP
r'(?:eval|assert|create_function|preg_replace.*\/e)\s*\(\s*\$_(?:GET|POST|REQUEST)'

# Ruby
r'(?:eval|instance_eval|class_eval)\s*\(\s*(?:params|request|input)'
```

**Expected FP Rate:** 5-10% (Low)

---

### 10. CWE-77: Command Injection

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #13 (Score: 6.74) |
| **SAST Detectability** | **High** - Same as CWE-78 |
| **Implementation Complexity** | **Simple** - Combined with CWE-78 |
| **Security Impact** | **Critical** - RCE |
| **Recommendation** | **SHOULD IMPLEMENT** (combine with CWE-78) |

*Note: CWE-77 and CWE-78 are closely related. CWE-77 is generic command injection, CWE-78 is specifically OS command injection. Implement together.*

---

### 11. CWE-611: XML External Entity (XXE)

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | Not in Top 25 |
| **SAST Detectability** | **High** - XML parser configuration patterns |
| **Implementation Complexity** | **Simple** - 5-8 patterns per language |
| **Security Impact** | **High** - File disclosure, SSRF, DoS |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python
r'(?:etree\.parse|xml\.dom\.minidom\.parse|xml\.sax\.parse)\s*\('  # Without defusedxml

# Java
r'(?:DocumentBuilderFactory|SAXParserFactory|XMLInputFactory)\.newInstance'
r'(?:setFeature|setProperty)\s*\([^,]+,\s*(?:false|true)\)'  # Need context

# PHP
r'(?:simplexml_load_string|simplexml_load_file|DOMDocument::loadXML)\s*\('

# C#
r'(?:XmlReader|XmlDocument|XmlTextReader)\.(?:Create|Load)'
```

**False Positive Mitigation:**
- Check for `FEATURE_DISALLOW_DOCTYPE_DECL`
- Look for `defusedxml` usage in Python
- Detect `XmlResolver = null` in C#

**Expected FP Rate:** 20-30% (Medium)

---

## Tier 3: Nice to Have (Medium Priority)

These CWEs are valuable but either have lower SAST detectability or require sophisticated analysis.

### 12. CWE-862: Missing Authorization

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #9 (Score: 10.11) |
| **SAST Detectability** | **Low-Medium** - Hard to detect missing logic |
| **Implementation Complexity** | **Complex** - Semantic understanding required |
| **Security Impact** | **High** - Privilege escalation |
| **Recommendation** | **NICE TO HAVE** |

**Approach:** Detect patterns where sensitive operations lack authorization checks.

**Example Patterns (Limited Effectiveness):**
```python
# Controllers/endpoints without auth decorators
r'@app\.route\s*\([^)]*(?:admin|user|delete|update)[^)]*\)(?:(?!@login_required|@requires_auth).)*def'

# Direct database modification without auth check
r'\.(?:update|delete|insert)\s*\((?:(?!if.*(?:auth|user|role|permission)).)*\)'
```

**Expected FP Rate:** 40-60% (Very High)

---

### 13. CWE-863: Incorrect Authorization

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #18 (Score: 4.05) |
| **SAST Detectability** | **Low** - Logic flaws hard to detect |
| **Implementation Complexity** | **Complex** - Requires understanding auth logic |
| **Security Impact** | **High** - Privilege escalation |
| **Recommendation** | **NICE TO HAVE** |

**Note:** This is primarily a logic vulnerability. SAST can detect some patterns but effectiveness is limited.

---

### 14. CWE-287: Improper Authentication

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #14 (Score: 5.94) |
| **SAST Detectability** | **Low-Medium** - Some patterns detectable |
| **Implementation Complexity** | **Complex** - Many variations |
| **Security Impact** | **Critical** - Authentication bypass |
| **Recommendation** | **NICE TO HAVE** |

**Detectable Patterns:**
```python
# Hardcoded credentials in auth
r'if\s+(?:password|pass)\s*==\s*["\'][^"\']+["\']'
r'if\s+(?:user|username)\s*==\s*["\']admin["\']'

# Always-true auth conditions
r'if\s+(?:true|1|authenticated\s*=\s*true)'
```

---

### 15. CWE-269: Improper Privilege Management

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #15 (Score: 5.22) |
| **SAST Detectability** | **Low** - Semantic analysis needed |
| **Implementation Complexity** | **Complex** |
| **Security Impact** | **High** |
| **Recommendation** | **NICE TO HAVE** |

---

### 16. CWE-20: Improper Input Validation

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #12 (Score: 6.78) |
| **SAST Detectability** | **Low** - Absence of validation hard to detect |
| **Implementation Complexity** | **Very Complex** - Need to understand expected validation |
| **Security Impact** | **Medium** - Varies by context |
| **Recommendation** | **NICE TO HAVE** |

**Note:** This is a root cause CWE. Better to detect specific manifestations (XSS, SQLi, etc.).

---

### 17. CWE-306: Missing Authentication for Critical Function

| Attribute | Value |
|-----------|-------|
| **Top 25 Rank** | #25 (Score: 2.73) |
| **SAST Detectability** | **Low** - Requires understanding critical functions |
| **Implementation Complexity** | **Complex** |
| **Security Impact** | **High** |
| **Recommendation** | **NICE TO HAVE** |

---

## Tier 4: Additional SAST-Relevant CWEs

These are not in Top 25 but are well-suited for regex-based detection.

### 18. CWE-90: LDAP Injection

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **High** - Similar to SQL injection patterns |
| **Implementation Complexity** | **Simple** - 3-5 patterns per language |
| **Security Impact** | **High** - Directory manipulation |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python
r'(?:ldap\.search|ldap\.modify|ldap\.add)\s*\(.*\+.*(?:request|input|user)'

# Java
r'(?:search|modifyAttributes|createSubcontext)\s*\(\s*["\'].*\+.*(?:request|input)'

# C#
r'DirectorySearcher.*Filter\s*=.*\+.*(?:Request|input)'
```

---

### 19. CWE-643: XPath Injection

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **High** - Distinct XPath APIs |
| **Implementation Complexity** | **Simple** - 3-5 patterns per language |
| **Security Impact** | **Medium-High** - Data disclosure |
| **Recommendation** | **NICE TO HAVE** |

**Example Patterns:**
```python
# Python
r'\.xpath\s*\(\s*(?:f["\']|.*\+.*(?:request|input|user))'

# Java
r'\.compile\s*\(\s*["\'].*\+.*(?:request|input|getParameter)'
r'XPath.*evaluate\s*\(\s*["\'].*\+'

# PHP
r'xpath\s*\(\s*["\'].*\$_(?:GET|POST|REQUEST)'
```

---

### 20. CWE-113: HTTP Response Splitting

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **Medium** - Header injection patterns |
| **Implementation Complexity** | **Simple** - 5-8 patterns |
| **Security Impact** | **Medium** - Cache poisoning, XSS |
| **Recommendation** | **NICE TO HAVE** |

**Example Patterns:**
```python
# Detect CRLF in header values
r'(?:setHeader|addHeader|set_header)\s*\(\s*[^,]+,\s*(?:request|input|user)'
r'response\.headers\[[^\]]+\]\s*=\s*(?:request|input|user)'
```

---

### 21. CWE-917: Expression Language Injection

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **Medium** - EL syntax patterns |
| **Implementation Complexity** | **Medium** - Framework-specific |
| **Security Impact** | **Critical** - RCE |
| **Recommendation** | **NICE TO HAVE** |

**Example Patterns (Java EL, Spring SpEL):**
```java
# Java
r'(?:getValue|evaluateExpression|parseExpression)\s*\(\s*(?:request|input|getParameter)'
r'#\{.*(?:request|param|input)'  # JSF EL
```

---

### 22. CWE-943: NoSQL Injection

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **Medium-High** - Query construction patterns |
| **Implementation Complexity** | **Medium** - 10-12 patterns |
| **Security Impact** | **High** - Data breach |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python (MongoDB)
r'(?:find|find_one|update|delete).*\$(?:where|regex|gt|lt|ne).*(?:request|input|user)'
r'\.find\s*\(\s*\{[^}]*:\s*(?:request|input|user)'

# JavaScript
r'\.find\s*\(\s*\{[^}]*:\s*(?:req\.|params\.|body\.)'
r'(?:db|collection)\.(?:find|update|delete)\s*\(\s*JSON\.parse'
```

---

### 23. CWE-1336: Template Injection (SSTI)

| Attribute | Value |
|-----------|-------|
| **SAST Detectability** | **High** - Template engine patterns |
| **Implementation Complexity** | **Medium** - Multiple template engines |
| **Security Impact** | **Critical** - RCE |
| **Recommendation** | **SHOULD IMPLEMENT** |

**Example Patterns:**
```python
# Python Jinja2
r'render_template_string\s*\(\s*(?:request|input|user)'
r'Template\s*\(\s*(?:request|input|user)'

# JavaScript
r'(?:ejs|pug|handlebars)\.(?:render|compile)\s*\(\s*(?:req\.|input|user)'

# Java
r'(?:Velocity|FreeMarker|Thymeleaf).*(?:evaluate|process|merge)\s*\(\s*(?:request|input)'
```

---

## Implementation Roadmap

### Phase 1: Critical Injection Scanner (Weeks 1-2)
Create new `InjectionDetector` scanner covering:
- CWE-79: XSS (15-20 patterns)
- CWE-89: SQL Injection (20-25 patterns)
- CWE-78/77: Command Injection (10-15 patterns)
- CWE-22: Path Traversal (10-12 patterns)

**Estimated Rules:** 55-70 patterns
**Languages:** Python, JavaScript/TypeScript, Java, C#, PHP, Ruby, Go

### Phase 2: Serialization & SSRF Scanner (Weeks 3-4)
Extend `InjectionDetector` or create `DataFlowDetector`:
- CWE-502: Deserialization (15-20 patterns)
- CWE-918: SSRF (12-15 patterns)
- CWE-611: XXE (10-12 patterns)

**Estimated Rules:** 37-47 patterns

### Phase 3: Web Security Expansion (Weeks 5-6)
Extend `WebSecurityDetector`:
- CWE-352: CSRF detection (8-10 patterns)
- CWE-434: File Upload (10-12 patterns)
- CWE-94: Code Injection (8-10 patterns)
- CWE-1336: Template Injection (8-10 patterns)

**Estimated Rules:** 34-42 patterns

### Phase 4: NoSQL & Additional Patterns (Week 7)
- CWE-90: LDAP Injection (6-8 patterns)
- CWE-943: NoSQL Injection (10-12 patterns)
- CWE-643: XPath Injection (5-7 patterns)
- CWE-113: HTTP Response Splitting (5-7 patterns)
- CWE-917: Expression Language Injection (6-8 patterns)

**Estimated Rules:** 32-42 patterns

---

## Summary Table

| CWE | Name | Tier | Detectability | Complexity | FP Rate | Priority |
|-----|------|------|---------------|------------|---------|----------|
| CWE-79 | XSS | 1 | High | Medium | 15-25% | **P0** |
| CWE-89 | SQL Injection | 1 | High | Medium | 10-20% | **P0** |
| CWE-78 | OS Command Injection | 1 | High | Simple | 10-15% | **P0** |
| CWE-22 | Path Traversal | 1 | High | Simple | 15-20% | **P0** |
| CWE-502 | Deserialization | 1 | High | Simple | 5-10% | **P0** |
| CWE-918 | SSRF | 1 | Medium-High | Medium | 20-30% | **P0** |
| CWE-352 | CSRF | 2 | Medium | Medium | 30-40% | **P1** |
| CWE-434 | File Upload | 2 | Medium | Medium | 25-35% | **P1** |
| CWE-94 | Code Injection | 2 | High | Simple | 5-10% | **P1** |
| CWE-77 | Command Injection | 2 | High | Simple | 10-15% | **P1** |
| CWE-611 | XXE | 2 | High | Simple | 20-30% | **P1** |
| CWE-90 | LDAP Injection | 2 | High | Simple | 10-15% | **P1** |
| CWE-943 | NoSQL Injection | 2 | Medium-High | Medium | 15-25% | **P1** |
| CWE-1336 | Template Injection | 2 | High | Medium | 10-15% | **P1** |
| CWE-862 | Missing Authorization | 3 | Low-Medium | Complex | 40-60% | **P2** |
| CWE-863 | Incorrect Authorization | 3 | Low | Complex | 50-70% | **P2** |
| CWE-287 | Improper Authentication | 3 | Low-Medium | Complex | 30-50% | **P2** |
| CWE-269 | Privilege Management | 3 | Low | Complex | 50-70% | **P2** |
| CWE-20 | Input Validation | 3 | Low | Very Complex | 60-80% | **P3** |
| CWE-306 | Missing Auth Critical | 3 | Low | Complex | 50-70% | **P3** |
| CWE-643 | XPath Injection | 3 | High | Simple | 10-15% | **P2** |
| CWE-113 | HTTP Response Split | 3 | Medium | Simple | 20-30% | **P2** |
| CWE-917 | EL Injection | 3 | Medium | Medium | 15-25% | **P2** |

---

## Conclusion

This evaluation identifies **6 Tier 1 (Must Implement)** CWEs that should be prioritized immediately:
1. CWE-79: XSS
2. CWE-89: SQL Injection
3. CWE-78: OS Command Injection
4. CWE-22: Path Traversal
5. CWE-502: Deserialization
6. CWE-918: SSRF

These represent the most critical gaps in our current coverage and have high SAST detectability with reasonable false positive rates.

**Recommended Next Steps:**
1. Create a new `InjectionDetector` scanner following the existing pattern architecture
2. Implement Phase 1 patterns (55-70 rules) covering the top injection vulnerabilities
3. Add comprehensive unit tests with both true positive and false positive test cases
4. Integrate with the orchestrator and enable gradual rollout

After implementing Tier 1, our CWE coverage will increase to approximately **85-90 CWEs**, covering nearly all of the CWE Top 25 (2024) with regex-detectable patterns.
