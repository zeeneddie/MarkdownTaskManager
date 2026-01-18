# Security Scanners - Complete False Negative Analysis

## Executive Summary

Comprehensive false negative analysis across ALL security scanners. Total **52 false negatives** found across 6 scanner categories covering 25+ CWEs.

| Scanner Category | False Negatives | Key CWEs Tested |
|-----------------|-----------------|-----------------|
| **Fase 39: Web Security** | 11 | CWE-1321, CWE-1236, CWE-1284 |
| **Fase 39: Path Security** | 13 | CWE-427, CWE-428, CWE-1333 |
| **Fase 38: Memory Safety** | 5 | CWE-119, CWE-416, CWE-190 |
| **Fase 38: Concurrency** | 5 | CWE-362, CWE-367, CWE-833 |
| **Fase 36: Crypto** | 5 | CWE-327, CWE-329, CWE-916 |
| **Fase 36: Control Flow** | 4 | CWE-193, CWE-484, CWE-835 |
| **Fase 36: Boolean Logic** | 5 | CWE-480, CWE-570, CWE-476 |
| **Generic Security** | 4 | CWE-330, CWE-602, CWE-208 |

---

## CWE Coverage Tracking

### CWEs Investigated for False Negatives

| CWE | Name | Scanner | Tests | False Negatives |
|-----|------|---------|-------|-----------------|
| CWE-119 | Buffer Overflow | Memory Safety | 3 | 3 |
| CWE-190 | Integer Overflow | Memory Safety | 1 | 1 |
| CWE-208 | Timing Attack | Generic Security | 1 | 1 |
| CWE-327 | Weak Crypto | Crypto | 3 | 3 |
| CWE-329 | Static IV | Crypto | 1 | 1 |
| CWE-330 | Weak PRNG | Generic Security | 2 | 1 |
| CWE-362 | Race Condition | Concurrency | 5 | 5 |
| CWE-390 | Empty Exception | Control Flow | 1 | 0 (partial) |
| CWE-416 | Use After Free | Memory Safety | 1 | 0 (detected) |
| CWE-427 | Uncontrolled Path | Path Security | 5 | 5 |
| CWE-428 | Unquoted Path | Path Security | 4 | 4 |
| CWE-476 | Null Deref | Boolean Logic | 1 | 1 |
| CWE-480 | Operator Error | Boolean Logic | 3 | 3 |
| CWE-484 | Missing Break | Control Flow | 1 | 0 (detected) |
| CWE-570 | Always False | Boolean Logic | 1 | 1 |
| CWE-602 | Auth Bypass | Generic Security | 2 | 2 |
| CWE-835 | Infinite Loop | Control Flow | 1 | 1 |
| CWE-916 | Weak Hash | Crypto | 1 | 1 |
| CWE-1236 | CSV Injection | Web Security | 5 | 3 |
| CWE-1284 | Invalid Quantity | Web Security | 5 | 3 |
| CWE-1321 | Prototype Pollution | Web Security | 6 | 5 |
| CWE-1333 | ReDoS | Path Security | 5 | 4 |

### Total: 25 CWEs Tested | 52 False Negatives Found

---

## Part 1: Fase 39 Web Security Scanner

### CWE-1321: Prototype Pollution (5 False Negatives)

**Current Detection:**
- `__proto__` assignments
- `constructor.prototype` manipulation
- `Object.assign` with user input keywords

**Missing Patterns:**

#### 1. Spread Operator (`...`)
```javascript
// NOT DETECTED
function mergeConfig(userInput) {
    return { ...defaults, ...userInput };  // Copies __proto__
}
```
**Fix:** Add pattern: `\{\s*\.{3}\s*(?:req\.|params\.|body\.|input|userInput)`

#### 2. Lodash/Underscore Merge (CVE-2019-10744)
```javascript
// NOT DETECTED
_.merge(config, req.body);
_.defaultsDeep(options, userInput);
```
**Fix:** Add pattern: `_\.(?:merge|defaultsDeep|assign|extend)\s*\(`

#### 3. jQuery $.extend()
```javascript
// NOT DETECTED
$.extend(true, globalConfig, userSettings);
```

#### 4. Reflect.set()
```javascript
// NOT DETECTED
Reflect.set(obj, req.body.key, value);
```

#### 5. Object.defineProperty()
```javascript
// NOT DETECTED
Object.defineProperty(obj, userInput.prop, { value: val });
```

---

### CWE-1236: CSV Injection (3 False Negatives)

#### 1. String Concatenation CSV
```python
# NOT DETECTED
csv_content = f"{user.name},{user.email}\n"
```

