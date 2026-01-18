# Critical Software Error Patterns Reference

A comprehensive technical reference for detecting and preventing critical system failures. This document covers four major categories: Crashes, Data Loss, Deadlocks, and Performance issues.

---

## 1. CRASHES

Code patterns that cause application/system crashes or abnormal termination.

### 1.1 Null Pointer Dereference (CWE-476)

**Description**: Occurs when a program dereferences a pointer that is NULL, typically causing immediate crash or exit.

**Affected Languages**: C, C++, Assembly, and any language with direct pointer manipulation. Higher-level languages (Java, Python, C#) manifest as NullPointerException/AttributeError.

**Common Code Patterns**:
```c
// Pattern 1: Unchecked function return value
char* hostname = gethostbyaddr(addr);
strcpy(buffer, hostname);  // CRASH if gethostbyaddr returns NULL

// Pattern 2: Uninitialized pointer
int *p = NULL;
arr[0] = *p;  // CRASH: dereferencing NULL

// Pattern 3: Check-after-dereference
void process(char* ptr) {
    char c = *ptr;       // Use before check
    if (ptr == NULL) {   // Too late!
        return;
    }
}

// Pattern 4: Logic error with parameters
if (argc < 2) {
    getaddrinfo(NULL, ...);  // Passes NULL due to logic error
}
```

**Detection Methods**:
- Static analysis: FindBugs, Coverity, Polyspace
- Runtime: AddressSanitizer, Valgrind
- Pattern matching: Check for pointer use before NULL checks

**CWE Mapping**: CWE-476 (NULL Pointer Dereference), CWE-252 (Unchecked Return Value)

**Real-World Example**: Numerous CVEs involve NULL pointer crashes in web servers, media parsers, and system utilities.

---

### 1.2 Stack Overflow / Buffer Overflow (CWE-121, CWE-120)

**Description**: Buffer overflows occur when data exceeds allocated buffer boundaries. Stack overflows from excessive recursion exhaust stack memory.

**Affected Languages**: Primarily C/C++; any language allowing direct memory access

**Common Code Patterns**:
```c
// Pattern 1: Classic buffer overflow (CWE-120)
char buffer[64];
strcpy(buffer, user_input);  // No size check

// Pattern 2: Off-by-one error
char buf[10];
for (int i = 0; i <= 10; i++) {  // Should be i < 10
    buf[i] = data[i];
}

// Pattern 3: Uncontrolled recursion (CWE-674)
void recurse(int n) {
    recurse(n);  // n never changes - infinite recursion
}

// Pattern 4: Unsafe string functions
gets(buffer);           // NEVER use
sprintf(buf, "%s", s);  // Use snprintf instead
strcat(dst, src);       // No bounds check
```

**Dangerous Functions (C/C++)**:
- `gets()` - NEVER safe
- `strcpy()`, `strcat()` - Use `strncpy()`, `strncat()`
- `sprintf()` - Use `snprintf()`
- `scanf("%s", ...)` - Use width specifier

**Detection Methods**:
- Compiler flags: `/GS` (MSVC), `FORTIFY_SOURCE` (GCC)
- Runtime: Stack canaries (StackGuard, ProPolice)
- Static: Polyspace, Coverity

**CWE Mapping**: CWE-121 (Stack-based Buffer Overflow), CWE-120 (Classic Buffer Overflow), CWE-674 (Uncontrolled Recursion)

**Real-World Example**:
- **Morris Worm (1988)**: Exploited buffer overflow in fingerd
- **Qualcomm Snapdragon CVE-2025-47388**: Classic buffer overflow in DSP handling

---

### 1.3 Use-After-Free / Double-Free (CWE-416, CWE-415)

**Description**: Use-after-free occurs when memory is accessed after being freed. Double-free occurs when free() is called twice on the same pointer.

**Affected Languages**: C, C++, and languages with manual memory management

**Common Code Patterns**:
```c
// Pattern 1: Use-after-free
char* ptr = malloc(SIZE);
free(ptr);
ptr[0] = 'A';  // CRASH or corruption - ptr is dangling

// Pattern 2: Double-free
char* data = malloc(100);
free(data);
// ... other code ...
free(data);  // Double-free - corrupts heap metadata

// Pattern 3: Error path double-free
void process() {
    char* buf = malloc(100);
    if (error_condition) {
        free(buf);
        // Missing return - falls through
    }
    // ... more code ...
    free(buf);  // Double-free in error case
}

// Pattern 4: Aliased pointers
char* a = malloc(100);
char* b = a;  // Alias
free(a);
free(b);  // Double-free through alias
```

**Prevention**:
```c
// Set pointer to NULL after free
free(ptr);
ptr = NULL;

// C++: Use smart pointers
std::unique_ptr<char[]> ptr(new char[100]);
std::shared_ptr<Data> shared = std::make_shared<Data>();
```

**Detection Methods**:
- Runtime: Valgrind, AddressSanitizer (ASan)
- Static: Coverity, Polyspace
- Modern glibc has built-in double-free detection

**CWE Mapping**: CWE-416 (Use After Free), CWE-415 (Double Free), CWE-825 (Expired Pointer Dereference)

**Real-World Example**: CVE-2025-62215 - Windows Kernel 0-day combining race condition with double-free for privilege escalation

---

### 1.4 Unhandled Exceptions

**Description**: Exceptions that propagate up the call stack without being caught, causing program termination.

**Affected Languages**: All languages with exception handling (Java, Python, C++, C#, JavaScript)

**Common Code Patterns**:
```python
# Pattern 1: Missing exception handler
def process_file(path):
    f = open(path)  # FileNotFoundError possible
    return f.read()

# Pattern 2: Catching wrong exception type
try:
    data = json.loads(input)
except ValueError:  # JSONDecodeError is subclass, but incomplete
    pass

# Pattern 3: Exception in cleanup code
try:
    resource = acquire()
    process(resource)
finally:
    resource.release()  # What if resource is None?
```

```java
// Pattern 4: Unchecked exceptions in threads
new Thread(() -> {
    throw new RuntimeException("Unhandled!");
}).start();  // Thread dies silently or crashes app
```

**Detection Methods**:
- Static: SonarQube, FindBugs, Checkstyle
- IDE plugins: IntelliJ, Eclipse built-in analysis
- Runtime: Sentry, Raygun crash reporting

**Best Practices**:
- Always have top-level exception handlers
- Log exceptions with full context (timestamp, stack trace, parameters)
- Use exception monitoring platforms in production

---

### 1.5 Assertion Failures (CWE-617)

**Description**: assert() statements that can be triggered by external input, causing program abort via SIGABRT.

**Affected Languages**: C, C++, Python, Java, and most languages with assertion support

**Common Code Patterns**:
```c
// Pattern 1: Reachable assertion with user input
void process(int user_value) {
    assert(user_value > 0);  // Attacker can provide <= 0
    // ...
}

// Pattern 2: Assertion in production code
void parse_data(char* data) {
    assert(data != NULL);  // Should use proper error handling
    assert(strlen(data) < MAX_LEN);  // DoS via assertion
}
```

**Security Implications**:
- Assertions typically call `abort()` sending SIGABRT
- Can cause DoS in server applications handling multiple connections
- Should never be used for input validation in production

**Detection Methods**:
- Static: Review for assert() with external data
- Fuzzing: Can trigger assertion failures
- Code review: Ensure assertions are for internal invariants only

**CWE Mapping**: CWE-617 (Reachable Assertion)

---

### 1.6 Signal Handler Issues (CWE-479, CWE-364)

**Description**: Calling non-reentrant functions from signal handlers causes crashes or corruption.

**Affected Languages**: C, C++, and languages with signal handling

**Unsafe Functions in Signal Handlers**:
- `malloc()`, `free()` - Global metadata structures
- `printf()`, `fprintf()` - Buffer state corruption
- `syslog()` - Allocates scratch memory
- `exit()` - Use `_exit()` instead

**Common Code Patterns**:
```c
// DANGEROUS: Non-reentrant function in handler
void handler(int sig) {
    printf("Caught signal %d\n", sig);  // UNSAFE
    free(global_ptr);  // UNSAFE - double-free risk
    exit(1);  // UNSAFE
}

// SAFE pattern: Set flag only
volatile sig_atomic_t got_signal = 0;
void handler(int sig) {
    got_signal = 1;  // SAFE
}
```

**Detection Methods**:
- GCC 11+ with `-fanalyzer` flag
- Static analysis: Detect non-async-signal-safe calls in handlers
- Code review: Check POSIX async-signal-safe function list

**CWE Mapping**: CWE-479 (Signal Handler Use of Non-reentrant Function), CWE-364 (Signal Handler Race Condition), CWE-828 (Signal Handler with Functionality not Async-Safe)

---

## 2. DATA LOSS

Patterns that lead to data loss, corruption, or inconsistency.

### 2.1 Race Conditions / TOCTOU (CWE-362, CWE-367)

**Description**: Time-of-Check-Time-of-Use occurs when a security check and the use of the checked resource have a time gap that can be exploited.

**Affected Languages**: All languages; particularly dangerous in file operations

**Common Code Patterns**:
```c
// Pattern 1: Classic TOCTOU in file operations
if (access(filename, W_OK) == 0) {  // CHECK
    // WINDOW: Attacker can replace file with symlink
    fd = open(filename, O_WRONLY);   // USE
    write(fd, data, len);
}

// Pattern 2: Stat-then-open
struct stat st;
stat(filename, &st);
if (st.st_mode & S_IFREG) {  // CHECK: is regular file?
    // WINDOW: File could be replaced
    open(filename, ...);      // USE
}
```

```python
# Pattern 3: Python file race
import os
if os.path.exists(filename):  # CHECK
    # WINDOW
    with open(filename) as f:  # USE
        data = f.read()
```

**Prevention**:
```c
// Open first, then check
int fd = open(filename, O_WRONLY);
if (fd >= 0) {
    struct stat st;
    fstat(fd, &st);  // Check via already-open fd
    // Safe to use fd
}
```

**Detection Methods**:
- Static: Pattern matching for check-then-use sequences
- Dynamic: Stress testing with race condition triggers
- Fuzzing: Insert delays between check and use

**CWE Mapping**: CWE-362 (Race Condition), CWE-367 (TOCTOU Race Condition)

**Real-World Example**: CVE-2026-22701 - filelock TOCTOU symlink vulnerability where attacker creates symlink between permission check and file creation

---

### 2.2 Missing Atomic Operations (CWE-366)

**Description**: Operations assumed to be atomic but aren't, causing data races and corruption.

**Affected Languages**: All languages with concurrent execution

**Common Code Patterns**:
```c
// Pattern 1: Non-atomic increment
int counter = 0;
// Thread 1 and Thread 2 both execute:
counter++;  // NOT atomic! Read-modify-write

// Pattern 2: Non-atomic flag check
int ready = 0;
// Thread 1:
data = compute();
ready = 1;
// Thread 2:
if (ready) {
    use(data);  // May see stale data due to reordering
}
```

```java
// Pattern 3: Check-then-act (Java)
if (map.containsKey(key)) {  // Check
    return map.get(key);      // Act - another thread may have removed it
}
```

**Prevention**:
```c
// C11 atomics
#include <stdatomic.h>
atomic_int counter = 0;
atomic_fetch_add(&counter, 1);  // Atomic increment

// Or use mutex
pthread_mutex_lock(&lock);
counter++;
pthread_mutex_unlock(&lock);
```

```java
// Java: ConcurrentHashMap
map.computeIfAbsent(key, k -> compute(k));  // Atomic operation
```

**Detection Methods**:
- Static: RacerD (Facebook Infer), ThreadSanitizer
- Dynamic: ThreadSanitizer (TSan), Helgrind
- Pattern matching: Look for shared variable access without synchronization

**CWE Mapping**: CWE-366 (Race Condition within a Thread), CWE-362 (Race Condition)

---

### 2.3 Incomplete Transactions / Rollback Failures

**Description**: Database operations that partially complete, leaving data in inconsistent state.

**Common Code Patterns**:
```python
# Pattern 1: Missing transaction boundary
def transfer_money(from_acc, to_acc, amount):
    db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?",
               (amount, from_acc))
    # CRASH HERE = inconsistent state
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?",
               (amount, to_acc))

# Pattern 2: Auto-commit disaster
connection.autocommit = True  # Each statement is its own transaction
for row in data:
    db.execute("INSERT ...")  # Partial insert on failure
```

```java
// Pattern 3: Exception before commit
try {
    connection.setAutoCommit(false);
    stmt1.execute();
    stmt2.execute();  // Exception here
    connection.commit();
} catch (Exception e) {
    // Missing rollback!
    throw e;
}
```

**Prevention**:
```python
# Proper transaction handling
try:
    with db.transaction():  # Context manager ensures rollback
        db.execute("UPDATE accounts SET balance = balance - ?...", ...)
        db.execute("UPDATE accounts SET balance = balance + ?...", ...)
        # Implicit commit at end
except Exception:
    # Implicit rollback
    raise
```

**Key Concepts**:
- **Write-Ahead Logging (WAL)**: Changes logged before writing to data files
- **ARIES Recovery**: Algorithm for crash recovery using redo/undo logs
- **Two-Phase Commit**: For distributed transactions

**Detection Methods**:
- Code review: Check all DB operations use transactions
- Static analysis: Detect missing commit/rollback in exception paths
- Testing: Simulate crashes at various points

---

### 2.4 Buffer Overflow Data Corruption (CWE-787)

**Description**: Writing beyond buffer boundaries corrupts adjacent memory.

**Affected Languages**: C, C++, Assembly

**Common Code Patterns**:
```c
// Pattern 1: Adjacent structure corruption
struct {
    char name[32];
    int privilege_level;  // Gets overwritten!
} user;
strcpy(user.name, long_untrusted_input);

// Pattern 2: Heap metadata corruption
char* buf1 = malloc(64);
char* buf2 = malloc(64);
strcpy(buf1, very_long_string);  // Corrupts buf2's heap metadata
free(buf2);  // CRASH - corrupted metadata
```

**CWE Mapping**: CWE-787 (Out-of-bounds Write), CWE-120 (Buffer Copy without Size Check)

---

## 3. DEADLOCKS

Resource contention causing threads/processes to wait indefinitely.

### 3.1 Lock Ordering Issues (CWE-833)

**Description**: Deadlock occurs when threads acquire locks in different orders, creating circular wait.

**Common Code Patterns**:
```java
// DEADLOCK PATTERN
// Thread 1:
synchronized(lockA) {
    synchronized(lockB) {
        // work
    }
}

// Thread 2:
synchronized(lockB) {  // Opposite order!
    synchronized(lockA) {
        // work - DEADLOCK!
    }
}
```

```python
# Python threading deadlock
lock_a = threading.Lock()
lock_b = threading.Lock()

def thread1():
    with lock_a:
        time.sleep(0.1)  # Increases deadlock probability
        with lock_b:
            pass

def thread2():
    with lock_b:
        time.sleep(0.1)
        with lock_a:  # DEADLOCK - opposite order
            pass
```

**Prevention - Lock Ordering**:
```java
// Always acquire locks in consistent order
// Define global ordering: lockA < lockB < lockC
void safeMethod() {
    synchronized(lockA) {  // Always A first
        synchronized(lockB) {  // Then B
            // work
        }
    }
}
```

**Prevention - Lock Timeout**:
```java
// Use tryLock with timeout
if (lock.tryLock(1, TimeUnit.SECONDS)) {
    try {
        // work
    } finally {
        lock.unlock();
    }
} else {
    // Handle timeout - avoid deadlock
}
```

**Detection Methods**:
- Static: RacerX, Polyspace deadlock checker
- Runtime: JVM thread dump, database deadlock detection
- Pattern matching: Look for nested lock acquisitions

**CWE Mapping**: CWE-833 (Deadlock), CWE-667 (Improper Locking)

---

### 3.2 Database Deadlocks

**Description**: Multiple transactions waiting for locks held by each other.

**Common Pattern**:
```sql
-- Transaction 1:
BEGIN;
UPDATE accounts SET balance = 100 WHERE id = 1;  -- Locks row 1
UPDATE accounts SET balance = 200 WHERE id = 2;  -- Waits for row 2

-- Transaction 2 (concurrent):
BEGIN;
UPDATE accounts SET balance = 300 WHERE id = 2;  -- Locks row 2
UPDATE accounts SET balance = 400 WHERE id = 1;  -- Waits for row 1 - DEADLOCK!
```

**Prevention**:
- Access tables/rows in consistent order
- Use SELECT ... FOR UPDATE to acquire locks upfront
- Keep transactions short
- Use appropriate isolation levels

**Detection**:
- Database deadlock monitors
- PostgreSQL: `log_lock_waits = on`
- MySQL: `SHOW ENGINE INNODB STATUS`

---

### 3.3 Thread Pool Exhaustion

**Description**: All threads in pool are blocked, preventing new work from executing.

**Common Code Patterns**:
```java
// Pattern 1: Blocking call in async context
ExecutorService pool = Executors.newFixedThreadPool(10);
for (int i = 0; i < 100; i++) {
    pool.submit(() -> {
        // Blocking call exhausts all threads
        Thread.sleep(60000);
    });
}

// Pattern 2: Sync-over-async (C#/.NET)
public void BadMethod() {
    var result = AsyncMethod().Result;  // BLOCKS THREAD
}

// Pattern 3: Nested task submission
pool.submit(() -> {
    Future<?> inner = pool.submit(() -> work());
    inner.get();  // If all threads doing this, deadlock
});
```

**Symptoms**:
- High latency despite low CPU usage
- Timeouts on requests
- Thread pool at max size for extended periods

**Detection Methods**:
- .NET: ETW events for ThreadPool starvation
- JVM: Thread dumps showing blocked threads
- APM tools: Datadog, New Relic, Dynatrace

**Prevention**:
- Use async/await properly (avoid `.Result`, `.Wait()`)
- Separate thread pools for different task types
- Set appropriate pool sizes
- Add circuit breakers

**CWE Mapping**: Related to CWE-400 (Uncontrolled Resource Consumption)

---

## 4. PERFORMANCE

Patterns causing severe performance degradation.

### 4.1 N+1 Query Problem

**Description**: Initial query fetches N records, then N additional queries fetch related data.

**Common Code Patterns**:
```python
# Django N+1 Pattern
books = Book.objects.all()  # 1 query
for book in books:
    print(book.author.name)  # N queries! (lazy load)

# Ruby/Rails N+1
posts = Post.all
posts.each do |post|
    puts post.comments.count  # N queries
end
```

```java
// Hibernate N+1 (default lazy loading)
List<Order> orders = session.createQuery("FROM Order").list();
for (Order order : orders) {
    order.getItems().size();  // N additional queries
}
```

**Solution Patterns**:
```python
# Django: select_related (FK) / prefetch_related (M2M)
books = Book.objects.select_related('author').all()

# SQLAlchemy: joinedload
from sqlalchemy.orm import joinedload
session.query(Book).options(joinedload(Book.author)).all()
```

```java
// Hibernate: JOIN FETCH
session.createQuery("FROM Order o JOIN FETCH o.items").list();
```

**Detection Methods**:
- Django Debug Toolbar
- Hibernate Statistics
- APM tools (New Relic, Datadog)
- SQL query logging: Look for repeated similar queries

---

### 4.2 Memory Leaks (CWE-401)

**Description**: Allocated memory not released after use, causing gradual memory exhaustion.

**Affected Languages**: All languages; C/C++ (missing free), GC languages (retained references)

**Common Code Patterns**:
```c
// C: Missing free in error path
void process() {
    char* buf = malloc(1024);
    if (error_condition) {
        return;  // LEAK - buf not freed
    }
    free(buf);
}
```

```java
// Java: Retained references
class Cache {
    private Map<String, Object> cache = new HashMap<>();
    void add(String key, Object value) {
        cache.put(key, value);  // Never removed = leak
    }
}

// Event listener not removed
button.addActionListener(listener);
// Window closed but listener holds reference to window
```

```javascript
// JavaScript: Closure leak
function setup() {
    const largeData = new Array(1000000);
    element.addEventListener('click', () => {
        console.log(largeData.length);  // Closure keeps largeData alive
    });
}
```

**Detection Methods**:
- C/C++: Valgrind, AddressSanitizer, BoundsChecker
- Java: VisualVM, Eclipse MAT, JProfiler
- .NET: dotMemory, ANTS Memory Profiler
- JavaScript: Chrome DevTools Memory tab

**Prevention**:
- C++: RAII pattern, smart pointers
- GC languages: Weak references for caches
- Remove event listeners when done
- Clear collections when no longer needed

**CWE Mapping**: CWE-401 (Missing Release of Memory after Effective Lifetime)

---

### 4.3 Connection Pool Exhaustion

**Description**: All database connections in use, new requests cannot get connections.

**Common Code Patterns**:
```java
// Pattern 1: Connection leak
Connection conn = dataSource.getConnection();
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT ...");
// Exception thrown here = connection never returned!
return processResults(rs);

// Pattern 2: Holding connection too long
Connection conn = dataSource.getConnection();
callExternalService();  // 30 second timeout
// Connection held during slow external call
conn.close();
```

**Symptoms**:
- "Cannot acquire connection" errors
- Timeout waiting for connection
- Pool size at maximum for extended periods

**Prevention**:
```java
// Always use try-with-resources
try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT ...")) {
    return processResults(rs);
}  // Automatically closed even on exception

// Configure pool properly
HikariConfig config = new HikariConfig();
config.setMaximumPoolSize(10);
config.setConnectionTimeout(30000);
config.setLeakDetectionThreshold(60000);  // Detect leaks
```

**Detection Methods**:
- HikariCP leak detection
- Pool metrics monitoring
- APM tools showing connection wait times

---

### 4.4 Thundering Herd / Cache Stampede

**Description**: Multiple clients simultaneously regenerate cached data when it expires.

**The Problem**:
```
Cache expires for popular key
  -> 1000 concurrent requests find cache empty
  -> 1000 identical database queries execute
  -> Database overwhelmed
  -> Cascade failure
```

**Detection**:
- Spikes in DB queries aligned with cache TTL
- Sawtooth latency patterns
- High p99 latency with normal p50

**Solutions**:

```python
# 1. TTL Jitter - Stagger expirations
import random
ttl = base_ttl + random.randint(-60, 60)  # Add randomness

# 2. Locking - Single writer
def get_with_lock(key):
    value = cache.get(key)
    if value is None:
        lock = cache.lock(f"lock:{key}", timeout=10)
        if lock.acquire():
            try:
                value = cache.get(key)  # Double-check
                if value is None:
                    value = expensive_compute()
                    cache.set(key, value, ttl=300)
            finally:
                lock.release()
        else:
            # Another process is computing, wait and retry
            time.sleep(0.1)
            return get_with_lock(key)
    return value

# 3. Stale-While-Revalidate
def get_with_stale(key):
    value, expiry = cache.get_with_meta(key)
    if time.time() > expiry:
        # Serve stale, refresh in background
        background_refresh(key)
    return value
```

**Additional Techniques**:
- Probabilistic early expiration
- Hot key splitting across cache nodes
- Circuit breakers and rate limiting

---

### 4.5 Algorithmic Complexity Attacks (Hash Collision DoS)

**Description**: Attackers craft inputs that trigger worst-case O(n^2) behavior in hash tables.

**The Attack**:
```
Normal hash table: O(1) lookup
With collision attack: O(n) lookup per item
Inserting n items: O(n^2) total
```

**Vulnerable Code**:
```python
# Web framework parsing POST parameters
# Attacker sends thousands of parameters with colliding hashes
@app.route('/submit', methods=['POST'])
def submit():
    data = request.form  # Parsing triggers O(n^2) behavior
```

**Affected Systems**:
- PHP, Python, Java, Ruby web frameworks (pre-2012 patches)
- Any hash table with predictable hash function
- QUIC protocol implementations (discovered 2022)

**Prevention**:
- Use keyed hash functions (SipHash)
- Randomize hash seeds per process
- Limit POST parameter count
- Use sorted data structures for untrusted input

**Real-World Example**: 2011 HashDoS attack affected most web frameworks globally

**CWE Mapping**: Related to CWE-400 (Uncontrolled Resource Consumption)

---

### 4.6 Catastrophic Regex Backtracking (ReDoS)

**Description**: Regex patterns that cause exponential backtracking with crafted input.

**Dangerous Patterns**:
```regex
# Nested quantifiers
(a+)+
(a*)*
(a|aa)+

# Overlapping alternatives
(a|a)+
.*.*

# Real vulnerable pattern (Cloudflare 2019)
.*(?:.*=.*)
```

**Attack Example**:
```python
import re
# Evil regex with nested quantifiers
pattern = re.compile(r'(a+)+$')
# Malicious input
evil_input = 'a' * 30 + 'X'
pattern.match(evil_input)  # Takes exponential time
```

**Prevention**:
- Use RE2 or Rust regex (guaranteed linear time)
- Avoid nested quantifiers
- Set regex timeout limits
- Test with ReDoS checkers

**Detection**:
- Static analysis: ReDoS pattern detection
- Fuzzing: Generate pathological inputs
- Runtime: Monitor regex execution time

**Real-World Example**:
- **Cloudflare July 2, 2019**: 27-minute global outage from single regex in WAF
- Pattern `.*(?:.*=.*)` caused CPU exhaustion across all edge servers

---

### 4.7 Unbounded Loops

**Description**: Loops without proper termination conditions or iteration limits.

**Common Code Patterns**:
```python
# Pattern 1: While-true without break
while True:
    data = fetch_next()
    process(data)
    # Missing break condition

# Pattern 2: Iterator that never ends
def bad_generator():
    while True:
        yield compute_value()

for item in bad_generator():  # Never terminates
    process(item)

# Pattern 3: Retry without limit
def fetch_with_retry():
    while True:
        try:
            return http_get(url)
        except:
            time.sleep(1)  # Retries forever
```

**Prevention**:
```python
# Always have exit conditions
MAX_ITERATIONS = 1000
for i, item in enumerate(generator()):
    if i >= MAX_ITERATIONS:
        raise Exception("Too many iterations")
    process(item)

# Retry with limit
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        return http_get(url)
    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            raise
        time.sleep(2 ** attempt)  # Exponential backoff
```

**CWE Mapping**: CWE-835 (Loop with Unreachable Exit Condition)

---

## Famous Incidents Summary

| Incident | Year | Category | Root Cause | Impact |
|----------|------|----------|------------|--------|
| Ariane 5 Explosion | 1996 | Crash | Integer overflow (64-bit to 16-bit) | $370M loss |
| Mars Climate Orbiter | 1999 | Data Loss | Unit conversion error (metric/imperial) | $125M loss |
| Therac-25 Deaths | 1985-87 | Race Condition | Race condition in safety checks | 6 deaths/injuries |
| Northeast Blackout | 2003 | Crash | Race condition + alarm failure | 55M without power |
| Knight Capital | 2012 | Data Loss | Old test code deployed | $440M loss in 45 min |
| Cloudflare Outage | 2019 | Performance | Regex catastrophic backtracking | 27 min global outage |
| CrowdStrike Outage | 2024 | Crash | Bad update to Windows systems | $3B+ losses, 72hr downtime |
| Boeing 737 MAX | 2018-19 | Crash | MCAS software relying on single sensor | 346 deaths |

---

## Detection Tools Summary

| Category | Tool | Languages | Detection Type |
|----------|------|-----------|----------------|
| Memory Safety | Valgrind | C/C++ | Runtime |
| Memory Safety | AddressSanitizer | C/C++/Go | Runtime |
| Memory Safety | Coverity | C/C++/Java | Static |
| Race Conditions | RacerD | Java/C++/ObjC | Static |
| Race Conditions | ThreadSanitizer | C/C++/Go | Runtime |
| Race Conditions | RacerX | C | Static |
| Deadlocks | Polyspace | C/C++ | Static |
| General | SonarQube | Multi-language | Static |
| General | FindBugs/SpotBugs | Java | Static |
| Regex | ReDoS checkers | Multi-language | Static |
| N+1 Queries | Sentry Performance | Multi-language | Runtime |
| Memory Leaks | VisualVM | Java | Runtime |
| Memory Leaks | dotMemory | .NET | Runtime |

---

## Quick Reference: CWE Mappings

| CWE ID | Name | Category |
|--------|------|----------|
| CWE-120 | Classic Buffer Overflow | Crash/Data Loss |
| CWE-121 | Stack-based Buffer Overflow | Crash |
| CWE-362 | Race Condition | Data Loss |
| CWE-366 | Race Condition within Thread | Data Loss |
| CWE-367 | TOCTOU Race Condition | Data Loss |
| CWE-401 | Missing Release of Memory | Performance |
| CWE-415 | Double Free | Crash |
| CWE-416 | Use After Free | Crash |
| CWE-476 | NULL Pointer Dereference | Crash |
| CWE-479 | Signal Handler Non-reentrant | Crash |
| CWE-617 | Reachable Assertion | Crash |
| CWE-667 | Improper Locking | Deadlock |
| CWE-674 | Uncontrolled Recursion | Crash |
| CWE-787 | Out-of-bounds Write | Data Loss |
| CWE-833 | Deadlock | Deadlock |
| CWE-835 | Unreachable Loop Exit | Performance |

---

## Sources

### Crash Patterns
- [CWE-476: NULL Pointer Dereference](https://cwe.mitre.org/data/definitions/476.html)
- [CWE-121: Stack-based Buffer Overflow](https://cwe.mitre.org/data/definitions/121.html)
- [CWE-415: Double Free](https://cwe.mitre.org/data/definitions/415.html)
- [CWE-416: Use After Free](https://cwe.mitre.org/data/definitions/416.html)
- [CWE-617: Reachable Assertion](https://cwe.mitre.org/data/definitions/617.html)
- [CWE-674: Uncontrolled Recursion](https://cwe.mitre.org/data/definitions/674.html)
- [CWE-479: Signal Handler Use of Non-reentrant Function](https://cwe.mitre.org/data/definitions/479.html)
- [Sternum IoT: Double Free and Use-After-Free](https://sternumiot.com/iot-blog/double-free-and-use-after-free-common-security-weaknesses-iot/)
- [OWASP: Buffer Overflow](https://owasp.org/www-community/vulnerabilities/Buffer_Overflow)

### Data Loss Patterns
- [CWE-362: Race Condition](https://cwe.mitre.org/data/definitions/362.html)
- [CWE-367: TOCTOU Race Condition](https://cwe.mitre.org/data/definitions/367.html)
- [CWE-787: Out-of-bounds Write](https://cwe.mitre.org/data/definitions/787.html)
- [Wikipedia: ACID](https://en.wikipedia.org/wiki/ACID)
- [GeeksforGeeks: ACID Properties in DBMS](https://www.geeksforgeeks.org/dbms/acid-properties-in-dbms/)
- [DevTo: Database Crash Recovery](https://dev.to/itxsahil/what-happens-when-a-database-crashes-mid-transaction-understanding-recovery-and-data-integrity-4090)

### Deadlock Patterns
- [CWE-833: Deadlock](https://cwe.mitre.org/data/definitions/833.html)
- [CWE-667: Improper Locking](https://cwe.mitre.org/data/definitions/667.html)
- [Microsoft Learn: Debug ThreadPool Starvation](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/debug-threadpool-starvation)
- [Oracle: Database Deadlock Detection](https://docs.oracle.com/cd/E17275_01/html/programmer_reference/lock_dead.html)

### Performance Patterns
- [Sentry: N+1 Queries](https://docs.sentry.io/product/issues/issue-details/performance-issues/n-one-queries/)
- [CWE-401: Missing Release of Memory](https://cwe.mitre.org/data/definitions/401.html)
- [Wikipedia: Thundering Herd Problem](https://en.wikipedia.org/wiki/Thundering_herd_problem)
- [Wikipedia: Cache Stampede](https://en.wikipedia.org/wiki/Cache_stampede)
- [Connection Pool Exhaustion: The Silent Killer](https://howtech.substack.com/p/connection-pool-exhaustion-the-silent)
- [CWE-120: Classic Buffer Overflow](https://cwe.mitre.org/data/definitions/120.html)

### Algorithmic Complexity
- [Denial of Service via Algorithmic Complexity Attacks (PDF)](https://www.cs.auckland.ac.nz/~mcw/Teaching/refs/misc/denial-of-service.pdf)
- [LWN: Denial of Service via Hash Collisions](https://lwn.net/Articles/474912/)
- [NCC Group: Hash DoS in QUIC](https://www.nccgroup.com/research-blog/technical-advisory-hash-denial-of-service-attack-in-multiple-quic-implementations/)

### Detection Tools
- [RacerD - Facebook Infer](https://fbinfer.com/docs/checker-racerd/)
- [Microsoft Learn: Concurrency Tools](https://learn.microsoft.com/en-us/archive/msdn-magazine/2008/june/tools-and-techniques-to-identify-concurrency-issues)
- [ResearchGate: Static Analysis for Concurrency](https://www.researchgate.net/publication/48872915_Comparing_Four_Static_Analysis_Tools_for_Java_Concurrency_Bugs)

### Famous Incidents
- [Raygun: 11 Costly Software Errors](https://raygun.com/blog/costly-software-errors-history/)
- [Embedded Artistry: Historical Software Accidents](https://embeddedartistry.com/fieldatlas/historical-software-accidents-and-errors/)
- [Cloudflare: July 2, 2019 Outage Details](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/)
- [Pingdom: 10 Historical Software Bugs](https://www.pingdom.com/blog/10-historical-software-bugs-with-extreme-consequences/)
- [Wikipedia: List of Software Bugs](https://en.wikipedia.org/wiki/List_of_software_bugs)
