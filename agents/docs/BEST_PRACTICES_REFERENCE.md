# Best Practices Reference: SIG-TOP-10 & SOLID Principles

## Overview

This document defines the best practice checks integrated into the Code-Maintenance-Agent quality gates and checklists, based on industry-standard methodologies:

- **SIG-TOP-10**: Software Improvement Group's Top 10 Guidelines for Maintainability
- **SOLID**: Object-Oriented Design Principles

---

## SIG-TOP-10 Guidelines for Maintainability

### 1. Write Short Units of Code
**Guideline**: Keep methods/functions under 15 lines of code

**Quality Gate Check**:
- **Threshold**: Functions > 15 lines flagged
- **Category**: code_quality
- **Severity**: medium (15-30 lines), high (>30 lines)

**Checklist Actions**:
1. Identify long methods/functions (>15 lines)
2. Apply Extract Method refactoring pattern
3. Verify extracted methods have single responsibility
4. Update tests for refactored code

---

### 2. Write Simple Units of Code
**Guideline**: Limit cyclomatic complexity to ≤10 per unit

**Quality Gate Check**:
- **Threshold**: Complexity > 10 flagged
- **Category**: code_quality
- **Severity**: medium (10-15), high (>15)

**Checklist Actions**:
1. Measure cyclomatic complexity per function
2. Refactor complex conditionals into strategy patterns
3. Extract complex logic into separate functions
4. Add unit tests for each code path

---

### 3. Write Code Once (DRY - Don't Repeat Yourself)
**Guideline**: Avoid code duplication; maximum 3% duplication

**Quality Gate Check**:
- **Threshold**: Duplication > 3% flagged
- **Category**: code_quality
- **Severity**: medium (3-5%), high (>5%)

**Checklist Actions**:
1. Detect duplicate code blocks (≥6 lines)
2. Extract duplicated logic into reusable functions/modules
3. Apply Template Method or Strategy pattern
4. Update callers to use extracted code

---

### 4. Keep Unit Interfaces Small
**Guideline**: Maximum 4 parameters per function

**Quality Gate Check**:
- **Threshold**: Functions with >4 parameters flagged
- **Category**: code_quality
- **Severity**: medium (4-6 params), high (>6 params)

**Checklist Actions**:
1. Identify functions with many parameters
2. Group related parameters into objects/structs
3. Apply Parameter Object refactoring
4. Update function signatures and callers

---

### 5. Separate Concerns in Modules
**Guideline**: Modules should have a single, well-defined purpose

**Quality Gate Check**:
- **Threshold**: Modules with >5 responsibilities flagged
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Analyze module cohesion and coupling
2. Identify mixed responsibilities (e.g., data + presentation)
3. Split modules by concern (business logic, data access, UI)
4. Verify each module has single purpose

---

### 6. Couple Architecture Components Loosely
**Guideline**: Minimize dependencies between components

**Quality Gate Check**:
- **Threshold**: >10 imports per module flagged
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Measure coupling between modules
2. Apply Dependency Inversion (depend on interfaces)
3. Use dependency injection for loose coupling
4. Introduce abstraction layers where needed

---

### 7. Keep Architecture Components Balanced
**Guideline**: Avoid overly large modules (max 50 units per component)

**Quality Gate Check**:
- **Threshold**: Modules >50 functions/classes flagged
- **Category**: code_quality
- **Severity**: high

**Checklist Actions**:
1. Identify oversized modules/components
2. Decompose into smaller, focused modules
3. Apply Facade pattern if needed for API stability
4. Verify balanced distribution of responsibilities

---

### 8. Keep Your Codebase Small
**Guideline**: Minimize lines of code; avoid unnecessary code

**Quality Gate Check**:
- **Threshold**: Dead code detected
- **Category**: code_quality
- **Severity**: low

**Checklist Actions**:
1. Detect unused functions, imports, variables
2. Remove dead code and commented-out code
3. Eliminate redundant abstractions
4. Verify all code is used

---

### 9. Automate Development Pipeline
**Guideline**: CI/CD, automated testing, code quality checks

**Quality Gate Check**:
- **Threshold**: Missing CI/CD, <80% test coverage
- **Category**: tests
- **Severity**: medium

**Checklist Actions**:
1. Setup continuous integration (GitHub Actions, etc.)
2. Add automated testing to pipeline
3. Integrate linting and code quality checks
4. Configure automated deployments

---

### 10. Write Clean Code
**Guideline**: Meaningful names, clear structure, good documentation

**Quality Gate Check**:
- **Threshold**: Unclear naming, missing docs
- **Category**: documentation
- **Severity**: low

