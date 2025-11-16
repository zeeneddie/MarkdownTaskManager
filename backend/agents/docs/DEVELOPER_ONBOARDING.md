# Developer Onboarding: "By Design" Quality Principles

## Philosophy: Shift-Left Quality

**Build it right from the start, not fix it later.**

Quality gates in this project enforce standards **proactively** through:
1. ✅ Pre-implementation checklists
2. ✅ Real-time quality feedback
3. ✅ Automated blocking for critical violations
4. ✅ Training and documentation

---

## 🧪 TDD (Test-Driven Development) - MANDATORY

### The Red-Green-Refactor Cycle

**ALWAYS write tests BEFORE production code:**

```typescript
// ❌ WRONG: Code first, tests later
class UserService {
  createUser(data) { /* implementation */ }
}
// ... much later ...
test('createUser works', () => { /* test */ });

// ✅ CORRECT: Test first (RED-GREEN-REFACTOR)

// 1. RED: Write failing test
test('createUser should create user with valid data', () => {
  const service = new UserService();
  const user = service.createUser({ name: 'John', email: 'john@example.com' });
  expect(user.id).toBeDefined();
  expect(user.name).toBe('John');
});
// Test fails ❌ - UserService doesn't exist yet

// 2. GREEN: Minimal implementation
class UserService {
  createUser(data) {
    return { id: '123', name: data.name, email: data.email };
  }
}
// Test passes ✅

// 3. REFACTOR: Improve while keeping tests green
class UserService {
  constructor(private db: Database) {}

  createUser(data: UserData): User {
    const user = this.db.users.create(data);
    return user;
  }
}
// Tests still pass ✅, code is better
```

### TDD Checklist (Before Starting ANY Feature)

- [ ] Create test file FIRST: `<filename>.test.ts`
- [ ] Write failing test for first public method
- [ ] Run test to confirm it fails (RED)
- [ ] Write minimal code to pass test (GREEN)
- [ ] Refactor code while keeping tests green
- [ ] Repeat for each method
- [ ] Achieve 80%+ coverage BEFORE committing

**Pre-commit hook will BLOCK if:**
- ❌ Production code exists without tests
- ❌ Test coverage decreased
- ❌ Tests were added after production code (detected via git history)

---

## 🔒 Security - MANDATORY "Secure by Design"

### Security Checklist (Before Writing ANY Code)

#### Input Validation
- [ ] **Validate ALL user input** (never trust user data)
- [ ] Use whitelist validation (allow known good, not block known bad)
- [ ] Sanitize data before using in SQL, HTML, commands
- [ ] Set max length limits on all string inputs

```typescript
// ❌ WRONG: No validation
function createUser(req) {
  const user = db.query(`INSERT INTO users VALUES ('${req.body.name}')`);
}

// ✅ CORRECT: Validate + sanitize + parameterized query
function createUser(req) {
  const schema = z.object({
    name: z.string().min(1).max(100).regex(/^[a-zA-Z\s]+$/),
    email: z.string().email(),
    age: z.number().min(18).max(120)
  });

  const data = schema.parse(req.body); // Throws if invalid
  const user = db.query('INSERT INTO users (name, email, age) VALUES (?, ?, ?)',
    [data.name, data.email, data.age]
  );
}
```

#### Authentication & Authorization
- [ ] Require authentication for ALL protected routes
- [ ] Use JWT or session tokens (never pass credentials in URL)
- [ ] Implement role-based access control (RBAC)
- [ ] Check authorization BEFORE accessing resources

```typescript
// ❌ WRONG: No auth check
app.get('/api/admin/users', (req, res) => {
  const users = db.users.findAll();
  res.json(users);
});

// ✅ CORRECT: Auth + Authorization
app.get('/api/admin/users',
  requireAuth,           // Middleware: Is user logged in?
  requireRole('admin'),  // Middleware: Does user have admin role?
  (req, res) => {
    const users = db.users.findAll();
    res.json(users);
  }
);
```

