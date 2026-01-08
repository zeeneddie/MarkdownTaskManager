# Additional Software Development Best Practices

## Overview

This document catalogs additional industry-standard best practices that can be integrated into the Code-Maintenance-Agent quality gates, beyond SIG-TOP-10 and SOLID principles.

**Current Integration**: SIG-TOP-10, SOLID
**Future Candidates**: The practices documented below

---

## 1. Object-Oriented Programming (OOP) Principles

### GRASP Principles (General Responsibility Assignment Software Patterns)

#### Information Expert
**Principle**: Assign responsibility to the class that has the information needed to fulfill it

**Quality Gate Check**:
- **Detection**: Methods accessing data from multiple unrelated classes
- **Severity**: medium

**Example Violation**:
```typescript
// ❌ Customer class shouldn't calculate order totals
class Customer {
  calculateOrderTotal(order: Order) {
    return order.items.reduce((sum, item) => sum + item.price, 0);
  }
}

// ✅ Order has the information, Order should calculate
class Order {
  calculateTotal() {
    return this.items.reduce((sum, item) => sum + item.price, 0);
  }
}
```

---

#### Creator
**Principle**: Class A should create instances of Class B if A aggregates, contains, or closely uses B

**Quality Gate Check**:
- **Detection**: Objects created far from their usage
- **Severity**: low

---

#### Low Coupling
**Principle**: Minimize dependencies between classes

**Quality Gate Check**:
- **Metric**: >10 class dependencies = high coupling
- **Severity**: medium

---

#### High Cohesion
**Principle**: Keep responsibilities of a class focused and related

**Quality Gate Check**:
- **Detection**: Classes with >5 unrelated public methods
- **Severity**: medium

---

### Law of Demeter (Principle of Least Knowledge)
**Principle**: A method should only call methods on:
- Itself
- Objects passed as parameters
- Objects it creates
- Its direct component objects

**Quality Gate Check**:
- **Detection**: Chained method calls like `a.getB().getC().doSomething()`
- **Severity**: medium

**Example**:
```typescript
// ❌ Violates Law of Demeter
class Customer {
  placeOrder(order: Order) {
    const total = order.getCart().getItems().calculateTotal();
  }
}

// ✅ Follows Law of Demeter
class Customer {
  placeOrder(order: Order) {
    const total = order.calculateTotal();  // Order delegates internally
  }
}
```

---

## 2. .NET-Specific Best Practices

### Framework Design Guidelines

#### Naming Conventions
**Principle**: PascalCase for public members, camelCase for private, `I` prefix for interfaces

**Quality Gate Check**:
- **Tool**: StyleCop, FxCop
- **Severity**: low

---

#### Async/Await Patterns
**Principle**: All async methods should return Task/Task<T> and end with `Async` suffix

**Quality Gate Check**:
- **Detection**: Async methods without `Async` suffix
- **Severity**: low

**Example**:
```csharp
// ❌ Wrong
public async Task<User> GetUser(int id) { }

// ✅ Correct
public async Task<User> GetUserAsync(int id) { }
```

---

#### IDisposable Pattern
**Principle**: Implement IDisposable for classes that use unmanaged resources

**Quality Gate Check**:
- **Detection**: Classes using streams, connections without IDisposable
- **Severity**: high

---

#### Nullable Reference Types (C# 8+)
**Principle**: Enable nullable reference types to prevent null reference exceptions

**Quality Gate Check**:
- **Detection**: Disabled nullable reference types in project
- **Severity**: medium

---

## 3. Testing Best Practices

### TDD (Test-Driven Development)
**Principle**: Write tests BEFORE writing production code

**The TDD Cycle (Red-Green-Refactor)**:
1. **Red**: Write a failing test
2. **Green**: Write minimal code to make test pass
3. **Refactor**: Improve code while keeping tests green

**Quality Gate Check**:
- **Detection**: Production code committed without corresponding tests
- **Detection**: Test coverage decrease in commits
- **Severity**: high

**Benefits**:
- Better design (testable code is good code)
- Living documentation (tests show how to use code)
- Fewer bugs (tests written before bugs exist)
- Confidence to refactor

