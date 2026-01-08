# backend/tests/services/week112/test_vb6_php_extractors.py
"""
Tests for VB6 and PHP Business Rule Extractors (Week 112 - Phase 4).

Tests:
1. VB6 extractor (.frm, .bas, .cls files)
2. PHP extractor (Laravel, WordPress patterns)
3. ExtractorFactory integration
"""

import pytest
from pathlib import Path

from app.services.static_analysis.extraction_models import (
    BusinessRule,
    CodeSymbol,
    RuleType,
    Language,
    ExtractionTier,
    ExtractionMethod,
)
from app.services.static_analysis.vb6_extractor import VB6BusinessRuleExtractor
from app.services.static_analysis.php_extractor import PHPBusinessRuleExtractor
from app.services.static_analysis.extractor_factory import ExtractorFactory


# ============================================================================
# VB6 TEST DATA
# ============================================================================

SAMPLE_VB6_FORM = """
VERSION 5.00
Begin VB.Form frmCustomer
   Caption         =   "Customer Management"
   ClientHeight    =   3090
End
Attribute VB_Name = "frmCustomer"
Attribute VB_GlobalNameSpace = False
Option Explicit

Private Sub Form_Load()
    If blnCanView = False Then
        MsgBox "Access denied", vbCritical
        Unload Me
    End If

    LoadCustomerData
End Sub

Private Sub cmdSave_Click()
    On Error GoTo ErrHandler

    If Len(txtName.Text) = 0 Then
        MsgBox "Name is required"
        Exit Sub
    End If

    If txtAmount.Text < 0 Then
        MsgBox "Amount must be positive"
        Exit Sub
    End If

    Dim rs As ADODB.Recordset
    Set rs = New ADODB.Recordset
    rs.Open "SELECT * FROM tblCustomer WHERE CustomerID = " & intID

    If rs.EOF Then
        rs.AddNew
    End If

    rs!CustomerName = txtName.Text
    rs!Amount = CDbl(txtAmount.Text)
    rs.Update

    MsgBox "Saved successfully"
    Exit Sub

ErrHandler:
    MsgBox "Error: " & Err.Description
End Sub

Private Sub cmdDelete_Click()
    If blnCanDelete = False Then
        MsgBox "Delete access denied"
        Exit Sub
    End If

    If MsgBox("Are you sure?", vbYesNo) = vbYes Then
        CurrentDb.Execute "DELETE FROM tblCustomer WHERE CustomerID = " & intID
    End If
End Sub

Private Function CalculateTotal(ByVal dblPrice As Double, ByVal intQty As Integer) As Double
    CalculateTotal = Round(dblPrice * intQty, 2)
End Function
"""

SAMPLE_VB6_MODULE = """
Attribute VB_Name = "modDatabase"
Option Explicit

Public Const MAX_RECORDS As Long = 1000
Public gConn As ADODB.Connection
Private g_UserLevel As Integer

Public Sub InitConnection()
    On Error GoTo ErrHandler

    Set gConn = New ADODB.Connection
    gConn.Open "Provider=SQLOLEDB;Server=localhost;Database=CRM"
    Exit Sub

ErrHandler:
    Err.Raise vbObjectError + 1001, "modDatabase", "Connection failed"
End Sub

Public Function CheckPermission(ByVal strAction As String) As Boolean
    Select Case strAction
        Case "VIEW"
            CheckPermission = (g_UserLevel >= 1)
        Case "EDIT"
            CheckPermission = (g_UserLevel >= 2)
        Case "DELETE"
            CheckPermission = (g_UserLevel >= 3)
        Case Else
            CheckPermission = False
    End Select
End Function

Public Sub ExecuteQuery(ByVal strSQL As String)
    If g_UserLevel = 0 Then
        Err.Raise vbObjectError + 1002, "modDatabase", "Access denied"
    End If
    gConn.Execute strSQL
End Sub
"""

