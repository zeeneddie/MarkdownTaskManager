# Cryptographic Errors and Vulnerabilities Research

## Executive Summary

This document catalogs common cryptographic errors and vulnerabilities found in software development. Each section provides vulnerable code examples, explanations of the logical flaws, CWE mappings, correct implementations, and real-world incidents where applicable.

**Key Statistics:**
- Cryptographic Failures ranked #4 in OWASP Top 10:2025
- 27.2% of crypto library vulnerabilities are cryptographic issues
- 37.2% are memory safety issues
- Median exploitable lifetime of crypto vulnerabilities: 4.18 years

---

## 1. Key Management Errors

### 1.1 Hardcoded Keys/Secrets

**CWE-321: Use of Hard-coded Cryptographic Key**
**CWE-798: Use of Hard-coded Credentials**

#### Vulnerable Code (Python)

```python
# VULNERABLE: Hardcoded encryption key
import hashlib
from cryptography.fernet import Fernet

# Key embedded directly in source code
ENCRYPTION_KEY = b'my-super-secret-key-12345678901'
API_KEY = "sk_test_EXAMPLE_REDACTED_KEY"  # Example - not a real key

def encrypt_data(data: str) -> bytes:
    # Using hardcoded key
    key = base64.urlsafe_b64encode(hashlib.sha256(ENCRYPTION_KEY).digest())
    f = Fernet(key)
    return f.encrypt(data.encode())

class PaymentProcessor:
    def __init__(self):
        # Hardcoded API credentials
        self.api_secret = "whsec_1234567890abcdef"
```

#### Why It's Wrong

1. **Source Code Exposure**: Keys committed to version control are visible to anyone with repository access
2. **Binary Extraction**: Compiled applications can be reverse-engineered to extract hardcoded keys
3. **No Rotation**: Changing keys requires code changes and redeployment
4. **Shared Risk**: Same key used across all environments (dev, staging, production)

#### Correct Implementation

```python
import os
from cryptography.fernet import Fernet

def get_encryption_key() -> bytes:
    """Retrieve encryption key from secure environment or key management service."""
    # Option 1: Environment variable (minimum security)
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    return key.encode()

    # Option 2: AWS KMS (recommended for production)
    # import boto3
    # kms = boto3.client('kms')
    # response = kms.decrypt(CiphertextBlob=encrypted_key)
    # return response['Plaintext']

    # Option 3: HashiCorp Vault
    # import hvac
    # client = hvac.Client(url=os.environ['VAULT_ADDR'])
    # secret = client.secrets.kv.read_secret_version(path='app/encryption')
    # return secret['data']['data']['key'].encode()

def encrypt_data(data: str) -> bytes:
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(data.encode())
```

#### Real-World Incidents

- **CVE-2025-30406 (Gladinet CentreStack)**: Hardcoded machineKey values in ASP.NET config enabled RCE through ViewState deserialization. Exploited as zero-day, added to CISA KEV catalog April 2025.
- **Toyota Supply Chain (2022)**: Subcontractor exposed private encryption keys through misconfigured GitHub repository.
- **CVE-2022-34442 (Dell EMC)**: Hard-coded cryptographic key allowed attackers to gain LDAP admin privileges.

---

### 1.2 Weak Key Generation

**CWE-330: Use of Insufficiently Random Values**
**CWE-331: Insufficient Entropy**

#### Vulnerable Code (Python)

```python
import random
import time
import hashlib

# VULNERABLE: Using predictable seed for key generation
def generate_weak_key():
    # Seeding with predictable value
    random.seed(int(time.time()))

    # Using non-cryptographic PRNG
    key_bytes = bytes([random.randint(0, 255) for _ in range(32)])
    return key_bytes

# VULNERABLE: Deriving key from low-entropy source
def derive_key_from_password(password: str) -> bytes:
    # No salt, single iteration
    return hashlib.sha256(password.encode()).digest()

# VULNERABLE: Predictable session token
def generate_session_token(user_id: int) -> str:
    timestamp = int(time.time())
    return hashlib.md5(f"{user_id}{timestamp}".encode()).hexdigest()
```

#### Why It's Wrong

1. **Predictable Seeds**: `time.time()` has limited entropy (~seconds precision)
2. **Non-CSPRNG**: `random.random()` is designed for simulations, not security
3. **No Salt**: Same password always produces same key
4. **Low Iteration Count**: Single hash iteration is trivially fast to brute-force

#### Correct Implementation

```python
import secrets
import hashlib
import os

def generate_secure_key(key_length: int = 32) -> bytes:
    """Generate cryptographically secure random key."""
    # Uses OS entropy source (urandom)
    return secrets.token_bytes(key_length)

def derive_key_from_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """Derive key using proper KDF with salt and iterations."""
    import hashlib

    if salt is None:
        salt = os.urandom(16)

    # PBKDF2 with recommended iteration count (OWASP 2023: 600,000 for SHA-256)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        iterations=600_000,
        dklen=32
    )
    return key, salt

def generate_session_token() -> str:
    """Generate unpredictable session token."""
    return secrets.token_urlsafe(32)
```

#### Real-World Incidents

- **Debian OpenSSL (2008)**: Changes to PRNG reduced entropy to process ID only, making all keys generated over 2 years predictable.
- **PlayStation 3 ECDSA (2010)**: Sony reused a static nonce, allowing extraction of private signing key.
- **Netscape SSL (1994)**: PRNG seeded with time, PID, and PPID - all predictable values.

---

### 1.3 Key Reuse

**CWE-323: Reusing a Nonce, Key Pair in Encryption**

#### Vulnerable Code (Python)

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# VULNERABLE: Reusing key and nonce across different purposes
GLOBAL_KEY = b'0123456789abcdef0123456789abcdef'
STATIC_NONCE = b'000000000000'  # 12 bytes

class CryptoService:
    def __init__(self):
        self.aesgcm = AESGCM(GLOBAL_KEY)

    def encrypt_user_data(self, data: bytes) -> bytes:
        # Same key for all operations
        return self.aesgcm.encrypt(STATIC_NONCE, data, None)

    def encrypt_session_token(self, token: bytes) -> bytes:
        # Same key and nonce reused!
        return self.aesgcm.encrypt(STATIC_NONCE, token, None)

    def encrypt_file(self, file_data: bytes) -> bytes:
        # Again, same key and nonce
        return self.aesgcm.encrypt(STATIC_NONCE, file_data, None)
```

#### Why It's Wrong

1. **Keystream Recovery**: In AES-GCM, reusing nonce with same key leaks XOR of plaintexts
2. **Authentication Key Recovery**: Two messages with same nonce allow extraction of GHASH key
3. **Cross-Purpose Attacks**: Compromise in one system affects all systems sharing the key
4. **No Cryptographic Isolation**: Different data types should use different keys

#### Correct Implementation

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecureCryptoService:
    def __init__(self, master_key: bytes):
        # Derive separate keys for different purposes
        self.user_data_key = self._derive_key(master_key, b'user_data')
        self.session_key = self._derive_key(master_key, b'session')
        self.file_key = self._derive_key(master_key, b'files')

    def _derive_key(self, master: bytes, context: bytes) -> bytes:
        """Derive purpose-specific key using HKDF."""
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=context,
        )
        return hkdf.derive(master)

    def encrypt(self, key: bytes, data: bytes) -> bytes:
        """Encrypt with unique nonce per operation."""
        aesgcm = AESGCM(key)
        # Generate fresh random nonce for EVERY encryption
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # Prepend nonce to ciphertext
        return nonce + ciphertext

    def encrypt_user_data(self, data: bytes) -> bytes:
        return self.encrypt(self.user_data_key, data)

    def encrypt_session_token(self, token: bytes) -> bytes:
        return self.encrypt(self.session_key, token)
```

#### Real-World Incidents

