# Control Flow Errors Reference Guide

## Static Analysis Detection Rules for Syntactically Correct but Logically Wrong Code

This document catalogs common logical errors in control flow statements that compile successfully but produce incorrect behavior. Each error includes multi-language examples, detection strategies, CWE mappings, and historical context.

---

# 1. LOOP ERRORS

## 1.1 Off-by-One Errors (Fencepost Errors)

**CWE-193: Off-by-one Error**

### Description
An off-by-one error occurs when a loop iterates one time too many or too few, typically due to incorrect boundary conditions. The name comes from the fencepost problem: "If you build a fence 100 feet long with posts 10 feet apart, how many posts do you need?" (The answer is 11, not 10.)

### Code Examples

**C:**
```c
// BUG: Iterates 9 times instead of 10 (excludes upper bound)
int arr[10];
for (int i = 0; i < 10; i++) {
    arr[i] = i;  // Correct: 0-9
}

// BUG: Buffer overflow - writes past array end
for (int i = 0; i <= 10; i++) {  // Should be i < 10
    arr[i] = i;  // OVERFLOW at i=10
}

// BUG: strncat off-by-one (classic vulnerability)
char dest[10] = "hello";
char src[] = "world";
strncat(dest, src, sizeof(dest) - strlen(dest));  // Off by one!
// strncat writes null terminator BEYOND the specified length
```

**Java:**
```java
// BUG: Skips first element
int[] arr = new int[10];
for (int i = 1; i < arr.length; i++) {  // Should start at 0
    process(arr[i]);
}

// BUG: Skips last element
for (int i = 0; i < arr.length - 1; i++) {  // Should be i < arr.length
    process(arr[i]);
}

// BUG: String substring off-by-one
String s = "hello";
String sub = s.substring(0, s.length() - 1);  // Gets "hell" not "hello"
```

**Python:**
```python
# BUG: Range excludes endpoint (common confusion)
arr = [1, 2, 3, 4, 5]
for i in range(1, 5):  # Iterates 1,2,3,4 - misses index 0 and includes wrong end
    print(arr[i])

# BUG: Off-by-one in slice
data = [1, 2, 3, 4, 5]
subset = data[1:4]  # Gets [2, 3, 4], not [2, 3, 4, 5]

# CORRECT patterns:
for i in range(len(arr)):      # 0 to len-1
for i in range(1, len(arr)):   # 1 to len-1
```

**JavaScript:**
```javascript
// BUG: Iterates one too many times
const arr = [1, 2, 3, 4, 5];
for (let i = 0; i <= arr.length; i++) {  // Should be i < arr.length
    console.log(arr[i]);  // arr[5] is undefined
}

// BUG: Wrong boundary in binary search
function binarySearch(arr, target) {
    let left = 0;
    let right = arr.length;  // Should be arr.length - 1
    while (left < right) {   // May access arr[arr.length]
        // ...
    }
}
```

### Why It Compiles
- Array indices are not validated at compile time in C/C++
- Loop conditions are syntactically valid regardless of semantic correctness
- The compiler cannot infer the programmer's intent

### Detection Strategies
1. **Static Analysis**: Check loop bounds against array declarations
2. **Pattern Matching**: Flag `<= array.length` patterns (should usually be `<`)
3. **Symbolic Execution**: Track array bounds through execution paths
4. **Runtime Instrumentation**: AddressSanitizer, Valgrind

### Famous Bugs
- **CVE-2021-3156 (Baron Samedit)**: Off-by-one in sudo's argument parsing led to heap-based buffer overflow allowing root privilege escalation
- **OpenSSL Heartbleed** (related): Buffer over-read due to missing bounds check
- **Julian Calendar Leap Year**: Original calculation used inclusive counting, causing leap years every 3 years instead of 4

---

## 1.2 Infinite Loops

**CWE-835: Loop with Unreachable Exit Condition**

### Description
Infinite loops occur when the loop's termination condition can never be satisfied, causing the program to hang indefinitely.

### Code Examples

**C:**
```c
// BUG: Missing increment
int i = 0;
while (i < 10) {
    printf("%d\n", i);
    // MISSING: i++;
}

// BUG: Wrong variable incremented
int i = 0, j = 0;
while (i < 10) {
    printf("%d\n", i);
    j++;  // Should be i++
}

// BUG: Unsigned integer wrap-around
unsigned int i = 10;
while (i >= 0) {  // ALWAYS TRUE for unsigned!
    printf("%d\n", i);
    i--;
}

// BUG: Assignment instead of comparison
int x = 0;
while (x = 1) {  // Always assigns 1, which is truthy
    // Infinite loop
}
```

**Java:**
```java
// BUG: Condition always true
int count = 0;
while (count != 10) {
    if (count % 2 == 0) {
        count += 2;  // Only increments by 2, skips 10 if starting odd
    }
}

// BUG: Float comparison (may never equal exactly)
for (float f = 0.0f; f != 1.0f; f += 0.1f) {
    // May never terminate due to floating-point precision
}

// BUG: Modifying wrong variable
int i = 0;
int limit = 10;
while (i < limit) {
    limit++;  // Wrong! Should modify i
    process(i);
}
```

**Python:**
```python
# BUG: Condition never changes
x = 5
while x > 0:
    print(x)
    # MISSING: x -= 1

# BUG: Wrong comparison operator
count = 0
while count > -1:  # Always true for incrementing counter
    count += 1

# BUG: Boolean always True
running = True
while running:
    process()
    # MISSING: running = check_stop_condition()
```

**JavaScript:**
```javascript
// BUG: Missing update in for loop
for (let i = 0; i < 10; ) {  // Missing i++
    console.log(i);
}

// BUG: Decrementing when should increment
for (let i = 0; i < 10; i--) {  // Will never reach 10
    console.log(i);
}

// BUG: Typo in condition variable
let index = 0;
let indx = 0;
while (indx < 10) {  // Checks wrong variable
    index++;  // Increments different variable
}
```

### Why It Compiles
- Loop conditions are syntactically valid expressions
- The compiler cannot determine if conditions are satisfiable
- Missing statements are not syntax errors

### Detection Strategies
1. **Data Flow Analysis**: Track which variables are modified in loop body
2. **Pattern Matching**: Flag loops where condition variables aren't modified
3. **Abstract Interpretation**: Determine if exit condition is reachable
4. **Loop Variant Analysis**: Check if loop has a valid termination measure

---

## 1.3 Empty Loop Body (Semicolon After For/While)

**CWE-561: Dead Code (related)**

### Description
A semicolon immediately after a loop declaration creates an empty loop body, causing the actual intended body to execute only once (or infinite loop for while).

### Code Examples

**C:**
```c
// BUG: Semicolon creates empty body
for (int i = 0; i < 10; i++);  // Empty loop!
{
    printf("%d\n", i);  // Only executes once, i is now 10
}

// BUG: While with empty body (infinite loop if condition true)
int i = 0;
while (i < 10);  // INFINITE LOOP - semicolon is the body
{
    printf("%d\n", i);  // Never reached
    i++;
}

// BUG: Looks intentional but probably isn't
for (int i = 0; i < n; i++);
    array[i] = 0;  // Only sets array[n], not 0..n-1
```

**Java:**
```java
// BUG: Empty for loop body
for (int i = 0; i < 5; i++);  // Semicolon terminates loop
System.out.println("Done");   // Only prints once

// BUG: Empty while loop
int sum = 0;
int i = 0;
while (i < 10);  // INFINITE LOOP!
{
    sum += i;
    i++;
}

// BUG: Do-while with misplaced semicolon
int count = 0;
do;  // Empty body
{
    count++;
} while (count < 10);  // Never executes block
```

**Python:**
```python
# Python doesn't have this exact issue due to significant whitespace
# But similar issues exist:

# BUG: Pass statement when code was intended
for i in range(10):
    pass  # Probably forgot to add loop body
print("Done")

# BUG: Colon on wrong line (SyntaxError in Python, but conceptually similar)
```

**JavaScript:**
```javascript
// BUG: Empty for loop
for (let i = 0; i < 10; i++);  // Empty body!
console.log("Executed once");

// BUG: Empty while loop (infinite)
let i = 0;
while (i < 10);  // HANGS FOREVER
{
    console.log(i);
    i++;
}

// BUG: Empty do-while
let count = 0;
do;  // Empty body executed once
while (count++ < 10);  // Just increments count
```

### Why It Compiles
- A semicolon alone is a valid "null statement" in C-family languages
- The syntax `for(...);` is legal (empty body)
- Indentation has no semantic meaning in C/Java/JavaScript

### Detection Strategies
1. **AST Analysis**: Check for EmptyStatement as loop body
2. **Whitespace Analysis**: Flag semicolons immediately after loop headers
3. **Warning Flags**: GCC `-Wempty-body`, Clang `-Wempty-body`
4. **Code Style Enforcement**: Require braces for all loop bodies

---

## 1.4 Loop Variable Modification Inside Loop

**CWE-369: Divide By Zero (potential consequence)**

### Description
Modifying the loop counter inside the loop body can lead to unexpected iteration counts, infinite loops, or skipped elements.

### Code Examples

