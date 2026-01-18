# Extended False Negative Analysis Report

Analysis of all security scanners beyond Fase 39.


## Memory Safety (CWE-119, CWE-416, CWE-190)


**5 false negative(s) found:**


### strncat improper size


**CWE:** CWE-119


**Description:** strncat with wrong size calculation still overflows


**Expected Rules:** MS001, MS004


**Detected Rules:** None


**Vulnerable Code (strncat.c):**

```c
char dest[10] = "Hello";
void concat(const char *src) {
    strncat(dest, src, sizeof(dest));  // Wrong! Should be sizeof(dest)-strlen(dest)-1
}
```


### realloc without null check


**CWE:** CWE-416


**Description:** realloc failure loses original pointer


**Expected Rules:** MS005


**Detected Rules:** MS008


**Vulnerable Code (realloc.c):**

```c
void resize(char **buf, size_t newsize) {
    *buf = realloc(*buf, newsize);  // If realloc fails, original is leaked
    if (*buf == NULL) return;
}
```


### Array decay sizeof


**CWE:** CWE-119


**Description:** sizeof on pointer gives wrong size


**Expected Rules:** MS004


**Detected Rules:** None


**Vulnerable Code (sizeof.c):**

```c
void process(char *buf) {
    char local[100];
    memcpy(local, buf, sizeof(buf));  // sizeof(buf) is 8, not buffer size
}
```


### snprintf truncation unchecked


**CWE:** CWE-119


**Description:** snprintf return value not checked for truncation


**Expected Rules:** MS001


**Detected Rules:** None


**Vulnerable Code (snprintf.c):**

```c
void format(char *dest, size_t size, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(dest, size, fmt, args);  // Truncation silently ignored
    va_end(args);
}
```


### Integer underflow in size calc


**CWE:** CWE-190


**Description:** Subtraction can underflow to huge value


**Expected Rules:** MS008


**Detected Rules:** None


**Vulnerable Code (underflow.c):**

```c
void copy_data(char *dest, size_t dest_size, char *src, size_t header_size) {
    size_t data_size = dest_size - header_size;  // Underflow if header_size > dest_size
    memcpy(dest, src, data_size);
}
```


## Concurrency (CWE-362, CWE-367, CWE-833)


**5 false negative(s) found:**


### Check-then-act race


**CWE:** CWE-362


**Description:** Check and modify without atomicity


**Expected Rules:** CC001, CC008


**Detected Rules:** None


**Vulnerable Code (check_act.py):**

```py
import threading

counter = 0
def increment():
    global counter
    if counter < 100:  # Check
        counter += 1   # Act - race between check and act
```


### Broken double-checked locking


**CWE:** CWE-362


**Description:** Classic broken double-checked locking pattern


**Expected Rules:** CC001, CC007


**Detected Rules:** None


**Vulnerable Code (dcl.java):**

```java
public class Singleton {
    private static Singleton instance;

    public static Singleton getInstance() {
        if (instance == null) {  // First check
            synchronized(Singleton.class) {
                if (instance == null) {  // Second check
                    instance = new Singleton();  // Can be reordered!
                }
            }
        }
        return instance;
    }
}
```


### asyncio shared state


**CWE:** CWE-362


**Description:** Asyncio coroutines sharing mutable state


**Expected Rules:** CC001


**Detected Rules:** None


**Vulnerable Code (async_race.py):**

```py
import asyncio

shared_list = []

async def producer():
    for i in range(100):
        shared_list.append(i)  # Not thread-safe in asyncio with threads

async def consumer():
    while len(shared_list) > 0:
        shared_list.pop()  # Race condition
```


### Goroutine closure capture


**CWE:** CWE-362


**Description:** Go closure captures loop variable by reference


**Expected Rules:** CC001


**Detected Rules:** None


**Vulnerable Code (closure.go):**

```go
package main

func main() {
    for i := 0; i < 10; i++ {
        go func() {
            println(i)  // Captures i by reference, race condition
        }()
    }
}
```