- **184 HTTPS Servers (2016)**: Internet-wide scan found servers repeating GCM nonces, including financial institutions.
- **IBM Lotus Domino**: Vulnerable to nonce reuse attack, vendor confirmed and patched.
- **A10 Load Balancer**: Model AX1030 found vulnerable to GCM nonce reuse.

---

### 1.4 Improper Key Storage

**CWE-312: Cleartext Storage of Sensitive Information**
**CWE-313: Cleartext Storage in a File**

#### Vulnerable Code (Python)

```python
import json
import sqlite3

# VULNERABLE: Storing keys in plaintext config file
def save_config():
    config = {
        'database_encryption_key': 'aes256-key-abcdefghijklmnop',
        'api_secret': 'sk_live_1234567890',
        'jwt_signing_key': 'my-jwt-secret-key'
    }
    with open('/etc/myapp/config.json', 'w') as f:
        json.dump(config, f)

# VULNERABLE: Storing keys in database without encryption
def store_user_encryption_key(user_id: int, key: bytes):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    # Key stored in plaintext
    cursor.execute(
        "INSERT INTO user_keys (user_id, encryption_key) VALUES (?, ?)",
        (user_id, key.hex())
    )
    conn.commit()

# VULNERABLE: Logging sensitive data
import logging
logger = logging.getLogger(__name__)

def process_payment(card_number: str, api_key: str):
    logger.info(f"Processing payment with key: {api_key}")
    # ... processing
```

#### Why It's Wrong

1. **File System Access**: Config files readable by anyone with system access
2. **Database Dumps**: Backups expose all stored keys
3. **Log Files**: Keys in logs persist and may be shipped to log aggregators
4. **Memory Dumps**: Core dumps can contain unprotected keys

#### Correct Implementation

```python
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

class SecureKeyStorage:
    def __init__(self, master_password: str):
        """Initialize with master password from secure source (HSM, KMS, etc.)."""
        self.kek = self._derive_kek(master_password)

    def _derive_kek(self, password: str) -> bytes:
        """Derive Key Encryption Key from master password."""
        # In production, salt should be stored securely
        salt = os.environ.get('KEY_SALT', '').encode() or os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_key_for_storage(self, key: bytes) -> bytes:
        """Encrypt a key before storing it."""
        f = Fernet(self.kek)
        return f.encrypt(key)

    def decrypt_stored_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt a stored key."""
        f = Fernet(self.kek)
        return f.decrypt(encrypted_key)

# Use environment variables or KMS for the master key
# NEVER log sensitive data
def process_payment_secure(card_token: str):
    logger.info(f"Processing payment for token: {card_token[:4]}****")
```

---

### 1.5 Missing Key Rotation

**CWE-324: Use of a Key Past its Expiration Date**

#### Vulnerable Code (Python)

```python
# VULNERABLE: Static key with no rotation mechanism
class EncryptionService:
    # Key set once, never changed
    KEY = b'static-key-never-rotated-123456'

    def __init__(self):
        self.cipher = AES.new(self.KEY, AES.MODE_GCM)

    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

# No mechanism to:
# 1. Track key age
# 2. Generate new keys
# 3. Re-encrypt data with new keys
# 4. Gracefully deprecate old keys
```

#### Why It's Wrong

1. **Extended Exposure Window**: Longer key lifetime = more encrypted data at risk if compromised
2. **Cryptanalysis Risk**: More ciphertext under same key aids cryptanalysis
3. **Compliance Violations**: PCI-DSS, HIPAA require periodic key rotation
4. **No Breach Response**: Cannot invalidate compromised keys

#### Correct Implementation

```python
import os
import time
from dataclasses import dataclass
from typing import Optional
from cryptography.fernet import Fernet, MultiFernet

@dataclass
class KeyMetadata:
    key_id: str
    key: bytes
    created_at: float
    expires_at: float
    is_active: bool = True

class KeyRotationManager:
    def __init__(self, rotation_interval_days: int = 90):
        self.rotation_interval = rotation_interval_days * 86400
        self.keys: dict[str, KeyMetadata] = {}
        self.current_key_id: Optional[str] = None

    def generate_new_key(self) -> KeyMetadata:
        """Generate a new key with metadata."""
        key_id = os.urandom(8).hex()
        key = Fernet.generate_key()
        now = time.time()

        metadata = KeyMetadata(
            key_id=key_id,
            key=key,
            created_at=now,
            expires_at=now + self.rotation_interval
        )
        self.keys[key_id] = metadata
        self.current_key_id = key_id
        return metadata

    def should_rotate(self) -> bool:
        """Check if current key needs rotation."""
        if not self.current_key_id:
            return True
        current = self.keys.get(self.current_key_id)
        if not current:
            return True
        return time.time() >= current.expires_at

    def rotate_if_needed(self) -> None:
        """Rotate key if expiration reached."""
        if self.should_rotate():
            old_key_id = self.current_key_id
            self.generate_new_key()

            # Mark old key as inactive but keep for decryption
            if old_key_id and old_key_id in self.keys:
                self.keys[old_key_id].is_active = False

    def get_encryptor(self) -> MultiFernet:
        """Get encryptor that uses current key but can decrypt with old keys."""
        # Current key first (for encryption)
        # Old keys follow (for decryption of old data)
        fernets = []

        # Add current key first
        if self.current_key_id:
            fernets.append(Fernet(self.keys[self.current_key_id].key))

        # Add old keys for decryption
        for key_id, metadata in self.keys.items():
            if key_id != self.current_key_id:
                fernets.append(Fernet(metadata.key))

        return MultiFernet(fernets)
```

---

## 2. Algorithm Errors

### 2.1 Using Broken Algorithms (MD5, SHA1, DES, RC4)

**CWE-327: Use of a Broken or Risky Cryptographic Algorithm**
**CWE-328: Use of Weak Hash**

#### Vulnerable Code (Python)

```python
import hashlib
from Crypto.Cipher import DES, ARC4

# VULNERABLE: MD5 for password hashing
def hash_password_md5(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# VULNERABLE: SHA1 for integrity verification
def sign_document_sha1(document: bytes, key: bytes) -> str:
    import hmac
    return hmac.new(key, document, hashlib.sha1).hexdigest()

# VULNERABLE: DES encryption (56-bit key)
def encrypt_des(data: bytes, key: bytes) -> bytes:
    cipher = DES.new(key[:8], DES.MODE_ECB)
    # Pad data to 8-byte boundary
    padded = data + b'\x00' * (8 - len(data) % 8)
    return cipher.encrypt(padded)

# VULNERABLE: RC4 stream cipher
def encrypt_rc4(data: bytes, key: bytes) -> bytes:
    cipher = ARC4.new(key)
    return cipher.encrypt(data)
```

#### Why It's Wrong

| Algorithm | Vulnerability | Practical Attack Cost |
|-----------|--------------|----------------------|
| MD5 | Collision in minutes on laptop | Free |
| SHA1 | Collision ~$110,000 (2017), ~$45,000 (2020) | Decreasing |
| DES | 56-bit key brute-forced in hours | ~$10,000 |
| RC4 | Statistical biases, broken in TLS | Practical |

#### Correct Implementation

```python
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argon2

# CORRECT: Use Argon2 for password hashing
def hash_password_argon2(password: str) -> str:
    ph = argon2.PasswordHasher(
        time_cost=3,          # Number of iterations
        memory_cost=65536,    # 64MB memory
        parallelism=4,        # Parallel threads
    )
    return ph.hash(password)

def verify_password_argon2(password: str, hash: str) -> bool:
    ph = argon2.PasswordHasher()
    try:
        ph.verify(hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False

# CORRECT: Use SHA-256 or SHA-3 for integrity
def sign_document_sha256(document: bytes, key: bytes) -> str:
    import hmac
    return hmac.new(key, document, hashlib.sha256).hexdigest()

# CORRECT: Use AES-256-GCM for encryption
def encrypt_aes_gcm(data: bytes, key: bytes) -> bytes:
    if len(key) != 32:
        raise ValueError("Key must be 256 bits (32 bytes)")

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext

def decrypt_aes_gcm(encrypted: bytes, key: bytes) -> bytes:
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
```