**C:**
```c
// BUG: Loop counter modified in body
for (int i = 0; i < 10; i++) {
    if (condition) {
        i++;  // Skip next iteration - often unintended
    }
    process(i);
}

// BUG: Decrementing counter in increment loop
for (int i = 0; i < n; i++) {
    if (array[i] == target) {
        i--;  // Go back one - may cause infinite loop
    }
}

// BUG: Assignment instead of comparison
for (int i = 0; i < 10; i++) {
    if (i = 5) {  // Always true, sets i to 5 repeatedly
        // Infinite loop!
    }
}
```

**Java:**
```java
// BUG: Modifying for-each loop variable (no effect on iteration)
int[] arr = {1, 2, 3, 4, 5};
for (int num : arr) {
    num = num * 2;  // Has no effect on array!
}
// arr is still {1, 2, 3, 4, 5}

// BUG: Index manipulation in traditional loop
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
for (int i = 0; i < list.size(); i++) {
    list.remove(i);  // Modifies list, skips elements!
}
// Result: {"b"} - not empty as expected
```

**Python:**
```python
# BUG: Modifying loop variable in for loop (resets each iteration)
for i in range(10):
    i += 5  # Has no effect on iteration!
    print(i)  # Prints 5,6,7,8,9,10,11,12,13,14

# BUG: Modifying list while iterating
items = [1, 2, 3, 4, 5]
for item in items:
    if item % 2 == 0:
        items.remove(item)  # Skips elements!
# Result: [1, 3, 5] - works by accident, not by design
```

**JavaScript:**
```javascript
// BUG: Modifying array during iteration
const arr = [1, 2, 3, 4, 5];
for (let i = 0; i < arr.length; i++) {
    if (arr[i] % 2 === 0) {
        arr.splice(i, 1);  // Shifts array, skips next element
    }
}
// arr is [1, 3, 5] but process was inconsistent

// BUG: Incrementing i twice
for (let i = 0; i < 10; i++) {
    if (someCondition) {
        i++;  // Skips an iteration
    }
    process(arr[i]);
}
```

### Why It Compiles
- Loop variables are just regular variables that can be modified
- The compiler doesn't enforce immutability of loop counters
- Iterator invalidation is a runtime concern

### Detection Strategies
1. **Data Flow Analysis**: Flag writes to loop counter inside body
2. **Pattern Matching**: Detect assignment to for-each variables
3. **Collection Modification Detection**: Track collection mutations during iteration

---

## 1.5 Wrong Loop Bounds

**CWE-119: Improper Restriction of Operations within the Bounds of a Memory Buffer**

### Description
Using incorrect bounds in loop conditions leads to under-processing (missing elements) or over-processing (buffer overflows, undefined behavior).

### Code Examples

**C:**
```c
// BUG: Hardcoded bound doesn't match array
int arr[5];
for (int i = 0; i < 10; i++) {  // Buffer overflow!
    arr[i] = i;
}

// BUG: Wrong sizeof calculation
int arr[10];
for (int i = 0; i < sizeof(arr); i++) {  // 40 iterations, not 10!
    arr[i] = 0;  // Writes past end
}
// CORRECT: sizeof(arr) / sizeof(arr[0])

// BUG: Using wrong length variable
void process(int* arr, int len) {
    int local_len = 5;
    for (int i = 0; i < local_len; i++) {  // Should use len
        arr[i] = 0;
    }
}
```

**Java:**
```java
// BUG: Off-by-one in nested array
int[][] matrix = new int[3][4];
for (int i = 0; i < matrix.length; i++) {
    for (int j = 0; j < matrix.length; j++) {  // Should be matrix[i].length
        matrix[i][j] = 0;  // Only fills 3x3, misses column
    }
}

// BUG: Using wrong collection's size
List<String> list1 = getList1();
List<String> list2 = getList2();
for (int i = 0; i < list1.size(); i++) {
    process(list2.get(i));  // IndexOutOfBoundsException if list2 smaller
}
```

**Python:**
```python
# BUG: Hardcoded range doesn't match data
data = get_data()  # Returns variable-length list
for i in range(100):  # Should be range(len(data))
    print(data[i])  # IndexError if data has fewer elements

# BUG: Wrong dimension in nested loop
matrix = [[1, 2, 3], [4, 5, 6]]
for i in range(len(matrix)):
    for j in range(len(matrix)):  # Should be len(matrix[i])
        print(matrix[i][j])  # IndexError: matrix[1][2] ok, but stops at 2
```

**JavaScript:**
```javascript
// BUG: Magic number instead of array length
const data = getData();
for (let i = 0; i < 100; i++) {  // Should be data.length
    process(data[i]);  // undefined if fewer elements
}

// BUG: Caching length that changes
const arr = [1, 2, 3, 4, 5];
const len = arr.length;
for (let i = 0; i < len; i++) {
    if (arr[i] % 2 === 0) {
        arr.push(arr[i] * 2);  // Array grows, len doesn't update
    }
}
```

### Detection Strategies
1. **Symbolic Bounds Checking**: Compare loop bounds with array declarations
2. **Type Analysis**: Detect sizeof misuse on pointers vs arrays
3. **Correlation Analysis**: Match loop variable with array access variable

---

## 1.6 Break/Continue Misuse

**Related to CWE-670: Always-Incorrect Control Flow Implementation**

### Description
`break` and `continue` only affect the innermost loop. Developers often mistakenly expect them to affect outer loops in nested structures.

### Code Examples

**C:**
```c
// BUG: Break only exits inner loop
for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
        if (found) {
            break;  // Only exits inner loop, outer continues
        }
    }
    // Execution continues here after break
}

// BUG: Continue in switch inside loop
for (int i = 0; i < 10; i++) {
    switch (arr[i]) {
        case 1:
            continue;  // Actually works - continues the for loop
            break;     // This break is never reached
        case 2:
            break;     // Only exits switch, not loop!
    }
    process(i);  // Still executes for case 2
}
```

**Java:**
```java
// BUG: Break doesn't exit outer loop
outer:  // Label needed for outer break
for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
        if (matrix[i][j] == target) {
            break;  // Should be: break outer;
        }
    }
}

// BUG: Continue in wrong context
for (String line : lines) {
    lines.stream().forEach(word -> {
        if (word.isEmpty()) {
            continue;  // COMPILE ERROR: continue not in loop context
            // Lambda is not a loop body!
        }
    });
}
```

**Python:**
```python
# BUG: Break only exits inner loop
for i in range(10):
    for j in range(10):
        if found:
            break  # Only exits inner for
    # This still executes after break

# SOLUTION: Use flag or exception
found = False
for i in range(10):
    for j in range(10):
        if condition:
            found = True
            break
    if found:
        break

# Or use else clause (Pythonic but confusing):
for i in range(10):
    for j in range(10):
        if found:
            break
    else:
        continue  # Only executes if inner loop didn't break
    break
```

**JavaScript:**
```javascript
// BUG: Break in forEach (doesn't work!)
const arr = [1, 2, 3, 4, 5];
arr.forEach(item => {
    if (item === 3) {
        break;  // SyntaxError! forEach is not a loop
        return; // Only exits current callback, not iteration
    }
    console.log(item);
});
// Prints 1, 2, 4, 5 (with return), not 1, 2

// SOLUTION: Use for...of or traditional for
for (const item of arr) {
    if (item === 3) break;  // Works correctly
    console.log(item);
}

// BUG: Break in nested structure
outer: for (let i = 0; i < 10; i++) {
    switch (arr[i]) {
        case 1:
            break outer;  // Exits for loop (correct if intended)
        case 2:
            break;        // Only exits switch
    }
}
```

### Detection Strategies
1. **Control Flow Analysis**: Track break/continue targets
2. **Pattern Matching**: Flag break inside switch inside loop
3. **Lint Rules**: Warn on forEach with return

---

## 1.7 Iterator Invalidation During Loop

**CWE-416: Use After Free (related concept)**

### Description
Modifying a collection while iterating over it can invalidate iterators, causing crashes, skipped elements, or undefined behavior.

### Code Examples

**C++ (Most Severe):**
```cpp
// BUG: Iterator invalidated by erase
std::vector<int> vec = {1, 2, 3, 4, 5};
for (auto it = vec.begin(); it != vec.end(); ++it) {
    if (*it % 2 == 0) {
        vec.erase(it);  // Iterator invalidated!
        // Subsequent ++it is undefined behavior
    }
}

// CORRECT: Use return value of erase
for (auto it = vec.begin(); it != vec.end(); ) {
    if (*it % 2 == 0) {
        it = vec.erase(it);  // Returns next valid iterator
    } else {
        ++it;
    }
}

// BUG: push_back may reallocate
std::vector<int> vec = {1, 2, 3};
for (auto it = vec.begin(); it != vec.end(); ++it) {
    if (*it == 2) {
        vec.push_back(4);  // May reallocate, invalidating all iterators
    }
}
```

**Java:**
```java
// BUG: ConcurrentModificationException
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
for (String s : list) {
    if (s.equals("b")) {
        list.remove(s);  // Throws ConcurrentModificationException
    }
}

// CORRECT: Use Iterator.remove()
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (it.next().equals("b")) {
        it.remove();  // Safe removal
    }
}

// CORRECT: Use removeIf (Java 8+)
list.removeIf(s -> s.equals("b"));
```