### Non-atomic increment


**CWE:** CWE-362


**Description:** Increment is not atomic operation


**Expected Rules:** CC001, CC008


**Detected Rules:** None


**Vulnerable Code (nonatomic.cpp):**

```cpp
#include <thread>

int counter = 0;

void increment() {
    for (int i = 0; i < 1000; i++) {
        counter++;  // Read-modify-write is not atomic
    }
}
```


## Crypto (CWE-327, CWE-328, CWE-321, CWE-798)


**5 false negative(s) found:**


### Base64 as encryption


**CWE:** CWE-327


**Description:** Base64 encoding used thinking it's encryption


**Expected Rules:** CR006


**Detected Rules:** None


**Vulnerable Code (base64_crypto.py):**

```py
import base64

def encrypt_password(password):
    return base64.b64encode(password.encode()).decode()  # NOT encryption!

def decrypt_password(encoded):
    return base64.b64decode(encoded).decode()
```


### XOR cipher


**CWE:** CWE-327


**Description:** Simple XOR used for 'encryption'


**Expected Rules:** CR006


**Detected Rules:** None


**Vulnerable Code (xor.py):**

```py
def xor_encrypt(data, key):
    return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
```


### AES-CBC without authentication


**CWE:** CWE-327


**Description:** CBC mode without MAC is vulnerable to padding oracle


**Expected Rules:** CR007


**Detected Rules:** None


**Vulnerable Code (cbc.py):**

```py
from Crypto.Cipher import AES

def encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_CBC)
    return cipher.iv + cipher.encrypt(pad(plaintext))
```


### Static IV in encryption


**CWE:** CWE-329


**Description:** Using constant IV defeats encryption


**Expected Rules:** CR007, CR008


**Detected Rules:** None


**Vulnerable Code (static_iv.py):**

```py
from Crypto.Cipher import AES

IV = b'0000000000000000'  # Static IV!

def encrypt(key, plaintext):
    cipher = AES.new(key, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(plaintext))
```


### bcrypt low cost factor


**CWE:** CWE-916


**Description:** bcrypt with cost < 10 is too fast


**Expected Rules:** CR009


**Detected Rules:** None


**Vulnerable Code (bcrypt.py):**

```py
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4))  # Too low!
```


## Control Flow (CWE-193, CWE-481, CWE-484, CWE-835)


**4 false negative(s) found:**


### Side effect in loop condition


**CWE:** CWE-835


**Description:** Function call in loop condition may cause infinite loop


**Expected Rules:** CF002


**Detected Rules:** None


**Vulnerable Code (side_effect.js):**

```js
function process(items) {
    while (items.pop()) {  // Relies on truthiness, may loop forever with 0
        console.log("processing");
    }
}
```


### Unreachable code


**CWE:** CWE-561


**Description:** Code after return is never executed


**Expected Rules:** CF021


**Detected Rules:** None


**Vulnerable Code (unreachable.js):**

```js
function calculate(x) {
    return x * 2;
    console.log("This never runs");  // Dead code
    return x * 3;
}
```


### Nested ternary operators


**CWE:** CWE-783


**Description:** Nested ternary is hard to read and error-prone


**Expected Rules:** CF011


**Detected Rules:** None


**Vulnerable Code (ternary.js):**

```js
function getValue(a, b, c) {
    return a > 0 ? b > 0 ? b : c : c > 0 ? c : 0;  // What does this even do?
}
```


### Empty exception handler


**CWE:** CWE-390


**Description:** Exception caught but not handled


**Expected Rules:** CF030


**Detected Rules:** CF032


**Vulnerable Code (swallow.py):**

```py
def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except Exception:
        pass  # Silently swallows ALL exceptions
```


## Boolean Logic (CWE-480, CWE-783, CWE-843)


**5 false negative(s) found:**


### Always false condition


**CWE:** CWE-570


**Description:** Condition that is always false