#### Sensitive Data
- [ ] **NEVER** store passwords in plain text (use bcrypt/argon2)
- [ ] **NEVER** log sensitive data (passwords, tokens, credit cards)
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Encrypt sensitive data at rest (e.g., PII, payment info)

```typescript
// ❌ WRONG: Plain text password
const user = { password: '123456' };
db.users.create(user);

// ✅ CORRECT: Hashed password
import bcrypt from 'bcrypt';
const hashedPassword = await bcrypt.hash(password, 10);
const user = { password: hashedPassword };
db.users.create(user);
```

#### OWASP Top 10 Prevention

1. **Injection (SQL, NoSQL, Command)**: Use parameterized queries, ORM
2. **Broken Authentication**: Strong password policy, MFA, session management
3. **Sensitive Data Exposure**: Encryption, HTTPS only, secure headers
4. **XML External Entities (XXE)**: Disable XML external entity processing
5. **Broken Access Control**: Verify authorization on EVERY request
6. **Security Misconfiguration**: Disable debug mode in production, update dependencies
7. **XSS**: Sanitize output, Content-Security-Policy headers
8. **Insecure Deserialization**: Validate serialized data, use safe formats (JSON)
9. **Using Components with Known Vulnerabilities**: `npm audit`, Snyk scans
10. **Insufficient Logging & Monitoring**: Log security events, set up alerts

**Pre-commit hook will BLOCK if:**
- ❌ Critical security vulnerability detected (Snyk/OWASP ZAP)
- ❌ Hardcoded secrets found in code
- ❌ SQL injection vulnerability detected

---

## 🔐 Privacy (GDPR/Privacy by Design)

### Privacy Checklist (Before Collecting ANY User Data)

#### Data Minimization
- [ ] Collect **ONLY** data you actually need
- [ ] Set retention periods (delete data after X days/months)
- [ ] Allow users to delete their data (Right to be Forgotten)

```typescript
// ❌ WRONG: Collecting unnecessary data
const user = {
  name: 'John',
  email: 'john@example.com',
  phone: '555-1234',
  address: '123 Main St',
  ssn: '123-45-6789',        // ❌ Do you REALLY need this?
  favoriteColor: 'blue',      // ❌ Why are you collecting this?
  browserHistory: [...]       // ❌ Creepy and unnecessary
};

// ✅ CORRECT: Only necessary data
const user = {
  name: 'John',
  email: 'john@example.com'  // Only what's needed for the feature
};
```

#### User Consent
- [ ] Get **explicit consent** before collecting personal data
- [ ] Provide clear privacy policy (what data, why, how long)
- [ ] Allow users to withdraw consent

```typescript
// ✅ CORRECT: Consent mechanism
interface User {
  email: string;
  consents: {
    marketing: boolean;      // User opted in
    analytics: boolean;      // User opted in
    thirdPartySharing: boolean;  // User opted in
    consentDate: Date;
  };
}

// Before sending marketing email:
if (user.consents.marketing) {
  sendMarketingEmail(user.email);
}
```

#### Data Access & Portability
- [ ] Allow users to **view** all their data
- [ ] Allow users to **download** their data (JSON/CSV)
- [ ] Allow users to **delete** their data

```typescript
// ✅ GDPR-compliant endpoints
app.get('/api/users/me/data', requireAuth, (req, res) => {
  const userData = db.users.findById(req.user.id);
  res.json(userData);  // User can see all their data
});

app.get('/api/users/me/export', requireAuth, (req, res) => {
  const userData = db.users.findById(req.user.id);
  res.json(userData);  // User can download their data
});

app.delete('/api/users/me', requireAuth, (req, res) => {
  db.users.delete(req.user.id);  // Right to be Forgotten
  res.json({ message: 'Account deleted' });
});
```

**Pre-commit hook will WARN if:**
- ⚠️ New personal data fields added without consent mechanism
- ⚠️ Data retention policy not defined