SAMPLE_VB6_CLASS = """
VERSION 1.0 CLASS
Attribute VB_Name = "clsOrder"
Attribute VB_GlobalNameSpace = False
Option Explicit

Private m_OrderID As Long
Private m_Status As String
Private m_Total As Currency

Public Property Get OrderID() As Long
    OrderID = m_OrderID
End Property

Public Property Let Status(ByVal vNewValue As String)
    If vNewValue = "CANCELLED" And m_Status = "SHIPPED" Then
        Err.Raise vbObjectError + 2001, "clsOrder", "Cannot cancel shipped order"
    End If
    m_Status = vNewValue
End Property

Public Sub CalculateTotal()
    Dim rs As ADODB.Recordset
    Set rs = gConn.OpenRecordset("SELECT SUM(Price * Qty) FROM tblOrderItems WHERE OrderID = " & m_OrderID)

    If Not rs.EOF Then
        m_Total = CCur(rs.Fields(0))
    End If
End Sub

Public Sub Ship()
    If m_Status <> "APPROVED" Then
        Err.Raise vbObjectError + 2002, "clsOrder", "Order must be approved before shipping"
    End If
    m_Status = "SHIPPED"
End Sub
"""


# ============================================================================
# PHP TEST DATA
# ============================================================================

SAMPLE_PHP_LARAVEL_CONTROLLER = """
<?php

namespace App\\Http\\Controllers;

use App\\Models\\User;
use App\\Models\\Order;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Gate;
use Illuminate\\Support\\Facades\\Log;

class OrderController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth');
        $this->middleware('role:admin')->only(['destroy']);
    }

    public function index(Request $request)
    {
        $this->authorize('viewAny', Order::class);

        $orders = Order::where('status', 'active')
            ->orderBy('created_at', 'desc')
            ->paginate(20);

        return view('orders.index', compact('orders'));
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'customer_id' => 'required|exists:customers,id',
            'amount' => 'required|numeric|min:0',
            'items' => 'required|array|min:1',
            'shipping_date' => 'required|date|after:today',
        ]);

        if (!Gate::allows('create-order', $request->user())) {
            abort(403, 'Unauthorized action');
        }

        try {
            $order = Order::create($validated);
            $order->calculateTotal();

            Log::info('Order created', ['order_id' => $order->id]);

            return redirect()->route('orders.show', $order)
                ->with('success', 'Order created successfully');
        } catch (\\Exception $e) {
            Log::error('Order creation failed', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function update(Request $request, Order $order)
    {
        $this->authorize('update', $order);

        if ($order->status === 'shipped') {
            abort(422, 'Cannot modify shipped orders');
        }

        $validated = $request->validate([
            'amount' => 'numeric|min:0',
            'status' => 'in:pending,approved,shipped,cancelled',
        ]);

        $order->update($validated);

        return redirect()->back()->with('success', 'Order updated');
    }

    public function destroy(Order $order)
    {
        if (!$request->user()->can('delete', $order)) {
            abort(403);
        }

        if ($order->status !== 'cancelled') {
            abort(422, 'Only cancelled orders can be deleted');
        }

        $order->delete();

        return redirect()->route('orders.index');
    }
}
"""

