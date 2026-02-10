# Security Scanner Overview

**Gegenereerd:** 2026-02-04
**Totaal scanners:** 21

## Scanner Status Samenvatting

| Status | Aantal | Beschrijving |
|--------|--------|--------------|
| WORKS (async) | 4 | Externe CLI tools met async I/O - timeout werkt correct |
| BLOCKS (sync) | 17 | Pattern-based scanners met sync file I/O - timeout werkt NIET |

## Probleem: Synchronous File I/O

De meeste scanners gebruiken `file_path.read_text()` wat een **synchrone** operatie is. Dit betekent:
- `asyncio.wait_for()` kan de scanner NIET onderbreken
- De scanner blijft hangen tot ALLE bestanden zijn gelezen
- Op grote projecten (hci-crs: 5000+ bestanden) kan dit 10-60+ minuten duren

## Scanner Details

### Externe CLI Scanners (ASYNC - Timeout WERKT)

| Scanner | Type | Binary | Talen | Status |
|---------|------|--------|-------|--------|
| **OpenGrep** | `OPENGREP` | `opengrep` | Python, JS, Java, Go, C, etc. | WORKS - als binary geinstalleerd |
| **Bandit** | `BANDIT` | `bandit` | Python | WORKS - als binary geinstalleerd |
| **Gosec** | `GOSEC` | `gosec` | Go | WORKS - als binary geinstalleerd |
| **Trivy** | `TRIVY` | `trivy` | Container/Dependency scan | WORKS - als binary geinstalleerd |

**Waarom werken deze?** Ze gebruiken `asyncio.create_subprocess_exec()` wat kan worden ge-timeout met `asyncio.wait_for()`.

---

### Custom Pattern Scanners (SYNC - Timeout werkt NIET)

#### CustomPatternScanner subclasses

| Scanner | Type | Focus | Sync I/O | Geschikt voor grote projecten |
|---------|------|-------|----------|------------------------------|
| **OWASP Scanner** | `OWASP_SCANNER` | OWASP Top 10 2021 | read_text() | NEE - blokkeert |
| **Secret Scanner** | `SECRET_SCANNER` | Hardcoded secrets | read_text() + open() | NEE - blokkeert |
| **ASP Scanner** | `CUSTOM_ASP` | Classic ASP/VBScript | read_text() | NEE - blokkeert |
| **CVE Scanner** | `CVE_SCANNER` | CVE database patterns | read_text() | NEE - blokkeert |

#### BaseScanner subclasses (custom impl)

| Scanner | Type | Focus | Sync I/O | Geschikt voor grote projecten |
|---------|------|-------|----------|------------------------------|
| **Injection Detector** | `INJECTION` | XSS, SQLi, CMDi, etc. | read_text() | NEE - blokkeert |
| **Auth Logic Detector** | `AUTH_LOGIC` | Authorization bugs | read_text() | NEE - blokkeert |
| **Generic Security** | `GENERIC_SECURITY` | Multi-language patterns | read_text() | NEE - blokkeert |
| **Code Quality** | `CODE_QUALITY` | Code quality issues | read_text() | NEE - blokkeert |
| **Crypto Error** | `CRYPTO_ERROR` | Cryptographic errors | read_text() | NEE - blokkeert |
| **Control Flow Logic** | `CONTROL_FLOW_LOGIC` | Logic errors | read_text() | NEE - blokkeert |
| **Boolean Logic** | `BOOLEAN_LOGIC` | Boolean logic bugs | read_text() | NEE - blokkeert |
| **Memory Safety** | `MEMORY_SAFETY` | Memory bugs (C/C++) | read_text() | NEE - blokkeert |
| **Concurrency Error** | `CONCURRENCY_ERROR` | Race conditions | read_text() | NEE - blokkeert |
| **Web Security** | `WEB_SECURITY` | Web vulnerabilities | read_text() | NEE - blokkeert |
| **Path Security** | `PATH_SECURITY` | Path traversal | read_text() | NEE - blokkeert |
| **AST Taint Tracker** | `AST_TAINT` | Cross-function taint | read_text() | NEE - blokkeert |
| **Dynamic Feature** | `DYNAMIC_FEATURE` | eval/exec detection | read_text() | NEE - blokkeert |
| **Framework Security** | `FRAMEWORK_SECURITY` | Framework-specific | read_text() | NEE - blokkeert |
| **Obfuscation** | `OBFUSCATION` | Obfuscated code | read_text() | NEE - blokkeert |