---

## 🏗️ DDD (Domain-Driven Design)

### DDD Checklist (Before Designing ANY Feature)

#### 1. Identify Bounded Contexts
- [ ] What is the core domain?
- [ ] What are the subdomains?
- [ ] Where are the boundaries between contexts?

```typescript
// Example: E-commerce system

// Bounded Context 1: Order Management
class Order {
  id: OrderId;
  customerId: CustomerId;
  items: OrderItem[];
  total: Money;
  status: OrderStatus;

  place() { /* ... */ }
  cancel() { /* ... */ }
}

// Bounded Context 2: Inventory Management
class Product {
  id: ProductId;
  sku: string;
  stock: number;

  reserveStock(quantity: number) { /* ... */ }
  releaseStock(quantity: number) { /* ... */ }
}

// Bounded Context 3: Payment Processing
class Payment {
  id: PaymentId;
  orderId: OrderId;
  amount: Money;
  status: PaymentStatus;

  process() { /* ... */ }
  refund() { /* ... */ }
}
```

#### 2. Use Ubiquitous Language
- [ ] Use the **same terms** as domain experts (business, product)
- [ ] Avoid technical jargon in domain models
- [ ] Class/method names should match business language

```typescript
// ❌ WRONG: Technical language
class DataRecord {
  processStuff() { /* ... */ }
  doThing() { /* ... */ }
}

// ✅ CORRECT: Ubiquitous language
class Order {
  place() { /* Business term: "place an order" */ }
  ship() { /* Business term: "ship an order" */ }
  cancel() { /* Business term: "cancel an order" */ }
}
```

#### 3. Aggregate Roots
- [ ] Identify aggregates (cluster of related entities)
- [ ] Define aggregate root (entry point for accessing aggregate)
- [ ] Enforce invariants in aggregate root

```typescript
// ✅ CORRECT: Order is Aggregate Root
class Order {
  private items: OrderItem[] = [];

  // Aggregate root enforces business rules
  addItem(product: Product, quantity: number) {
    if (quantity <= 0) {
      throw new Error('Quantity must be positive');
    }
    if (this.items.length >= 10) {
      throw new Error('Maximum 10 items per order');
    }
    this.items.push(new OrderItem(product, quantity));
  }

  // External code cannot directly modify items
  // Must go through aggregate root
}
```

**Pre-commit hook will WARN if:**
- ⚠️ Domain models contain technical concerns (e.g., database details)
- ⚠️ Bounded context boundaries are violated (cross-context dependencies)

---

## 📏 SOLID Principles

### S - Single Responsibility Principle (SRP)

**Each class should have ONE reason to change.**

```typescript
// ❌ WRONG: Multiple responsibilities
class UserManager {
  createUser(data) { /* database logic */ }
  sendWelcomeEmail(user) { /* email logic */ }
  generateReport(users) { /* reporting logic */ }
}

// ✅ CORRECT: Separate responsibilities
class UserRepository {
  create(data) { /* only database */ }
}

class EmailService {
  sendWelcomeEmail(user) { /* only email */ }
}

class UserReportGenerator {
  generate(users) { /* only reporting */ }
}
```

### O - Open/Closed Principle (OCP)

**Open for extension, closed for modification.**

```typescript
// ❌ WRONG: Modify class for each new payment type
class PaymentProcessor {
  process(payment) {
    if (payment.type === 'credit_card') { /* ... */ }
    else if (payment.type === 'paypal') { /* ... */ }
    else if (payment.type === 'crypto') { /* ... */ }
    // Need to modify class for each new payment type ❌
  }
}

// ✅ CORRECT: Use strategy pattern (extend, don't modify)
interface PaymentMethod {
  process(payment: Payment): Promise<PaymentResult>;
}

class CreditCardPayment implements PaymentMethod {
  process(payment) { /* credit card logic */ }
}

class PayPalPayment implements PaymentMethod {
  process(payment) { /* PayPal logic */ }
}

class PaymentProcessor {
  constructor(private method: PaymentMethod) {}

  process(payment) {
    return this.method.process(payment);
  }
}

// Add new payment types WITHOUT modifying PaymentProcessor ✅
```