**Example TDD Session**:
```typescript
// 1. RED: Write failing test first
describe('OrderCalculator', () => {
  it('should calculate total with tax', () => {
    const calculator = new OrderCalculator();
    const order = { subtotal: 100, taxRate: 0.1 };

    expect(calculator.calculateTotal(order)).toBe(110);
  });
});
// Test fails: OrderCalculator doesn't exist yet ❌

// 2. GREEN: Write minimal code to pass
class OrderCalculator {
  calculateTotal(order: { subtotal: number; taxRate: number }): number {
    return order.subtotal + (order.subtotal * order.taxRate);
  }
}
// Test passes ✅

// 3. REFACTOR: Improve while keeping tests green
class OrderCalculator {
  calculateTotal(order: { subtotal: number; taxRate: number }): number {
    const tax = this.calculateTax(order.subtotal, order.taxRate);
    return order.subtotal + tax;
  }

  private calculateTax(subtotal: number, rate: number): number {
    return subtotal * rate;
  }
}
// Tests still pass, code is cleaner ✅
```

**TDD Anti-Patterns to Detect**:

1. **No Test, Code First**
```typescript
// ❌ Writing production code without tests
class UserService {
  createUser(data: UserData) {
    // 100 lines of code...
  }
}
// No tests exist for this class!
```

2. **Testing After the Fact**
```typescript
// ❌ Tests written after bugs are found
// Git history shows: 10 commits of production code, then 1 commit adding tests
```

3. **Tests That Don't Drive Design**
```typescript
// ❌ Tests that don't influence implementation
// Test written, but production code ignores what test needs
```

**Quality Gate Actions**:
1. Check git history for test-first commits
2. Measure test coverage per commit (should increase, not decrease)
3. Flag files without corresponding test files
4. Detect large production code commits without test commits

---

### AAA Pattern (Arrange-Act-Assert)
**Principle**: Structure tests in three sections: setup, execution, verification

**Quality Gate Check**:
- **Detection**: Tests without clear AAA structure
- **Severity**: low

**Example**:
```typescript
test('should calculate order total correctly', () => {
  // Arrange
  const order = new Order();
  order.addItem(new Item('Book', 10));
  order.addItem(new Item('Pen', 2));

  // Act
  const total = order.calculateTotal();

  // Assert
  expect(total).toBe(12);
});
```

---

### F.I.R.S.T Principles
**Principle**: Tests should be:
- **Fast**: Run quickly
- **Independent**: No dependencies between tests
- **Repeatable**: Same result every time
- **Self-Validating**: Pass/fail without manual inspection
- **Timely**: Written before/with code (TDD)

**Quality Gate Check**:
- **Fast**: Tests >1 second flagged
- **Independent**: Tests with shared state flagged
- **Severity**: medium

---

### Test Pyramid
**Principle**: Many unit tests, fewer integration tests, minimal E2E tests

**Quality Gate Check**:
- **Ratio**: 70% unit, 20% integration, 10% E2E
- **Severity**: medium

---

### Given-When-Then (BDD)
**Principle**: Structure tests as user scenarios

**Example**:
```typescript
describe('Order Checkout', () => {
  it('should apply discount when user has coupon', () => {
    // Given a user with a 10% coupon
    const user = new User({ coupon: '10OFF' });
    const order = new Order(user, [item1, item2]);

    // When the user checks out
    const total = order.checkout();

    // Then the total should include 10% discount
    expect(total).toBe(expectedDiscountedTotal);
  });
});
```

---

### Test Doubles Patterns
**Principle**: Use mocks, stubs, spies, fakes, dummies appropriately

**Quality Gate Check**:
- **Detection**: Tests with excessive mocking (>5 mocks)
- **Severity**: low

---

## 4. Design Patterns (Gang of Four + Modern)

### Creational Patterns

#### Factory Pattern
**Use Case**: Create objects without specifying exact class

**Quality Gate Check**:
- **Detection**: Direct `new` calls for complex objects with many dependencies
- **Recommendation**: Consider Factory pattern
- **Severity**: low

---