**Python:**
```python
# BUG: Modifying list during iteration (skips elements)
items = [1, 2, 3, 4, 5, 6]
for item in items:
    if item % 2 == 0:
        items.remove(item)
# Result: [1, 3, 5] - but iteration was inconsistent

# BUG: Modifying dict during iteration
d = {'a': 1, 'b': 2, 'c': 3}
for key in d:
    if d[key] == 2:
        del d[key]  # RuntimeError: dictionary changed size

# CORRECT: Iterate over copy
for item in items[:]:  # Slice creates a copy
    if item % 2 == 0:
        items.remove(item)

# CORRECT: List comprehension
items = [item for item in items if item % 2 != 0]
```

**JavaScript:**
```javascript
// BUG: Splice shifts indices
const arr = [1, 2, 3, 4, 5];
for (let i = 0; i < arr.length; i++) {
    if (arr[i] % 2 === 0) {
        arr.splice(i, 1);  // Shifts array, skips next element
    }
}
// Expected: [1, 3, 5], but iteration is inconsistent

// CORRECT: Iterate backwards
for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] % 2 === 0) {
        arr.splice(i, 1);  // Safe - doesn't affect earlier indices
    }
}

// CORRECT: Use filter
const result = arr.filter(item => item % 2 !== 0);
```

### Detection Strategies
1. **Data Flow Analysis**: Track collection modifications within iteration scope
2. **Pattern Matching**: Flag remove/add calls on iterated collection
3. **Static Analysis Tools**: PVS-Studio V789, IntelliJ inspections

---

## 1.8 Floating-Point Loop Counters

**FLP30-C (CERT), NUM09-J (CERT)**

### Description
Using floating-point variables as loop counters leads to precision errors, causing loops to execute the wrong number of times or never terminate.

### Code Examples

**C:**
```c
// BUG: May iterate 9 or 10 times depending on platform
for (float x = 0.1f; x <= 1.0f; x += 0.1f) {
    printf("%f\n", x);
}
// 0.1 cannot be exactly represented in binary floating-point

// BUG: Infinite loop due to precision limits
for (float x = 100000001.0f; x <= 100000010.0f; x += 1.0f) {
    printf("%f\n", x);
    // Loop never terminates: 1.0 is too small to change x
}

// CORRECT: Use integer counter
for (int i = 1; i <= 10; i++) {
    float x = i * 0.1f;  // Derive float from integer
    printf("%f\n", x);
}
```

**Java:**
```java
// BUG: Imprecise iteration count
for (double d = 0.1; d <= 1.0; d += 0.1) {
    System.out.println(d);
}
// May print 9, 10, or 11 values depending on JVM

// BUG: Equality check on floats
for (float f = 0.0f; f != 1.0f; f += 0.1f) {
    // May never terminate: f might never exactly equal 1.0
}

// CORRECT: Integer counter with derived value
for (int i = 1; i <= 10; i++) {
    double value = i / 10.0;
    process(value);
}
```

**Python:**
```python
# BUG: Floating-point range issues
# Python's range() doesn't support floats, but numpy's arange does:
import numpy as np
for x in np.arange(0.1, 1.0, 0.1):
    print(x)  # May have precision issues

# BUG: Manual float loop
x = 0.0
while x < 1.0:
    print(x)
    x += 0.1
# May iterate unexpected number of times

# CORRECT: Use integer range
for i in range(10):
    x = (i + 1) / 10.0
    print(x)

# CORRECT: Use Decimal for exact arithmetic
from decimal import Decimal
x = Decimal('0.0')
while x < Decimal('1.0'):
    print(float(x))
    x += Decimal('0.1')
```

**JavaScript:**
```javascript
// BUG: Precision error in loop
for (let x = 0.1; x <= 1.0; x += 0.1) {
    console.log(x);
}
// Output varies, may not include exactly 1.0

// BUG: Comparison using equality
for (let x = 0; x !== 1; x += 0.1) {
    console.log(x);
    // May not terminate: x might be 0.9999999999999999
}

// CORRECT: Integer-based iteration
for (let i = 1; i <= 10; i++) {
    const x = i / 10;
    console.log(x);
}
```

### Why It Compiles
- Floating-point arithmetic is syntactically identical to integer arithmetic
- Compilers don't validate semantic correctness of loop conditions
- IEEE 754 floating-point is well-defined (though imprecise)

### Detection Strategies
1. **Type Analysis**: Flag floating-point types as loop counters
2. **Pattern Matching**: Detect float equality comparisons
3. **Lint Rules**: CERT FLP30-C, NUM09-J checkers

---

# 2. IF-THEN-ELSE ERRORS

## 2.1 Assignment vs Comparison (= vs ==)

**CWE-481: Assigning instead of Comparing**

### Description
Using the assignment operator `=` instead of the comparison operator `==` in a condition causes the condition to always evaluate to the assigned value's truthiness.

### Code Examples

**C:**
```c
// BUG: Assignment instead of comparison
int x = 0;
if (x = 1) {  // Always true! Assigns 1 to x, then evaluates 1 as true
    printf("Always executes\n");
}

// BUG: In while condition
while (c = getchar()) {  // May be intentional, but often a bug
    process(c);
}

// BUG: With function return
if (result = validate(input)) {  // Assigns return value, then tests it
    // Might be intentional, but unclear
}

// DEFENSIVE: Put constant on left (Yoda conditions)
if (1 = x) {  // Compile error! Catches the bug
}
if (1 == x) {  // Correct
}
```

**Java:**
```java
// SAFE: Java requires boolean in conditions
int x = 0;
if (x = 1) {  // COMPILE ERROR: incompatible types
}

// BUG: Still possible with booleans
boolean flag = false;
if (flag = true) {  // Legal! Always true, assigns true to flag
    System.out.println("Always executes");
}

// BUG: With method returning boolean
if (result = checkValid()) {  // Assigns and tests
    // Probably unintended
}
```

**Python:**
```python
# SAFE: Python 3 doesn't allow assignment in conditions
x = 0
if x = 1:  # SyntaxError: invalid syntax
    pass

# However, Python 3.8+ has walrus operator:
if (x := getValue()) > 0:  # Legal assignment expression
    process(x)

# BUG: Mutable default argument (related pattern)
if items = []:  # SyntaxError
    pass
```

**JavaScript:**
```javascript
// BUG: Assignment instead of comparison
let x = 0;
if (x = 1) {  // Always truthy! Assigns 1, evaluates as true
    console.log("Always executes");
}

// BUG: Comparison with assignment side effect
if (x = getValue()) {  // Might be intentional, but unclear
    // x is now the return value
}

// BUG: == vs === (different issue)
if (x == "1") {  // Type coercion: true if x is 1 (number)
}
if (x === "1") {  // Strict: false if x is 1 (number)
}
```

### Famous Bugs
- Countless security vulnerabilities stem from this error
- Linux kernel had several instances caught by code review

### Detection Strategies
1. **Static Analysis**: Flag assignments in condition expressions
2. **Compiler Warnings**: GCC `-Wparentheses`, MSVC C4706
3. **Yoda Conditions**: Enforce constant-on-left style
4. **ESLint**: `no-cond-assign` rule

---

## 2.2 Dangling Else Problem

**CWE-483: Incorrect Block Delimitation**

### Description
When an `else` clause could associate with multiple `if` statements, the language's resolution may not match the programmer's intent (usually indicated by indentation).

### Code Examples

**C:**
```c
// BUG: Else binds to inner if, not outer
if (x > 0)
    if (y > 0)
        printf("Both positive\n");
else  // Misleading indentation! Binds to "if (y > 0)"
    printf("x is not positive\n");  // WRONG: actually prints when y <= 0

// CORRECT: Use braces to clarify intent
if (x > 0) {
    if (y > 0) {
        printf("Both positive\n");
    }
} else {
    printf("x is not positive\n");
}

// Alternative interpretation the programmer might have wanted:
if (x > 0) {
    if (y > 0) {
        printf("Both positive\n");
    } else {
        printf("x positive, y not\n");
    }
}
```

**Java:**
```java
// BUG: Dangling else with misleading indentation
double gpa = 1.2;
if (gpa >= 1.5)
    if (gpa < 2.0)
        System.out.println("On probation");
else
    System.out.println("Failing");  // Prints when gpa >= 2.0, not when gpa < 1.5

// CORRECT: Always use braces
if (gpa >= 1.5) {
    if (gpa < 2.0) {
        System.out.println("On probation");
    }
} else {
    System.out.println("Failing");
}
```

**Python:**
```python
# SAFE: Python uses significant indentation
if x > 0:
    if y > 0:
        print("Both positive")
else:
    print("x is not positive")  # Clearly belongs to outer if

# The indentation defines the structure unambiguously
```

**JavaScript:**
```javascript
// BUG: Same issue as C/Java
if (x > 0)
    if (y > 0)
        console.log("Both positive");
else  // Binds to inner if!
    console.log("x is not positive");

// CORRECT: Use braces
if (x > 0) {
    if (y > 0) {
        console.log("Both positive");
    }
} else {
    console.log("x is not positive");
}
```

