# Logical Operator Errors Reference Guide

## Static Analysis Detection Rules for Boolean Logic Mistakes

This document catalogs common logical errors with boolean operators, parentheses, and logical expressions that are syntactically correct but produce wrong results.

---

## 1. PARENTHESES / BRACKET ERRORS

### 1.1 Operator Precedence Mistakes

**CWE-783: Operator Precedence Logic Error**

```c
// BUG: & has lower precedence than ==
if (flags & MASK == EXPECTED) {  // Parsed as: flags & (MASK == EXPECTED)
    // ...
}

// CORRECT:
if ((flags & MASK) == EXPECTED) {
    // ...
}
```

```java
// BUG: Ternary precedence confusion
int result = condition ? a : b + c;  // Parsed as: condition ? a : (b + c)

// If you meant (condition ? a : b) + c, add parentheses:
int result = (condition ? a : b) + c;
```

```javascript
// BUG: Assignment in condition without parentheses
if (x = getValue()) {  // Assignment, not comparison!
    // Always executes if getValue() returns truthy
}

// CORRECT (if assignment intended):
if ((x = getValue())) {  // Extra parens signal intent
    // ...
}

// CORRECT (if comparison intended):
if (x === getValue()) {
    // ...
}
```

### 1.2 Macro Expansion Without Parentheses (C/C++)

**CWE-783: Operator Precedence Logic Error**

```c
// BUG: Macro without parentheses
#define SQUARE(x) x * x

int result = SQUARE(a + b);  // Expands to: a + b * a + b = a + (b*a) + b

// CORRECT:
#define SQUARE(x) ((x) * (x))

int result = SQUARE(a + b);  // Expands to: ((a + b) * (a + b))
```

```c
// BUG: Macro argument used twice with side effects
#define MAX(a, b) ((a) > (b) ? (a) : (b))

int x = 5;
int result = MAX(x++, 3);  // x++ evaluated twice if x > 3!

// Result: x becomes 7, not 6
```

### 1.3 Complex Expression Grouping

```python
# BUG: Wrong grouping changes meaning
if not user.is_admin and user.is_active:  # (not user.is_admin) and user.is_active
    grant_access()

# If you meant: not (user.is_admin and user.is_active)
if not (user.is_admin and user.is_active):
    deny_access()
```

---

## 2. AND/OR OPERATOR ERRORS

### 2.1 && vs & (Logical vs Bitwise)

**CWE-480: Use of Incorrect Operator**

```c
// BUG: Bitwise AND instead of logical AND
if (a > 0 & b > 0) {  // Bitwise &, not logical &&
    // Works sometimes but wrong semantics
}

// CORRECT:
if (a > 0 && b > 0) {
    // Logical AND with short-circuit
}
```

```java
// BUG: Bitwise on booleans (no short-circuit!)
boolean result = checkA() & checkB();  // Both ALWAYS evaluated!

// CORRECT: Short-circuit evaluation
boolean result = checkA() && checkB();  // checkB() skipped if checkA() false
```

### 2.2 || vs | (Logical vs Bitwise)

```javascript
// BUG: Bitwise OR on booleans
if (isAdmin | isModerator) {  // Works but no short-circuit
    grantAccess();
}

// CORRECT:
if (isAdmin || isModerator) {  // Short-circuit evaluation
    grantAccess();
}
```

### 2.3 AND/OR Precedence Mistakes

**CWE-783: Operator Precedence Logic Error**

AND (`&&`) binds tighter than OR (`||`):

```python
# BUG: AND has higher precedence than OR
if is_admin or is_editor and is_active:
    # Parsed as: is_admin or (is_editor and is_active)
    # Admin gets access even if inactive!
    grant_access()

# If you meant all conditions required for non-admins:
if is_admin or (is_editor and is_active):
    grant_access()  # Same as above (explicit)

# If you meant admin OR editor must also be active:
if (is_admin or is_editor) and is_active:
    grant_access()  # Different logic!
```

```java
// BUG: Common security mistake
if (role == ADMIN || role == EDITOR && isActive) {
    // ADMIN gets in even if !isActive
    // Only EDITOR is checked for isActive
}

// CORRECT: Explicit grouping
if ((role == ADMIN || role == EDITOR) && isActive) {
    // Both roles require isActive
}
```

### 2.4 De Morgan's Law Violations