**Checklist Actions**:
1. Review variable/function naming clarity
2. Add JSDoc/docstrings to public APIs
3. Remove misleading comments
4. Ensure README/docs are up-to-date

---

## SOLID Principles

### S - Single Responsibility Principle (SRP)
**Principle**: A class/module should have only one reason to change

**Quality Gate Check**:
- **Detection**: Classes with >3 public methods doing unrelated things
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Identify classes with multiple responsibilities
2. Apply Extract Class refactoring
3. Ensure each class has one well-defined purpose
4. Update tests for separated responsibilities

**Example Violation**:
```typescript
// ❌ Violates SRP - mixing data access, business logic, and presentation
class UserManager {
  saveUser(user: User) { /* database logic */ }
  calculateDiscount(user: User) { /* business logic */ }
  renderUserCard(user: User) { /* presentation logic */ }
}

// ✅ Follows SRP - separated concerns
class UserRepository {
  saveUser(user: User) { /* database logic */ }
}

class DiscountCalculator {
  calculate(user: User) { /* business logic */ }
}

class UserView {
  renderCard(user: User) { /* presentation logic */ }
}
```

---

### O - Open/Closed Principle (OCP)
**Principle**: Classes should be open for extension, closed for modification

**Quality Gate Check**:
- **Detection**: Large switch/if-else chains for type-based behavior
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Identify switch statements on object types
2. Apply Strategy or Factory pattern
3. Use polymorphism instead of conditionals
4. Add new behavior via extension, not modification

**Example Violation**:
```typescript
// ❌ Violates OCP - must modify for new payment types
class PaymentProcessor {
  process(type: string, amount: number) {
    if (type === 'credit_card') {
      // credit card logic
    } else if (type === 'paypal') {
      // paypal logic
    }
    // Adding stripe requires modifying this method
  }
}

// ✅ Follows OCP - extend via new classes
interface PaymentMethod {
  process(amount: number): void;
}

class CreditCardPayment implements PaymentMethod {
  process(amount: number) { /* ... */ }
}

class PayPalPayment implements PaymentMethod {
  process(amount: number) { /* ... */ }
}

// Add Stripe without modifying existing code
class StripePayment implements PaymentMethod {
  process(amount: number) { /* ... */ }
}
```

---

### L - Liskov Substitution Principle (LSP)
**Principle**: Subclasses should be substitutable for their base classes

**Quality Gate Check**:
- **Detection**: Override methods throwing "not implemented"
- **Category**: code_quality
- **Severity**: high

**Checklist Actions**:
1. Identify overridden methods that break contracts
2. Fix violated preconditions/postconditions
3. Ensure subclasses honor base class contracts
4. Add integration tests for polymorphic behavior

**Example Violation**:
```typescript
// ❌ Violates LSP - Square changes Rectangle behavior
class Rectangle {
  width: number;
  height: number;

  setWidth(w: number) { this.width = w; }
  setHeight(h: number) { this.height = h; }
  getArea() { return this.width * this.height; }
}

class Square extends Rectangle {
  setWidth(w: number) {
    this.width = w;
    this.height = w;  // Breaks expectation!
  }
}

// ✅ Follows LSP - use composition instead
interface Shape {
  getArea(): number;
}

class Rectangle implements Shape {
  constructor(private width: number, private height: number) {}
  getArea() { return this.width * this.height; }
}

class Square implements Shape {
  constructor(private side: number) {}
  getArea() { return this.side * this.side; }
}
```

---

### I - Interface Segregation Principle (ISP)
**Principle**: Clients shouldn't depend on interfaces they don't use

**Quality Gate Check**:
- **Detection**: Interfaces with >5 methods
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Identify "fat" interfaces with many methods
2. Split into smaller, focused interfaces
3. Ensure clients depend only on needed methods
4. Apply Interface Segregation refactoring

**Example Violation**:
```typescript
// ❌ Violates ISP - forces implementation of unused methods
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
}

class HumanWorker implements Worker {
  work() { /* ... */ }
  eat() { /* ... */ }
  sleep() { /* ... */ }
}

class RobotWorker implements Worker {
  work() { /* ... */ }
  eat() { throw new Error('Robots don\'t eat!'); }  // Forced to implement
  sleep() { throw new Error('Robots don\'t sleep!'); }
}

// ✅ Follows ISP - segregated interfaces
interface Workable {
  work(): void;
}

interface Eatable {
  eat(): void;
}

interface Sleepable {
  sleep(): void;
}

class HumanWorker implements Workable, Eatable, Sleepable {
  work() { /* ... */ }
  eat() { /* ... */ }
  sleep() { /* ... */ }
}

class RobotWorker implements Workable {
  work() { /* ... */ }
}
```