### Why It Compiles
- Languages resolve ambiguity by binding else to nearest if
- Indentation is ignored by C-family language parsers
- Both interpretations are syntactically valid

### Detection Strategies
1. **Style Enforcement**: Require braces for all if/else blocks
2. **Indentation Analysis**: Flag mismatched indentation and binding
3. **AST Analysis**: Detect else binding that contradicts formatting

---

## 2.3 Missing Braces Causing Wrong Scope

**CWE-483: Incorrect Block Delimitation**

### Description
When braces are omitted, only the first statement after an if/else is controlled by the condition. Subsequent statements execute unconditionally, regardless of indentation.

### Code Examples

**C:**
```c
// BUG: Second statement always executes
if (authenticated)
    grantAccess();
    logAccess();  // ALWAYS EXECUTES regardless of authentication!

// BUG: Added line breaks existing code
if (error)
    logError();
    return -1;  // ALWAYS RETURNS - breaks control flow

// INFAMOUS: Apple goto fail (CVE-2014-1266)
if ((err = SSLHashSHA1.update(&hashCtx, &signedParams)) != 0)
    goto fail;
    goto fail;  // Duplicate! Always executes, skipping verification
if ((err = SSLHashSHA1.final(&hashCtx, &hashOut)) != 0)
    goto fail;  // Never reached - dead code
```

**Java:**
```java
// BUG: Only first statement is conditional
if (user.isAdmin())
    System.out.println("Admin access");
    deleteAllRecords();  // ALWAYS EXECUTES - catastrophic!

// BUG: In else clause
if (valid)
    process();
else
    logError();
    abort();  // Always executes! Not part of else
```

**JavaScript:**
```javascript
// BUG: Hoisting makes this worse
if (condition)
    var x = 1;  // x is hoisted, declared regardless
    processWithX(x);  // Always executes

// BUG: With arrow functions looking like blocks
if (condition)
    () => {  // This is not executed! It's a function expression
        doSomething();
    };  // Followed by semicolon, does nothing

// CORRECT: Call the function
if (condition) {
    (() => {
        doSomething();
    })();
}
```

**Python:**
```python
# SAFE: Python enforces indentation as block structure
if authenticated:
    grant_access()
    log_access()  # Clearly in the if block

# But similar issues exist with one-liners:
if authenticated: grant_access(); log_access()  # Both conditional
# vs
if authenticated: grant_access()
log_access()  # NOT conditional - outside the if
```

### Famous Bugs
- **Apple goto fail (CVE-2014-1266)**: Duplicate goto statement due to missing braces caused SSL verification to be skipped, enabling man-in-the-middle attacks

### Detection Strategies
1. **Style Enforcement**: Require braces for all control structures
2. **Indentation Analysis**: Flag statements indented like they're in a block but aren't
3. **Duplicate Statement Detection**: Flag consecutive identical statements after if
4. **Compiler Warnings**: `-Wmisleading-indentation` (GCC 6+)

---

## 2.4 Short-Circuit Evaluation Surprises

**CWE-569: Expression Issues (related)**

### Description
Short-circuit evaluation causes the second operand of `&&` and `||` to be skipped when the result is determined by the first operand. Side effects in the second operand may not execute.

### Code Examples

**C:**
```c
// BUG: Second condition never evaluated when first is false
int i = 0;
if (checkPermission() && (i++ > 0)) {
    // If checkPermission() returns false, i++ never executes
}
// i might be 0 or 1 depending on permission check

// BUG: Null check order (divide by zero)
if (denominator != 0 && numerator / denominator > threshold) {
    // Safe - short-circuits if denominator is 0
}
if (numerator / denominator > threshold && denominator != 0) {
    // BUG: Divides before checking! Division by zero possible
}

// BUG: Side effect not executed
if (x || (y = getValue())) {
    // If x is truthy, y is never assigned
}
```

**Java:**
```java
// BUG: Object null check with side effect
Object obj = null;
int count = 0;
if (obj != null && ++count > 0) {
    // count never incremented when obj is null
}

// BUG: Function with side effects skipped
if (quickCheck() || expensiveOperationWithSideEffects()) {
    // Side effects don't occur if quickCheck() returns true
}

// NOTE: Java has & and | for non-short-circuit evaluation
if (a & b) {  // Both a and b always evaluated
}
```

**Python:**
```python
# BUG: Side effect in short-circuit
x = []
if True or x.append(1):  # x.append never called
    pass
# x is still []

# BUG: Assignment-like operation not executed
result = None
if condition and (result := compute()):  # result not assigned if condition false
    use(result)
# result might be None

# Intentional use (common pattern):
obj = get_obj()
if obj and obj.is_valid():  # Safe - doesn't call is_valid() on None
    pass
```

**JavaScript:**
```javascript
// BUG: Default value not set
let config;
if (false || (config = getConfig())) {
    // config is set
}
// config is set, but if first operand were truthy, it wouldn't be

// BUG: Side effect skipped
let initialized = false;
if (cache.exists || (initialized = init())) {
    // initialized might not be set
}

// Intentional use (common pattern):
const value = inputValue || defaultValue;  // Default if falsy
const value2 = inputValue ?? defaultValue; // Default only if null/undefined
```

### Detection Strategies
1. **Side Effect Analysis**: Flag expressions with side effects in short-circuit positions
2. **Pattern Matching**: Detect assignment operators in && or || operands
3. **Data Flow Analysis**: Track variables that may or may not be assigned

---

## 2.5 Null Check Order Errors

**CWE-476: NULL Pointer Dereference**

### Description
Performing operations on a potentially null value before checking if it's null leads to null pointer dereferences.

### Code Examples

**C:**
```c
// BUG: Dereference before null check
void process(struct Node* node) {
    int value = node->value;  // Dereference first
    if (node == NULL) {       // Check second - too late!
        return;
    }
    // Use value
}

// BUG: Redundant null check after dereference
void process(char* str) {
    int len = strlen(str);  // Crashes if str is NULL
    if (str != NULL) {      // Redundant - already used str
        printf("%s\n", str);
    }
}

// CORRECT: Check first
void process(struct Node* node) {
    if (node == NULL) {
        return;
    }
    int value = node->value;  // Safe now
}
```

**Java:**
```java
// BUG: Method call before null check
String result = obj.toString();  // NPE if obj is null
if (obj != null) {
    process(result);
}

// BUG: Null check after exception already possible
int length = str.length();  // NPE if str is null
if (str == null) {
    return 0;  // Never reached if str was null
}
return length;

// BUG: Null check on wrong variable
if (other != null) {
    return obj.getValue();  // Should check obj, not other
}
```

**Python:**
```python
# BUG: Method call before None check
result = obj.process()  # AttributeError if obj is None
if obj is None:
    return default

# BUG: Using truthiness instead of None check
if obj:  # False for None, but also for [], {}, 0, ""
    obj.process()

# CORRECT: Explicit None check
if obj is not None:
    result = obj.process()
```

**JavaScript:**
```javascript
// BUG: Property access before null check
const name = user.name;  // TypeError if user is null/undefined
if (user === null) {
    return "Unknown";
}

// BUG: Truthy check misses 0 and ""
const count = obj.count;  // Might throw
if (obj) {  // Too late, and also wrong (0 is falsy)
    process(count);
}

// CORRECT: Optional chaining (ES2020)
const name = user?.name;  // Returns undefined if user is null
const value = obj?.nested?.property;  // Safe chain

// CORRECT: Check first
if (user !== null && user !== undefined) {
    const name = user.name;
}
```

### Detection Strategies
1. **Data Flow Analysis**: Track null checks and dereferences, flag wrong order
2. **Pattern Matching**: Detect dereference-then-check patterns
3. **Static Analysis Tools**: FindBugs, NullAway, TypeScript strict null checks

---

## 2.6 Inverted Conditions

**CWE-697: Incorrect Comparison**

### Description
Using the wrong logical operator or negation leads to conditions that are the opposite of what was intended.

### Code Examples

**C:**
```c
// BUG: Wrong comparison operator
if (x < 0) {  // Should be x > 0
    handlePositive(x);  // Handles negative instead!
}

// BUG: Double negation confusion
if (!(!authorized)) {  // Same as: if (authorized)
    // Confusing and error-prone
}

// BUG: Wrong logical operator
if (x < min && x > max) {  // Impossible! Should be ||
    handleOutOfRange(x);
}

// BUG: Negation of compound condition
if (!(a && b)) {  // Equivalent to: !a || !b (De Morgan's law)
    // Programmer might think this means "not a AND not b"
}
```

**Java:**
```java
// BUG: Inverted return value
boolean isValid() {
    return value < 0;  // Should be value >= 0
}

// BUG: Wrong operator in range check
if (value < min || value > max) {  // Correct: out of range
}
if (value > min || value < max) {  // BUG: Almost always true!
}

// BUG: Negation applied to wrong part
if (!user.isAdmin() && user.hasPermission()) {
    // Did they mean: if (!(user.isAdmin() && user.hasPermission()))?
}
```

