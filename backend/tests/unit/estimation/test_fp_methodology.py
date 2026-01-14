# Unit tests for FP Methodology module
# Tests IFPUG CPM 4.3.1 compliant Function Point calculation
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

import pytest
from app.services.fp_methodology import (
    WorkTypeClassifier,
    WorkType,
    EstimationMethod,
    WorkTypeClassification,
    EnhancementFPCalculator,
    EnhancementFPResult,
    ChangeType,
    FPComponentValidator,
    ValidationResult,
    ValidationSeverity,
)


class TestWorkTypeClassifier:
    """Tests for WorkTypeClassifier."""

    @pytest.fixture
    def classifier(self):
        return WorkTypeClassifier()

    # === NESMA Terminology Tests ===

    def test_classify_analyse_dutch(self, classifier):
        """Test Dutch 'Analyse' classification (NO FP!)."""
        result = classifier.classify("Brown Paper analyse van legacy systeem")

        assert result.work_type == WorkType.ANALYSIS
        assert result.fp_applicable is False
        assert result.recommended_method == EstimationMethod.TIME_AND_MATERIALS
        assert "analyse" in [kw.lower() for kw in result.matched_keywords]

    def test_classify_nieuwe_bouw_dutch(self, classifier):
        """Test Dutch 'Nieuwe bouw' classification (Development FP)."""
        result = classifier.classify("Nieuwe bouw klantportaal met React")

        assert result.work_type == WorkType.DEVELOPMENT
        assert result.fp_applicable is True
        assert result.recommended_method == EstimationMethod.DEVELOPMENT_FP

    def test_classify_verbouw_dutch(self, classifier):
        """Test Dutch 'Verbouw' classification (Enhancement FP)."""
        result = classifier.classify("Verbouw van bestaande module")

        assert result.work_type == WorkType.ENHANCEMENT
        assert result.fp_applicable is True
        assert result.recommended_method == EstimationMethod.ENHANCEMENT_FP

    def test_classify_herbouw_dutch(self, classifier):
        """Test Dutch 'Herbouw' classification (Rebuild FP)."""
        result = classifier.classify("Herbouw legacy systeem naar modern platform")

        assert result.work_type == WorkType.REBUILD
        assert result.fp_applicable is True
        assert result.recommended_method == EstimationMethod.REBUILD_FP

    def test_classify_onderhoud_dutch(self, classifier):
        """Test Dutch 'Onderhoud' classification (NO FP!)."""
        result = classifier.classify("Onderhoud en beheer van productiesysteem")

        assert result.work_type == WorkType.MAINTENANCE
        assert result.fp_applicable is False
        assert result.recommended_method == EstimationMethod.SUPPORT_HOURS

    # === English Terminology Tests ===

    def test_classify_analysis_english(self, classifier):
        """Test English 'Analysis' classification."""
        result = classifier.classify("Code review and security audit")

        assert result.work_type == WorkType.ANALYSIS
        assert result.fp_applicable is False

    def test_classify_development_english(self, classifier):
        """Test English 'Development' classification."""
        result = classifier.classify("Build new customer portal from scratch")

        assert result.work_type == WorkType.DEVELOPMENT
        assert result.fp_applicable is True

    def test_classify_enhancement_english(self, classifier):
        """Test English 'Enhancement' classification."""
        result = classifier.classify("Fix bug in payment processing")

        assert result.work_type == WorkType.ENHANCEMENT
        assert result.fp_applicable is True

    def test_classify_rebuild_english(self, classifier):
        """Test English 'Rebuild' classification."""
        result = classifier.classify("Complete rewrite of legacy system")

        assert result.work_type == WorkType.REBUILD
        assert result.fp_applicable is True

    def test_classify_maintenance_english(self, classifier):
        """Test English 'Maintenance' classification."""
        result = classifier.classify("24/7 monitoring and support")

        assert result.work_type == WorkType.MAINTENANCE
        assert result.fp_applicable is False

    # === FP Misuse Detection Tests ===

    def test_analysis_warns_no_fp(self, classifier):
        """Analysis work should warn about no FP."""
        result = classifier.classify("ADO leak audit and documentation")

        assert result.work_type == WorkType.ANALYSIS
        assert any("NO Function Points" in w or "GEEN" in w for w in result.warnings)

    def test_source_code_review_not_fp(self, classifier):
        """Source code review should not have FP."""
        result = classifier.classify("Review source code for security issues")

        assert result.fp_applicable is False

    # === Validation Tests ===

    def test_validate_fp_usage_valid(self, classifier):
        """Valid FP usage for development."""
        is_valid, issues = classifier.validate_fp_usage(
            "Build new customer registration feature",
            fp_count=15
        )

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_fp_usage_invalid_analysis(self, classifier):
        """Invalid FP usage for analysis work."""
        is_valid, issues = classifier.validate_fp_usage(
            "Security audit of legacy system",
            fp_count=50
        )

        assert is_valid is False
        assert len(issues) > 0
        assert "time_and_materials" in issues[0].lower()

    def test_validate_fp_usage_missing_fp(self, classifier):
        """Missing FP for development work."""
        is_valid, issues = classifier.validate_fp_usage(
            "Build new reporting module",
            fp_count=0
        )

        assert is_valid is False
        assert len(issues) > 0

    # === Estimation Guidance Tests ===

    def test_guidance_analysis_no_fp(self, classifier):
        """Guidance for analysis should show no FP."""
        guidance = classifier.get_estimation_guidance(WorkType.ANALYSIS)

        assert guidance["fp_applicable"] is False
        assert "time_and_materials" in guidance["recommended_method"]
        assert guidance["estimation_approach"]["fp_count"] == 0

    def test_guidance_development_has_fp(self, classifier):
        """Guidance for development should show FP formula."""
        guidance = classifier.get_estimation_guidance(WorkType.DEVELOPMENT)

        assert guidance["fp_applicable"] is True
        assert "UFP" in guidance["estimation_approach"]["formula"]

    def test_guidance_enhancement_has_efp(self, classifier):
        """Guidance for enhancement should show EFP formula."""
        guidance = classifier.get_estimation_guidance(WorkType.ENHANCEMENT)

        assert guidance["fp_applicable"] is True
        assert "EFP" in guidance["estimation_approach"]["formula"]

    def test_guidance_rebuild_has_rfp(self, classifier):
        """Guidance for rebuild should show RFP formula."""
        guidance = classifier.get_estimation_guidance(WorkType.REBUILD)

        assert guidance["fp_applicable"] is True
        assert "RFP" in guidance["estimation_approach"]["formula"]