---

### D - Dependency Inversion Principle (DIP)
**Principle**: Depend on abstractions, not concretions

**Quality Gate Check**:
- **Detection**: Direct instantiation of concrete classes in business logic
- **Category**: code_quality
- **Severity**: medium

**Checklist Actions**:
1. Identify tight coupling to concrete implementations
2. Introduce interfaces/abstractions
3. Use dependency injection
4. Invert control flow to depend on abstractions

**Example Violation**:
```typescript
// ❌ Violates DIP - depends on concrete class
class UserService {
  private db = new MySQLDatabase();  // Tight coupling!

  getUser(id: string) {
    return this.db.query('SELECT * FROM users WHERE id = ?', [id]);
  }
}

// ✅ Follows DIP - depends on abstraction
interface Database {
  query(sql: string, params: any[]): any;
}

class MySQLDatabase implements Database {
  query(sql: string, params: any[]) { /* ... */ }
}

class UserService {
  constructor(private db: Database) {}  // Injected abstraction

  getUser(id: string) {
    return this.db.query('SELECT * FROM users WHERE id = ?', [id]);
  }
}

// Can now swap implementations easily
const service1 = new UserService(new MySQLDatabase());
const service2 = new UserService(new PostgreSQLDatabase());
```

---

## Integration with Code-Maintenance-Agent

### Stage 1: Analysis
All SIG-TOP-10 and SOLID violations are detected as findings:

```typescript
{
  id: 'SIG-001',
  category: 'code_quality',
  severity: 'medium',
  title: 'SIG Guideline #2 Violation: High cyclomatic complexity',
  description: 'Function processPayment() has complexity of 18, exceeding SIG threshold of 10',
  location: 'src/payment/processor.ts:42',
  recommendation: 'Refactor using strategy pattern to reduce complexity',
  estimatedEffort: 3,
  riskIfNotFixed: 'medium',
  autoFixable: false,
  bestPractice: 'SIG-TOP-10 #2: Write Simple Units of Code'
}

{
  id: 'SOLID-001',
  category: 'code_quality',
  severity: 'medium',
  title: 'SOLID SRP Violation: Class has multiple responsibilities',
  description: 'UserManager class mixes data access, business logic, and presentation concerns',
  location: 'src/user/UserManager.ts',
  recommendation: 'Split into UserRepository, UserService, and UserView',
  estimatedEffort: 5,
  riskIfNotFixed: 'medium',
  autoFixable: false,
  bestPractice: 'SOLID: Single Responsibility Principle'
}
```

### Action Breakdown Checklists
Each best practice violation has specific checklist actions (see individual principle sections above).

### Quality Score
```typescript
interface BestPracticeScore {
  sigCompliance: {
    overall: number;  // 0-100%
    guidelines: Array<{
      number: number;
      name: string;
      compliance: number;
      violations: number;
    }>;
  };
  solidCompliance: {
    overall: number;  // 0-100%
    principles: Array<{
      name: 'SRP' | 'OCP' | 'LSP' | 'ISP' | 'DIP';
      compliance: number;
      violations: number;
    }>;
  };
  totalScore: number;  // Combined 0-100%
}
```

---

## Tools for Detection

### SIG-TOP-10 Detection
- **#1 Short Units**: ESLint max-lines-per-function, SonarQube
- **#2 Simple Units**: ESLint complexity, SonarQube cognitive complexity
- **#3 Write Once**: SonarQube duplication, jscpd
- **#4 Small Interfaces**: ESLint max-params
- **#5 Separate Concerns**: Manual review, SonarQube
- **#6 Loose Coupling**: dependency-cruiser
- **#7 Balanced Components**: SonarQube, cloc
- **#8 Small Codebase**: SonarQube, cloc
- **#9 Automate Pipeline**: GitHub Actions, pre-commit hooks
- **#10 Clean Code**: ESLint, Prettier, documentation linters

### SOLID Detection
- **SRP**: SonarQube (too many responsibilities)
- **OCP**: Manual review (type switch detection)
- **LSP**: TypeScript compiler (type violations)
- **ISP**: ESLint (interface size), manual review
- **DIP**: Manual review, dependency analysis

---

## See Also

- [MAINTENANCE Work Type Documentation](./MAINTENANCE_WORK_TYPE.md)
- [Code-Maintenance-Agent Workflow](../workflows/codeMaintenanceAgent.ts)
- [Action Breakdown Examples](../WEEK_8_DAY_5_ACTION_BREAKDOWN.md)

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Status**: ✅ Active in Quality Gates