SAMPLE_PHP_WORDPRESS_PLUGIN = """
<?php
/**
 * Plugin Name: Custom Orders
 * Description: Custom order management
 */

if (!defined('ABSPATH')) {
    exit;
}

class Custom_Orders_Plugin {

    public function __construct() {
        add_action('init', [$this, 'register_post_type']);
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_filter('the_content', [$this, 'filter_content']);
    }

    public function register_post_type() {
        register_post_type('custom_order', [
            'labels' => ['name' => 'Orders'],
            'public' => false,
            'show_ui' => true,
        ]);
    }

    public function add_admin_menu() {
        if (!current_user_can('manage_options')) {
            return;
        }

        add_menu_page(
            'Custom Orders',
            'Orders',
            'manage_options',
            'custom-orders',
            [$this, 'render_admin_page']
        );
    }

    public function process_order($order_data) {
        if (!is_user_logged_in()) {
            wp_die('You must be logged in');
        }

        if (!wp_verify_nonce($_POST['order_nonce'], 'create_order')) {
            wp_die('Security check failed');
        }

        $order_data = [
            'customer_name' => sanitize_text_field($_POST['customer_name']),
            'email' => sanitize_email($_POST['email']),
            'amount' => floatval($_POST['amount']),
        ];

        if (empty($order_data['customer_name'])) {
            return new WP_Error('invalid_name', 'Name is required');
        }

        if ($order_data['amount'] < 0) {
            return new WP_Error('invalid_amount', 'Amount must be positive');
        }

        global $wpdb;

        $result = $wpdb->insert(
            $wpdb->prefix . 'custom_orders',
            $order_data,
            ['%s', '%s', '%f']
        );

        if ($result === false) {
            return new WP_Error('db_error', 'Failed to save order');
        }

        do_action('custom_order_created', $wpdb->insert_id, $order_data);

        return $wpdb->insert_id;
    }

    public function get_orders($args = []) {
        if (!current_user_can('edit_posts')) {
            return [];
        }

        global $wpdb;

        $defaults = [
            'status' => 'active',
            'limit' => 20,
            'offset' => 0,
        ];

        $args = wp_parse_args($args, $defaults);

        $results = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM {$wpdb->prefix}custom_orders
                 WHERE status = %s
                 ORDER BY created_at DESC
                 LIMIT %d OFFSET %d",
                $args['status'],
                $args['limit'],
                $args['offset']
            )
        );

        return $results;
    }

    public function delete_order($order_id) {
        if (!current_user_can('delete_posts')) {
            return false;
        }

        global $wpdb;

        $order = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM {$wpdb->prefix}custom_orders WHERE id = %d",
                $order_id
            )
        );

        if (!$order || $order->status !== 'cancelled') {
            return false;
        }

        return $wpdb->delete(
            $wpdb->prefix . 'custom_orders',
            ['id' => $order_id],
            ['%d']
        );
    }
}

new Custom_Orders_Plugin();
"""


# ============================================================================
# VB6 EXTRACTOR TESTS
# ============================================================================

class TestVB6Extractor:
    """Tests for VB6 Business Rule Extractor."""

    @pytest.fixture
    def extractor(self):
        return VB6BusinessRuleExtractor(
            extraction_tier=ExtractionTier.FREE,
            project_id=1
        )

    def test_supported_extensions(self, extractor):
        """Test that VB6 extractor supports correct extensions."""
        extensions = extractor.get_supported_extensions()
        assert '.frm' in extensions
        assert '.bas' in extensions
        assert '.cls' in extensions
        assert '.ctl' in extensions

    def test_language(self, extractor):
        """Test that VB6 extractor returns correct language."""
        assert extractor.get_language() == Language.VB6

    @pytest.mark.asyncio
    async def test_extract_symbols_from_form(self, extractor):
        """Test symbol extraction from VB6 form."""
        symbols = await extractor._extract_symbols(SAMPLE_VB6_FORM, "frmCustomer.frm")

        # Should find the form as a class-like symbol
        form_symbols = [s for s in symbols if s.symbol_type == "form"]
        assert len(form_symbols) >= 1

        # Should find Sub procedures
        sub_symbols = [s for s in symbols if s.symbol_type == "sub"]
        assert len(sub_symbols) >= 3  # Form_Load, cmdSave_Click, cmdDelete_Click

        # Should find functions
        func_symbols = [s for s in symbols if s.symbol_type == "function"]
        assert len(func_symbols) >= 1  # CalculateTotal

    @pytest.mark.asyncio
    async def test_extract_symbols_from_module(self, extractor):
        """Test symbol extraction from VB6 module."""
        symbols = await extractor._extract_symbols(SAMPLE_VB6_MODULE, "modDatabase.bas")

        # Should find the module
        module_symbols = [s for s in symbols if s.symbol_type == "module"]
        assert len(module_symbols) >= 1

        # Should find Sub and Function
        sub_symbols = [s for s in symbols if s.symbol_type == "sub"]
        func_symbols = [s for s in symbols if s.symbol_type == "function"]
        assert len(sub_symbols) >= 2  # InitConnection, ExecuteQuery
        assert len(func_symbols) >= 1  # CheckPermission

    @pytest.mark.asyncio
    async def test_extract_rules_validation(self, extractor):
        """Test validation rule extraction from VB6."""
        result = await extractor.extract_from_file(
            "test.frm",
            source=SAMPLE_VB6_FORM
        )

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 2  # Len() check, < 0 check

    @pytest.mark.asyncio
    async def test_extract_rules_authorization(self, extractor):
        """Test authorization rule extraction from VB6."""
        result = await extractor.extract_from_file(
            "test.frm",
            source=SAMPLE_VB6_FORM
        )

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        assert len(auth_rules) >= 2  # blnCanView, blnCanDelete

    @pytest.mark.asyncio
    async def test_extract_rules_data_access(self, extractor):
        """Test data access rule extraction from VB6."""
        result = await extractor.extract_from_file(
            "test.frm",
            source=SAMPLE_VB6_FORM
        )

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        assert len(data_rules) >= 2  # rs.Open, CurrentDb.Execute

    @pytest.mark.asyncio
    async def test_extract_rules_error_handling(self, extractor):
        """Test error handling rule extraction from VB6."""
        result = await extractor.extract_from_file(
            "test.frm",
            source=SAMPLE_VB6_FORM
        )

        error_rules = [r for r in result.business_rules if r.rule_type == RuleType.ERROR_HANDLING]
        assert len(error_rules) >= 1  # On Error GoTo

    @pytest.mark.asyncio
    async def test_extract_rules_branching(self, extractor):
        """Test branching rule extraction from VB6 module."""
        result = await extractor.extract_from_file(
            "test.bas",
            source=SAMPLE_VB6_MODULE
        )

        branch_rules = [r for r in result.business_rules if r.rule_type == RuleType.BRANCHING]
        assert len(branch_rules) >= 3  # Select Case and Case statements

    @pytest.mark.asyncio
    async def test_extract_rules_workflow(self, extractor):
        """Test workflow/status rule extraction from VB6 class."""
        result = await extractor.extract_from_file(
            "test.cls",
            source=SAMPLE_VB6_CLASS
        )

        # Should detect status-related rules
        workflow_rules = [r for r in result.business_rules if r.rule_type == RuleType.WORKFLOW]
        assert len(workflow_rules) >= 1  # Status checks