#### Real-World Incidents

- **Rogue CA Attack (2008)**: MD5 collision used to forge X.509 certificate
- **Flame Malware (2012)**: MD5 collision forged Microsoft code signing certificate
- **SHAttered (2017)**: Google/CWI demonstrated first practical SHA-1 collision
- **EDF GDPR Fine (2022)**: French utility fined EUR 600,000 for storing passwords with MD5

---

### 2.2 ECB Mode Usage

**CWE-327: Use of a Broken or Risky Cryptographic Algorithm**

#### Vulnerable Code (Python)

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# VULNERABLE: ECB mode preserves patterns
def encrypt_ecb(data: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(data, AES.block_size)
    return cipher.encrypt(padded_data)

# Example: Encrypting image data
def encrypt_image_ecb(image_data: bytes, key: bytes) -> bytes:
    # This will preserve visible patterns in the image!
    return encrypt_ecb(image_data, key)

# Example: Encrypting structured data
def encrypt_user_records(records: list[dict], key: bytes) -> list[bytes]:
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = []
    for record in records:
        data = json.dumps(record).encode()
        padded = pad(data, AES.block_size)
        encrypted.append(cipher.encrypt(padded))
    return encrypted
    # Problem: Identical records produce identical ciphertext!
```

#### Why It's Wrong

1. **Pattern Preservation**: Identical 16-byte blocks encrypt to identical ciphertext
2. **No Diffusion**: Each block encrypted independently
3. **The "ECB Penguin"**: Famous demonstration showing Tux penguin visible in ECB-encrypted bitmap
4. **Replay Attacks**: Encrypted blocks can be rearranged without detection

#### Correct Implementation

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# CORRECT: Use GCM mode (authenticated encryption)
def encrypt_gcm(data: bytes, key: bytes, associated_data: bytes = None) -> bytes:
    """
    AES-GCM provides:
    - Confidentiality (encryption)
    - Integrity (authentication tag)
    - Unique ciphertext per encryption (random nonce)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce, unique per encryption
    ciphertext = aesgcm.encrypt(nonce, data, associated_data)
    return nonce + ciphertext

def decrypt_gcm(encrypted: bytes, key: bytes, associated_data: bytes = None) -> bytes:
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data)

# Alternative: CTR mode with separate MAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hmac, hashes

def encrypt_ctr_then_mac(data: bytes, enc_key: bytes, mac_key: bytes) -> bytes:
    # Generate random IV
    iv = os.urandom(16)

    # Encrypt with CTR mode
    cipher = Cipher(algorithms.AES(enc_key), modes.CTR(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()

    # MAC the ciphertext (encrypt-then-MAC)
    h = hmac.HMAC(mac_key, hashes.SHA256())
    h.update(iv + ciphertext)
    tag = h.finalize()

    return iv + ciphertext + tag
```

#### Real-World Impact

- **Visual Pattern Leakage**: Any data with repeating patterns (images, structured data) leaks information
- **Block Manipulation**: Attackers can swap, duplicate, or delete blocks without detection
- **Chosen Plaintext Attacks**: Practical attacks demonstrated in security assessments

---

### 2.3 Missing/Weak IV

**CWE-329: Generation of Predictable IV with CBC Mode**

#### Vulnerable Code (Python)

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# VULNERABLE: Static IV
STATIC_IV = b'0000000000000000'

def encrypt_static_iv(data: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(data, 16))

# VULNERABLE: Predictable IV (counter-based)
iv_counter = 0

def encrypt_counter_iv(data: bytes, key: bytes) -> bytes:
    global iv_counter
    iv = iv_counter.to_bytes(16, 'big')
    iv_counter += 1
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, 16))

# VULNERABLE: IV derived from data being encrypted
def encrypt_derived_iv(data: bytes, key: bytes) -> bytes:
    # IV is hash of first block - predictable!
    import hashlib
    iv = hashlib.md5(data[:16]).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, 16))
```

#### Why It's Wrong

1. **Static IV**: Same plaintext always produces same ciphertext
2. **Counter IV**: Attacker can predict next IV, enabling BEAST-style attacks
3. **Derived IV**: If attacker can influence plaintext, they control the IV
4. **IV Reuse**: Enables distinguishing attack and pattern analysis

#### Correct Implementation

```python
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def encrypt_random_iv(data: bytes, key: bytes) -> bytes:
    """CBC mode with cryptographically random IV."""
    # Generate unpredictable IV for each encryption
    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # Pad data
    padding_length = 16 - (len(data) % 16)
    padded_data = data + bytes([padding_length] * padding_length)

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Prepend IV to ciphertext (IV is not secret, just unpredictable)
    return iv + ciphertext