#### 2. Flask Response with CSV MIME Type
```python
# NOT DETECTED
return Response(csv_data, mimetype='text/csv')
```

#### 3. DictWriter Partial Detection
```python
# Detected as WS010, but WS011 not triggered
writer.writerow(user)
```

---

### CWE-1284: Invalid Quantity (3 False Negatives)

#### 1. Python Slice with User Bounds
```python
# NOT DETECTED
return items[start:end]  # start/end from request
```

#### 2. String.repeat() DoS
```javascript
// NOT DETECTED
str.repeat(parseInt(req.query.count));
```

#### 3. new Array() with User Size
```javascript
// NOT DETECTED
new Array(parseInt(req.params.size))
```

---

## Part 2: Fase 39 Path Security Scanner

### CWE-427: Uncontrolled Search Path (5 False Negatives)

#### 1. subprocess.run with Relative Command
```python
# NOT DETECTED
subprocess.run(['mytool', '--version'])  # Relies on PATH
```

#### 2. Node.js exec with Relative Command
```javascript
// NOT DETECTED
exec('imagemagick convert input.png output.jpg');
```

#### 3. sys.path.insert with Variable
```python
# NOT DETECTED
sys.path.insert(0, user_plugins)  # Variable from env
```

#### 4. Node.js require() (Design Limitation)
```javascript
// NOT DETECTED - normal Node behavior
const plugin = require('user-plugin');
```

#### 5. LD_LIBRARY_PATH Modification
```c
// NOT DETECTED - only checks PATH, not LD_LIBRARY_PATH
setenv("LD_LIBRARY_PATH", new_path, 1);
```

---

### CWE-428: Unquoted Search Path (4 False Negatives)

#### 1. f-string Path with Spaces
```python
# NOT DETECTED
subprocess.Popen(f'{app_path} --config', shell=True)
```

#### 2. Service Binary Path Declaration
```csharp
// NOT DETECTED
string binaryPath = @"C:\Program Files\...";
```

#### 3. Shell Variable Unquoted
```bash
# NOT DETECTED
$APP_DIR/run.sh  # APP_DIR may contain spaces
```

#### 4. String Concatenation with shell=True
```python
# NOT DETECTED
subprocess.call(tool_path + ' --run', shell=True)
```

---

### CWE-1333: ReDoS (4 False Negatives)

#### 1. Complex Email Regex
```python
# NOT DETECTED - requires semantic analysis
re.compile(r'^([a-zA-Z0-9_\.-]+)@...')
```

#### 2. HTML Tag Stripping
```python
# NOT DETECTED
re.sub(r'<[^>]*>', '', text)
```

#### 3. Phone Number Regex
```java
// NOT DETECTED
Pattern.compile("^(\\+\\d{1,3}[- ]?)?...")
```

#### 4. Regex from Configuration
```python
# NOT DETECTED
re.compile(config['validators']['email'])
```

---

## Part 3: Fase 38 Memory Safety Scanner

### CWE-119: Buffer Overflow (3 False Negatives)

#### 1. strncat Improper Size
```c
// NOT DETECTED
strncat(dest, src, sizeof(dest));  // Should be sizeof(dest)-strlen(dest)-1
```

#### 2. sizeof on Pointer (Array Decay)
```c
// NOT DETECTED
memcpy(local, buf, sizeof(buf));  // sizeof(buf) is 8, not buffer size
```

#### 3. snprintf Truncation Unchecked
```c
// NOT DETECTED
vsnprintf(dest, size, fmt, args);  // Truncation silently ignored
```

### CWE-190: Integer Underflow (1 False Negative)

```c
// NOT DETECTED
size_t data_size = dest_size - header_size;  // Underflow if header_size > dest_size
```

---

## Part 4: Fase 38 Concurrency Scanner

### CWE-362: Race Condition (5 False Negatives)

#### 1. Check-then-Act
```python
# NOT DETECTED
if counter < 100:  # Check
    counter += 1   # Act - race between check and act
```

#### 2. Broken Double-Checked Locking
```java
// NOT DETECTED
if (instance == null) {
    synchronized(Singleton.class) {
        if (instance == null) {
            instance = new Singleton();  // Can be reordered!
        }
    }
}
```

#### 3. asyncio Shared State
```python
# NOT DETECTED
shared_list.append(i)  # Not thread-safe in asyncio with threads
```

#### 4. Goroutine Closure Capture
```go
// NOT DETECTED
go func() {
    println(i)  // Captures i by reference
}()
```

