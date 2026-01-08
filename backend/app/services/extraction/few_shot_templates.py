"""
Few-Shot Templates per Domain - Week 102

Domain-specific examples for story extraction that improve LLM accuracy
by providing relevant context and patterns for each business domain.

Usage:
    templates = FewShotTemplateLoader()

    # Get templates for a domain
    healthcare_templates = templates.get_templates("healthcare")

    # Get prompt with few-shot examples
    prompt = templates.build_extraction_prompt(
        code_snippet="...",
        domain="finance"
    )

    # Auto-detect domain and get best templates
    prompt = templates.build_smart_prompt(code_snippet)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import re


class ExtractionDomain(Enum):
    """Supported domains for few-shot templates."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    GENERIC = "generic"


@dataclass
class FewShotExample:
    """A single few-shot example for story extraction."""
    name: str
    domain: ExtractionDomain
    code_input: str
    expected_output: str
    explanation: str
    tags: List[str] = field(default_factory=list)


@dataclass
class DomainTemplateSet:
    """Collection of templates for a domain."""
    domain: ExtractionDomain
    description: str
    examples: List[FewShotExample]
    domain_context: str
    common_entities: List[str]
    common_actions: List[str]


class FewShotTemplateLoader:
    """
    Loads and manages domain-specific few-shot templates.

    Provides examples that help LLMs understand the expected
    output format and domain-specific patterns.
    """

    def __init__(self):
        self._templates: Dict[ExtractionDomain, DomainTemplateSet] = {}
        self._load_all_templates()

    def _load_all_templates(self) -> None:
        """Load all domain templates."""
        self._templates[ExtractionDomain.HEALTHCARE] = self._build_healthcare_templates()
        self._templates[ExtractionDomain.FINANCE] = self._build_finance_templates()
        self._templates[ExtractionDomain.ECOMMERCE] = self._build_ecommerce_templates()
        self._templates[ExtractionDomain.GENERIC] = self._build_generic_templates()

    # =========================================================================
    # Healthcare Templates
    # =========================================================================

    def _build_healthcare_templates(self) -> DomainTemplateSet:
        """Build healthcare domain templates."""
        examples = [
            FewShotExample(
                name="Patient Registration",
                domain=ExtractionDomain.HEALTHCARE,
                code_input='''
def register_patient(patient_data: dict) -> Patient:
    """Register a new patient in the system."""
    # Validate BSN (Dutch citizen ID)
    if not validate_bsn(patient_data.get('bsn')):
        raise ValidationError("Invalid BSN format")

    # Check for duplicate registration
    existing = Patient.query.filter_by(bsn=patient_data['bsn']).first()
    if existing:
        raise DuplicateError("Patient already registered")

    # Create patient record
    patient = Patient(
        bsn=patient_data['bsn'],
        name=patient_data['name'],
        date_of_birth=patient_data['dob'],
        email=patient_data.get('email'),
        phone=patient_data.get('phone'),
        insurance_number=patient_data.get('insurance_number')
    )

    # Log for audit trail (NEN7510 compliance)
    audit_log.record('patient_registration', patient.id)

    db.session.add(patient)
    db.session.commit()
    return patient
''',
                expected_output='''
## User Story: Patient Registration

**As a** healthcare administrator
**I want to** register new patients in the system
**So that** their medical records can be properly managed

### Acceptance Criteria

**Given** a new patient with valid identification
**When** the administrator submits registration data
**Then** the system should:
- Validate the BSN format according to Dutch standards
- Check for existing patient records with the same BSN
- Create a new patient record with all provided information
- Record the registration in the audit trail for NEN7510 compliance
- Return confirmation of successful registration

### Business Rules
1. BSN must be valid according to Dutch 11-check algorithm
2. Duplicate registrations are not allowed
3. All patient registrations must be audit logged (NEN7510)
4. Email and phone are optional fields
5. Insurance number is optional but recommended

### Non-Functional Requirements
- Audit trail must be immutable
- Patient data must be encrypted at rest (HIPAA/NEN7510)
''',
                explanation="Extracts patient registration story with compliance requirements",
                tags=["registration", "compliance", "NEN7510"],
            ),
            FewShotExample(
                name="Medication Prescription",
                domain=ExtractionDomain.HEALTHCARE,
                code_input='''
def create_prescription(doctor_id: int, patient_id: int, medication: dict) -> Prescription:
    """Create a new prescription for a patient."""
    # Verify doctor authorization
    doctor = Doctor.query.get(doctor_id)
    if not doctor or not doctor.is_active:
        raise AuthorizationError("Doctor not authorized to prescribe")

    # Check patient allergies
    patient = Patient.query.get(patient_id)
    allergies = patient.get_allergies()
    if medication['name'] in allergies:
        raise SafetyError(f"Patient allergic to {medication['name']}")

    # Check drug interactions
    current_medications = patient.get_current_medications()
    interactions = check_drug_interactions(medication['name'], current_medications)
    if interactions:
        raise SafetyError(f"Drug interaction detected: {interactions}")

    # Create prescription
    prescription = Prescription(
        doctor_id=doctor_id,
        patient_id=patient_id,
        medication_name=medication['name'],
        dosage=medication['dosage'],
        frequency=medication['frequency'],
        duration_days=medication['duration'],
        refills_allowed=medication.get('refills', 0)
    )

    db.session.add(prescription)
    db.session.commit()
    return prescription
''',
                expected_output='''
## User Story: Medication Prescription

**As a** licensed doctor
**I want to** create prescriptions for my patients
**So that** they can receive appropriate medication treatment

### Acceptance Criteria

**Given** an authorized doctor and a registered patient
**When** the doctor creates a prescription
**Then** the system should:
- Verify the doctor's authorization and active status
- Check patient's allergy records against prescribed medication
- Verify no dangerous drug interactions exist
- Create the prescription with complete dosage information
- Store refill allowance if specified

### Business Rules
1. Only active, authorized doctors can create prescriptions
2. System MUST block prescriptions for medications patient is allergic to
3. System MUST check for drug interactions with current medications
4. Dosage, frequency, and duration are required fields
5. Refills default to 0 if not specified

### Safety Requirements
- Allergy check is MANDATORY before prescription creation
- Drug interaction check is MANDATORY
- All prescription events must be logged for medical audit
''',
                explanation="Extracts prescription workflow with safety checks",
                tags=["prescription", "safety", "authorization"],
            ),
            FewShotExample(
                name="Appointment Scheduling",
                domain=ExtractionDomain.HEALTHCARE,
                code_input='''
def schedule_appointment(patient_id: int, doctor_id: int,
                         datetime: datetime, appointment_type: str) -> Appointment:
    """Schedule a patient appointment with a doctor."""
    # Check doctor availability
    if not is_doctor_available(doctor_id, datetime):
        raise AvailabilityError("Doctor not available at requested time")

    # Check for conflicting appointments
    existing = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.datetime == datetime,
        Appointment.status != 'cancelled'
    ).first()
    if existing:
        raise ConflictError("Patient has existing appointment at this time")

    # Determine appointment duration based on type
    duration = get_appointment_duration(appointment_type)

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        datetime=datetime,
        duration_minutes=duration,
        appointment_type=appointment_type,
        status='scheduled'
    )

    # Send confirmation
    send_appointment_confirmation(patient_id, appointment)

    db.session.add(appointment)
    db.session.commit()
    return appointment
''',
                expected_output='''
## User Story: Appointment Scheduling

**As a** patient or healthcare staff
**I want to** schedule appointments with doctors
**So that** patients can receive timely medical care

### Acceptance Criteria

**Given** a patient needs to see a doctor
**When** scheduling an appointment
**Then** the system should:
- Verify doctor availability at the requested time
- Check for conflicting patient appointments
- Determine appropriate duration based on appointment type
- Create the appointment with 'scheduled' status
- Send confirmation notification to the patient

### Business Rules
1. Cannot schedule when doctor is unavailable
2. Patient cannot have overlapping appointments
3. Cancelled appointments do not block new scheduling
4. Appointment duration varies by type (consultation, follow-up, etc.)
5. Confirmation must be sent upon successful scheduling

### Edge Cases
- Handle timezone differences
- Consider buffer time between appointments
''',
                explanation="Extracts scheduling workflow with availability checks",
                tags=["scheduling", "availability", "notification"],
            ),
        ]

        return DomainTemplateSet(
            domain=ExtractionDomain.HEALTHCARE,
            description="Healthcare and medical system templates",
            examples=examples,
            domain_context="""
Healthcare systems must comply with regulations like HIPAA, NEN7510, and GDPR.
Key concerns: patient privacy, data security, audit trails, medical safety.
Common workflows: patient registration, appointments, prescriptions, medical records.
""",
            common_entities=["Patient", "Doctor", "Appointment", "Prescription", "MedicalRecord", "Insurance"],
            common_actions=["register", "schedule", "prescribe", "diagnose", "refer", "discharge"],
        )

    # =========================================================================
    # Finance Templates
    # =========================================================================

    def _build_finance_templates(self) -> DomainTemplateSet:
        """Build finance domain templates."""
        examples = [
            FewShotExample(
                name="Fund Transfer",
                domain=ExtractionDomain.FINANCE,
                code_input='''
def transfer_funds(from_account: str, to_account: str,
                   amount: Decimal, description: str) -> Transaction:
    """Transfer funds between accounts."""
    # Validate accounts
    source = Account.query.filter_by(iban=from_account).first()
    if not source:
        raise AccountNotFoundError(f"Source account {from_account} not found")

    destination = Account.query.filter_by(iban=to_account).first()
    if not destination:
        raise AccountNotFoundError(f"Destination account {to_account} not found")

    # Check sufficient balance
    if source.available_balance < amount:
        raise InsufficientFundsError("Insufficient balance for transfer")

    # Check daily transfer limit
    daily_total = get_daily_transfer_total(from_account)
    if daily_total + amount > source.daily_limit:
        raise LimitExceededError("Daily transfer limit exceeded")

    # AML check for large transfers
    if amount > Decimal('10000'):
        aml_check(from_account, to_account, amount)

    # Execute transfer
    source.balance -= amount
    destination.balance += amount

    transaction = Transaction(
        from_account=from_account,
        to_account=to_account,
        amount=amount,
        description=description,
        status='completed',
        timestamp=datetime.utcnow()
    )

    db.session.add(transaction)
    db.session.commit()
    return transaction
''',
                expected_output='''
## User Story: Fund Transfer

**As a** bank customer
**I want to** transfer money between accounts
**So that** I can pay bills and move funds as needed

### Acceptance Criteria

**Given** a customer with a valid source account
**When** initiating a fund transfer
**Then** the system should:
- Validate both source and destination accounts exist
- Verify sufficient available balance in source account
- Check transfer against daily limit
- Perform AML screening for transfers over €10,000
- Debit source and credit destination atomically
- Record transaction with timestamp and status

### Business Rules
1. Both accounts must exist and be valid
2. Source account must have sufficient available balance
3. Transfer cannot exceed daily limit
4. Transfers over €10,000 require AML (Anti-Money Laundering) check
5. Transaction must be atomic (all or nothing)

### Compliance Requirements
- AML screening mandatory for large transfers
- All transactions must be logged with timestamp
- PCI-DSS compliance for cardholder data
''',
                explanation="Extracts fund transfer with compliance checks",
                tags=["transfer", "AML", "balance"],
            ),
            FewShotExample(
                name="Account Opening",
                domain=ExtractionDomain.FINANCE,
                code_input='''
def open_account(customer_id: int, account_type: str,
                 initial_deposit: Decimal = None) -> Account:
    """Open a new bank account for a customer."""
    # KYC verification
    customer = Customer.query.get(customer_id)
    if not customer:
        raise CustomerNotFoundError("Customer not found")

    if not customer.kyc_verified:
        raise KYCError("Customer KYC verification incomplete")

    # Check account limits
    existing_accounts = Account.query.filter_by(
        customer_id=customer_id,
        account_type=account_type,
        status='active'
    ).count()

    max_accounts = get_max_accounts_by_type(account_type)
    if existing_accounts >= max_accounts:
        raise LimitError(f"Maximum {account_type} accounts reached")

    # Generate IBAN
    iban = generate_iban(country_code='NL', bank_code='MARK')

    # Create account
    account = Account(
        customer_id=customer_id,
        iban=iban,
        account_type=account_type,
        balance=initial_deposit or Decimal('0'),
        status='active',
        daily_limit=get_default_daily_limit(account_type)
    )

    db.session.add(account)
    db.session.commit()

    # Send welcome notification
    send_account_opened_notification(customer, account)

    return account
''',
                expected_output='''
## User Story: Account Opening

**As a** verified bank customer
**I want to** open a new bank account
**So that** I can manage my finances with the bank

### Acceptance Criteria

**Given** a KYC-verified customer
**When** requesting to open a new account
**Then** the system should:
- Verify customer exists and KYC is complete
- Check customer hasn't exceeded account limits for this type
- Generate a valid IBAN for the new account
- Create account with appropriate default settings
- Process initial deposit if provided
- Send welcome notification to customer

### Business Rules
1. KYC verification MUST be complete before account opening
2. Maximum number of accounts per type is enforced
3. IBAN must follow standard format (country + bank code + account)
4. Initial deposit is optional (defaults to 0)
5. Daily limit set based on account type

### Compliance Requirements
- KYC (Know Your Customer) mandatory
- IBAN format must comply with ISO 13616
''',
                explanation="Extracts account opening with KYC requirements",
                tags=["account", "KYC", "IBAN"],
            ),
            FewShotExample(
                name="Fraud Detection Alert",
                domain=ExtractionDomain.FINANCE,
                code_input='''
def process_transaction_with_fraud_check(transaction_data: dict) -> Transaction:
    """Process transaction with real-time fraud detection."""
    account = Account.query.get(transaction_data['account_id'])

    # Calculate fraud score
    fraud_score = calculate_fraud_score(
        account=account,
        amount=transaction_data['amount'],
        merchant=transaction_data.get('merchant'),
        location=transaction_data.get('location'),
        device_fingerprint=transaction_data.get('device_id')
    )

    # High risk - block and alert
    if fraud_score > 0.8:
        block_account(account.id, reason='fraud_suspected')
        notify_fraud_team(account, transaction_data, fraud_score)
        raise FraudSuspectedError("Transaction blocked due to fraud risk")

    # Medium risk - require additional verification
    if fraud_score > 0.5:
        require_2fa_verification(account, transaction_data)

    # Process transaction
    transaction = create_transaction(transaction_data)
    transaction.fraud_score = fraud_score

    db.session.add(transaction)
    db.session.commit()
    return transaction
''',
                expected_output='''
## User Story: Fraud Detection

**As a** financial institution
**I want to** detect and prevent fraudulent transactions
**So that** customers are protected from financial crime

### Acceptance Criteria

**Given** a transaction is initiated
**When** processing the transaction
**Then** the system should:
- Calculate fraud risk score based on multiple factors
- Block transaction and account if fraud score > 80%
- Require 2FA verification if fraud score > 50%
- Alert fraud team for high-risk transactions
- Record fraud score with transaction for audit

### Business Rules
1. Fraud score considers: amount, merchant, location, device
2. Score > 0.8: Block account, alert fraud team, reject transaction
3. Score > 0.5: Require additional 2FA verification
4. Score <= 0.5: Process normally with recorded score
5. All blocked transactions must notify fraud team

### Security Requirements
- Real-time fraud scoring is mandatory
- Account blocking must be immediate
- Fraud alerts must reach team within 1 minute
''',
                explanation="Extracts fraud detection workflow",
                tags=["fraud", "security", "2FA"],
            ),
        ]

        return DomainTemplateSet(
            domain=ExtractionDomain.FINANCE,
            description="Banking and financial services templates",
            examples=examples,
            domain_context="""
Financial systems must comply with PCI-DSS, AML/KYC regulations, and banking laws.
Key concerns: transaction security, fraud prevention, regulatory compliance, audit trails.
Common workflows: transfers, payments, account management, fraud detection.
""",
            common_entities=["Account", "Transaction", "Customer", "Payment", "Card", "Loan"],
            common_actions=["transfer", "deposit", "withdraw", "verify", "block", "authorize"],
        )

    # =========================================================================
    # E-Commerce Templates
    # =========================================================================

    def _build_ecommerce_templates(self) -> DomainTemplateSet:
        """Build e-commerce domain templates."""
        examples = [
            FewShotExample(
                name="Add to Cart",
                domain=ExtractionDomain.ECOMMERCE,
                code_input='''
def add_to_cart(user_id: int, product_id: int, quantity: int) -> CartItem:
    """Add a product to the user's shopping cart."""
    # Get or create cart
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        cart = Cart(user_id=user_id, status='active')
        db.session.add(cart)

    # Validate product
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        raise ProductNotFoundError("Product not available")

    # Check stock
    if product.stock_quantity < quantity:
        raise OutOfStockError(f"Only {product.stock_quantity} items available")

    # Check for existing cart item
    existing_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product_id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if product.stock_quantity < new_quantity:
            raise OutOfStockError("Not enough stock for requested quantity")
        existing_item.quantity = new_quantity
        return existing_item

    # Create new cart item
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=product_id,
        quantity=quantity,
        price_at_addition=product.current_price
    )

    db.session.add(cart_item)
    db.session.commit()
    return cart_item
''',
                expected_output='''
## User Story: Add to Cart

**As a** shopper
**I want to** add products to my shopping cart
**So that** I can purchase multiple items together

### Acceptance Criteria

**Given** a logged-in user browsing products
**When** adding a product to cart
**Then** the system should:
- Create a cart if user doesn't have an active one
- Validate product exists and is active
- Check sufficient stock is available
- Update quantity if product already in cart
- Capture price at time of addition
- Confirm item was added successfully

### Business Rules
1. Each user has one active cart at a time
2. Cannot add inactive or non-existent products
3. Cannot add more items than available stock
4. Adding existing product increases quantity (doesn't duplicate)
5. Total quantity cannot exceed available stock
6. Price is captured at addition time (may differ at checkout)

### Edge Cases
- Handle concurrent stock updates
- Guest cart conversion on login
''',
                explanation="Extracts add-to-cart workflow with stock management",
                tags=["cart", "stock", "product"],
            ),
            FewShotExample(
                name="Checkout Process",
                domain=ExtractionDomain.ECOMMERCE,
                code_input='''
def process_checkout(user_id: int, payment_method: str,
                     shipping_address: dict) -> Order:
    """Process checkout and create order."""
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart or not cart.items:
        raise EmptyCartError("Cart is empty")

    # Validate shipping address
    if not validate_address(shipping_address):
        raise InvalidAddressError("Invalid shipping address")

    # Calculate totals
    subtotal = sum(item.quantity * item.price_at_addition for item in cart.items)
    shipping_cost = calculate_shipping(shipping_address, cart.items)
    tax = calculate_tax(subtotal, shipping_address)
    total = subtotal + shipping_cost + tax

    # Apply discount if available
    discount = apply_cart_discounts(cart)
    total -= discount

    # Reserve inventory
    for item in cart.items:
        reserve_inventory(item.product_id, item.quantity)

    # Process payment
    payment_result = process_payment(user_id, payment_method, total)
    if not payment_result.success:
        release_inventory_reservations(cart.items)
        raise PaymentFailedError(payment_result.error)

    # Create order
    order = Order(
        user_id=user_id,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        discount=discount,
        total=total,
        shipping_address=shipping_address,
        payment_id=payment_result.transaction_id,
        status='confirmed'
    )

    # Transfer cart items to order
    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price_at_addition
        )
        db.session.add(order_item)

    # Clear cart
    cart.status = 'converted'

    # Send confirmation
    send_order_confirmation(user_id, order)

    db.session.commit()
    return order
''',
                expected_output='''
## User Story: Checkout Process

**As a** customer with items in cart
**I want to** complete my purchase
**So that** I can receive the products I selected

### Acceptance Criteria

**Given** a customer with items in their cart
**When** proceeding to checkout
**Then** the system should:
- Validate cart is not empty
- Validate shipping address format
- Calculate subtotal, shipping, tax, and apply discounts
- Reserve inventory for cart items
- Process payment through selected method
- Create order with all line items and totals
- Send order confirmation email
- Convert cart status (prevent reuse)

### Business Rules
1. Cannot checkout with empty cart
2. Shipping address must be valid and complete
3. Inventory must be reserved before payment
4. If payment fails, release inventory reservations
5. Discounts applied after subtotal calculation
6. Order confirmation sent on successful payment
7. Cart marked as 'converted' after successful order

### Payment Flow
1. Reserve inventory → 2. Process payment → 3. Create order
- On payment failure: release reservations, show error

### Non-Functional Requirements
- Payment processing must complete within 30 seconds
- Order confirmation email within 5 minutes
''',
                explanation="Extracts complete checkout workflow",
                tags=["checkout", "payment", "order"],
            ),
            FewShotExample(
                name="Product Return",
                domain=ExtractionDomain.ECOMMERCE,
                code_input='''
def initiate_return(order_id: int, items: list, reason: str) -> Return:
    """Initiate a product return request."""
    order = Order.query.get(order_id)
    if not order:
        raise OrderNotFoundError("Order not found")

    # Check return window (30 days)
    days_since_delivery = (datetime.utcnow() - order.delivered_at).days
    if days_since_delivery > 30:
        raise ReturnWindowExpiredError("Return window has expired (30 days)")

    # Validate items are from this order
    order_product_ids = {item.product_id for item in order.items}
    for item in items:
        if item['product_id'] not in order_product_ids:
            raise InvalidReturnItemError(f"Product {item['product_id']} not in order")

    # Check items not already returned
    existing_returns = Return.query.filter_by(order_id=order_id).all()
    returned_product_ids = {r.product_id for r in existing_returns if r.status != 'rejected'}
    for item in items:
        if item['product_id'] in returned_product_ids:
            raise DuplicateReturnError(f"Product {item['product_id']} already returned")

    # Calculate refund amount
    refund_amount = sum(
        get_item_price(order_id, item['product_id']) * item['quantity']
        for item in items
    )

    # Create return request
    return_request = Return(
        order_id=order_id,
        user_id=order.user_id,
        items=items,
        reason=reason,
        refund_amount=refund_amount,
        status='pending',
        return_label=generate_return_label()
    )

    db.session.add(return_request)
    db.session.commit()

    # Send return instructions
    send_return_instructions(order.user_id, return_request)

    return return_request
''',
                expected_output='''
## User Story: Product Return

**As a** customer who received an order
**I want to** return products I'm not satisfied with
**So that** I can get a refund or exchange

### Acceptance Criteria

**Given** a customer with a delivered order
**When** initiating a return request
**Then** the system should:
- Verify order exists and was delivered
- Check return is within 30-day window
- Validate all items are from the specified order
- Ensure items haven't already been returned
- Calculate refund amount based on original prices
- Generate return shipping label
- Send return instructions to customer

### Business Rules
1. Returns only allowed within 30 days of delivery
2. Can only return items from the specified order
3. Cannot return same item twice (unless previous return rejected)
4. Refund calculated at original purchase price
5. Return label generated automatically
6. Return status starts as 'pending'

### Consumer Rights
- 30-day return window per EU consumer protection
- Full refund for items in original condition
- Return shipping label provided free of charge
''',
                explanation="Extracts return workflow with consumer rights",
                tags=["return", "refund", "consumer_rights"],
            ),
        ]

        return DomainTemplateSet(
            domain=ExtractionDomain.ECOMMERCE,
            description="E-commerce and retail templates",
            examples=examples,
            domain_context="""
E-commerce systems must handle GDPR, consumer protection laws, and payment security.
Key concerns: inventory management, payment processing, order fulfillment, returns.
Common workflows: browsing, cart management, checkout, order tracking, returns.
""",
            common_entities=["Product", "Cart", "Order", "Customer", "Payment", "Shipping"],
            common_actions=["browse", "add", "remove", "checkout", "pay", "ship", "return"],
        )

    # =========================================================================
    # Generic Templates
    # =========================================================================

    def _build_generic_templates(self) -> DomainTemplateSet:
        """Build generic domain templates."""
        examples = [
            FewShotExample(
                name="User Registration",
                domain=ExtractionDomain.GENERIC,
                code_input='''
def register_user(email: str, password: str, name: str) -> User:
    """Register a new user account."""
    # Validate email format
    if not is_valid_email(email):
        raise ValidationError("Invalid email format")

    # Check for existing user
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise DuplicateError("Email already registered")

    # Validate password strength
    if not is_strong_password(password):
        raise ValidationError("Password does not meet requirements")

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        name=name,
        status='pending_verification'
    )

    db.session.add(user)
    db.session.commit()

    # Send verification email
    send_verification_email(user)

    return user
''',
                expected_output='''
## User Story: User Registration

**As a** new visitor
**I want to** create an account
**So that** I can access the system's features

### Acceptance Criteria

**Given** a visitor on the registration page
**When** submitting registration details
**Then** the system should:
- Validate email format
- Check email is not already registered
- Validate password meets strength requirements
- Hash password securely (never store plain text)
- Create user with 'pending_verification' status
- Send verification email to user

### Business Rules
1. Email must be valid format
2. Email must be unique in the system
3. Password must meet strength requirements
4. Passwords stored as secure hash only
5. New accounts require email verification

### Security Requirements
- Password hashing with bcrypt or similar
- Rate limiting on registration endpoint
- CAPTCHA for bot prevention
''',
                explanation="Extracts generic user registration workflow",
                tags=["registration", "authentication", "security"],
            ),
        ]

        return DomainTemplateSet(
            domain=ExtractionDomain.GENERIC,
            description="Generic application templates",
            examples=examples,
            domain_context="""
Generic application patterns applicable across domains.
Key concerns: authentication, authorization, data management, user experience.
Common workflows: registration, login, CRUD operations, notifications.
""",
            common_entities=["User", "Role", "Permission", "Setting", "Notification"],
            common_actions=["create", "read", "update", "delete", "authenticate", "authorize"],
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def get_templates(self, domain: str) -> Optional[DomainTemplateSet]:
        """
        Get template set for a domain.

        Args:
            domain: Domain name (healthcare, finance, ecommerce, generic)

        Returns:
            DomainTemplateSet or None
        """
        try:
            domain_enum = ExtractionDomain(domain.lower())
            return self._templates.get(domain_enum)
        except ValueError:
            return None

    def get_all_domains(self) -> List[str]:
        """Get list of all supported domains."""
        return [d.value for d in ExtractionDomain]

    def get_examples(
        self,
        domain: str,
        max_examples: int = 3,
    ) -> List[FewShotExample]:
        """
        Get examples for a domain.

        Args:
            domain: Domain name
            max_examples: Maximum number of examples to return

        Returns:
            List of FewShotExample objects
        """
        template_set = self.get_templates(domain)
        if not template_set:
            return []
        return template_set.examples[:max_examples]

    def build_extraction_prompt(
        self,
        code_snippet: str,
        domain: str,
        num_examples: int = 2,
    ) -> str:
        """
        Build a complete extraction prompt with few-shot examples.

        Args:
            code_snippet: Code to extract stories from
            domain: Target domain
            num_examples: Number of examples to include

        Returns:
            Complete prompt string
        """
        template_set = self.get_templates(domain)
        if not template_set:
            template_set = self._templates[ExtractionDomain.GENERIC]

        prompt_parts = [
            "# Story Extraction Task\n",
            f"## Domain Context\n{template_set.domain_context}\n",
            f"## Common Entities: {', '.join(template_set.common_entities)}\n",
            f"## Common Actions: {', '.join(template_set.common_actions)}\n",
            "\n## Examples\n",
        ]

        # Add few-shot examples
        for i, example in enumerate(template_set.examples[:num_examples], 1):
            prompt_parts.append(f"\n### Example {i}: {example.name}\n")
            prompt_parts.append(f"**Input Code:**\n```python\n{example.code_input.strip()}\n```\n")
            prompt_parts.append(f"**Expected Output:**\n{example.expected_output.strip()}\n")

        # Add the actual task
        prompt_parts.append("\n## Your Task\n")
        prompt_parts.append("Extract user stories from the following code:\n")
        prompt_parts.append(f"```python\n{code_snippet}\n```\n")
        prompt_parts.append("\nProvide output in the same format as the examples above.")

        return "".join(prompt_parts)

    def detect_domain(self, code_snippet: str) -> Tuple[ExtractionDomain, float]:
        """
        Auto-detect domain from code snippet.

        Args:
            code_snippet: Code to analyze

        Returns:
            Tuple of (detected domain, confidence score)
        """
        code_lower = code_snippet.lower()

        domain_scores = {}

        for domain, template_set in self._templates.items():
            score = 0
            # Check for entity mentions
            for entity in template_set.common_entities:
                if entity.lower() in code_lower:
                    score += 2

            # Check for action mentions
            for action in template_set.common_actions:
                if action.lower() in code_lower:
                    score += 1

            domain_scores[domain] = score

        if not domain_scores or max(domain_scores.values()) == 0:
            return ExtractionDomain.GENERIC, 0.0

        best_domain = max(domain_scores, key=lambda d: domain_scores[d])
        total_score = sum(domain_scores.values())
        confidence = domain_scores[best_domain] / total_score if total_score > 0 else 0

        return best_domain, round(confidence, 2)

    def build_smart_prompt(
        self,
        code_snippet: str,
        num_examples: int = 2,
    ) -> str:
        """
        Build prompt with auto-detected domain.

        Args:
            code_snippet: Code to extract from
            num_examples: Number of examples

        Returns:
            Complete prompt string
        """
        domain, _ = self.detect_domain(code_snippet)
        return self.build_extraction_prompt(code_snippet, domain.value, num_examples)


# Convenience functions
def get_few_shot_prompt(code: str, domain: str = "generic") -> str:
    """Quick function to get extraction prompt."""
    return FewShotTemplateLoader().build_extraction_prompt(code, domain)


def get_smart_prompt(code: str) -> str:
    """Quick function with auto-domain detection."""
    return FewShotTemplateLoader().build_smart_prompt(code)