class TestEnhancementFPCalculator:
    """Tests for EnhancementFPCalculator."""

    @pytest.fixture
    def calculator(self):
        return EnhancementFPCalculator()

    # === Basic Calculation Tests ===

    def test_calculate_added_components(self, calculator):
        """Test FP calculation for added components."""
        result = calculator.calculate(
            added=[
                {"name": "NewFunc1", "type": "EI", "complexity": "low"},
                {"name": "NewFunc2", "type": "EI", "complexity": "average"},
            ]
        )

        assert result.add_fp == 7  # 3 (low EI) + 4 (avg EI)
        assert len(result.added) == 2

    def test_calculate_changed_components(self, calculator):
        """Test FP calculation for changed components."""
        result = calculator.calculate(
            changed=[
                {"name": "ModFunc", "type": "EO", "complexity": "average"},
            ]
        )

        assert result.change_fp == 5  # avg EO
        assert len(result.changed) == 1

    def test_calculate_deleted_40_percent(self, calculator):
        """Test deleted components count at 40%."""
        result = calculator.calculate(
            deleted=[
                {"name": "OldFunc", "type": "EQ", "complexity": "average", "original_fp": 10},
            ]
        )

        assert result.delete_fp == 4.0  # 10 * 0.40
        assert len(result.deleted) == 1

    def test_calculate_deleted_default_fp(self, calculator):
        """Test deleted components with default FP when original not specified."""
        result = calculator.calculate(
            deleted=[
                {"name": "OldFunc", "type": "EQ", "complexity": "average"},
            ]
        )

        # Default EQ average = 4, so 4 * 0.40 = 1.6
        assert result.delete_fp == pytest.approx(1.6, rel=0.1)

    def test_calculate_conversion_components(self, calculator):
        """Test FP calculation for conversion components."""
        result = calculator.calculate(
            conversion=[
                {"name": "DataMigration", "type": "EI", "complexity": "high"},
            ]
        )

        assert result.conversion_fp == 6  # high EI

    # === Total EFP Calculation Tests ===

    def test_total_efp_formula(self, calculator):
        """Test EFP = ADD + CHNG + DEL + CFP."""
        result = calculator.calculate(
            added=[{"name": "A", "type": "EI", "complexity": "low"}],  # 3
            changed=[{"name": "B", "type": "EO", "complexity": "average"}],  # 5
            deleted=[{"name": "C", "type": "EQ", "original_fp": 10}],  # 4
            conversion=[{"name": "D", "type": "EI", "complexity": "low"}],  # 3
        )

        expected = 3 + 5 + 4 + 3  # 15
        assert result.total_efp == expected

    def test_vaf_deprecated_warning(self, calculator, caplog):
        """Test VAF usage produces deprecation warning."""
        import logging
        caplog.set_level(logging.WARNING)

        result = calculator.calculate(
            added=[{"name": "A", "type": "EI", "complexity": "low"}],
            use_vaf=True,
            vaf=1.1,
        )

        # Access total_efp to trigger VAF calculation
        _ = result.total_efp

        assert any("deprecated" in record.message.lower() for record in caplog.records)

    # === Component Type Tests ===

    @pytest.mark.parametrize("comp_type,complexity,expected_fp", [
        ("EI", "low", 3),
        ("EI", "average", 4),
        ("EI", "high", 6),
        ("EO", "low", 4),
        ("EO", "average", 5),
        ("EO", "high", 7),
        ("EQ", "low", 3),
        ("EQ", "average", 4),
        ("EQ", "high", 6),
    ])
    def test_transaction_fp_values(self, calculator, comp_type, complexity, expected_fp):
        """Test IFPUG transaction FP values."""
        result = calculator.calculate(
            added=[{"name": "Test", "type": comp_type, "complexity": complexity}]
        )

        assert result.add_fp == expected_fp

    # === Productivity Estimation Tests ===

    def test_estimate_productivity_normal(self, calculator):
        """Test normal productivity range."""
        analysis = calculator.estimate_productivity(efp=10, hours=20)

        assert analysis["fp_per_hour"] == 0.5
        assert analysis["category"] == "normal"
        assert analysis["is_anomaly"] is False

    def test_estimate_productivity_anomaly(self, calculator):
        """Test anomaly detection for high productivity."""
        analysis = calculator.estimate_productivity(efp=100, hours=10)

        assert analysis["fp_per_hour"] == 10.0
        assert analysis["category"] == "anomaly"
        assert analysis["is_anomaly"] is True
        assert "verify" in analysis["recommendation"].lower()