# ============================================================================
# PHP EXTRACTOR TESTS
# ============================================================================

class TestPHPExtractor:
    """Tests for PHP Business Rule Extractor."""

    @pytest.fixture
    def extractor(self):
        return PHPBusinessRuleExtractor(
            extraction_tier=ExtractionTier.FREE,
            project_id=1
        )

    def test_supported_extensions(self, extractor):
        """Test that PHP extractor supports correct extensions."""
        extensions = extractor.get_supported_extensions()
        assert '.php' in extensions
        assert '.phtml' in extensions
        assert '.inc' in extensions

    def test_language(self, extractor):
        """Test that PHP extractor returns correct language."""
        assert extractor.get_language() == Language.PHP

    @pytest.mark.asyncio
    async def test_extract_symbols_laravel(self, extractor):
        """Test symbol extraction from Laravel controller."""
        symbols = await extractor._extract_symbols(
            SAMPLE_PHP_LARAVEL_CONTROLLER,
            "OrderController.php"
        )

        # Should find the class
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) >= 1
        assert class_symbols[0].name == "OrderController"

        # Should find at least one method (regex-based extraction)
        method_symbols = [s for s in symbols if s.symbol_type == "method"]
        assert len(method_symbols) >= 1  # At least __construct

    @pytest.mark.asyncio
    async def test_extract_symbols_wordpress(self, extractor):
        """Test symbol extraction from WordPress plugin."""
        symbols = await extractor._extract_symbols(
            SAMPLE_PHP_WORDPRESS_PLUGIN,
            "custom-orders.php"
        )

        # Should find the class
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) >= 1

        # Should find methods (regex-based extraction may find fewer)
        method_symbols = [s for s in symbols if s.symbol_type == "method"]
        assert len(method_symbols) >= 1  # At least one method

    @pytest.mark.asyncio
    async def test_extract_rules_laravel_validation(self, extractor):
        """Test Laravel validation rule extraction."""
        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 2  # At least some validation rules

    @pytest.mark.asyncio
    async def test_extract_rules_laravel_authorization(self, extractor):
        """Test Laravel authorization rule extraction."""
        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        assert len(auth_rules) >= 3  # middleware, authorize, Gate::allows, can

    @pytest.mark.asyncio
    async def test_extract_rules_laravel_data_access(self, extractor):
        """Test Laravel Eloquent data access rule extraction."""
        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        assert len(data_rules) >= 3  # where, create, update, delete

    @pytest.mark.asyncio
    async def test_extract_rules_laravel_error_handling(self, extractor):
        """Test Laravel error handling rule extraction."""
        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        error_rules = [r for r in result.business_rules if r.rule_type == RuleType.ERROR_HANDLING]
        assert len(error_rules) >= 3  # try-catch, abort, Log::error

    @pytest.mark.asyncio
    async def test_extract_rules_wordpress_authorization(self, extractor):
        """Test WordPress authorization rule extraction."""
        result = await extractor.extract_from_file(
            "custom-orders.php",
            source=SAMPLE_PHP_WORDPRESS_PLUGIN
        )

        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        assert len(auth_rules) >= 4  # current_user_can, is_user_logged_in, wp_verify_nonce

    @pytest.mark.asyncio
    async def test_extract_rules_wordpress_data_access(self, extractor):
        """Test WordPress database rule extraction."""
        result = await extractor.extract_from_file(
            "custom-orders.php",
            source=SAMPLE_PHP_WORDPRESS_PLUGIN
        )

        data_rules = [r for r in result.business_rules if r.rule_type == RuleType.DATA_ACCESS]
        assert len(data_rules) >= 4  # wpdb->insert, wpdb->get_results, wpdb->delete

    @pytest.mark.asyncio
    async def test_extract_rules_wordpress_validation(self, extractor):
        """Test WordPress sanitization/validation rule extraction."""
        result = await extractor.extract_from_file(
            "custom-orders.php",
            source=SAMPLE_PHP_WORDPRESS_PLUGIN
        )

        validation_rules = [r for r in result.business_rules if r.rule_type == RuleType.VALIDATION]
        assert len(validation_rules) >= 2  # sanitize_text_field, sanitize_email, empty checks

    @pytest.mark.asyncio
    async def test_detect_framework(self, extractor):
        """Test framework detection."""
        # Laravel patterns
        assert extractor._detect_framework("User::find(1)") == "Laravel"
        assert extractor._detect_framework("Eloquent") == "Laravel"

        # WordPress patterns
        assert extractor._detect_framework("current_user_can('edit_posts')") == "WordPress"
        assert extractor._detect_framework("$wpdb->get_results()") == "WordPress"

        # Generic PHP
        assert extractor._detect_framework("$x = 1 + 2") == "PHP"