# BETTER: Use GCM mode which handles nonce/IV properly
def encrypt_gcm_proper(data: bytes, key: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    aesgcm = AESGCM(key)
    # GCM nonce should be 12 bytes, random
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext
```

---

### 2.4 Deterministic Encryption Where Randomness Needed

**CWE-329: Generation of Predictable IV with CBC Mode**

#### Vulnerable Code (Python)

```python
import hashlib

# VULNERABLE: Deterministic encryption for searchable fields
class DeterministicEncryption:
    def __init__(self, key: bytes):
        self.key = key

    def encrypt_email(self, email: str) -> str:
        """
        Same email always produces same ciphertext.
        Enables database lookups but leaks equality information.
        """
        # Derive "IV" deterministically from email
        iv = hashlib.sha256(email.encode()).digest()[:16]

        from Crypto.Cipher import AES
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        padded = email.encode().ljust(64, b'\x00')
        return cipher.encrypt(padded).hex()

# Usage that leaks information:
# encrypt_email("alice@example.com") always produces same output
# Attacker can build rainbow table of encrypted common emails
```

#### Why It's Wrong

1. **Equality Leakage**: Attacker knows when two users share same email
2. **Frequency Analysis**: Can identify common values (e.g., admin@company.com)
3. **Chosen Plaintext**: If attacker can cause encryptions, they can test guesses
4. **No Forward Secrecy**: Past data vulnerable if key compromised

#### Correct Implementation

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecureEncryption:
    def __init__(self, key: bytes):
        self.key = key

    def encrypt_email(self, email: str) -> bytes:
        """
        Randomized encryption - same email produces different ciphertext.
        Cannot search directly, but secure.
        """
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)  # Random per encryption
        ciphertext = aesgcm.encrypt(nonce, email.encode(), None)
        return nonce + ciphertext

# For searchable encryption, use specialized schemes:
class BlindIndexEncryption:
    """
    Blind indexing: Store random encryption + searchable hash.
    Trade-off between searchability and security.
    """
    def __init__(self, encryption_key: bytes, index_key: bytes):
        self.enc_key = encryption_key
        self.idx_key = index_key

    def store_email(self, email: str) -> dict:
        import hmac
        import hashlib

        # Random encryption for storage (secure)
        aesgcm = AESGCM(self.enc_key)
        nonce = os.urandom(12)
        encrypted = nonce + aesgcm.encrypt(nonce, email.encode(), None)

        # Blind index for searching (keyed, but deterministic)
        # Uses separate key and truncated hash to limit leakage
        blind_index = hmac.new(
            self.idx_key,
            email.lower().encode(),  # Normalize
            hashlib.sha256
        ).hexdigest()[:16]  # Truncate to increase collisions

        return {
            'encrypted_email': encrypted,
            'email_index': blind_index  # For WHERE clause
        }
```

---

### 2.5 Custom Crypto Implementations

**CWE-327: Use of a Broken or Risky Cryptographic Algorithm**

#### Vulnerable Code (Python)

```python
# VULNERABLE: Custom "encryption" algorithm
class CustomCipher:
    def __init__(self, key: str):
        self.key = key

    def encrypt(self, plaintext: str) -> str:
        """Custom XOR-based cipher - COMPLETELY BROKEN."""
        result = []
        for i, char in enumerate(plaintext):
            key_char = self.key[i % len(self.key)]
            encrypted_char = chr(ord(char) ^ ord(key_char))
            result.append(encrypted_char)
        return ''.join(result)

    def decrypt(self, ciphertext: str) -> str:
        # XOR is symmetric
        return self.encrypt(ciphertext)

# VULNERABLE: Custom hash function
def custom_hash(data: bytes) -> bytes:
    """Custom hash - NOT cryptographically secure."""
    result = [0] * 16
    for i, byte in enumerate(data):
        result[i % 16] ^= byte
        result[(i + 1) % 16] = (result[(i + 1) % 16] + byte) % 256
    return bytes(result)

# VULNERABLE: "Improved" version of standard algorithm
def enhanced_aes_encrypt(data: bytes, key: bytes) -> bytes:
    """
    Adding custom operations doesn't improve security,
    likely introduces vulnerabilities.
    """
    from Crypto.Cipher import AES

    # Custom "pre-processing" - serves no cryptographic purpose
    preprocessed = bytes(b ^ 0x55 for b in data)

    cipher = AES.new(key, AES.MODE_ECB)  # Still using ECB!
    encrypted = cipher.encrypt(preprocessed.ljust(16, b'\x00'))

    # Custom "post-processing"
    return bytes(b ^ 0xAA for b in encrypted)
```

#### Why It's Wrong

1. **No Peer Review**: Custom algorithms not analyzed by cryptographers
2. **Subtle Flaws**: Cryptographic weaknesses are non-obvious
3. **XOR Vulnerability**: Key reuse in XOR completely breaks confidentiality
4. **Linear Operations**: Custom hashes often lack avalanche effect

#### Correct Implementation

```python
# CORRECT: Use established, peer-reviewed cryptographic libraries
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

class SecureCrypto:
    """Use standard algorithms from reputable libraries."""

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """AES-256-GCM - NIST approved, widely analyzed."""
        if len(key) != 32:
            raise ValueError("Use 256-bit key")

        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        return nonce + aesgcm.encrypt(nonce, data, None)

    @staticmethod
    def hash(data: bytes) -> bytes:
        """SHA-256 - NIST approved, collision resistant."""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(data)
        return digest.finalize()

    @staticmethod
    def password_hash(password: str) -> str:
        """Argon2id - winner of Password Hashing Competition."""
        import argon2
        ph = argon2.PasswordHasher()
        return ph.hash(password)
```

#### Real-World Incidents

- **IOTA Cryptocurrency (2017)**: Custom hash function Curl had collisions, enabling signature forgery. $1.9B market cap at risk.
- **Telegram MTProto**: Custom protocol had multiple cryptographic weaknesses identified by researchers.
- **Adobe Password Breach (2013)**: Custom encryption scheme leaked password hints and patterns for 153 million accounts.

---

## 3. Implementation Errors

### 3.1 Timing Attacks (Non-Constant-Time Comparison)

**CWE-208: Observable Timing Discrepancy**

#### Vulnerable Code (Python)

```python
# VULNERABLE: Early-exit string comparison
def verify_api_key(provided_key: str, stored_key: str) -> bool:
    """
    Standard string comparison exits on first mismatch.
    Timing difference reveals how many characters match.
    """
    if len(provided_key) != len(stored_key):
        return False

    for i in range(len(provided_key)):
        if provided_key[i] != stored_key[i]:
            return False  # EXITS EARLY - timing leak!

    return True

# VULNERABLE: Using == operator
def check_signature(provided: bytes, expected: bytes) -> bool:
    return provided == expected  # Python's == uses early exit

# VULNERABLE: Hash comparison with timing leak
def verify_password_hash(password: str, stored_hash: str) -> bool:
    import hashlib
    computed = hashlib.sha256(password.encode()).hexdigest()
    return computed == stored_hash  # Timing leak!
```

#### Why It's Wrong

1. **Information Leakage**: Each matching byte adds ~nanoseconds to response
2. **Statistical Analysis**: Thousands of requests reveal timing patterns
3. **Byte-by-Byte Recovery**: Attacker can guess secrets one character at a time
4. **Remote Exploitability**: Works over network with enough samples

#### Correct Implementation

```python
import hmac
import secrets

def verify_api_key_secure(provided_key: str, stored_key: str) -> bool:
    """
    Constant-time comparison using hmac.compare_digest.
    Time is independent of where strings differ.
    """
    # Handle length difference without timing leak
    if len(provided_key) != len(stored_key):
        # Compare against dummy to maintain constant time
        hmac.compare_digest(provided_key, provided_key)
        return False

    return hmac.compare_digest(provided_key, stored_key)

def verify_signature_secure(provided: bytes, expected: bytes) -> bool:
    """Constant-time comparison for cryptographic values."""
    return hmac.compare_digest(provided, expected)

# For password verification, use the library's built-in method
def verify_password_secure(password: str, stored_hash: str) -> bool:
    import argon2
    ph = argon2.PasswordHasher()
    try:
        # Library handles constant-time comparison internally
        ph.verify(stored_hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False

# Language-specific constant-time functions:
# Python: hmac.compare_digest()
# Java: MessageDigest.isEqual()
# PHP: hash_equals()
# Node.js: crypto.timingSafeEqual()
# Go: crypto/subtle.ConstantTimeCompare()
# Rust: ring::constant_time::verify_slices_are_equal()
```

#### Real-World Incidents

- **CVE-2025-59432 (SCRAM Java)**: `Arrays.equals()` used for authentication, enabling timing attack
- **CVE-2019-18887 (Symfony)**: UriSigner timing vulnerability in ESI fragment URLs
- **CVE-2024-52307 (authentik)**: SECRET_KEY brute-forceable via metrics endpoint timing

---

### 3.2 Padding Oracle Vulnerabilities

**CWE-209: Generation of Error Message Containing Sensitive Information**
**CWE-696: Incorrect Behavior Order**

#### Vulnerable Code (Python)

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

# VULNERABLE: Different errors for padding vs authentication
class VulnerableDecryptor:
    def __init__(self, key: bytes):
        self.key = key

    def decrypt(self, iv: bytes, ciphertext: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)

        try:
            # VULNERABLE: Padding check happens AFTER decryption
            # and BEFORE MAC verification (if any)
            return unpad(plaintext, 16)
        except ValueError:
            # Different error message reveals padding validity!
            raise ValueError("Invalid padding")

# VULNERABLE: HTTP responses leak padding validity
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/decrypt', methods=['POST'])
def decrypt_endpoint():
    try:
        data = request.get_json()
        decrypted = decryptor.decrypt(
            bytes.fromhex(data['iv']),
            bytes.fromhex(data['ciphertext'])
        )
        return jsonify({'success': True})
    except ValueError as e:
        if 'padding' in str(e).lower():
            # LEAKS: 400 for bad padding
            return jsonify({'error': 'Bad padding'}), 400
        else:
            # LEAKS: 500 for other errors
            return jsonify({'error': 'Decryption failed'}), 500
```

#### Why It's Wrong

1. **Binary Oracle**: Attacker learns if padding is valid (yes/no)
2. **Block-by-Block Decryption**: Each byte recoverable in ~256 requests
3. **No Authentication**: CBC mode provides no integrity protection
4. **Error Differentiation**: Distinct responses for padding vs. other errors

#### Correct Implementation

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# CORRECT: Use authenticated encryption (no padding oracle possible)
class SecureEncryption:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 256 bits")
        self.aesgcm = AESGCM(key)

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes) -> bytes:
        """
        GCM verifies authentication tag BEFORE returning plaintext.
        No padding oracle because:
        1. No padding (CTR mode internally)
        2. Authentication checked first
        3. Same error for any tampering
        """
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        try:
            return self.aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            # SAME error for ALL failure types
            raise ValueError("Decryption failed")

# If you MUST use CBC, use Encrypt-then-MAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class CBCWithMAC:
    def __init__(self, enc_key: bytes, mac_key: bytes):
        self.enc_key = enc_key
        self.mac_key = mac_key

    def encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)

        # Pad
        pad_len = 16 - (len(data) % 16)
        padded = data + bytes([pad_len] * pad_len)

        # Encrypt
        cipher = Cipher(algorithms.AES(self.enc_key), modes.CBC(iv))
        ciphertext = cipher.encryptor().update(padded) + cipher.encryptor().finalize()

        # MAC the IV + ciphertext (Encrypt-then-MAC)
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        mac = h.finalize()

        return iv + ciphertext + mac

    def decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:16]
        mac = encrypted[-32:]
        ciphertext = encrypted[16:-32]

        # VERIFY MAC FIRST (before any padding check)
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        try:
            h.verify(mac)
        except Exception:
            raise ValueError("Decryption failed")  # Generic error

        # Only check padding after MAC is verified
        cipher = Cipher(algorithms.AES(self.enc_key), modes.CBC(iv))
        plaintext = cipher.decryptor().update(ciphertext)

        pad_len = plaintext[-1]
        if pad_len > 16 or not all(b == pad_len for b in plaintext[-pad_len:]):
            raise ValueError("Decryption failed")  # Same generic error

        return plaintext[:-pad_len]
```

#### Real-World Incidents

- **CVE-2016-2107 (OpenSSL)**: Padding oracle introduced while fixing Lucky13
- **POODLE (2014)**: SSL 3.0 padding oracle + downgrade attack
- **Lucky Thirteen (2013)**: Timing-based padding oracle in TLS
- **ASP.NET (2010)**: Padding oracle enabled view state decryption

---

### 3.3 Nonce Reuse

**CWE-323: Reusing a Nonce, Key Pair in Encryption**

#### Vulnerable Code (Python)

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# VULNERABLE: Static nonce
class BrokenGCMEncryption:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)
        self.nonce = b'static_nonce'  # FATAL ERROR

    def encrypt(self, data: bytes) -> bytes:
        return self.aesgcm.encrypt(self.nonce, data, None)