class TestFPComponentValidator:
    """Tests for FPComponentValidator."""

    @pytest.fixture
    def validator(self):
        return FPComponentValidator()

    # === ILF Validation Tests ===

    def test_ilf_valid(self, validator):
        """Test valid ILF."""
        result = validator.validate_ilf(
            name="CustomerMaster",
            description="Customer master data maintained by the application",
            dets=15,
            rets=2,
        )

        assert result.is_valid is True
        error_issues = [i for i in result.issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

    def test_ilf_rejects_source_code(self, validator):
        """Test ILF rejects source code files."""
        result = validator.validate_ilf(
            name="SourceFiles",
            description="ASP source code files",
            dets=500,
            rets=100,
        )

        assert result.is_valid is False
        # Check if any issue mentions source code
        all_messages = " ".join([i.get("message", "") for i in result.issues])
        assert "source" in all_messages.lower() or "code" in all_messages.lower()

    def test_ilf_rejects_high_det_ret(self, validator):
        """Test ILF rejects abnormally high DET/RET counts."""
        result = validator.validate_ilf(
            name="SuspiciousFile",
            description="Data file",
            dets=1000,  # Way too high for real business data
            rets=500,
        )

        # Should have issues or suggestions for suspicious counts
        assert len(result.issues) > 0 or len(result.suggestions) > 0

    # === EIF Validation Tests ===

    def test_eif_valid(self, validator):
        """Test valid EIF."""
        result = validator.validate_eif(
            name="ProductCatalog",
            description="External product catalog referenced by application",
            dets=20,
            rets=3,
        )

        assert result.is_valid is True

    def test_eif_requires_external(self, validator):
        """Test EIF requires external reference."""
        result = validator.validate_eif(
            name="InternalData",
            description="Internal data maintained by us",
            dets=10,
            rets=1,
        )

        # Should have suggestions about internal vs external
        assert len(result.suggestions) > 0 or result.is_valid is False or len(result.issues) > 0

    # === Transaction Validation Tests ===

    def test_ei_valid(self, validator):
        """Test valid EI."""
        result = validator.validate_ei(
            name="CreateCustomer",
            description="Create new customer record",
            dets=10,
            ftrs=2,
        )

        assert result.is_valid is True

    def test_eo_valid(self, validator):
        """Test valid EO."""
        result = validator.validate_eo(
            name="GenerateReport",
            description="Generate sales report with calculations",
            dets=15,
            ftrs=3,
        )

        assert result.is_valid is True

    def test_eq_valid(self, validator):
        """Test valid EQ."""
        result = validator.validate_eq(
            name="SearchCustomer",
            description="Search customer by name",
            dets=5,
            ftrs=1,
        )

        assert result.is_valid is True

    def test_eq_rejects_calculations(self, validator):
        """Test EQ should not have calculations."""
        result = validator.validate_eq(
            name="CalculateTotal",
            description="Calculate total with discount",
            dets=10,
            ftrs=2,
        )

        # Should have suggestions that EQ shouldn't have calculations
        assert len(result.suggestions) > 0 or len(result.issues) > 0