**Python:**
```python
# BUG: Wrong operator
if x < threshold:  # Should be x > threshold
    trigger_alert()

# BUG: not applied incorrectly
if not a and b:    # Equivalent to: (not a) and b
if not (a and b):  # Different: not a OR not b

# BUG: Using != when == was intended
if status != "SUCCESS":  # Should be ==
    celebrate()  # Celebrates on failure!
```

**JavaScript:**
```javascript
// BUG: ! vs !! confusion
if (!value) {      // True for null, undefined, 0, "", false, NaN
}
if (!!value) {     // True for everything else (double negation to boolean)
}

// BUG: Wrong equality check
if (response.status !== 200) {  // Should be ===
    handleSuccess();  // Handles errors!
}

// BUG: Inverted array method
if (!array.includes(item)) {  // True when item NOT in array
    removeItem(item);  // Probably meant to remove existing items
}
```

### Detection Strategies
1. **Semantic Analysis**: Flag impossible conditions (e.g., x < 0 && x > 0)
2. **Pattern Matching**: Detect double negation
3. **Code Review**: Variable/function names should match condition polarity

---

## 2.7 Dead Code (Unreachable Branches)

**CWE-561: Dead Code**

### Description
Code that can never be executed due to impossible conditions or prior control flow statements.

### Code Examples

**C:**
```c
// BUG: Code after unconditional return
int process() {
    return 0;
    cleanup();  // Dead code - never executes
}

// BUG: Impossible condition
int x = 5;
if (x > 10) {  // Always false, dead branch
    printf("Unreachable\n");
}

// BUG: Condition always same
if (x > 0) {
    // ...
} else if (x > 5) {  // Dead code if first branch taken
    // Never executed
}

// BUG: Redundant code after goto/break
for (int i = 0; i < 10; i++) {
    if (error) {
        break;
        handleError();  // Dead code
    }
}
```

**Java:**
```java
// BUG: Code after throw
void validate(Object obj) {
    if (obj == null) {
        throw new IllegalArgumentException("null");
        log.error("Object was null");  // Dead code
    }
}

// BUG: Unreachable catch block (compiler error in Java)
try {
    // Code that doesn't throw IOException
} catch (IOException e) {  // Compile error: unreachable
    // ...
}

// BUG: Always-false condition
final int MAX = 100;
if (MAX > 200) {  // Always false
    // Dead code
}
```

**Python:**
```python
# BUG: Code after return
def process():
    return 42
    print("Done")  # Dead code (some IDEs warn)

# BUG: Always-false condition
DEBUG = False
if DEBUG:
    print("Debug info")  # Dead code in production

# BUG: Unreachable except
try:
    x = int("42")  # Can't raise ValueError here
except ValueError:  # Dead code (but Python allows it)
    print("Invalid")
```

**JavaScript:**
```javascript
// BUG: Code after return
function calculate() {
    return result;
    console.log("Complete");  // Dead code
}

// BUG: Impossible type check
function process(x) {
    if (typeof x === "string" && typeof x === "number") {
        // Dead code - impossible condition
    }
}

// BUG: Unreachable code in switch
switch (value) {
    default:
        return "default";
    case 1:  // Dead code if default catches all
        return "one";
}
```

### Famous Bugs
- **Apple goto fail (CVE-2014-1266)**: The SSL verification code became dead code due to duplicate goto statement

### Detection Strategies
1. **Control Flow Analysis**: Build CFG, find unreachable nodes
2. **Constant Propagation**: Evaluate conditions with known values
3. **Compiler Warnings**: `-Wunreachable-code`, `-Wdead-code`

---

## 2.8 Overlapping Conditions

**CWE-561: Dead Code (related)**

### Description
When multiple conditions can be true simultaneously, the order determines which branch executes. Later branches may be dead code or may not execute as intended.

### Code Examples

**C:**
```c
// BUG: Order matters, may not match intent
if (x > 0) {
    printf("Positive\n");
} else if (x > 10) {  // Never executes! Always caught by first condition
    printf("Greater than 10\n");
}

// BUG: Non-exhaustive, overlapping ranges
if (score >= 90) {
    grade = 'A';
} else if (score >= 80) {  // 80-89
    grade = 'B';
} else if (score >= 85) {  // Dead code! Already caught by >= 80
    grade = 'B+';
}

// CORRECT: Order from most specific to least
if (x > 10) {
    printf("Greater than 10\n");
} else if (x > 0) {
    printf("Positive (1-10)\n");
}
```

**Java:**
```java
// BUG: instanceof order matters
if (obj instanceof Object) {  // Always true for non-null
    handleObject(obj);
} else if (obj instanceof String) {  // Dead code!
    handleString((String) obj);
}

// CORRECT: Most specific first
if (obj instanceof String) {
    handleString((String) obj);
} else if (obj instanceof Object) {
    handleObject(obj);
}

// BUG: Overlapping number ranges
if (age < 18) {
    category = "Minor";
} else if (age < 13) {  // Dead code! age < 13 implies age < 18
    category = "Child";
}
```

**Python:**
```python
# BUG: First matching condition wins
if x > 0:
    result = "positive"
elif x > 100:  # Dead code - caught by x > 0
    result = "large positive"

# BUG: isinstance with base class first
if isinstance(obj, Animal):
    handle_animal(obj)
elif isinstance(obj, Dog):  # Dead code - Dog is Animal
    handle_dog(obj)

# CORRECT: Specific first
if isinstance(obj, Dog):
    handle_dog(obj)
elif isinstance(obj, Animal):
    handle_animal(obj)
```

**JavaScript:**
```javascript
// BUG: Type coercion causes overlap
if (x == 0) {
    console.log("Zero");
} else if (x == false) {  // May be dead code! 0 == false is true
    console.log("False");
}

// BUG: Range overlap
if (temperature > 30) {
    status = "hot";
} else if (temperature > 35) {  // Dead code!
    status = "very hot";
}
```

### Detection Strategies
1. **Constraint Analysis**: Check if later conditions can be true when earlier ones are false
2. **Type Hierarchy Analysis**: Detect instanceof/isinstance with subclass after superclass
3. **Range Analysis**: Find overlapping numeric ranges

---

## 2.9 Missing Else Clause

**CWE-478: Missing Default Case in Multiple Condition Expression (related)**

### Description
Failing to handle the "else" case can lead to uninitialized variables, undefined behavior, or logic errors when none of the conditions match.

### Code Examples

**C:**
```c
// BUG: Variable uninitialized if no condition matches
int result;
if (x > 0) {
    result = 1;
} else if (x < 0) {
    result = -1;
}
// If x == 0, result is uninitialized!

// BUG: Function with no return in some paths
int categorize(int x) {
    if (x > 0) {
        return 1;
    } else if (x < 0) {
        return -1;
    }
    // No return for x == 0! Undefined behavior
}

// CORRECT: Always have else or default return
int categorize(int x) {
    if (x > 0) {
        return 1;
    } else if (x < 0) {
        return -1;
    } else {
        return 0;
    }
}
```

**Java:**
```java
// BUG: Unhandled case
String status;
if (code == 200) {
    status = "OK";
} else if (code == 404) {
    status = "Not Found";
}
// status not initialized for other codes!

// BUG: No else in boolean return (Java catches at compile time though)
boolean isValid(int x) {
    if (x > 0) {
        return true;
    }
    // Compile error: missing return statement
}
```

**Python:**
```python
# BUG: Variable may not be defined
if condition_a:
    result = "A"
elif condition_b:
    result = "B"
# NameError: result is not defined if neither condition is true

# CORRECT: Always initialize or provide else
result = "default"
if condition_a:
    result = "A"
elif condition_b:
    result = "B"
```

**JavaScript:**
```javascript
// BUG: Function returns undefined implicitly
function categorize(x) {
    if (x > 0) {
        return "positive";
    } else if (x < 0) {
        return "negative";
    }
    // Returns undefined for x === 0
}

// CORRECT: Handle all cases
function categorize(x) {
    if (x > 0) {
        return "positive";
    } else if (x < 0) {
        return "negative";
    } else {
        return "zero";
    }
}
```

### Detection Strategies
1. **Data Flow Analysis**: Track variable initialization across all paths
2. **Missing Return Analysis**: Ensure all paths return a value
3. **Exhaustiveness Checking**: Require else for if-else chains

---

## 2.10 Type Coercion in Conditions (JavaScript)

**CWE-843: Access of Resource Using Incompatible Type**

### Description
JavaScript's loose equality (`==`) and truthy/falsy evaluation can cause unexpected condition outcomes due to implicit type conversion.

### Code Examples

**JavaScript:**
```javascript
// BUG: Falsy values cause unexpected behavior
function hasValue(x) {
    if (x) {  // False for: 0, "", null, undefined, NaN, false
        return true;
    }
    return false;
}
hasValue(0);   // false - but 0 IS a value!
hasValue("");  // false - but "" IS a value!

// BUG: Loose equality surprises
if (0 == false) {       // true
if (0 == "")    {       // true
if (false == "")  {     // true
if (null == undefined) { // true
if ([] == false) {      // true (empty array coerces to 0)
if ([] == ![])  {       // true! (both coerce to 0)

// BUG: The "zero price" problem
const price = 0;  // Valid price
if (!price) {  // True! Zero is falsy
    console.log("Price not set");  // Wrong!
}

// BUG: String "0" vs number 0
if ("0") {           // true - non-empty string is truthy
}
if ("0" == false) {  // true - "0" coerces to 0, which equals false
}

// CORRECT: Use strict equality and explicit checks
if (x === 0) {  // Only matches number 0
}
if (x === null || x === undefined) {  // Explicit null check
}
if (typeof x !== 'undefined') {  // Check if defined
}

// CORRECT: Nullish coalescing for defaults
const value = input ?? defaultValue;  // Only if null/undefined, not 0 or ""
```