**Expected Rules:** BL030


**Detected Rules:** None


**Vulnerable Code (always_false.js):**

```js
function check(x) {
    if (x > 10 && x < 5) {  // Impossible condition
        console.log("Never reached");
    }
}
```


### Null check after use


**CWE:** CWE-476


**Description:** Object used before null check


**Expected Rules:** BL040


**Detected Rules:** None


**Vulnerable Code (null_check.java):**

```java
public void process(String s) {
    int len = s.length();  // Dereference
    if (s != null) {       // Null check after use!
        System.out.println(len);
    }
}
```


### Boolean assignment


**CWE:** CWE-480


**Description:** Assigning boolean instead of comparing


**Expected Rules:** BL001


**Detected Rules:** None


**Vulnerable Code (bool_assign.py):**

```py
def is_valid(x):
    valid = True
    if valid = False:  # Assignment! Not comparison (Python won't allow this actually)
        return False
```


### Incorrect De Morgan


**CWE:** CWE-480


**Description:** Incorrect negation of compound condition


**Expected Rules:** BL010


**Detected Rules:** None


**Vulnerable Code (demorgan.js):**

```js
function check(a, b) {
    // Wrong: !(a && b) should be (!a || !b), not (!a && !b)
    if (!a && !b) {  // May be incorrect depending on intent
        console.log("neither");
    }
}
```


### Yoda condition hiding error


**CWE:** CWE-480


**Description:** Yoda style can hide assignment bugs


**Expected Rules:** BL001


**Detected Rules:** None


**Vulnerable Code (yoda.c):**

```c
void check(int x) {
    if (NULL = ptr) {  // Assignment to NULL, always false
        process(ptr);
    }
}
```


## Generic Security (CWE-337, CWE-602, CWE-208)


**4 false negative(s) found:**


### UUID as security token


**CWE:** CWE-330


**Description:** UUID v1/v4 used as security token


**Expected Rules:** GEN-CWE-337-001


**Detected Rules:** None


**Vulnerable Code (uuid_token.py):**

```py
import uuid

def generate_reset_token():
    return str(uuid.uuid4())  # UUID4 is not cryptographically secure for tokens
```


### Auth check continues


**CWE:** CWE-602


**Description:** Authentication failure doesn't stop execution


**Expected Rules:** GEN-CWE-602-001


**Detected Rules:** None


**Vulnerable Code (auth.py):**

```py
def admin_page(request):
    if not request.user.is_admin:
        flash("Not authorized")  # Warning shown but execution continues!

    return render_admin_dashboard()  # Executed even for non-admins
```


### Permission check logs only


**CWE:** CWE-602


**Description:** Permission failure only logs, doesn't block


**Expected Rules:** GEN-CWE-602-001


**Detected Rules:** None


**Vulnerable Code (perm.java):**

```java
public void deleteUser(User actor, User target) {
    if (!actor.hasPermission("delete_users")) {
        logger.warn("Unauthorized delete attempt by " + actor.getId());
    }

    userRepository.delete(target);  // Executed anyway!
}
```


### Timing attack vulnerable


**CWE:** CWE-208


**Description:** String comparison leaks password length


**Expected Rules:** GEN-CWE-208-001


**Detected Rules:** None


**Vulnerable Code (timing.py):**

```py
def verify_password(input_password, stored_password):
    return input_password == stored_password  # Timing attack vulnerable
```


---

## Summary


**Total False Negatives Found:** 28


- Memory Safety (CWE-119, CWE-416, CWE-190): ❌ 5

- Concurrency (CWE-362, CWE-367, CWE-833): ❌ 5

- Crypto (CWE-327, CWE-328, CWE-321, CWE-798): ❌ 5

- Control Flow (CWE-193, CWE-481, CWE-484, CWE-835): ❌ 4

- Boolean Logic (CWE-480, CWE-783, CWE-843): ❌ 5

- Generic Security (CWE-337, CWE-602, CWE-208): ❌ 4