# VULNERABLE: Counter-based nonce without persistence
class CounterNonce:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)
        self.counter = 0  # Resets on restart!

    def encrypt(self, data: bytes) -> bytes:
        nonce = self.counter.to_bytes(12, 'big')
        self.counter += 1
        return nonce + self.aesgcm.encrypt(nonce, data, None)
    # Problem: After restart, counter resets to 0, reusing nonces

# VULNERABLE: Truncated random nonce
class ShortNonce:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(4)  # Only 32 bits - collision after ~65k messages!
        nonce = nonce + b'\x00' * 8  # Padded to 12 bytes
        return nonce + self.aesgcm.encrypt(nonce, data, None)
```

#### Why It's Wrong

1. **XOR Keystream**: Same nonce + key = same keystream; XORing ciphertexts reveals plaintext XOR
2. **GHASH Key Recovery**: Two messages with same nonce leak authentication key
3. **Complete Break**: Attacker can forge arbitrary messages after nonce reuse
4. **Birthday Bound**: Random nonces have ~50% collision probability at 2^(n/2) messages

#### Correct Implementation

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecureGCMEncryption:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Use 256-bit key")
        self.aesgcm = AESGCM(key)

    def encrypt(self, data: bytes, associated_data: bytes = None) -> bytes:
        """
        Generate random 96-bit nonce for each encryption.
        Safe for ~2^32 messages before birthday bound concern.
        """
        nonce = os.urandom(12)  # 96 bits, random
        ciphertext = self.aesgcm.encrypt(nonce, data, associated_data)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes, associated_data: bytes = None) -> bytes:
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, associated_data)

# For high-volume encryption, use XChaCha20-Poly1305 (192-bit nonce)
# or AES-GCM-SIV (nonce-misuse resistant)

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

class HighVolumeEncryption:
    """
    ChaCha20-Poly1305 with extended nonce for high-volume scenarios.
    """
    def __init__(self, key: bytes):
        self.cipher = ChaCha20Poly1305(key)

    def encrypt(self, data: bytes) -> bytes:
        # 96-bit random nonce
        nonce = os.urandom(12)
        return nonce + self.cipher.encrypt(nonce, data, None)

# For nonce-misuse resistance (defense in depth)
# Consider AES-GCM-SIV (RFC 8452)
```

#### Real-World Incidents

- **184 HTTPS Servers (2016)**: Research found servers reusing GCM nonces
- **PS3 ECDSA Key (2010)**: Sony used static nonce, private key extracted
- **A10 Load Balancers**: Vulnerable to nonce reuse attacks

---

### 3.4 Insufficient Entropy / PRNG Misuse

**CWE-331: Insufficient Entropy**
**CWE-332: Insufficient Entropy in PRNG**
**CWE-338: Use of Cryptographically Weak PRNG**

#### Vulnerable Code (Python)

```python
import random
import time

# VULNERABLE: Using random module for cryptography
def generate_token():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32))

# VULNERABLE: Predictable seeding
def generate_session_id():
    random.seed(int(time.time()))  # Seconds since epoch - easily guessed
    return random.getrandbits(128)

# VULNERABLE: Low entropy source
def generate_key():
    # User input has very low entropy
    user_password = "password123"  # Typical user password
    return hashlib.sha256(user_password.encode()).digest()

# VULNERABLE: PRNG state leakage
class TokenGenerator:
    def __init__(self):
        random.seed(12345)  # Fixed seed for "reproducibility"

    def generate(self):
        return random.getrandbits(64)

# VULNERABLE: Seeding with PID
def insecure_init():
    import os
    random.seed(os.getpid())  # PIDs are small integers (1-65535)
```

#### Why It's Wrong

1. **Predictable Output**: `random` module uses Mersenne Twister, not cryptographic
2. **State Recovery**: ~624 outputs from MT19937 reveal internal state
3. **Low Seed Space**: Time/PID seeds have few possibilities to brute-force
4. **No Cryptographic Properties**: Statistical randomness != unpredictability

#### Correct Implementation

```python
import secrets
import os

# CORRECT: Use secrets module for cryptographic randomness
def generate_secure_token(length: int = 32) -> str:
    """Generate unpredictable URL-safe token."""
    return secrets.token_urlsafe(length)

def generate_secure_hex(length: int = 32) -> str:
    """Generate unpredictable hex string."""
    return secrets.token_hex(length)

def generate_secure_bytes(length: int = 32) -> bytes:
    """Generate unpredictable bytes."""
    return secrets.token_bytes(length)

# CORRECT: Derive key from password with proper KDF
def derive_key_from_password(password: str) -> tuple[bytes, bytes]:
    """
    Use Argon2 or PBKDF2 with:
    - Random salt
    - High iteration count
    - Memory hardness (Argon2)
    """
    import hashlib

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        iterations=600_000,  # OWASP 2023 recommendation
        dklen=32
    )
    return key, salt

# CORRECT: System entropy sources
def get_system_random_bytes(n: int) -> bytes:
    """
    os.urandom() uses:
    - /dev/urandom on Linux/macOS
    - CryptGenRandom on Windows
    """
    return os.urandom(n)

# For when you need a PRNG with specific seed (testing only!)
def create_reproducible_prng_for_testing():
    """Use only in test environments, never in production."""
    import random
    test_rng = random.Random()
    test_rng.seed(42)  # Deterministic for test reproducibility
    return test_rng
```

#### Real-World Incidents

- **Debian OpenSSL (2008)**: PRNG seeded only with PID, all keys generated over 2 years predictable
- **Netscape SSL (1994)**: PRNG seeded with time + PID + PPID
- **Android SecureRandom (2013)**: Insufficient entropy on some devices compromised Bitcoin wallets

---

## 4. Protocol Errors

### 4.1 Missing Authentication

**CWE-306: Missing Authentication for Critical Function**

#### Vulnerable Code (Python)

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Crypto.Cipher import AES