### Falsy Values Reference
```javascript
// All falsy values in JavaScript:
false           // boolean false
0               // number zero
-0              // negative zero
0n              // BigInt zero
""              // empty string
null            // null
undefined       // undefined
NaN             // Not a Number

// Everything else is truthy, including:
"0"             // string zero
"false"         // string false
[]              // empty array
{}              // empty object
function(){}    // empty function
```

### Detection Strategies
1. **Type Analysis**: Flag loose equality with different types
2. **Pattern Matching**: Detect truthy checks on values that could be 0 or ""
3. **ESLint Rules**: `eqeqeq`, `no-implicit-coercion`

---

# 3. SWITCH/CASE ERRORS

## 3.1 Missing Break (Fall-Through Bugs)

**CWE-484: Omitted Break Statement in Switch**

### Description
Without a `break` statement, execution continues ("falls through") to the next case, which is usually unintended.

### Code Examples

**C:**
```c
// BUG: Fall-through to next case
switch (command) {
    case CMD_READ:
        readData();
        // MISSING BREAK! Falls through to CMD_WRITE
    case CMD_WRITE:
        writeData();  // Also executes for CMD_READ!
        break;
    case CMD_DELETE:
        deleteData();
        break;
}

// BUG: Multiple fall-throughs
switch (level) {
    case 3:
        doLevel3();
    case 2:
        doLevel2();  // Executes for level 3 too
    case 1:
        doLevel1();  // Executes for level 2 and 3
        break;
}

// Intentional fall-through (should be documented)
switch (c) {
    case 'a':
    case 'e':
    case 'i':
    case 'o':
    case 'u':
        isVowel = true;
        break;
    default:
        isVowel = false;
}

// C23: [[fallthrough]] attribute for intentional fall-through
switch (x) {
    case 1:
        doSomething();
        [[fallthrough]];  // Explicit: intentional fall-through
    case 2:
        doMore();
        break;
}
```

**Java:**
```java
// BUG: Classic fall-through
switch (day) {
    case MONDAY:
        startWeek();
        // MISSING BREAK!
    case TUESDAY:
        normalDay();  // Also runs on Monday!
        break;
}

// Java 14+: Switch expressions don't need break
String result = switch (day) {
    case MONDAY -> "Start of week";  // No fall-through possible
    case FRIDAY -> "End of week";
    default -> "Middle of week";
};

// If you need fall-through in switch expressions, use yield:
String result = switch (day) {
    case SATURDAY, SUNDAY:
        yield "Weekend";  // Multiple cases, one result
    default:
        yield "Weekday";
};
```

**JavaScript:**
```javascript
// BUG: Fall-through
switch (fruit) {
    case 'apple':
        console.log('Apple');
        // Falls through!
    case 'banana':
        console.log('Banana');  // Prints for 'apple' too!
        break;
}

// Intentional fall-through pattern
switch (errorCode) {
    case 400:
    case 401:
    case 403:
        handleClientError();  // All client errors
        break;
    case 500:
    case 502:
    case 503:
        handleServerError();  // All server errors
        break;
}
```

### Famous Bugs
- Chromium mouse button injection bug: Fall-through caused incorrect handling
- Numerous security vulnerabilities from unintended fall-through

### Detection Strategies
1. **Pattern Matching**: Flag case without break/return/throw
2. **Compiler Warnings**: `-Wimplicit-fallthrough` (GCC/Clang)
3. **Require Annotation**: Mandate `[[fallthrough]]` or comments for intentional fall-through

---

## 3.2 Missing Default Case

**CWE-478: Missing Default Case in Multiple Condition Expression**

### Description
Without a default case, unexpected values pass through silently, potentially leaving variables uninitialized or skipping necessary actions.

### Code Examples

**C:**
```c
// BUG: No default handler
int result;
switch (input) {
    case 1: result = 10; break;
    case 2: result = 20; break;
    case 3: result = 30; break;
}
// If input is 4, result is uninitialized!

// BUG: Security-relevant missing default
switch (userRole) {
    case ADMIN:
        grantFullAccess();
        break;
    case USER:
        grantLimitedAccess();
        break;
    // No default! Unknown role gets no explicit denial
}

// CORRECT: Always have a default
switch (input) {
    case 1: result = 10; break;
    case 2: result = 20; break;
    default: result = 0; break;  // Handle unexpected values
}
```

**Java:**
```java
// BUG: No default in security check
switch (action) {
    case "read":
        checkReadPermission();
        break;
    case "write":
        checkWritePermission();
        break;
    // Unknown action proceeds without check!
}

// CORRECT: Fail-safe default
switch (action) {
    case "read":
        checkReadPermission();
        break;
    case "write":
        checkWritePermission();
        break;
    default:
        throw new IllegalArgumentException("Unknown action: " + action);
}
```

**JavaScript:**
```javascript
// BUG: Function returns undefined for unhandled cases
function getDiscount(customerType) {
    switch (customerType) {
        case 'premium':
            return 0.2;
        case 'regular':
            return 0.1;
    }
    // Returns undefined for unknown types!
}

// CORRECT: Default case
function getDiscount(customerType) {
    switch (customerType) {
        case 'premium':
            return 0.2;
        case 'regular':
            return 0.1;
        default:
            return 0;  // Or throw an error
    }
}
```

### Detection Strategies
1. **AST Analysis**: Flag switch statements without default
2. **Compiler Warnings**: `-Wswitch-default` (GCC)
3. **Static Analysis**: Require exhaustive handling or explicit default

---

## 3.3 Duplicate Case Values

**CWE-561: Dead Code**

### Description
Duplicate case values make the second occurrence unreachable dead code.

### Code Examples

**C:**
```c
// BUG: Duplicate case (compile error in most compilers)
switch (x) {
    case 1: doA(); break;
    case 2: doB(); break;
    case 1: doC(); break;  // Error: duplicate case value
}

// BUG: Duplicate due to macro expansion
#define OPTION_A 1
#define OPTION_B 1  // Accidentally same value!
switch (option) {
    case OPTION_A: handleA(); break;
    case OPTION_B: handleB(); break;  // Error or dead code
}

// BUG: Duplicate due to constant folding
const int X = 5;
const int Y = 2 + 3;  // Also 5
switch (value) {
    case X: handleX(); break;
    case Y: handleY(); break;  // Same as case X
}
```

**Java:**
```java
// BUG: Duplicate case (compile error)
switch (x) {
    case 1:
        doA();
        break;
    case 1:  // Compile error: duplicate case label
        doB();
        break;
}

// BUG: Compile-time constants with same value
final int OPTION_A = 1;
final int OPTION_B = 1;
switch (opt) {
    case OPTION_A: handleA(); break;
    case OPTION_B: handleB(); break;  // Error: duplicate
}
```

**JavaScript:**
```javascript
// BUG: Duplicate case (NO ERROR - second is dead code!)
switch (x) {
    case 1:
        console.log('First');
        break;
    case 1:  // Dead code - never reached!
        console.log('Second');
        break;
}

// BUG: Duplicate due to type coercion
switch (x) {
    case 1:
        console.log('Number 1');
        break;
    case '1':  // Different in strict comparison, but watch out
        console.log('String 1');
        break;
}
```

### Detection Strategies
1. **Compiler/Interpreter**: Most flag duplicate cases
2. **Static Analysis**: Evaluate constant expressions to detect duplicates
3. **Lint Rules**: ESLint `no-duplicate-case`

---

## 3.4 Enum Exhaustiveness

**Related to CWE-478**

### Description
When switching on an enum type, failing to handle all possible values can lead to bugs when new enum values are added.

### Code Examples

**C:**
```c
// BUG: Missing enum case
enum Color { RED, GREEN, BLUE, YELLOW };  // YELLOW added later

const char* colorName(enum Color c) {
    switch (c) {
        case RED:   return "red";
        case GREEN: return "green";
        case BLUE:  return "blue";
        // YELLOW not handled! Returns garbage or undefined
    }
}

// CORRECT: With GCC -Wswitch, this warns
// Or add default that asserts:
switch (c) {
    case RED:   return "red";
    case GREEN: return "green";
    case BLUE:  return "blue";
    case YELLOW: return "yellow";
    default:
        assert(0 && "Unknown color");
        return "unknown";
}
```

**Java:**
```java
// BUG: Missing enum case
enum Status { PENDING, APPROVED, REJECTED, CANCELLED }  // CANCELLED new

String getStatusMessage(Status s) {
    switch (s) {
        case PENDING:  return "Waiting";
        case APPROVED: return "Done";
        case REJECTED: return "Failed";
        // CANCELLED not handled!
    }
    return "Unknown";  // Dead code warning in IDE
}

// Java 14+: Switch expressions require exhaustiveness
String msg = switch (status) {
    case PENDING -> "Waiting";
    case APPROVED -> "Done";
    case REJECTED -> "Failed";
    // Compile error: 'switch' expression does not cover all possible input values
};
```