**CWE-570: Expression is Always False**
**CWE-571: Expression is Always True**

De Morgan's Laws:
- `!(A && B)` = `!A || !B`
- `!(A || B)` = `!A && !B`

```java
// BUG: Wrong negation of compound condition
// Original: if (a > 0 && b > 0)
// Negated INCORRECTLY:
if (!(a > 0) && !(b > 0)) {  // This is !(a > 0 || b > 0), not !(a > 0 && b > 0)
    handleNegativeCase();
}

// CORRECT negation of (a > 0 && b > 0):
if (!(a > 0) || !(b > 0)) {  // = (a <= 0 || b <= 0)
    handleNegativeCase();
}

// Or equivalently:
if (a <= 0 || b <= 0) {
    handleNegativeCase();
}
```

```python
# BUG: Double negation confusion
# Intent: Execute if user is NOT (admin AND active)
if not user.is_admin and not user.is_active:  # WRONG: both must be false
    restrict_access()

# CORRECT: Use De Morgan
if not (user.is_admin and user.is_active):  # Either not admin OR not active
    restrict_access()

# Or equivalently:
if not user.is_admin or not user.is_active:
    restrict_access()
```

---

## 3. COMPARISON OPERATOR ERRORS

### 3.1 Chained Comparisons

```python
# Python: Chained comparisons work as expected
if 0 < x < 10:  # Equivalent to: 0 < x and x < 10
    print("x is between 0 and 10")  # CORRECT in Python

# JavaScript: DOES NOT work as expected!
if (0 < x < 10) {  // Parsed as: (0 < x) < 10, which is: (true/false) < 10
    // Always true! true=1, false=0, both < 10
}

// CORRECT in JavaScript:
if (0 < x && x < 10) {
    console.log("x is between 0 and 10");
}
```

```c
// C: Same problem as JavaScript
if (0 < x < 10) {  // Always true (except x <= 0 gives (0 < 10) = true anyway)
    printf("Bug!");
}

// CORRECT:
if (0 < x && x < 10) {
    printf("Correct");
}
```

### 3.2 Floating-Point Equality

**CWE-1077: Floating Point Comparison with Incorrect Operator**

```python
# BUG: Direct float comparison
if 0.1 + 0.2 == 0.3:  # FALSE! 0.1 + 0.2 = 0.30000000000000004
    print("Equal")

# CORRECT: Use epsilon comparison
import math
if math.isclose(0.1 + 0.2, 0.3):
    print("Close enough")

# Or with explicit epsilon:
EPSILON = 1e-9
if abs((0.1 + 0.2) - 0.3) < EPSILON:
    print("Close enough")
```

```java
// BUG: Float equality
float a = 0.1f + 0.2f;
if (a == 0.3f) {  // May be false!
    System.out.println("Equal");
}

// CORRECT:
final float EPSILON = 1e-6f;
if (Math.abs(a - 0.3f) < EPSILON) {
    System.out.println("Close enough");
}
```

### 3.3 == vs === (JavaScript)

**CWE-480: Use of Incorrect Operator**
**CWE-843: Type Confusion**

```javascript
// BUG: Type coercion surprises with ==
console.log(0 == "");        // true (both coerce to 0)
console.log(0 == "0");       // true
console.log("" == "0");      // false
console.log(false == "0");   // true
console.log(null == undefined);  // true
console.log(" \t\n" == 0);   // true (whitespace coerces to 0)

// CORRECT: Use strict equality
console.log(0 === "");       // false
console.log(0 === "0");      // false
console.log(false === "0");  // false

// Security bug example:
if (userInput == "admin") {  // Type coercion possible
    grantAdminAccess();
}

// CORRECT:
if (userInput === "admin") {
    grantAdminAccess();
}
```

### 3.4 String vs Reference Comparison

```java
// BUG: String reference comparison
String a = new String("hello");
String b = new String("hello");
if (a == b) {  // FALSE - comparing references, not content
    System.out.println("Equal");
}

// CORRECT:
if (a.equals(b)) {
    System.out.println("Equal");
}

// Note: String literals are interned, so this works (but is fragile):
String x = "hello";
String y = "hello";
if (x == y) {  // TRUE - same interned reference (but don't rely on this!)
    System.out.println("Equal");
}
```