#### Builder Pattern
**Use Case**: Construct complex objects step-by-step

**Quality Gate Check**:
- **Detection**: Constructors with >5 parameters
- **Recommendation**: Consider Builder pattern
- **Severity**: medium

**Example**:
```typescript
// ❌ Complex constructor
const user = new User('John', 'Doe', 30, 'john@example.com', '123 Main St', 'USA', '+1234567890');

// ✅ Builder pattern
const user = new UserBuilder()
  .setFirstName('John')
  .setLastName('Doe')
  .setAge(30)
  .setEmail('john@example.com')
  .setAddress('123 Main St', 'USA')
  .setPhone('+1234567890')
  .build();
```

---

#### Singleton Pattern (Use Sparingly!)
**Use Case**: Ensure only one instance exists

**Quality Gate Check**:
- **Detection**: Overuse of Singleton (>2 in project)
- **Recommendation**: Consider dependency injection instead
- **Severity**: low

---

### Structural Patterns

#### Adapter Pattern
**Use Case**: Make incompatible interfaces work together

**Quality Gate Check**:
- **Detection**: Wrapper classes doing simple interface translation
- **Recommendation**: Document as Adapter pattern
- **Severity**: low

---

#### Decorator Pattern
**Use Case**: Add behavior to objects dynamically

**Quality Gate Check**:
- **Detection**: Excessive inheritance for adding features
- **Recommendation**: Consider Decorator pattern
- **Severity**: medium

---

#### Facade Pattern
**Use Case**: Simplify complex subsystems with unified interface

**Quality Gate Check**:
- **Detection**: Classes directly calling >10 classes in subsystem
- **Recommendation**: Consider Facade pattern
- **Severity**: medium

---

### Behavioral Patterns

#### Command Pattern
**Use Case**: Encapsulate requests as objects

**Quality Gate Check**:
- **Detection**: Functions passed as callbacks with complex state
- **Recommendation**: Consider Command pattern
- **Severity**: low

---

#### Observer Pattern
**Use Case**: Define one-to-many dependency for notifications

**Quality Gate Check**:
- **Detection**: Manual notification loops
- **Recommendation**: Consider Observer/Event pattern
- **Severity**: low

---

#### Strategy Pattern
**Use Case**: Define family of algorithms, make them interchangeable

**Quality Gate Check**:
- **Detection**: Large switch statements on behavior types
- **Recommendation**: Consider Strategy pattern
- **Severity**: medium (already covered by SOLID OCP)

---

## 5. Architecture Principles

### Clean Architecture (Robert C. Martin)
**Principles**:
1. **Independent of Frameworks**: Core business logic doesn't depend on frameworks
2. **Testable**: Business rules testable without UI, database, etc.
3. **Independent of UI**: UI can change without changing business rules
4. **Independent of Database**: Business rules not bound to database
5. **Independent of External Agencies**: Business rules don't know about outside world

**Quality Gate Check**:
- **Detection**: Business logic importing UI or database libraries
- **Severity**: high

**Layers**:
```
┌─────────────────────────────┐
│   UI / Controllers          │
├─────────────────────────────┤
│   Use Cases / Application   │
├─────────────────────────────┤
│   Entities / Domain         │
└─────────────────────────────┘
Dependencies point inward only ↑
```

---

### Hexagonal Architecture (Ports and Adapters)
**Principle**: Isolate core business logic from external concerns

**Quality Gate Check**:
- **Detection**: Domain logic with direct database/HTTP calls
- **Severity**: high

---

### CQRS (Command Query Responsibility Segregation)
**Principle**: Separate read and write operations

**Quality Gate Check**:
- **Detection**: Methods that both modify state AND return data
- **Severity**: medium

**Example**:
```typescript
// ❌ Violates CQRS
class UserService {
  updateAndGetUser(id: string, data: UserData): User {
    this.db.update(id, data);  // Command (write)
    return this.db.get(id);     // Query (read)
  }
}

// ✅ Follows CQRS
class UserService {
  updateUser(id: string, data: UserData): void {  // Command
    this.db.update(id, data);
  }

  getUser(id: string): User {  // Query
    return this.db.get(id);
  }
}
```