**TypeScript:**
```typescript
// TypeScript can enforce exhaustiveness
enum Color {
    Red,
    Green,
    Blue
}

function getColorName(c: Color): string {
    switch (c) {
        case Color.Red:
            return "red";
        case Color.Green:
            return "green";
        // Missing Color.Blue!
    }
    // Type error if strictNullChecks enabled and return type doesn't include undefined
}

// Exhaustiveness helper pattern
function assertNever(x: never): never {
    throw new Error("Unexpected value: " + x);
}

function getColorName(c: Color): string {
    switch (c) {
        case Color.Red: return "red";
        case Color.Green: return "green";
        case Color.Blue: return "blue";
        default: return assertNever(c);  // Compile error if case missed
    }
}
```

### Detection Strategies
1. **Compiler Warnings**: `-Wswitch-enum` (GCC/Clang)
2. **IDE Inspections**: JetBrains, VS Code warn on missing cases
3. **Type System**: TypeScript's never type exhaustiveness check
4. **Error Prone**: `MissingCasesInEnumSwitch` checker

---

## 3.5 Case Order Dependency

### Description
In some scenarios, the order of cases matters due to fall-through or efficiency concerns, but more commonly, wrong order causes dead code.

### Code Examples

```c
// BUG: Unreachable case due to order with fall-through
switch (priority) {
    case HIGH:
    case MEDIUM:  // Falls through from HIGH
        handleImportant();
        break;
    case HIGH:    // Error: duplicate, but conceptually...
        handleUrgent();  // Developer wanted separate handling
        break;
}

// Performance consideration (not a bug, but worth noting):
// Put most frequent cases first for some compilers
switch (opcode) {
    case LOAD:    // Most common - check first
        load();
        break;
    case ADD:     // Second most common
        add();
        break;
    case HALT:    // Rare
        halt();
        break;
}
```

---

# 4. GENERAL CONTROL FLOW ERRORS

## 4.1 Early Return Missing Cleanup

**CWE-459: Incomplete Cleanup**
**CWE-772: Missing Release of Resource after Effective Lifetime**

### Description
When a function returns early (due to error or other condition), resources allocated before the return may not be released.

### Code Examples

**C:**
```c
// BUG: Resource leak on early return
int processFile(const char* filename) {
    FILE* f = fopen(filename, "r");
    if (f == NULL) return -1;

    char* buffer = malloc(1024);
    if (buffer == NULL) {
        return -1;  // BUG: f not closed!
    }

    if (readData(f, buffer) < 0) {
        return -1;  // BUG: f not closed, buffer not freed!
    }

    // Normal path
    free(buffer);
    fclose(f);
    return 0;
}

// CORRECT: Centralized cleanup with goto
int processFile(const char* filename) {
    int result = -1;
    FILE* f = NULL;
    char* buffer = NULL;

    f = fopen(filename, "r");
    if (f == NULL) goto cleanup;

    buffer = malloc(1024);
    if (buffer == NULL) goto cleanup;

    if (readData(f, buffer) < 0) goto cleanup;

    result = 0;

cleanup:
    free(buffer);  // free(NULL) is safe
    if (f) fclose(f);
    return result;
}
```

**Java:**
```java
// BUG: Resource not closed on exception
void processFile(String filename) throws IOException {
    FileInputStream fis = new FileInputStream(filename);
    BufferedReader reader = new BufferedReader(new InputStreamReader(fis));

    String line = reader.readLine();
    if (line == null) {
        return;  // BUG: reader and fis not closed!
    }

    process(line);
    reader.close();  // Not reached if return or exception
}

// CORRECT: Try-with-resources
void processFile(String filename) throws IOException {
    try (FileInputStream fis = new FileInputStream(filename);
         BufferedReader reader = new BufferedReader(new InputStreamReader(fis))) {
        String line = reader.readLine();
        if (line == null) {
            return;  // Resources automatically closed
        }
        process(line);
    }  // Resources closed here, even on exception
}
```

**Python:**
```python
# BUG: File not closed on early return
def process_file(filename):
    f = open(filename, 'r')
    line = f.readline()
    if not line:
        return None  # BUG: f not closed!
    result = process(line)
    f.close()
    return result

# CORRECT: Context manager
def process_file(filename):
    with open(filename, 'r') as f:
        line = f.readline()
        if not line:
            return None  # f automatically closed
        return process(line)
```

**JavaScript:**
```javascript
// BUG: Resource not released
async function processDatabase() {
    const connection = await db.connect();

    const result = await connection.query('SELECT * FROM users');
    if (result.length === 0) {
        return null;  // BUG: connection not closed!
    }

    await connection.close();
    return result;
}

// CORRECT: Try-finally
async function processDatabase() {
    const connection = await db.connect();
    try {
        const result = await connection.query('SELECT * FROM users');
        if (result.length === 0) {
            return null;
        }
        return result;
    } finally {
        await connection.close();  // Always executes
    }
}
```

### Detection Strategies
1. **Data Flow Analysis**: Track resource allocation and release across all paths
2. **Pattern Matching**: Flag return statements with open resources in scope
3. **Static Analysis Tools**: Coverity, PVS-Studio, FindBugs

---

## 4.2 Exception Swallowing

**CWE-1069: Empty Exception Block**
**CWE-390: Detection of Error Condition Without Action**

### Description
Catching an exception and doing nothing (or only logging) can hide bugs and make debugging extremely difficult.

### Code Examples

**Java:**
```java
// BUG: Silent exception swallowing
try {
    riskyOperation();
} catch (Exception e) {
    // Empty catch - error completely hidden!
}

// BUG: Log and continue (often inappropriate)
try {
    processPayment();
} catch (PaymentException e) {
    logger.error("Payment failed", e);
    // Continues as if nothing happened!
}

// BUG: Catching too broad
try {
    parseUserInput();
} catch (Exception e) {  // Catches everything including NullPointerException!
    return defaultValue;
}

// CORRECT: Handle appropriately or rethrow
try {
    processPayment();
} catch (PaymentException e) {
    logger.error("Payment failed", e);
    throw new ServiceException("Could not process payment", e);
}
```

**Python:**
```python
# BUG: Bare except
try:
    do_something()
except:  # Catches EVERYTHING including SystemExit, KeyboardInterrupt!
    pass

# BUG: Catching Exception silently
try:
    parse_data()
except Exception:
    pass  # All errors hidden

# BUG: Pokemon exception handling ("gotta catch 'em all")
try:
    complex_operation()
except Exception as e:
    print(f"Error: {e}")  # Just prints, doesn't handle

# CORRECT: Specific exception, appropriate handling
try:
    parse_data()
except ValueError as e:
    logger.warning(f"Invalid data format: {e}")
    return default_value
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise unexpected exceptions
```

**JavaScript:**
```javascript
// BUG: Empty catch block
try {
    JSON.parse(userInput);
} catch (e) {
    // Silent failure - invalid JSON goes undetected
}

// BUG: Swallowing async errors
async function fetchData() {
    try {
        return await api.getData();
    } catch (error) {
        console.log(error);  // Logs but returns undefined!
    }
}

// CORRECT: Handle or rethrow
async function fetchData() {
    try {
        return await api.getData();
    } catch (error) {
        console.error('API error:', error);
        throw new Error('Failed to fetch data');  // Or return default
    }
}
```

**C#:**
```csharp
// BUG: Empty catch
try {
    ProcessFile();
} catch (IOException) {
    // Silent failure
}

// BUG: Catch and continue
try {
    UpdateDatabase();
} catch (SqlException ex) {
    Debug.WriteLine(ex.Message);
    // Database update failed but we proceed anyway!
}

// CORRECT: Handle appropriately
try {
    UpdateDatabase();
} catch (SqlException ex) when (ex.Number == 1205) {  // Deadlock
    // Retry logic
    Thread.Sleep(100);
    UpdateDatabase();
} catch (SqlException ex) {
    throw new DataAccessException("Database update failed", ex);
}
```

### Detection Strategies
1. **AST Analysis**: Flag empty catch blocks
2. **Pattern Matching**: Detect catch with only logging
3. **CodeQL/SonarQube**: Rules for exception handling anti-patterns

---

## 4.3 Goto Misuse

**CWE-1120: Excessive Code Complexity (related)**

### Description
While `goto` is sometimes justified (error handling in C, breaking nested loops), misuse creates "spaghetti code" that is difficult to understand and maintain.

### Code Examples