#### 5. Non-Atomic Increment
```cpp
// NOT DETECTED
counter++;  // Read-modify-write is not atomic
```

---

## Part 5: Fase 36 Crypto Scanner

### CWE-327: Weak Crypto (3 False Negatives)

#### 1. Base64 as "Encryption"
```python
# NOT DETECTED
base64.b64encode(password.encode())  # NOT encryption!
```

#### 2. XOR Cipher
```python
# NOT DETECTED
bytes(a ^ b for a, b in zip(data, key * n))
```

#### 3. AES-CBC Without Authentication
```python
# NOT DETECTED
cipher = AES.new(key, AES.MODE_CBC)  # Vulnerable to padding oracle
```

### CWE-329: Static IV (1 False Negative)

```python
# NOT DETECTED
IV = b'0000000000000000'  # Static IV defeats encryption
cipher = AES.new(key, AES.MODE_CBC, IV)
```

### CWE-916: Weak Password Hashing (1 False Negative)

```python
# NOT DETECTED
bcrypt.gensalt(rounds=4)  # Cost factor too low
```

---

## Part 6: Fase 36 Control Flow Scanner

### CWE-835: Infinite Loop (1 False Negative)

```javascript
// NOT DETECTED
while (items.pop()) {  // May loop forever with falsy values
    console.log("processing");
}
```

### CWE-561: Unreachable Code (1 False Negative)

```javascript
// NOT DETECTED
return x * 2;
console.log("This never runs");  // Dead code
```

### CWE-783: Nested Ternary (1 False Negative)

```javascript
// NOT DETECTED
return a > 0 ? b > 0 ? b : c : c > 0 ? c : 0;
```

---

## Part 7: Fase 36 Boolean Logic Scanner

### CWE-480: Operator Errors (3 False Negatives)

#### 1. Boolean Assignment vs Comparison
```python
# NOT DETECTED (Python prevents this)
if valid = False:
```

#### 2. De Morgan's Law Violation
```javascript
// NOT DETECTED - hard to determine intent
if (!a && !b) {  // vs !(a || b)
```

#### 3. Yoda Condition Error
```c
// NOT DETECTED
if (NULL = ptr) {  // Assignment to NULL
```

### CWE-570: Always False Condition (1 False Negative)

```javascript
// NOT DETECTED
if (x > 10 && x < 5) {  // Impossible condition
```

### CWE-476: Null Check After Use (1 False Negative)

```java
// NOT DETECTED
int len = s.length();  // Dereference
if (s != null) {       // Check after use!
```

---

## Part 8: Generic Security Scanner

### CWE-330: Weak PRNG (1 False Negative)

```python
# NOT DETECTED
uuid.uuid4()  # For reset tokens - not cryptographically secure
```

### CWE-602: Auth Check Without Block (2 False Negatives)

```python
# NOT DETECTED
if not request.user.is_admin:
    flash("Not authorized")  # Continues execution!
return render_admin_dashboard()
```

```java
// NOT DETECTED
if (!actor.hasPermission("delete_users")) {
    logger.warn("Unauthorized");  // Only logs
}
userRepository.delete(target);  // Executes anyway
```

### CWE-208: Timing Attack (1 False Negative)

```python
# NOT DETECTED
return input_password == stored_password  # Timing leak
```

---

## Priority Recommendations

### Critical (Security Impact)
1. Add spread operator detection for prototype pollution
2. Add lodash/underscore merge detection (known CVEs)
3. Add subprocess with relative command detection
4. Add LD_LIBRARY_PATH modification detection
5. Add timing-safe comparison detection

### High Priority
6. Add Base64/XOR "encryption" detection
7. Add AES-CBC without authentication warning
8. Add broken double-checked locking detection
9. Add auth check without return detection
10. Add static IV detection

### Medium Priority
11. Improve ReDoS detection with semantic analysis
12. Add array size from user input detection
13. Add check-then-act race condition detection
14. Add bcrypt low cost factor detection
15. Add impossible condition detection

---

## Testing Instructions

```bash
cd backend
source .venv/bin/activate

# Run Fase 39 tests
python -m tests.false_negative_finder

# Run extended tests (Fase 36, 38, Generic)
python -m tests.extended_false_negative_finder

# Run full test suite
pytest tests/unit/security_scanner/ -v
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total CWEs Tested | 25 |
| Total Test Cases | 60 |
| Total False Negatives | 52 |
| Detection Rate | 13.3% |
| Scanners Tested | 8 |

**Key Finding:** Regex-based pattern matching has fundamental limitations for detecting semantic vulnerabilities like race conditions, data flow issues, and complex cryptographic misuse.