```python
# Python: is vs ==
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)  # True - value equality
print(a is b)  # False - identity check

# BUG: Using 'is' for value comparison
if user_input is "admin":  # Works sometimes due to interning, but WRONG
    grant_access()

# CORRECT:
if user_input == "admin":
    grant_access()
```

### 3.5 Null/Undefined Comparisons

```javascript
// BUG: Null vs undefined confusion
let x;  // x is undefined
if (x == null) {  // TRUE - == coerces undefined to null
    console.log("x is null or undefined");
}

if (x === null) {  // FALSE - x is undefined, not null
    console.log("x is exactly null");
}

// CORRECT: Explicit check
if (x === null || x === undefined) {
    console.log("x is null or undefined");
}

// Or use loose equality intentionally (document it!):
if (x == null) {  // Checks both null AND undefined
    console.log("x is nullish");
}
```

---

## 4. NEGATION ERRORS

### 4.1 Double Negation Confusion

```python
# BUG: Double negation is hard to read and error-prone
if not not user.is_active:  # Same as: user.is_active
    process()

# CORRECT: Just use the direct condition
if user.is_active:
    process()
```

```javascript
// BUG: !! used incorrectly
if (!!value == true) {  // Redundant - just use if (value)
    process();
}

// The !! idiom converts to boolean, but often unnecessary:
const isValid = !!someValue;  // Usually unnecessary
const isValid = Boolean(someValue);  // More readable if needed
const isValid = someValue ? true : false;  // Even clearer
```

### 4.2 Negating Wrong Part of Expression

```java
// BUG: NOT applied to wrong operand
if (!user.hasPermission() == true) {  // Confusing: !hasPermission() == true
    denyAccess();
}

// CORRECT: Clear negation
if (!user.hasPermission()) {
    denyAccess();
}

// Or:
if (user.hasPermission() == false) {  // Explicit but verbose
    denyAccess();
}
```

### 4.3 NOT Precedence Issues

```c
// BUG: ! has high precedence
if (!a == b) {  // Parsed as: (!a) == b
    // If a=0, b=1: (!0) == 1 → 1 == 1 → true
}

// If you meant !(a == b):
if (!(a == b)) {
    // ...
}

// Or simply:
if (a != b) {
    // ...
}
```

```python
# BUG: 'not' precedence with 'in'
if not x in collection:  # Works, but unclear
    process()

# CORRECT: Use 'not in' operator
if x not in collection:  # Clearer and idiomatic
    process()
```

---

## 5. SHORT-CIRCUIT EVALUATION BUGS

### 5.1 Side Effects in Short-Circuited Expressions

**CWE-768: Incorrect Short Circuit Evaluation**

```java
// BUG: Side effect may not execute
int i = 0;
if (false && (i++ > 0)) {  // i++ NEVER executed
    process();
}
// i is still 0!

// BUG: Side effect depends on first condition
if (shouldProcess() && processAndReturnStatus()) {
    // processAndReturnStatus() only called if shouldProcess() is true
    // Bug if processAndReturnStatus() should ALWAYS run
}

// CORRECT: If both must execute:
boolean a = shouldProcess();
boolean b = processAndReturnStatus();  // Always runs
if (a && b) {
    // ...
}
```

### 5.2 Order-Dependent Null Checks

```java
// BUG: Wrong order - crashes on null
if (user.isActive() && user != null) {  // NullPointerException if user is null!
    process();
}

// CORRECT: Null check first
if (user != null && user.isActive()) {  // Safe - short-circuits on null
    process();
}
```

```python
# BUG: Wrong order
if data['key'] == 'value' and 'key' in data:  # KeyError if 'key' missing!
    process()

# CORRECT:
if 'key' in data and data['key'] == 'value':  # Safe - short-circuits
    process()

# Even better - use .get():
if data.get('key') == 'value':
    process()
```

### 5.3 Assuming Both Sides Execute

```javascript
// BUG: Assuming || default runs function
function process(callback) {
    callback || setDefaultCallback();  // setDefaultCallback NOT assigned to callback!
}

// CORRECT:
function process(callback) {
    callback = callback || setDefaultCallback;  // Assign the result
    // Or modern JS:
    callback = callback ?? getDefaultCallback();  // Nullish coalescing
    // Or:
    callback ??= getDefaultCallback();  // Assignment version
}
```

---