# VULNERABLE: Encryption without authentication (CBC mode alone)
class UnauthenticatedEncryption:
    def __init__(self, key: bytes):
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # Pad
        pad_len = 16 - (len(data) % 16)
        padded = data + bytes([pad_len] * pad_len)

        return iv + cipher.encrypt(padded)
        # NO MAC - attacker can modify ciphertext!

    def decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:16]
        ciphertext = encrypted[16:]

        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)

        # Remove padding
        pad_len = plaintext[-1]
        return plaintext[:-pad_len]
        # Accepts modified ciphertext without verification!

# VULNERABLE: MAC computed but not verified
class UnverifiedMAC:
    def decrypt(self, data: bytes) -> bytes:
        ciphertext = data[:-32]
        mac = data[-32:]

        # MAC is present but never checked!
        return self._decrypt(ciphertext)
```

#### Why It's Wrong

1. **Bit Flipping**: Attacker can modify ciphertext, changes affect plaintext predictably
2. **Malleability**: CBC mode allows surgical modifications to plaintext
3. **Padding Oracle**: Without MAC, padding errors leak information
4. **Chosen Ciphertext**: Attacker can craft ciphertexts to extract secrets

#### Correct Implementation

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hmac, hashes

# CORRECT: Use authenticated encryption (GCM)
class AuthenticatedEncryption:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)

    def encrypt(self, data: bytes, associated_data: bytes = None) -> bytes:
        """GCM provides authentication automatically."""
        nonce = os.urandom(12)
        # GCM generates authentication tag internally
        ciphertext = self.aesgcm.encrypt(nonce, data, associated_data)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes, associated_data: bytes = None) -> bytes:
        """Decryption fails if ciphertext modified."""
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        # Raises InvalidTag if authentication fails
        return self.aesgcm.decrypt(nonce, ciphertext, associated_data)

# CORRECT: If using CBC, add Encrypt-then-MAC
class CBCWithHMAC:
    def __init__(self, enc_key: bytes, mac_key: bytes):
        """Use separate keys for encryption and MAC."""
        self.enc_key = enc_key
        self.mac_key = mac_key

    def encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)

        # Encrypt
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)
        pad_len = 16 - (len(data) % 16)
        ciphertext = cipher.encrypt(data + bytes([pad_len] * pad_len))

        # MAC over IV + ciphertext (Encrypt-then-MAC)
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        mac = h.finalize()

        return iv + ciphertext + mac

    def decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:16]
        mac = encrypted[-32:]
        ciphertext = encrypted[16:-32]

        # VERIFY MAC FIRST
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        h.verify(mac)  # Raises on failure

        # Only decrypt after MAC verification
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)

        return plaintext[:-plaintext[-1]]
```

---

### 4.2 Encrypt-then-MAC vs MAC-then-Encrypt

**CWE-310: Cryptographic Issues**

#### Vulnerable Code (Python)

```python
import hmac
import hashlib
from Crypto.Cipher import AES

# VULNERABLE: MAC-then-Encrypt (used in TLS < 1.2)
class MACThenEncrypt:
    def __init__(self, enc_key: bytes, mac_key: bytes):
        self.enc_key = enc_key
        self.mac_key = mac_key

    def encrypt(self, data: bytes) -> bytes:
        # Step 1: Compute MAC on plaintext
        mac = hmac.new(self.mac_key, data, hashlib.sha256).digest()

        # Step 2: Encrypt plaintext + MAC together
        iv = os.urandom(16)
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)

        to_encrypt = data + mac
        pad_len = 16 - (len(to_encrypt) % 16)
        padded = to_encrypt + bytes([pad_len] * pad_len)

        return iv + cipher.encrypt(padded)

    def decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:16]
        ciphertext = encrypted[16:]

        # Step 1: Decrypt (padding oracle possible here!)
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)

        # Step 2: Check padding (oracle leak!)
        pad_len = decrypted[-1]
        if not all(b == pad_len for b in decrypted[-pad_len:]):
            raise ValueError("Bad padding")  # ORACLE!

        # Step 3: Verify MAC (too late!)
        plaintext = decrypted[:-pad_len-32]
        mac = decrypted[-pad_len-32:-pad_len]

        expected_mac = hmac.new(self.mac_key, plaintext, hashlib.sha256).digest()
        if mac != expected_mac:
            raise ValueError("Bad MAC")

        return plaintext
```

#### Why It's Wrong

| Composition | Security Property |
|------------|-------------------|
| **Encrypt-then-MAC** | Provably secure (INT-CTXT, IND-CCA2) |
| **MAC-then-Encrypt** | NOT generically secure, padding oracles |
| **Encrypt-and-MAC** | Not secure against chosen ciphertext |

1. **Padding Oracle**: In MAC-then-Encrypt, padding is checked before MAC
2. **Ciphertext Malleability**: MAC doesn't cover ciphertext modifications
3. **Error Ordering**: Different errors for padding vs MAC failures

#### Correct Implementation

```python
# CORRECT: Encrypt-then-MAC (ISO/IEC 19772:2009)
class EncryptThenMAC:
    def __init__(self, enc_key: bytes, mac_key: bytes):
        self.enc_key = enc_key
        self.mac_key = mac_key

    def encrypt(self, data: bytes) -> bytes:
        # Step 1: Encrypt the plaintext
        iv = os.urandom(16)
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)

        pad_len = 16 - (len(data) % 16)
        ciphertext = cipher.encrypt(data + bytes([pad_len] * pad_len))

        # Step 2: MAC the IV + ciphertext
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        mac = h.finalize()

        return iv + ciphertext + mac

    def decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:16]
        mac = encrypted[-32:]
        ciphertext = encrypted[16:-32]

        # Step 1: Verify MAC FIRST
        h = hmac.HMAC(self.mac_key, hashes.SHA256())
        h.update(iv + ciphertext)
        try:
            h.verify(mac)
        except:
            raise ValueError("Decryption failed")  # Generic error

        # Step 2: Decrypt only after MAC verified
        cipher = AES.new(self.enc_key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)

        pad_len = plaintext[-1]
        return plaintext[:-pad_len]

# BEST: Just use AEAD (GCM, ChaCha20-Poly1305)
# Handles all this correctly internally
```

#### Real-World Incidents

- **BEAST (2011)**: Exploited CBC in TLS 1.0 with MAC-then-Encrypt
- **Lucky13 (2013)**: Timing attack on MAC-then-Encrypt in TLS
- **POODLE (2014)**: Padding oracle in SSL 3.0's MAC-then-Encrypt

---

### 4.3 Replay Attacks Possible

**CWE-294: Authentication Bypass by Capture-replay**

#### Vulnerable Code (Python)

```python
import hmac
import hashlib
import time

# VULNERABLE: No replay protection
class VulnerableAPI:
    def __init__(self, api_key: bytes):
        self.api_key = api_key

    def create_request(self, action: str, data: dict) -> dict:
        """Create signed request without replay protection."""
        message = f"{action}:{json.dumps(data)}"
        signature = hmac.new(
            self.api_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'action': action,
            'data': data,
            'signature': signature
            # NO timestamp or nonce!
        }

    def verify_request(self, request: dict) -> bool:
        """Verify request - but allows replays!"""
        message = f"{request['action']}:{json.dumps(request['data'])}"
        expected = hmac.new(
            self.api_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(request['signature'], expected)
        # Valid signature can be replayed forever!

# VULNERABLE: Timestamp without nonce
class TimestampOnlyAPI:
    def verify(self, request: dict) -> bool:
        timestamp = request.get('timestamp', 0)
        now = time.time()

        # Allows 5 minute window
        if abs(now - timestamp) > 300:
            return False

        # But within that window, same request can be replayed!
        return self._verify_signature(request)
```

#### Why It's Wrong

1. **Duplicate Transactions**: Same signed request processed multiple times
2. **Financial Impact**: Transfer $100 becomes transfer $1000 via 10 replays
3. **State Manipulation**: Legitimate actions replayed at wrong time
4. **No Detection**: Server cannot distinguish replay from original