---

### Domain-Driven Design (DDD) Principles

#### Ubiquitous Language
**Principle**: Use the same terminology in code as business domain

**Quality Gate Check**:
- **Detection**: Unclear domain terminology in class/method names
- **Severity**: low

---

#### Bounded Contexts
**Principle**: Define clear boundaries for different domain models

**Quality Gate Check**:
- **Detection**: Domain models shared across unrelated modules
- **Severity**: medium

---

#### Aggregates
**Principle**: Cluster domain objects that are modified together

**Quality Gate Check**:
- **Detection**: Direct access to nested entities bypassing aggregate root
- **Severity**: medium

---

## 6. Clean Code Principles (Beyond SIG #10)

### Boy Scout Rule
**Principle**: "Leave the code cleaner than you found it"

**Quality Gate Check**:
- **Detection**: Commits that increase technical debt metrics
- **Severity**: low

---

### YAGNI (You Aren't Gonna Need It)
**Principle**: Don't add functionality until needed

**Quality Gate Check**:
- **Detection**: Unused public methods, interfaces
- **Severity**: low

---

### KISS (Keep It Simple, Stupid)
**Principle**: Simplest solution that works

**Quality Gate Check**:
- **Detection**: Over-engineered solutions (e.g., patterns for simple tasks)
- **Severity**: low

---

### Separation of Concerns
**Principle**: Different responsibilities in different modules