**C:**
```c
// BUG: Goto creating spaghetti code
int process(int* data, int size) {
    int i = 0;
start:
    if (i >= size) goto end;
    if (data[i] < 0) goto error;
    if (data[i] == 0) goto skip;
    process_item(data[i]);
skip:
    i++;
    goto start;
error:
    printf("Error at %d\n", i);
    return -1;
end:
    return 0;
}

// CORRECT: Structured version (much clearer)
int process(int* data, int size) {
    for (int i = 0; i < size; i++) {
        if (data[i] < 0) {
            printf("Error at %d\n", i);
            return -1;
        }
        if (data[i] != 0) {
            process_item(data[i]);
        }
    }
    return 0;
}

// ACCEPTABLE: Goto for cleanup (common C idiom)
int process_file(const char* path) {
    int ret = -1;
    FILE* f = NULL;
    char* buf = NULL;

    f = fopen(path, "r");
    if (!f) goto out;

    buf = malloc(SIZE);
    if (!buf) goto out;

    if (read_data(f, buf) < 0) goto out;

    ret = 0;
out:
    free(buf);
    if (f) fclose(f);
    return ret;
}
```

### Famous Bugs
- **Apple goto fail (CVE-2014-1266)**: Misplaced goto caused SSL verification bypass

### Detection Strategies
1. **Complexity Metrics**: Flag excessive goto usage
2. **Pattern Matching**: Allow only forward gotos to cleanup labels
3. **Style Enforcement**: Ban goto except for error handling

---

## 4.4 Unreachable Code After Return/Throw/Break

**CWE-561: Dead Code**

### Description
Code placed after unconditional control flow statements (return, throw, break, continue) is never executed.

### Code Examples

**C:**
```c
// BUG: Code after return
int getValue() {
    return 42;
    printf("This never prints\n");  // Dead code
    int x = 10;  // Dead code
}

// BUG: Code after break
for (int i = 0; i < 10; i++) {
    break;
    printf("%d\n", i);  // Dead code
}

// BUG: Code after infinite loop
while (1) {
    process();
}
cleanup();  // Dead code - never reached
```

**Java:**
```java
// BUG: Code after throw
void validate(Object obj) {
    if (obj == null) {
        throw new IllegalArgumentException("null object");
        log.info("Validation failed");  // Compile error: unreachable
    }
}

// BUG: Return in finally (replaces try's return!)
int getValue() {
    try {
        return 1;
    } finally {
        return 2;  // This is returned, not 1! Very confusing.
    }
}
```

**Python:**
```python
# BUG: Code after return
def calculate():
    return 42
    print("Done")  # Dead code (no error, but never runs)

# BUG: Code after raise
def validate(x):
    if x < 0:
        raise ValueError("Negative value")
        log.error("Invalid input")  # Dead code

# BUG: Code after sys.exit
import sys
def shutdown():
    sys.exit(0)
    cleanup()  # Dead code
```

**JavaScript:**
```javascript
// BUG: Code after return
function calculate() {
    return 42;
    console.log("Done");  // Dead code (no error in JS)
}

// BUG: Code after throw
function validate(x) {
    if (x < 0) {
        throw new Error("Negative");
        console.log("Logging error");  // Dead code
    }
}
```

### Detection Strategies
1. **Control Flow Analysis**: Mark code after terminating statements
2. **Compiler Warnings**: Most compilers warn about unreachable code
3. **IDE Support**: Visual indication of dead code

---

## 4.5 Multiple Return Complexity

### Description
Functions with many return points scattered throughout are harder to reason about, debug, and maintain.

### Code Examples

```java
// BUG-PRONE: Multiple returns hide complexity
int complexCalculation(int a, int b, int c) {
    if (a < 0) return -1;
    if (b == 0) return 0;

    int temp = a * b;
    if (temp > 100) return temp;

    if (c < 0) {
        if (temp < 50) return c;
        return temp + c;
    }

    for (int i = 0; i < c; i++) {
        if (condition(i)) return i;
    }

    return temp;
}

// CLEANER: Single exit point (when practical)
int complexCalculation(int a, int b, int c) {
    int result;

    if (a < 0) {
        result = -1;
    } else if (b == 0) {
        result = 0;
    } else {
        int temp = a * b;
        result = calculateResult(temp, c);
    }

    return result;
}
```

### Detection Strategies
1. **Cyclomatic Complexity**: Measure function complexity
2. **Return Count**: Flag functions with excessive returns
3. **Code Review**: Ensure each return is justified

---

# 5. CWE REFERENCE TABLE

| Error Category | Primary CWE | Related CWEs |
|---------------|-------------|--------------|
| Off-by-one | CWE-193 | CWE-119, CWE-120 |
| Infinite Loop | CWE-835 | CWE-400 |
| Empty Loop Body | CWE-561 | CWE-483 |
| Loop Variable Mod | CWE-369 | - |
| Wrong Loop Bounds | CWE-119 | CWE-787, CWE-125 |
| Break/Continue Misuse | CWE-670 | - |
| Iterator Invalidation | CWE-416 | CWE-825 |
| Float Loop Counter | - | CERT FLP30-C |
| Assignment vs Comparison | CWE-481 | CWE-480 |
| Dangling Else | CWE-483 | - |
| Missing Braces | CWE-483 | CWE-561 |
| Short-Circuit Side Effects | CWE-569 | - |
| Null Check Order | CWE-476 | CWE-690 |
| Inverted Conditions | CWE-697 | - |
| Dead Code | CWE-561 | - |
| Overlapping Conditions | CWE-561 | - |
| Missing Else | CWE-478 | - |
| Type Coercion (JS) | CWE-843 | CWE-704 |
| Missing Break | CWE-484 | - |
| Missing Default | CWE-478 | - |
| Duplicate Case | CWE-561 | - |
| Enum Exhaustiveness | CWE-478 | - |
| Early Return Cleanup | CWE-459 | CWE-772, CWE-401 |
| Exception Swallowing | CWE-1069 | CWE-390, CWE-755 |
| Goto Misuse | CWE-1120 | CWE-561 |
| Unreachable Code | CWE-561 | - |

---

# 6. FAMOUS BUGS SUMMARY

| Bug | Year | Error Type | Impact |
|-----|------|-----------|--------|
| Apple goto fail | 2014 | Missing braces/goto | SSL bypass, MITM attacks |
| Therac-25 | 1985-87 | Race condition/control flow | Patient deaths |
| Ariane 5 | 1996 | Integer overflow | $370M rocket explosion |
| Mars Climate Orbiter | 1999 | Unit conversion | $327M spacecraft loss |
| USS Yorktown | 1997 | Division by zero | Ship disabled |
| Baron Samedit (sudo) | 2021 | Off-by-one | Root privilege escalation |
| Boeing 787 | 2015 | Integer overflow | Power loss after 248 days |
| F-22 Date Line | 2007 | Date handling | Navigation failure |
| Julian Calendar | ~45 BCE | Off-by-one | Wrong leap year calculation |

---

# 7. DETECTION TOOL RECOMMENDATIONS

## Compiler Warnings (Enable These!)

**GCC/Clang:**
```
-Wall -Wextra -Werror
-Wunreachable-code
-Wswitch-enum
-Wswitch-default
-Wimplicit-fallthrough
-Wempty-body
-Wparentheses
-Wmisleading-indentation (GCC 6+)
```

**MSVC:**
```
/W4 /WX
/analyze
```

## Static Analysis Tools

| Tool | Languages | Key Detections |
|------|-----------|----------------|
| PVS-Studio | C/C++/C#/Java | All categories |
| Coverity | C/C++/Java | Memory, control flow |
| SonarQube | Multiple | All categories |
| ESLint | JavaScript | Type coercion, equality |
| Pylint | Python | Dead code, control flow |
| Error Prone | Java | Switch, null checks |
| FindBugs/SpotBugs | Java | All categories |
| Clang Static Analyzer | C/C++ | All categories |
| CodeQL | Multiple | Security-focused |
| Semgrep | Multiple | Custom rules |

## IDE Inspections

- **IntelliJ IDEA**: Comprehensive Java/Kotlin analysis
- **Visual Studio**: C/C#/C++ analysis
- **VS Code**: With appropriate extensions
- **Eclipse**: With SpotBugs/SonarLint plugins

---

# 8. IMPLEMENTATION NOTES FOR STATIC ANALYZER

## Priority Detection Rules

### Critical (Always Flag)
1. Assignment in condition without explicit parentheses
2. Empty loop body (semicolon after for/while)
3. Missing break in switch (without fallthrough comment)
4. Early return without resource cleanup
5. Null dereference before null check

### High (Flag with Context)
1. Off-by-one patterns (<=length, >0 with i++)
2. Loop variable modification inside body
3. Iterator modification during iteration
4. Float loop counters
5. Missing default in switch

### Medium (Configurable)
1. Multiple return statements
2. Complex nested conditions
3. Dead code after return
4. Overlapping conditions

## Pattern Recognition Examples

### Off-by-One Detection
```
PATTERN: for(init; i <= array.length; i++)
PATTERN: for(init; i < array.length - 1; i++)  // May be intentional
PATTERN: array[array.length]
```

### Empty Loop Body
```
PATTERN: for(...); statement
PATTERN: while(...); statement
PATTERN: do; while(...)
```

### Assignment in Condition
```
PATTERN: if(var = value)  // Without wrapping parens
PATTERN: while(var = func())  // Common intentional pattern
```

### Missing Break
```
PATTERN: case X: statements; case Y:  // No break/return/throw
EXCEPTION: case X: case Y: // Intentional grouping
EXCEPTION: // fallthrough comment present
```
