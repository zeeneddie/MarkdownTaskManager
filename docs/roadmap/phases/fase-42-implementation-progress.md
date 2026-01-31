# Fase 42: Advanced False Negative Detection - Implementation Progress

**Status:** COMPLETE
**Start:** 2026-01-31
**Doel:** FN rate van <5% naar <2% door 4 nieuwe scanner types

---

## Overzicht

| Scanner | Rules | ~Lines | Status |
|---------|-------|--------|--------|
| **ObfuscationDetector** | 5+entropy | ~1100 | COMPLETE |
| **DynamicFeatureDetector** | 33 | ~1600 | COMPLETE |
| **FrameworkSecurityPlugin** | 84 | ~1500 | COMPLETE |
| **ASTTaintTracker** | ~150 | ~1900 | COMPLETE |
| **Totaal** | **~272** | **~6100** | |

---

## Stappen

### Stap 1: ScannerType enum uitbreiden
- **Bestand:** `backend/app/services/security_scanner/models/findings.py`
- **Status:** COMPLETE
- [x] `AST_TAINT = "ast_taint"`
- [x] `DYNAMIC_FEATURE = "dynamic_feature"`
- [x] `FRAMEWORK_SECURITY = "framework_security"`
- [x] `OBFUSCATION = "obfuscation"`

### Stap 2: ObfuscationDetector
- **Bestand:** `backend/app/services/security_scanner/adapters/obfuscation_detector.py`
- **Status:** COMPLETE
- [x] ObfuscationRule dataclass
- [x] OBF-CONCAT-001..005 rules
- [x] OBF-ENCODE-001 (Base64/hex decode)
- [x] OBF-UNICODE-001 (Unicode escapes)
- [x] OBF-ENTROPY-001 (Shannon entropy > 3.5)
- [x] OBF-CHARCODE-001 (Character code arithmetic)
- [x] ObfuscationDetector(BaseScanner) class
- [x] Compiled patterns, async scan(), FP filtering
- [x] Factory function `create_obfuscation_detector()`

### Stap 3: DynamicFeatureDetector
- **Bestand:** `backend/app/services/security_scanner/adapters/dynamic_feature_detector.py`
- **Status:** COMPLETE
- [x] DynamicFeatureRule dataclass
- [x] JS rules (15): DYN-PROP-001..005, DYN-CALL-001..004, DYN-IMPORT-001..003, DYN-EVAL-001..003
- [x] Python rules (10): DYN-REFL-001..004, DYN-EXEC-001..003, DYN-META-001..003
- [x] Java rules (8): DYN-REFL-J001..004, DYN-DESER-J001..002, DYN-PROXY-J001..002
- [x] DynamicFeatureDetector(BaseScanner) class
- [x] Factory function `create_dynamic_feature_detector()`

### Stap 4: FrameworkSecurityPlugin
- **Bestand:** `backend/app/services/security_scanner/adapters/framework_security_plugin.py`
- **Status:** COMPLETE
- [x] FrameworkSecurityRule dataclass
- [x] Django rules (15): FW-DJ-001..015
- [x] Flask rules (10): FW-FL-001..010
- [x] Express rules (12): FW-EX-001..012
- [x] Spring rules (15): FW-SP-001..015
- [x] Rails rules (10): FW-RA-001..010
- [x] Laravel rules (12): FW-LA-001..012
- [x] ASP.NET rules (10): FW-AN-001..010
- [x] Lightweight `_detect_frameworks()` op basis van imports/config
- [x] FrameworkSecurityPlugin(BaseScanner) class
- [x] Factory function `create_framework_security_plugin()`

### Stap 5: ASTTaintTracker
- **Bestand:** `backend/app/services/security_scanner/adapters/ast_taint_tracker.py`
- **Status:** COMPLETE
- [x] TaintRule dataclass
- [x] SQL taint rules (20)
- [x] XSS taint rules (18)
- [x] CMD taint rules (15)
- [x] Path traversal taint rules (12)
- [x] Deserialization taint rules (10)
- [x] SSRF taint rules (10)
- [x] LDAP/NoSQL taint rules (8)
- [x] Code injection taint rules (10)
- [x] Log injection taint rules (8)
- [x] Header injection taint rules (8)
- [x] Email injection taint rules (6)
- [x] Regex injection taint rules (5)
- [x] Cross-function rules (Python AST, 20)
- [x] Python AST analyse: ast.parse, taint sources, propagation, sink check
- [x] Regex-based source->sink heuristics voor JS/Java/C#/PHP/Ruby/Go
- [x] ASTTaintTracker(BaseScanner) class
- [x] Factory function `create_ast_taint_tracker()`

### Stap 6: Registratie in orchestrator
- **Bestanden:**
  - `backend/app/services/security_scanner/adapters/__init__.py`
  - `backend/app/services/security_scanner/orchestrator.py`
- **Status:** COMPLETE
- [x] Imports in `__init__.py` + `__all__` uitbreiden
- [x] Imports in `orchestrator.py`
- [x] LANGUAGE_SCANNERS mapping bijwerken
- [x] `_initialize_scanners` bijwerken

### Stap 7: Tests schrijven
- **Status:** COMPLETE
- [x] `tests/unit/security_scanner/test_obfuscation_detector.py` (94 tests, 94 passed)
- [x] `tests/unit/security_scanner/test_dynamic_feature_detector.py` (100 tests, 100 passed)
- [x] `tests/unit/security_scanner/test_framework_security_plugin.py` (170 tests, 156 passed, 14 xfailed)
- [x] `tests/unit/security_scanner/test_ast_taint_tracker.py` (104 tests, 104 passed)

### Stap 8: Verificatie
- **Status:** COMPLETE
- [x] Alle nieuwe tests passing (454 passed, 14 xfailed)
- [x] Geen regressie in bestaande tests
- [x] Full security scanner suite groen (1092 passed, 28 xfailed)

### Stap 9: Roadmap en documentatie bijwerken
- **Status:** COMPLETE
- [x] `fase-42-advanced-fn-detection.md` status -> COMPLETE
- [x] `phases-current.md` bijwerken
- [x] `phases-planned.md` bijwerken

---

## Architectuurkeuzes
- Exact zelfde pattern als InjectionDetector: Rule dataclass, compiled patterns, async scan(), FP filtering, factory
- Dual taint approach: Python `ast` module (0.85 confidence) + regex overige talen (0.6-0.7)
- Geen nieuwe dependencies: Alleen stdlib (`ast`, `re`, `math`)
- Lightweight framework detection: Import/config-based in scanner zelf
- Confidence veld: Alle scanners zetten `confidence` op SecurityFinding

## Referentiebestanden
- `adapters/injection_detector.py` - exact template voor rule format + scan loop
- `models/findings.py` - ScannerType enum + SecurityFinding met confidence
- `adapters/base.py` - BaseScanner abstract class
- `orchestrator.py` - LANGUAGE_SCANNERS mapping + _initialize_scanners