**Quality Gate Check**:
- **Detection**: Modules handling multiple unrelated concerns
- **Severity**: medium (covered by SIG #5)

---

## 7. Security Best Practices (Beyond OWASP Top 10)

### Defense in Depth
**Principle**: Multiple layers of security controls

**Quality Gate Check**:
- **Detection**: Single authentication mechanism without 2FA option
- **Severity**: medium

---

### Principle of Least Privilege
**Principle**: Grant minimum permissions necessary

**Quality Gate Check**:
- **Detection**: Service accounts with admin privileges
- **Severity**: high

---

### Secure by Default
**Principle**: Default configuration should be secure

**Quality Gate Check**:
- **Detection**: Security features disabled by default
- **Severity**: high

**Example**:
```typescript
// ❌ Insecure by default
class API {
  constructor(config: { enableAuth?: boolean }) {
    this.authEnabled = config.enableAuth || false;  // Default: no auth!
  }
}

// ✅ Secure by default
class API {
  constructor(config: { disableAuth?: boolean }) {
    this.authEnabled = !config.disableAuth;  // Default: auth enabled
  }
}
```

---

### Input Validation (Whitelist > Blacklist)
**Principle**: Validate against allowed patterns, not forbidden ones

**Quality Gate Check**:
- **Detection**: Blacklist-based validation
- **Severity**: high

---

## 8. Performance Best Practices

### Big O Complexity Awareness
**Principle**: Understand algorithmic complexity

**Quality Gate Check**:
- **Detection**: O(n²) operations in loops
- **Severity**: medium

---

### Lazy Loading
**Principle**: Load resources only when needed

**Quality Gate Check**:
- **Detection**: Eager loading of large datasets
- **Severity**: medium

---

### Caching Strategies
**Principle**: Cache expensive operations appropriately

**Quality Gate Check**:
- **Detection**: Repeated expensive calculations without caching
- **Severity**: medium

---

### Database Query Optimization
**Principle**: Minimize database round-trips

**Quality Gate Check**:
- **Detection**: N+1 query problem
- **Severity**: high (already checked in Stage 1)

---

## 9. Database Design Principles

### Normalization (3NF)
**Principle**: Eliminate redundancy, maintain data integrity

**Quality Gate Check**:
- **Detection**: Repeated data across tables
- **Severity**: medium

---

### Denormalization (When Appropriate)
**Principle**: Sometimes duplicate data for performance

**Quality Gate Check**:
- **Detection**: Excessive joins (>5 tables)
- **Recommendation**: Consider denormalization
- **Severity**: low

---

### Indexing Strategy
**Principle**: Index frequently queried columns

**Quality Gate Check**:
- **Detection**: Slow queries without indexes
- **Severity**: medium

---

## 10. API Design Best Practices

### RESTful Principles
**Principles**:
1. **Stateless**: Each request contains all information needed
2. **Resource-Based**: URLs represent resources, not actions
3. **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (delete)
4. **HTTP Status Codes**: Use correct codes (200, 201, 400, 404, 500, etc.)

**Quality Gate Check**:
- **Detection**: Non-RESTful endpoints (e.g., `/getUser`, `/deleteUser`)
- **Severity**: low

**Example**:
```
❌ Not RESTful:
GET  /getUser?id=123
POST /createUser
POST /deleteUser

✅ RESTful:
GET    /users/123
POST   /users
DELETE /users/123
```

---

### API Versioning
**Principle**: Version APIs to maintain backward compatibility

**Quality Gate Check**:
- **Detection**: Breaking changes without version increment
- **Severity**: high

---

### Rate Limiting
**Principle**: Protect APIs from abuse

**Quality Gate Check**:
- **Detection**: Public APIs without rate limiting
- **Severity**: medium

---

### Idempotency
**Principle**: Repeated identical requests have same effect as single request

**Quality Gate Check**:
- **Detection**: POST/PUT/DELETE endpoints without idempotency keys
- **Severity**: medium

---

## 11. Microservices Principles

### Single Responsibility per Service
**Principle**: Each microservice does one thing well

**Quality Gate Check**:
- **Detection**: Services with >5 unrelated responsibilities
- **Severity**: high

---

### Database per Service
**Principle**: Each service owns its data

**Quality Gate Check**:
- **Detection**: Services sharing database tables
- **Severity**: high

---

### Circuit Breaker Pattern
**Principle**: Prevent cascade failures

**Quality Gate Check**:
- **Detection**: Service calls without circuit breakers
- **Severity**: medium

---

## 12. Reactive Programming Principles

### Backpressure Handling
**Principle**: Handle fast producers, slow consumers

**Quality Gate Check**:
- **Detection**: Observables without backpressure strategy
- **Severity**: medium

---

### Error Handling in Streams
**Principle**: Proper error propagation in reactive streams

**Quality Gate Check**:
- **Detection**: Streams without error handlers
- **Severity**: medium

---

## Integration Roadmap

### Phase 1 (Completed - Week 9)
- ✅ SIG-TOP-10
- ✅ SOLID Principles

### Phase 2 (Week 10-12) - Suggested
- GRASP Principles (Information Expert, Low Coupling, High Cohesion)
- Law of Demeter
- Clean Code: YAGNI, KISS
- Testing: AAA Pattern, F.I.R.S.T

### Phase 3 (Week 13-15) - Suggested
- Design Patterns detection (Factory, Builder, Strategy)
- Clean Architecture layer violations
- API Design (RESTful, versioning)

### Phase 4 (Week 16-18) - Suggested
- .NET-specific practices (for .NET projects)
- Database design (normalization, indexing)
- Security: Defense in Depth, Least Privilege

### Phase 5 (Future)
- Domain-Driven Design principles
- Microservices patterns
- Reactive programming principles

---

## Tools for Detection

| Best Practice | Detection Tool | Integration Complexity |
|---------------|----------------|------------------------|
| GRASP (Law of Demeter) | TSLint, Custom rules | Medium |
| .NET Guidelines | StyleCop, FxCop, Roslyn Analyzers | Low |
| Testing Patterns | Custom test analyzers | Medium |
| Design Patterns | SonarQube, CodeClimate | Medium |
| Clean Architecture | Dependency analyzers | High |
| API Design | OpenAPI validation, API linters | Low |
| Security | OWASP ZAP, Snyk, SonarQube | Low |
| Performance | Profilers (Clinic.js, dotMemory) | High |

---

## See Also

- [SIG-TOP-10 & SOLID Reference](./BEST_PRACTICES_REFERENCE.md)
- [MAINTENANCE Work Type Documentation](./MAINTENANCE_WORK_TYPE.md)

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Status**: 📋 Planning Document
**Next Review**: Week 10 (Fase 3 Planning)