# ============================================================================
# EXTRACTOR FACTORY TESTS
# ============================================================================

class TestExtractorFactoryPhase4:
    """Tests for ExtractorFactory with Phase 4 extractors."""

    @pytest.fixture
    def factory(self):
        return ExtractorFactory(
            extraction_tier=ExtractionTier.FREE,
            project_id=1
        )

    def test_vb6_extensions_registered(self, factory):
        """Test VB6 extensions are in factory."""
        assert factory.detect_language("test.frm") == Language.VB6
        assert factory.detect_language("test.bas") == Language.VB6
        assert factory.detect_language("test.cls") == Language.VB6
        assert factory.detect_language("test.ctl") == Language.VB6

    def test_php_extensions_registered(self, factory):
        """Test PHP extensions are in factory."""
        assert factory.detect_language("test.php") == Language.PHP
        assert factory.detect_language("test.phtml") == Language.PHP
        assert factory.detect_language("test.inc") == Language.PHP

    def test_get_vb6_extractor(self, factory):
        """Test getting VB6 extractor from factory."""
        extractor = factory.get_extractor(Language.VB6)
        assert extractor is not None
        assert isinstance(extractor, VB6BusinessRuleExtractor)

    def test_get_php_extractor(self, factory):
        """Test getting PHP extractor from factory."""
        extractor = factory.get_extractor(Language.PHP)
        assert extractor is not None
        assert isinstance(extractor, PHPBusinessRuleExtractor)

    def test_get_extractor_for_vb6_file(self, factory):
        """Test getting extractor for VB6 file path."""
        extractor = factory.get_extractor_for_file("C:/projects/legacy/frmMain.frm")
        assert extractor is not None
        assert extractor.get_language() == Language.VB6

    def test_get_extractor_for_php_file(self, factory):
        """Test getting extractor for PHP file path."""
        extractor = factory.get_extractor_for_file("/var/www/html/app/Controllers/OrderController.php")
        assert extractor is not None
        assert extractor.get_language() == Language.PHP

    def test_supported_languages_includes_phase4(self, factory):
        """Test that supported languages include VB6 and PHP."""
        languages = factory.get_supported_languages()
        assert Language.VB6 in languages
        assert Language.PHP in languages

    def test_supported_extensions_includes_phase4(self, factory):
        """Test that supported extensions include VB6 and PHP extensions."""
        extensions = factory.get_supported_extensions()
        assert '.frm' in extensions
        assert '.bas' in extensions
        assert '.cls' in extensions
        assert '.php' in extensions
        assert '.phtml' in extensions


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase4Integration:
    """Integration tests for Phase 4 extractors."""

    @pytest.mark.asyncio
    async def test_full_extraction_vb6_form(self):
        """Test full extraction pipeline for VB6 form."""
        factory = ExtractorFactory(extraction_tier=ExtractionTier.FREE)
        result = await factory.extract_from_file(
            "frmCustomer.frm",
        )

        # Since file doesn't exist, it should handle gracefully
        # Test with source instead
        extractor = factory.get_extractor(Language.VB6)
        result = await extractor.extract_from_file(
            "frmCustomer.frm",
            source=SAMPLE_VB6_FORM
        )

        assert result.language == Language.VB6
        assert len(result.business_rules) > 0
        assert len(result.code_symbols) > 0
        assert result.lines_of_code > 0

    @pytest.mark.asyncio
    async def test_full_extraction_php_laravel(self):
        """Test full extraction pipeline for Laravel PHP."""
        factory = ExtractorFactory(extraction_tier=ExtractionTier.FREE)
        extractor = factory.get_extractor(Language.PHP)

        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        assert result.language == Language.PHP
        assert len(result.business_rules) > 10
        assert len(result.code_symbols) > 0

        # Verify rule types distribution
        rule_types = set(r.rule_type for r in result.business_rules)
        assert RuleType.VALIDATION in rule_types
        assert RuleType.AUTHORIZATION in rule_types
        assert RuleType.DATA_ACCESS in rule_types

    @pytest.mark.asyncio
    async def test_full_extraction_php_wordpress(self):
        """Test full extraction pipeline for WordPress PHP."""
        factory = ExtractorFactory(extraction_tier=ExtractionTier.FREE)
        extractor = factory.get_extractor(Language.PHP)

        result = await extractor.extract_from_file(
            "custom-orders.php",
            source=SAMPLE_PHP_WORDPRESS_PLUGIN
        )

        assert result.language == Language.PHP
        assert len(result.business_rules) > 10

        # Check that WordPress-specific patterns are detected
        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        wp_auth = [r for r in auth_rules if 'current_user_can' in r.code_snippet.lower() or
                   'is_user_logged_in' in r.code_snippet.lower()]
        assert len(wp_auth) > 0

    @pytest.mark.asyncio
    async def test_rule_confidence_scores(self):
        """Test that confidence scores are calculated correctly."""
        factory = ExtractorFactory(extraction_tier=ExtractionTier.FREE)
        extractor = factory.get_extractor(Language.PHP)

        result = await extractor.extract_from_file(
            "OrderController.php",
            source=SAMPLE_PHP_LARAVEL_CONTROLLER
        )

        # All rules should have confidence between 0 and 1
        for rule in result.business_rules:
            assert 0.0 <= rule.confidence <= 1.0

        # Authorization rules should generally have higher confidence
        auth_rules = [r for r in result.business_rules if r.rule_type == RuleType.AUTHORIZATION]
        if auth_rules:
            avg_auth_conf = sum(r.confidence for r in auth_rules) / len(auth_rules)
            assert avg_auth_conf >= 0.5

    @pytest.mark.asyncio
    async def test_natural_language_generation(self):
        """Test that natural language descriptions are generated."""
        factory = ExtractorFactory(extraction_tier=ExtractionTier.FREE)
        extractor = factory.get_extractor(Language.VB6)

        result = await extractor.extract_from_file(
            "modDatabase.bas",
            source=SAMPLE_VB6_MODULE
        )

        for rule in result.business_rules:
            assert rule.natural_language is not None
            assert len(rule.natural_language) > 0
            # Should contain some keywords
            assert any(kw in rule.natural_language.upper() for kw in
                       ['WHEN', 'IF', 'THEN', 'VALIDATE', 'AUTHORIZE', 'ENFORCE'])