---

## Aanbevelingen voor Grote Projecten (>5000 bestanden)

### Optie 1: Fast Mode (huidige implementatie)
Gebruik alleen de snelste scanners:
```python
fast_scanners = {
    ScannerType.SECRET_SCANNER,  # Kritiek - detecteert hardcoded secrets
    ScannerType.CUSTOM_ASP,      # Als ASP code aanwezig
}
```
**Probleem:** Zelfs deze blokkeren op grote projecten.

### Optie 2: Async File I/O (toekomstige fix)
Vervang `read_text()` door `aiofiles`:
```python
# Van:
content = file_path.read_text(encoding="utf-8", errors="replace")

# Naar:
import aiofiles
async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as f:
    content = await f.read()
```
**Voordeel:** asyncio.wait_for() kan scanners nu WEL onderbreken.

### Optie 3: Process Pool Executor
Voer sync scanners uit in aparte processen:
```python
import concurrent.futures

def _sync_scan(scanner, path, config):
    return asyncio.run(scanner.scan(path, config))

async def run_with_timeout(scanner, path, config, timeout):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        future = loop.run_in_executor(pool, _sync_scan, scanner, path, config)
        return await asyncio.wait_for(future, timeout=timeout)
```
**Voordeel:** Process kan worden ge-killed bij timeout.

### Optie 4: File Batching
Scan in batches met timeouts per batch:
```python
async def scan_in_batches(files, batch_size=100, batch_timeout=30):
    results = []
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        try:
            result = await asyncio.wait_for(
                scan_batch(batch),
                timeout=batch_timeout
            )
            results.extend(result)
        except asyncio.TimeoutError:
            logger.warning(f"Batch {i//batch_size} timed out, skipping")
    return results
```

---

## Scanner Coverage Matrix

| CWE | OWASP | Secret | Injection | Generic | Quality | Crypto | Memory |
|-----|-------|--------|-----------|---------|---------|--------|--------|
| CWE-79 (XSS) | A03 | - | TIER 1 | YES | - | - | - |
| CWE-89 (SQLi) | A03 | - | TIER 1 | YES | - | - | - |
| CWE-78 (CMDi) | A03 | - | TIER 1 | YES | - | - | - |
| CWE-22 (Path) | A01 | - | TIER 1 | YES | - | - | - |
| CWE-798 (Hardcoded) | A07 | TIER 1 | - | YES | - | - | - |
| CWE-327 (Weak Crypto) | A02 | - | - | YES | - | TIER 1 | - |
| CWE-787 (OOB Write) | - | - | - | - | - | - | TIER 1 |
| CWE-416 (Use After Free) | - | - | - | - | - | - | TIER 1 |
| CWE-362 (Race) | - | - | - | - | - | - | - |

---

## Implementatie Status

### Werkt
- Sequential scanner execution met progress callback
- Per-scanner progress visibility: `[M6] security_scan: [█████░░░░░░░░░░░░░░░] 25% (1/4 scanners)`
- Fast mode voor grote projecten (beperkte scanner set)

### Blokkeert nog
- Individual scanner timeout (sync I/O probleem)
- Volledige progress voor pattern-based scanners

### Todo
1. Implementeer async file I/O met aiofiles
2. Of: Implementeer ProcessPoolExecutor voor sync scanners
3. Of: Implementeer file batching met per-batch timeouts