#### Correct Implementation

```python
import secrets
import time
from dataclasses import dataclass
from typing import Set

@dataclass
class SecureRequest:
    action: str
    data: dict
    timestamp: float
    nonce: str
    signature: str

class ReplayProtectedAPI:
    def __init__(self, api_key: bytes):
        self.api_key = api_key
        self.used_nonces: Set[str] = set()
        self.nonce_expiry = 600  # 10 minutes

    def create_request(self, action: str, data: dict) -> SecureRequest:
        """Create request with timestamp and nonce."""
        timestamp = time.time()
        nonce = secrets.token_hex(16)  # 128-bit random nonce

        # Include timestamp and nonce in signed message
        message = f"{action}:{json.dumps(data)}:{timestamp}:{nonce}"
        signature = hmac.new(
            self.api_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return SecureRequest(
            action=action,
            data=data,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature
        )

    def verify_request(self, request: SecureRequest) -> bool:
        """Verify request with replay protection."""
        # 1. Check timestamp freshness
        now = time.time()
        if abs(now - request.timestamp) > self.nonce_expiry:
            return False

        # 2. Check nonce hasn't been used
        if request.nonce in self.used_nonces:
            return False  # REPLAY DETECTED

        # 3. Verify signature
        message = f"{request.action}:{json.dumps(request.data)}:{request.timestamp}:{request.nonce}"
        expected = hmac.new(
            self.api_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(request.signature, expected):
            return False

        # 4. Record nonce as used
        self.used_nonces.add(request.nonce)
        self._cleanup_old_nonces()

        return True

    def _cleanup_old_nonces(self):
        """Remove expired nonces to prevent memory growth."""
        # In production, use Redis with TTL or similar
        pass

# For sequence-based protocols, use monotonic counters
class SequenceProtectedChannel:
    def __init__(self):
        self.expected_sequence = 0

    def verify_sequence(self, sequence: int) -> bool:
        """Reject out-of-order or replayed messages."""
        if sequence <= self.expected_sequence:
            return False  # Replay or out of order

        self.expected_sequence = sequence
        return True
```

---

### 4.4 Downgrade Attacks

**CWE-757: Selection of Less-Secure Algorithm During Negotiation**

#### Vulnerable Code (Python)

```python
# VULNERABLE: Accepting weak algorithms if client requests them
class VulnerableProtocol:
    SUPPORTED_ALGORITHMS = ['AES-256-GCM', 'AES-128-CBC', '3DES', 'RC4', 'DES']

    def negotiate_algorithm(self, client_algorithms: list) -> str:
        """Accept whatever the client proposes."""
        for alg in client_algorithms:
            if alg in self.SUPPORTED_ALGORITHMS:
                return alg  # Might return 'DES' if client proposes it!
        raise ValueError("No common algorithm")

# VULNERABLE: TLS configuration accepting old versions
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
# Does not restrict minimum version - accepts TLS 1.0, SSLv3!

# VULNERABLE: Weak cipher suites enabled
ssl_context.set_ciphers('ALL')  # Includes RC4, export ciphers!
```

#### Why It's Wrong

1. **MITM Manipulation**: Attacker modifies negotiation to force weak algorithm
2. **Known Breaks**: Weak algorithms have practical attacks
3. **False Sense of Security**: Encryption present but easily broken
4. **POODLE Attack**: Downgrade to SSLv3 + padding oracle

#### Correct Implementation

```python
import ssl

# CORRECT: Only allow strong algorithms
class SecureProtocol:
    # Minimum acceptable algorithms
    ALLOWED_ALGORITHMS = ['AES-256-GCM', 'CHACHA20-POLY1305', 'AES-128-GCM']

    def negotiate_algorithm(self, client_algorithms: list) -> str:
        """Only accept strong algorithms, server preference."""
        # Server chooses from its preferred order
        for alg in self.ALLOWED_ALGORITHMS:
            if alg in client_algorithms:
                return alg
        raise ValueError("Client must support modern encryption")

# CORRECT: TLS configuration
def create_secure_ssl_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Minimum TLS 1.2 (or 1.3 for highest security)
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Prefer TLS 1.3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    # Strong cipher suites only
    context.set_ciphers(
        'ECDHE+AESGCM:'
        'ECDHE+CHACHA20:'
        'DHE+AESGCM:'
        '!aNULL:!eNULL:!MD5:!DSS:!RC4:!3DES:!DES:!EXPORT'
    )

    # Disable compression (CRIME attack)
    context.options |= ssl.OP_NO_COMPRESSION

    return context

# CORRECT: Algorithm negotiation with signed list
class SignedNegotiation:
    """Prevent tampering with algorithm list."""

    def __init__(self, private_key):
        self.key = private_key

    def create_offer(self, algorithms: list) -> dict:
        """Sign the algorithm list to prevent modification."""
        data = json.dumps(algorithms).encode()
        signature = self._sign(data)

        return {
            'algorithms': algorithms,
            'signature': signature
        }

    def verify_offer(self, offer: dict) -> list:
        """Verify algorithm list hasn't been tampered with."""
        data = json.dumps(offer['algorithms']).encode()
        if not self._verify(data, offer['signature']):
            raise ValueError("Algorithm list was modified")
        return offer['algorithms']
```

---

## 5. TLS/SSL Errors

### 5.1 Certificate Validation Disabled

**CWE-295: Improper Certificate Validation**
**CWE-296: Improper Following of a Certificate's Chain of Trust**

#### Vulnerable Code (Python)

```python
import ssl
import requests
import urllib3

# VULNERABLE: Disable certificate verification globally
requests.packages.urllib3.disable_warnings()
response = requests.get('https://api.example.com', verify=False)

# VULNERABLE: Create unverified SSL context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# VULNERABLE: urllib with no verification
import urllib.request
context = ssl._create_unverified_context()
response = urllib.request.urlopen('https://api.example.com', context=context)

# VULNERABLE: Custom verify function that always returns True
def always_trust(cert, hostname):
    return True

# VULNERABLE: Ignoring certificate errors in aiohttp
import aiohttp
async def fetch():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get('https://api.example.com') as response:
            return await response.text()
```

#### Why It's Wrong

1. **MITM Attacks**: Any attacker on network can intercept traffic
2. **No Server Identity**: Cannot verify you're talking to intended server
3. **Credential Theft**: Login credentials sent to attacker's server
4. **Data Manipulation**: Attacker can modify requests and responses

#### Correct Implementation

```python
import ssl
import certifi
import requests

# CORRECT: Use proper certificate verification (default behavior)
response = requests.get('https://api.example.com')  # verify=True by default

# CORRECT: Specify CA bundle explicitly
response = requests.get(
    'https://api.example.com',
    verify=certifi.where()  # Use certifi's CA bundle
)

# CORRECT: Use custom CA for internal services
response = requests.get(
    'https://internal-api.company.com',
    verify='/path/to/company-ca-bundle.pem'
)

# CORRECT: Create properly configured SSL context
def create_secure_context() -> ssl.SSLContext:
    context = ssl.create_default_context()

    # These are defaults, but explicit is better
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True

    # Load system CA certificates
    context.load_default_certs()

    return context

# CORRECT: Pin specific certificate for high-security
def create_pinned_context(cert_path: str) -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.load_verify_locations(cert_path)
    return context

# CORRECT: aiohttp with verification
import aiohttp
import ssl

async def fetch_secure():
    ssl_context = ssl.create_default_context()
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get('https://api.example.com') as response:
            return await response.text()

# For development/testing ONLY - never in production
import os
if os.environ.get('ENVIRONMENT') == 'development':
    # Only in development, with explicit self-signed cert
    response = requests.get(
        'https://localhost:8443',
        verify='/path/to/dev-self-signed.pem'
    )
```

---

### 5.2 Weak Cipher Suites

**CWE-327: Use of a Broken or Risky Cryptographic Algorithm**