## 6. BOOLEAN EXPRESSION ANTI-PATTERNS

### 6.1 Redundant Boolean Expressions

**CWE-571: Expression is Always True**
**CWE-570: Expression is Always False**

```java
// BUG: Redundant comparison to true/false
if (isValid == true) {   // Redundant
    process();
}
if (isValid == false) {  // Redundant
    deny();
}

// CORRECT:
if (isValid) {
    process();
}
if (!isValid) {
    deny();
}
```

```python
# BUG: Redundant boolean operations
return isValid == True   # Just return isValid
return isValid != False  # Just return isValid
return not isValid == True  # Just return not isValid

# CORRECT:
return isValid
return not isValid
```

### 6.2 Tautologies (Always True)

```java
// BUG: Always true
if (x >= 0 || x < 0) {  // Tautology for any integer x
    // Always executes
}

// BUG: Unsigned always >= 0
unsigned int x;
if (x >= 0) {  // Always true for unsigned!
    // Always executes
}

// BUG: Overlapping conditions cover all cases
if (x > 5 || x <= 5) {  // Tautology
    // Always executes
}
```

### 6.3 Contradictions (Always False)

```java
// BUG: Always false
if (x > 5 && x < 3) {  // Contradiction - impossible!
    // Dead code - never executes
}

// BUG: Type-based contradiction
String s = "hello";
if (s instanceof String && s instanceof Integer) {  // Always false
    // Dead code
}
```

### 6.4 Impossible Conditions

```python
# BUG: Impossible due to earlier check
def process(x):
    if x is None:
        return

    # Later in same function:
    if x is None:  # Impossible - already returned above!
        handle_none()  # Dead code
```

```java
// BUG: Impossible enum value
enum Status { ACTIVE, INACTIVE }

Status s = getStatus();
if (s == Status.ACTIVE) {
    // ...
} else if (s == Status.INACTIVE) {
    // ...
} else {
    // Dead code - enum can only be ACTIVE or INACTIVE
    handleUnknown();
}
```

---

## 7. CWE REFERENCE TABLE

| CWE | Name | Category |
|-----|------|----------|
| CWE-480 | Use of Incorrect Operator | Operators |
| CWE-481 | Assigning instead of Comparing | Assignment |
| CWE-482 | Comparing instead of Assigning | Assignment |
| CWE-483 | Incorrect Block Delimitation | Braces |
| CWE-570 | Expression is Always False | Logic |
| CWE-571 | Expression is Always True | Logic |
| CWE-768 | Incorrect Short Circuit Evaluation | Short-circuit |
| CWE-783 | Operator Precedence Logic Error | Precedence |
| CWE-843 | Type Confusion | Types |
| CWE-1077 | Floating Point Comparison | Comparison |

---

## 8. DETECTION RULES SUMMARY

### High Priority Detection Patterns

| Pattern | Languages | Detection |
|---------|-----------|-----------|
| `& ` instead of `&&` | C, C++, Java | Regex + context |
| `\|` instead of `\|\|` | C, C++, Java | Regex + context |
| `=` in condition | C, C++, Java, JS | AST analysis |
| `==` with floats | All | AST + type analysis |
| `== null` after deref | All | Data flow |
| Missing parens in macro | C, C++ | Preprocessor analysis |
| De Morgan violations | All | Logic analysis |
| Tautology/contradiction | All | SMT solver |
| `== true` / `== false` | All | Simple pattern |

### Famous Bugs

| Bug | Error Type | Impact |
|-----|------------|--------|
| Apple goto fail (2014) | Duplicate statement | SSL bypass |
| Heartbleed | Missing bounds check | Memory leak |
| Toyota acceleration | Bit flip in condition | Vehicle accidents |
| Therac-25 | Race + flag logic | Patient deaths |

---

## 9. BEST PRACTICES

1. **Always use parentheses** for complex boolean expressions
2. **Use `===` in JavaScript** unless you specifically need type coercion
3. **Put null checks first** in short-circuit expressions
4. **Avoid side effects** in boolean expressions
5. **Use De Morgan's laws correctly** when negating compound conditions
6. **Never use `==` with floating-point** numbers
7. **Use `equals()` for object comparison** in Java
8. **Enable compiler warnings** for suspicious boolean expressions
9. **Use static analysis tools** to catch logic errors
10. **Write unit tests** for boundary conditions