### L - Liskov Substitution Principle (LSP)

**Subtypes must be substitutable for their base types.**

```typescript
// ❌ WRONG: Square violates Rectangle's contract
class Rectangle {
  setWidth(w) { this.width = w; }
  setHeight(h) { this.height = h; }
  getArea() { return this.width * this.height; }
}

class Square extends Rectangle {
  setWidth(w) { this.width = w; this.height = w; } // ❌ Breaks LSP
  setHeight(h) { this.width = h; this.height = h; } // ❌ Breaks LSP
}

// Test that works for Rectangle but fails for Square:
function test(rect: Rectangle) {
  rect.setWidth(5);
  rect.setHeight(4);
  assert(rect.getArea() === 20); // ❌ Fails for Square (25 instead of 20)
}

// ✅ CORRECT: Use composition or separate interfaces
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

### I - Interface Segregation Principle (ISP)

**Don't force clients to depend on methods they don't use.**

```typescript
// ❌ WRONG: Fat interface
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
  eat() { throw new Error('Robots don't eat'); } // ❌ Forced to implement
  sleep() { throw new Error('Robots don't sleep'); } // ❌ Forced to implement
}

// ✅ CORRECT: Segregated interfaces
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
  // No need to implement eat() or sleep() ✅
}
```

### D - Dependency Inversion Principle (DIP)

**Depend on abstractions, not concretions.**

```typescript
// ❌ WRONG: High-level depends on low-level (concrete class)
class MySQLDatabase {
  save(data) { /* MySQL-specific code */ }
}

class UserService {
  private db = new MySQLDatabase(); // ❌ Tight coupling

  createUser(data) {
    this.db.save(data);
  }
}

// ✅ CORRECT: Depend on abstraction (interface)
interface Database {
  save(data: any): Promise<void>;
}

class MySQLDatabase implements Database {
  save(data) { /* MySQL-specific */ }
}

class PostgreSQLDatabase implements Database {
  save(data) { /* PostgreSQL-specific */ }
}

class UserService {
  constructor(private db: Database) {} // ✅ Depends on interface

  createUser(data) {
    this.db.save(data);
  }
}

// Easy to swap database ✅
const service = new UserService(new PostgreSQLDatabase());
```

---

## 🧩 GRASP Principles

### Information Expert

**Assign responsibility to the class that has the information needed.**

```typescript
// ❌ WRONG: Customer calculating order total
class Customer {
  calculateOrderTotal(order: Order) {
    return order.items.reduce((sum, item) => sum + item.price, 0);
    // Customer doesn't have order information! ❌
  }
}

// ✅ CORRECT: Order has the information
class Order {
  constructor(private items: OrderItem[]) {}

  calculateTotal() {
    return this.items.reduce((sum, item) => sum + item.price, 0);
  }
}
```

### Low Coupling

**Minimize dependencies between classes.**

```typescript
// ❌ WRONG: High coupling
class OrderService {
  private userRepo = new UserRepository();
  private productRepo = new ProductRepository();
  private emailService = new EmailService();
  private smsService = new SMSService();
  private analyticsService = new AnalyticsService();
  // Too many dependencies! ❌
}

// ✅ CORRECT: Dependency injection (low coupling)
class OrderService {
  constructor(
    private userRepo: IUserRepository,
    private productRepo: IProductRepository,
    private notificationService: INotificationService
  ) {}
  // Fewer dependencies, interfaces instead of concrete classes ✅
}
```

### High Cohesion

**Keep related functionality together.**

```typescript
// ❌ WRONG: Low cohesion (unrelated methods)
class UserService {
  createUser(data) { /* user creation */ }
  sendEmail(to, subject) { /* email sending */ }
  generatePDF(data) { /* PDF generation */ }
  calculateTax(amount) { /* tax calculation */ }
  // Unrelated responsibilities! ❌
}

// ✅ CORRECT: High cohesion (related methods only)
class UserService {
  createUser(data) { /* ... */ }
  updateUser(id, data) { /* ... */ }
  deleteUser(id) { /* ... */ }
  findUserById(id) { /* ... */ }
  // All methods related to user management ✅
}

class EmailService {
  send(to, subject, body) { /* ... */ }
  sendTemplate(to, template, data) { /* ... */ }
  // All methods related to email ✅
}
```

---

## 🎯 Law of Demeter (Principle of Least Knowledge)

**Only talk to your immediate friends.**

```typescript
// ❌ WRONG: Too many dots (violates Law of Demeter)
const total = order.getCart().getItems().calculateTotal();
// order → cart → items → total (too many levels!) ❌

// ✅ CORRECT: Delegation (one dot)
const total = order.calculateTotal();
// Order internally delegates to cart and items ✅

class Order {
  calculateTotal() {
    return this.cart.calculateTotal(); // Order delegates to cart
  }
}

class Cart {
  calculateTotal() {
    return this.items.reduce((sum, item) => sum + item.price, 0);
  }
}
```

---

## 📋 Pre-Implementation Checklist

**Before writing ANY code, ask yourself:**

### Planning
- [ ] Did I write tests FIRST? (TDD)
- [ ] Did I validate requirements with domain experts? (DDD)
- [ ] Did I identify bounded contexts? (DDD)
- [ ] Did I check for existing similar code? (DRY)

### Design
- [ ] Does each class have a single responsibility? (SOLID-SRP)
- [ ] Can I extend without modifying? (SOLID-OCP)
- [ ] Did I use interfaces instead of concrete classes? (SOLID-DIP)
- [ ] Is the class with the information doing the work? (GRASP)
- [ ] Are my dependencies minimal? (GRASP Low Coupling)

### Security & Privacy
- [ ] Do I validate ALL user input?
- [ ] Do I use parameterized queries?
- [ ] Do I hash passwords with bcrypt?
- [ ] Do I have user consent for data collection?
- [ ] Do I minimize data collection?

### Quality
- [ ] Are my functions ≤15 lines? (SIG #1)
- [ ] Is my cyclomatic complexity ≤10? (SIG #2)
- [ ] Do I have ≤4 parameters per function? (SIG #4)
- [ ] Did I avoid code duplication? (SIG #3)

---

## 🚀 Getting Started Workflow

### For Every New Feature:

1. **READ** this document
2. **PLAN** using checklists above
3. **WRITE** tests first (RED)
4. **IMPLEMENT** minimal code (GREEN)
5. **REFACTOR** (keep tests green)
6. **REVIEW** against checklists
7. **COMMIT** (pre-commit hooks will validate)

### If Pre-Commit Hook Blocks You:

```bash
❌ BLOCKING: TDD violation - no test file found

💡 What to do:
1. Create <filename>.test.ts
2. Write failing test
3. Implement code to pass test
4. Commit both files together
```

Don't use `--no-verify` to bypass hooks unless you have a very good reason!

---

## 📚 Further Reading

- [TDD by Example - Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Domain-Driven Design - Eric Evans](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)
- [Clean Code - Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GDPR Compliance Checklist](https://gdpr.eu/checklist/)
- [SIG-TOP-10 Guidelines](./BEST_PRACTICES_REFERENCE.md)

---

## ❓ Questions?

Contact the Quality Team or check:
- [BEST_PRACTICES_REFERENCE.md](./BEST_PRACTICES_REFERENCE.md)
- [ADDITIONAL_BEST_PRACTICES.md](./ADDITIONAL_BEST_PRACTICES.md)
- [MAINTENANCE_WORK_TYPE.md](./MAINTENANCE_WORK_TYPE.md)

---

**Remember: Quality is not retrofitted - it's built in from the start! 🏗️**