#### Vulnerable Code (Python)

```python
import ssl

# VULNERABLE: Accepting all ciphers including weak ones
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.set_ciphers('ALL')  # Includes RC4, DES, export ciphers!

# VULNERABLE: Explicitly enabling weak ciphers
context.set_ciphers('RC4-SHA:DES-CBC3-SHA:AES256-SHA')

# VULNERABLE: Including export-grade ciphers
context.set_ciphers('ALL:EXPORT')

# VULNERABLE: Allowing anonymous Diffie-Hellman (no authentication)
context.set_ciphers('ADH-AES256-SHA')

# VULNERABLE: Including NULL ciphers (no encryption!)
context.set_ciphers('NULL-SHA256')
```

#### Why It's Wrong

| Weak Cipher/Feature | Vulnerability |
|--------------------|---------------|
| RC4 | Statistical biases, practical breaks |
| DES | 56-bit key, brute-force in hours |
| 3DES | Sweet32 attack (birthday bound) |
| Export ciphers | 40-bit keys, trivially broken |
| NULL ciphers | No encryption at all |
| Anonymous DH | No authentication, MITM |
| MD5 MAC | Collision attacks |
| CBC without ETM | Padding oracle attacks |

#### Correct Implementation

```python
import ssl

def create_secure_server_context() -> ssl.SSLContext:
    """Create TLS context with modern, secure cipher suites."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Minimum TLS 1.2
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Modern cipher suite configuration
    # Priority order: TLS 1.3 ciphers, then strong TLS 1.2 ciphers
    context.set_ciphers(
        # TLS 1.3 ciphers (automatically included if TLS 1.3 enabled)
        # TLS_AES_256_GCM_SHA384
        # TLS_CHACHA20_POLY1305_SHA256
        # TLS_AES_128_GCM_SHA256

        # TLS 1.2 with AEAD and forward secrecy
        'ECDHE+AESGCM:'
        'ECDHE+CHACHA20:'
        'DHE+AESGCM:'

        # Exclusions
        '!aNULL:'      # No anonymous ciphers
        '!eNULL:'      # No encryption-less ciphers
        '!MD5:'        # No MD5 MAC
        '!DSS:'        # No DSS signatures
        '!RC4:'        # No RC4
        '!3DES:'       # No Triple DES
        '!DES:'        # No DES
        '!EXPORT:'     # No export ciphers
        '!PSK:'        # No pre-shared key
        '!SRP:'        # No SRP
        '!CAMELLIA:'   # Prefer AES
        '!ARIA:'       # Prefer AES
    )

    # Disable compression (CRIME attack)
    context.options |= ssl.OP_NO_COMPRESSION

    # Prefer server cipher order
    context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

    return context

def create_secure_client_context() -> ssl.SSLContext:
    """Create TLS client context."""
    context = ssl.create_default_context()

    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Same cipher restrictions
    context.set_ciphers(
        'ECDHE+AESGCM:'
        'ECDHE+CHACHA20:'
        'DHE+AESGCM:'
        '!aNULL:!eNULL:!MD5:!RC4:!3DES:!DES:!EXPORT'
    )

    return context

# Recommended cipher suites by security level:
CIPHER_SUITES = {
    'high_security': [
        'TLS_AES_256_GCM_SHA384',
        'TLS_CHACHA20_POLY1305_SHA256',
        'ECDHE-ECDSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-GCM-SHA384',
    ],
    'standard': [
        'TLS_AES_128_GCM_SHA256',
        'ECDHE-ECDSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES128-GCM-SHA256',
    ],
}
```

---

### 5.3 Protocol Version Issues

**CWE-326: Inadequate Encryption Strength**

#### Vulnerable Code (Python)

```python
import ssl

# VULNERABLE: Using SSLv2 or SSLv3
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)  # Deprecated, allows old versions

# VULNERABLE: Explicitly allowing old TLS versions
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
# Does not set minimum version - allows TLS 1.0, 1.1

# VULNERABLE: Using deprecated constant
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  # TLS 1.0 only

# VULNERABLE: Not disabling old protocols
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
# Missing: context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
```

#### Why It's Wrong

| Protocol | Status | Vulnerabilities |
|----------|--------|-----------------|
| SSLv2 | BROKEN | Many, including DROWN |
| SSLv3 | BROKEN | POODLE |
| TLS 1.0 | DEPRECATED | BEAST, no AEAD support |
| TLS 1.1 | DEPRECATED | No AEAD support |
| TLS 1.2 | CURRENT | Secure with proper config |
| TLS 1.3 | RECOMMENDED | Modern, secure by default |

#### Correct Implementation

```python
import ssl

def create_modern_tls_context() -> ssl.SSLContext:
    """Create context with only modern TLS versions."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Method 1: Set minimum version directly (Python 3.7+)
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Optionally require TLS 1.3 only for highest security
    # context.minimum_version = ssl.TLSVersion.TLSv1_3

    # Method 2: Disable old protocols explicitly (also valid)
    context.options |= (
        ssl.OP_NO_SSLv2 |
        ssl.OP_NO_SSLv3 |
        ssl.OP_NO_TLSv1 |
        ssl.OP_NO_TLSv1_1
    )

    return context

def create_tls13_only_context() -> ssl.SSLContext:
    """Create context requiring TLS 1.3."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    return context

# Web server configuration examples:

# nginx.conf equivalent:
"""
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...;
"""

# Apache equivalent:
"""
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:...
SSLHonorCipherOrder on
"""
```

---

## Summary: CWE Quick Reference

| Category | CWE | Description |
|----------|-----|-------------|
| Key Management | CWE-321 | Use of Hard-coded Cryptographic Key |
| Key Management | CWE-798 | Use of Hard-coded Credentials |
| Key Management | CWE-330 | Use of Insufficiently Random Values |
| Key Management | CWE-331 | Insufficient Entropy |
| Key Management | CWE-323 | Reusing a Nonce, Key Pair |
| Key Management | CWE-312 | Cleartext Storage of Sensitive Information |
| Key Management | CWE-324 | Use of Key Past Expiration |
| Algorithm | CWE-327 | Use of Broken or Risky Crypto Algorithm |
| Algorithm | CWE-328 | Use of Weak Hash |
| Algorithm | CWE-329 | Predictable IV with CBC Mode |
| Implementation | CWE-208 | Observable Timing Discrepancy |
| Implementation | CWE-209 | Error Message Information Leak |
| Implementation | CWE-338 | Cryptographically Weak PRNG |
| Protocol | CWE-294 | Authentication Bypass by Replay |
| Protocol | CWE-306 | Missing Authentication |
| Protocol | CWE-757 | Less-Secure Algorithm Selection |
| TLS/SSL | CWE-295 | Improper Certificate Validation |
| TLS/SSL | CWE-296 | Improper Certificate Chain of Trust |
| TLS/SSL | CWE-326 | Inadequate Encryption Strength |

---

## Best Practices Summary

1. **Use established libraries**: cryptography, PyNaCl, libsodium
2. **Prefer AEAD modes**: AES-GCM, ChaCha20-Poly1305
3. **Generate random values securely**: `secrets` module, `os.urandom()`
4. **Use constant-time comparisons**: `hmac.compare_digest()`
5. **Store keys in KMS**: AWS KMS, HashiCorp Vault, Azure Key Vault
6. **Implement key rotation**: Automated with overlap period
7. **Minimum TLS 1.2**: Prefer TLS 1.3 where possible
8. **Always verify certificates**: Never set `verify=False` in production
9. **Use strong password hashing**: Argon2id, bcrypt with high cost
10. **Include replay protection**: Timestamps + nonces for APIs

---

## References and Sources

- [OWASP Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
- [CWE Category: Cryptographic Issues](https://cwe.mitre.org/data/definitions/310.html)
- [NIST Cryptographic Standards](https://csrc.nist.gov/publications)
- [Mozilla Server Side TLS](https://wiki.mozilla.org/Security/Server_Side_TLS)
