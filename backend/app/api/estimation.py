"""
Function Point Estimation API Endpoints

Provides REST API for IFPUG Function Point calculation.

Author: Claude Code (Week 13 Day 5)
Date: 2025-11-19
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

import sys
sys.path.insert(0, '/home/eddie/Projects/MarkdownTaskManager/backend')

from estimation.function_points import (
    FunctionPointCalculator,
    FunctionPointRequest,
    FunctionPointResponse
)
from estimation.story_points import (
    StoryPointEstimator,
    StoryPointRequest,
    StoryPointResponse
)

router = APIRouter(prefix="/estimation", tags=["estimation"])


@router.post("/function-points", response_model=FunctionPointResponse)
async def calculate_function_points(
    request: FunctionPointRequest
) -> FunctionPointResponse:
    """
    Calculate Function Points using IFPUG CPM 4.3.1 methodology.

    This endpoint implements the International Function Point Users Group (IFPUG)
    Counting Practices Manual (CPM) 4.3.1 for software size estimation.

    ## Request Body

    ```json
    {
      "project_name": "E-Commerce Platform",
      "ilfs": [
        {"name": "User Database", "rets": 2, "dets": 15}
      ],
      "eifs": [
        {"name": "Payment Gateway API", "rets": 1, "dets": 10}
      ],
      "eis": [
        {"name": "Login Form", "ftrs": 1, "dets": 3}
      ],
      "eos": [
        {"name": "Sales Report", "ftrs": 3, "dets": 15}
      ],
      "eqs": [
        {"name": "Search Products", "ftrs": 1, "dets": 5}
      ],
      "use_vaf": false,
      "gsc_ratings": null
    }
    ```

    ## Component Types

    - **ILF (Internal Logical File)**: Data stored within application
    - **EIF (External Interface File)**: Reference data from external systems
    - **EI (External Input)**: Data/control coming into system
    - **EO (External Output)**: Derived/calculated data going out
    - **EQ (External Query)**: Simple data retrieval (no calculations)

    ## Complexity Factors

    - **RETs (Record Element Types)**: Logical subgroups within data file
    - **DETs (Data Element Types)**: Unique user-recognizable fields
    - **FTRs (File Types Referenced)**: Number of ILFs/EIFs accessed

    ## Value Adjustment Factor (Optional)

    Set `use_vaf: true` and provide 14 GSC ratings (0-5 each) to apply
    Value Adjustment Factor. VAF formula: 0.65 + (TDI × 0.01)

    ## Response

    Returns detailed breakdown including:
    - Individual component calculations with complexity
    - Component totals by type
    - Unadjusted Function Points (UFP)
    - Value Adjustment Factor (VAF) if requested
    - Adjusted Function Points (AFP) = UFP × VAF
    - Summary with estimation guidance

    ## Examples

    ### Simple Project (No VAF)
    60 FP ≈ 7.5-12 person-days (Medium project)

    ### Complex Project (With VAF)
    94 UFP × 1.11 VAF = 104.34 AFP ≈ 13-21 person-days

    ## Error Handling

    - 400: Invalid input (missing required fields, out-of-range values)
    - 422: Validation error (incorrect data types, invalid complexity factors)
    - 500: Internal server error
    """
    try:
        calculator = FunctionPointCalculator(request)
        result = calculator.calculate()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/function-points/complexity-matrices")
async def get_complexity_matrices() -> Dict[str, Any]:
    """
    Get IFPUG complexity matrices for all component types.

    Returns the official IFPUG CPM 4.3.1 complexity determination matrices
    that are used to classify components as Low, Average, or High complexity.

    ## Response

    Returns matrices for:
    - ILF (Internal Logical Files): RETs × DETs → Complexity → FP Weight
    - EIF (External Interface Files): RETs × DETs → Complexity → FP Weight
    - EI (External Inputs): FTRs × DETs → Complexity → FP Weight
    - EO (External Outputs): FTRs × DETs → Complexity → FP Weight
    - EQ (External Queries): FTRs × DETs → Complexity → FP Weight
    """
    return {
        "ilf": {
            "description": "Internal Logical Files - Data maintained within application",
            "complexity_factors": ["RETs (Record Element Types)", "DETs (Data Element Types)"],
            "matrix": {
                "1_ret": {
                    "1_19_dets": {"complexity": "Low", "fp": 7},
                    "20_50_dets": {"complexity": "Low", "fp": 7},
                    "51_plus_dets": {"complexity": "Average", "fp": 10}
                },
                "2_5_rets": {
                    "1_19_dets": {"complexity": "Low", "fp": 7},
                    "20_50_dets": {"complexity": "Average", "fp": 10},
                    "51_plus_dets": {"complexity": "High", "fp": 15}
                },
                "6_plus_rets": {
                    "1_19_dets": {"complexity": "Average", "fp": 10},
                    "20_50_dets": {"complexity": "High", "fp": 15},
                    "51_plus_dets": {"complexity": "High", "fp": 15}
                }
            },
            "weights": {"Low": 7, "Average": 10, "High": 15}
        },
        "eif": {
            "description": "External Interface Files - Reference data from external systems",
            "complexity_factors": ["RETs (Record Element Types)", "DETs (Data Element Types)"],
            "matrix": {
                "1_ret": {
                    "1_19_dets": {"complexity": "Low", "fp": 5},
                    "20_50_dets": {"complexity": "Low", "fp": 5},
                    "51_plus_dets": {"complexity": "Average", "fp": 7}
                },
                "2_5_rets": {
                    "1_19_dets": {"complexity": "Low", "fp": 5},
                    "20_50_dets": {"complexity": "Average", "fp": 7},
                    "51_plus_dets": {"complexity": "High", "fp": 10}
                },
                "6_plus_rets": {
                    "1_19_dets": {"complexity": "Average", "fp": 7},
                    "20_50_dets": {"complexity": "High", "fp": 10},
                    "51_plus_dets": {"complexity": "High", "fp": 10}
                }
            },
            "weights": {"Low": 5, "Average": 7, "High": 10}
        },
        "ei": {
            "description": "External Inputs - Data/control coming into system",
            "complexity_factors": ["FTRs (File Types Referenced)", "DETs (Data Element Types)"],
            "matrix": {
                "0_1_ftr": {
                    "1_4_dets": {"complexity": "Low", "fp": 3},
                    "5_15_dets": {"complexity": "Low", "fp": 3},
                    "16_plus_dets": {"complexity": "Average", "fp": 4}
                },
                "2_ftrs": {
                    "1_4_dets": {"complexity": "Low", "fp": 3},
                    "5_15_dets": {"complexity": "Average", "fp": 4},
                    "16_plus_dets": {"complexity": "High", "fp": 6}
                },
                "3_plus_ftrs": {
                    "1_4_dets": {"complexity": "Average", "fp": 4},
                    "5_15_dets": {"complexity": "High", "fp": 6},
                    "16_plus_dets": {"complexity": "High", "fp": 6}
                }
            },
            "weights": {"Low": 3, "Average": 4, "High": 6}
        },
        "eo": {
            "description": "External Outputs - Derived/calculated data going out",
            "complexity_factors": ["FTRs (File Types Referenced)", "DETs (Data Element Types)"],
            "matrix": {
                "0_1_ftr": {
                    "1_5_dets": {"complexity": "Low", "fp": 4},
                    "6_19_dets": {"complexity": "Low", "fp": 4},
                    "20_plus_dets": {"complexity": "Average", "fp": 5}
                },
                "2_3_ftrs": {
                    "1_5_dets": {"complexity": "Low", "fp": 4},
                    "6_19_dets": {"complexity": "Average", "fp": 5},
                    "20_plus_dets": {"complexity": "High", "fp": 7}
                },
                "4_plus_ftrs": {
                    "1_5_dets": {"complexity": "Average", "fp": 5},
                    "6_19_dets": {"complexity": "High", "fp": 7},
                    "20_plus_dets": {"complexity": "High", "fp": 7}
                }
            },
            "weights": {"Low": 4, "Average": 5, "High": 7}
        },
        "eq": {
            "description": "External Queries - Simple data retrieval (no calculations)",
            "complexity_factors": ["FTRs (File Types Referenced)", "DETs (Data Element Types)"],
            "matrix": {
                "0_1_ftr": {
                    "1_5_dets": {"complexity": "Low", "fp": 3},
                    "6_19_dets": {"complexity": "Low", "fp": 3},
                    "20_plus_dets": {"complexity": "Average", "fp": 4}
                },
                "2_3_ftrs": {
                    "1_5_dets": {"complexity": "Low", "fp": 3},
                    "6_19_dets": {"complexity": "Average", "fp": 4},
                    "20_plus_dets": {"complexity": "High", "fp": 6}
                },
                "4_plus_ftrs": {
                    "1_5_dets": {"complexity": "Average", "fp": 4},
                    "6_19_dets": {"complexity": "High", "fp": 6},
                    "20_plus_dets": {"complexity": "High", "fp": 6}
                }
            },
            "weights": {"Low": 3, "Average": 4, "High": 6}
        },
        "vaf": {
            "description": "Value Adjustment Factor (Optional)",
            "formula": "VAF = 0.65 + (TDI × 0.01)",
            "tdi_range": "0 to 70 (sum of 14 GSC ratings, each 0-5)",
            "vaf_range": "0.65 to 1.35",
            "gsc_characteristics": [
                "1. Data communications",
                "2. Distributed data processing",
                "3. Performance",
                "4. Heavily used configuration",
                "5. Transaction rate",
                "6. On-line data entry",
                "7. End-user efficiency",
                "8. On-line update",
                "9. Complex processing",
                "10. Reusability",
                "11. Installation ease",
                "12. Operational ease",
                "13. Multiple sites",
                "14. Facilitate change"
            ],
            "note": "VAF is optional in IFPUG CPM 4.3.1 (moved to appendix)"
        },
        "standard": {
            "name": "IFPUG Counting Practices Manual",
            "version": "4.3.1",
            "release_date": "January 2010",
            "iso_standard": "ISO/IEC 20926:2003"
        }
    }


@router.get("/function-points/examples")
async def get_examples() -> Dict[str, Any]:
    """
    Get example Function Point calculations for different project sizes.

    Returns real-world examples demonstrating:
    - Simple CRUD application (~80 FP)
    - Medium e-commerce platform (~200 FP)
    - Large enterprise system (~500 FP)

    Each example includes complete component breakdown and estimation.
    """
    return {
        "simple_crud": {
            "description": "Simple CRUD application with basic user management",
            "estimated_fp": 80,
            "estimated_effort": "8-10 person-days",
            "components": {
                "ilfs": [
                    {"name": "Users", "rets": 1, "dets": 12, "complexity": "Low", "fp": 7},
                    {"name": "Posts", "rets": 2, "dets": 18, "complexity": "Low", "fp": 7},
                    {"name": "Comments", "rets": 1, "dets": 8, "complexity": "Low", "fp": 7}
                ],
                "eifs": [
                    {"name": "Authentication Service", "rets": 1, "dets": 6, "complexity": "Low", "fp": 5}
                ],
                "eis": [
                    {"name": "Register", "ftrs": 1, "dets": 10, "complexity": "Low", "fp": 3},
                    {"name": "Login", "ftrs": 1, "dets": 3, "complexity": "Low", "fp": 3},
                    {"name": "Create Post", "ftrs": 1, "dets": 8, "complexity": "Low", "fp": 3},
                    {"name": "Add Comment", "ftrs": 2, "dets": 5, "complexity": "Low", "fp": 3}
                ],
                "eos": [
                    {"name": "User Profile", "ftrs": 1, "dets": 12, "complexity": "Low", "fp": 4},
                    {"name": "Post Feed", "ftrs": 2, "dets": 10, "complexity": "Average", "fp": 5}
                ],
                "eqs": [
                    {"name": "Search Posts", "ftrs": 1, "dets": 6, "complexity": "Low", "fp": 3},
                    {"name": "View Post", "ftrs": 2, "dets": 10, "complexity": "Low", "fp": 3},
                    {"name": "List Comments", "ftrs": 1, "dets": 8, "complexity": "Low", "fp": 3}
                ]
            },
            "project_size": "Small"
        },
        "ecommerce_platform": {
            "description": "E-commerce platform with payments, inventory, and reporting",
            "estimated_fp": 200,
            "estimated_effort": "25-40 person-days",
            "components": {
                "ilfs": [
                    {"name": "Users", "rets": 3, "dets": 25, "complexity": "Average", "fp": 10},
                    {"name": "Products", "rets": 4, "dets": 35, "complexity": "Average", "fp": 10},
                    {"name": "Orders", "rets": 5, "dets": 40, "complexity": "Average", "fp": 10},
                    {"name": "Inventory", "rets": 3, "dets": 20, "complexity": "Low", "fp": 7},
                    {"name": "Cart", "rets": 2, "dets": 15, "complexity": "Low", "fp": 7}
                ],
                "eifs": [
                    {"name": "Payment Gateway", "rets": 2, "dets": 25, "complexity": "Average", "fp": 7},
                    {"name": "Shipping API", "rets": 1, "dets": 15, "complexity": "Low", "fp": 5},
                    {"name": "Tax Service", "rets": 1, "dets": 10, "complexity": "Low", "fp": 5}
                ],
                "eis": [
                    {"name": "Register", "ftrs": 1, "dets": 12, "complexity": "Low", "fp": 3},
                    {"name": "Add to Cart", "ftrs": 2, "dets": 8, "complexity": "Low", "fp": 3},
                    {"name": "Checkout", "ftrs": 3, "dets": 20, "complexity": "High", "fp": 6},
                    {"name": "Create Product", "ftrs": 2, "dets": 18, "complexity": "Average", "fp": 4},
                    {"name": "Update Inventory", "ftrs": 2, "dets": 12, "complexity": "Average", "fp": 4}
                ],
                "eos": [
                    {"name": "Order Confirmation", "ftrs": 2, "dets": 15, "complexity": "Average", "fp": 5},
                    {"name": "Sales Report", "ftrs": 4, "dets": 25, "complexity": "High", "fp": 7},
                    {"name": "Inventory Report", "ftrs": 3, "dets": 20, "complexity": "High", "fp": 7},
                    {"name": "Invoice Generation", "ftrs": 3, "dets": 22, "complexity": "High", "fp": 7}
                ],
                "eqs": [
                    {"name": "Search Products", "ftrs": 2, "dets": 12, "complexity": "Average", "fp": 4},
                    {"name": "View Order", "ftrs": 2, "dets": 15, "complexity": "Average", "fp": 4},
                    {"name": "Track Shipment", "ftrs": 1, "dets": 8, "complexity": "Low", "fp": 3}
                ]
            },
            "project_size": "Medium"
        },
        "enterprise_erp": {
            "description": "Enterprise ERP system with multi-module integration",
            "estimated_fp": 500,
            "estimated_effort": "100-167 person-days",
            "components": {
                "summary": "Large-scale system with 20+ ILFs, 10+ EIFs, 30+ transactions",
                "characteristics": [
                    "Multi-module architecture (Finance, HR, Supply Chain, Manufacturing)",
                    "Complex integrations with external systems",
                    "Advanced reporting and analytics",
                    "Workflow automation and approval chains",
                    "Role-based access control across modules"
                ],
                "complexity_distribution": {
                    "high_complexity_components": 35,
                    "average_complexity_components": 45,
                    "low_complexity_components": 20
                }
            },
            "project_size": "Enterprise"
        }
    }


@router.get("/function-points/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for Function Point calculator"""
    return {
        "status": "healthy",
        "service": "Function Point Calculator",
        "version": "1.0.0",
        "standard": "IFPUG CPM 4.3.1"
    }


# ==================== STORY POINTS ENDPOINTS ====================

@router.post("/story-points", response_model=StoryPointResponse)
async def estimate_story_points(
    request: StoryPointRequest
) -> StoryPointResponse:
    """
    Estimate Story Points using Fibonacci mapping and complexity analysis.

    This endpoint estimates story points (1, 2, 3, 5, 8, 13, 21) based on:
    - Technical complexity (1-10)
    - Business value (1-10)
    - Risk level (1-10)
    - Uncertainty level (1-10)
    - Number of dependencies (0-10)

    Optionally supports three-point estimation (PERT formula) to convert
    story points to hours with confidence intervals.

    ## Request Body

    ```json
    {
      "story_name": "Implement user authentication with OAuth",
      "complexity_factors": {
        "technical_complexity": 7,
        "business_value": 8,
        "risk_level": 5,
        "uncertainty": 6,
        "dependencies": 3
      },
      "three_point": {
        "optimistic_hours": 4,
        "most_likely_hours": 8,
        "pessimistic_hours": 16
      },
      "description": "Add OAuth 2.0 authentication with Google and GitHub providers"
    }
    ```

    ## Complexity Factors Explained

    - **technical_complexity**: How difficult is the implementation? (1=trivial, 10=extremely complex)
    - **business_value**: How important is this to the business? (1=low, 10=critical)
    - **risk_level**: How risky is this work? (1=no risk, 10=very risky)
    - **uncertainty**: How well do we understand requirements? (1=clear, 10=very unclear)
    - **dependencies**: How many other systems/teams are involved? (0=none, 10=many)

    ## Fibonacci Story Points

    - **1 point**: Trivial task (< 1 hour)
    - **2 points**: Simple task (1-2 hours)
    - **3 points**: Small story (2-4 hours)
    - **5 points**: Medium story (1 day)
    - **8 points**: Large story (2-3 days)
    - **13 points**: Very large story (1 week) - consider splitting
    - **21 points**: Epic-sized - MUST be split into smaller stories

    ## Three-Point Estimation (Optional)

    Provide optimistic, most likely, and pessimistic hour estimates to get:
    - PERT estimate: (O + 4M + P) / 6
    - Standard deviation
    - 68% confidence interval (±1σ)
    - 95% confidence interval (±2σ)

    ## Response

    Returns:
    - Fibonacci story points
    - Raw complexity score (0-100)
    - Confidence intervals (±10%, ±25%)
    - Hours estimate (if three-point provided)
    - Reasoning for the estimate
    - Risk factors identified
    - Recommendations for the team

    ## Example Response

    ```json
    {
      "story_name": "Implement user authentication with OAuth",
      "fibonacci_points": 8,
      "complexity_score": 62.5,
      "confidence_narrow": {"min": 7.2, "max": 8.8, "percentage": "±10%"},
      "confidence_wide": {"min": 6.0, "max": 10.0, "percentage": "±25%"},
      "hours_estimate": {
        "pert_estimate": 8.67,
        "optimistic": 4,
        "most_likely": 8,
        "pessimistic": 16,
        "range": "4-16 hours",
        "standard_deviation": 2.0,
        "confidence_68": {"min": 6.67, "max": 10.67},
        "confidence_95": {"min": 4.67, "max": 12.67}
      },
      "reasoning": "Estimated at 8 story points (Large story - 2-3 days) based on high technical complexity, very high business value, moderate risk. Complexity score: 62.5/100.",
      "risk_factors": [
        "High technical complexity - may require specialized expertise",
        "Very high business value - requires extra scrutiny and testing"
      ],
      "recommendations": [
        "👥 Pair programming recommended - complex technical implementation",
        "🎯 High value + risk - extra testing, code review, and stakeholder demos required"
      ]
    }
    ```

    ## Error Handling

    - 400: Invalid input (values out of range)
    - 422: Validation error (incorrect data types, three-point estimates not in order)
    - 500: Internal server error
    """
    try:
        result = StoryPointEstimator.estimate(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/story-points/fibonacci-guide")
async def get_fibonacci_guide() -> Dict[str, Any]:
    """
    Get comprehensive guide to Fibonacci story points.

    Returns detailed explanations of each Fibonacci value, when to use them,
    and guidelines for team estimation sessions (Planning Poker).
    """
    return {
        "fibonacci_scale": [1, 2, 3, 5, 8, 13, 21],
        "descriptions": {
            "1": {
                "name": "Trivial",
                "effort": "< 1 hour",
                "examples": [
                    "Update a text label",
                    "Change a color value",
                    "Fix a typo in documentation"
                ],
                "when_to_use": "Task is completely understood, no complexity, no risk"
            },
            "2": {
                "name": "Simple",
                "effort": "1-2 hours",
                "examples": [
                    "Add a new field to a form",
                    "Update validation rule",
                    "Add simple unit test"
                ],
                "when_to_use": "Task is well understood, low complexity, minimal risk"
            },
            "3": {
                "name": "Small",
                "effort": "2-4 hours",
                "examples": [
                    "Create a new API endpoint (simple)",
                    "Add basic CRUD operations",
                    "Implement simple business rule"
                ],
                "when_to_use": "Task is understood, some complexity, low risk"
            },
            "5": {
                "name": "Medium",
                "effort": "1 day",
                "examples": [
                    "Implement a feature with moderate complexity",
                    "Add API integration (documented)",
                    "Create database migration with data transformation"
                ],
                "when_to_use": "Moderate complexity, some unknowns, moderate risk"
            },
            "8": {
                "name": "Large",
                "effort": "2-3 days",
                "examples": [
                    "Implement complex feature with multiple components",
                    "Add OAuth authentication",
                    "Create reporting dashboard"
                ],
                "when_to_use": "High complexity, multiple unknowns, high risk"
            },
            "13": {
                "name": "Very Large",
                "effort": "1 week",
                "examples": [
                    "Implement major subsystem",
                    "Migrate to new architecture pattern",
                    "Build admin panel with multiple modules"
                ],
                "when_to_use": "Very high complexity - strongly consider splitting",
                "warning": "⚠️ Stories this large should usually be broken down into smaller stories (3-5 points each)"
            },
            "21": {
                "name": "Epic",
                "effort": "> 1 week",
                "examples": [
                    "Complete user management system",
                    "Build entire payment workflow",
                    "Implement full reporting suite"
                ],
                "when_to_use": "NEVER - must be split into smaller stories",
                "warning": "🚫 This is an epic, not a story. Break it down into multiple 3-8 point stories."
            }
        },
        "planning_poker_guide": {
            "overview": "Planning Poker is a consensus-based estimation technique",
            "steps": [
                "1. Product Owner reads the user story",
                "2. Team discusses and asks clarifying questions",
                "3. Each team member selects a card privately",
                "4. Everyone reveals cards simultaneously",
                "5. If consensus: done! If not: discuss and repeat"
            ],
            "discussion_triggers": {
                "wide_range": "If estimates vary widely (e.g., 3 and 13), highest and lowest explain their reasoning",
                "all_high": "If everyone votes high (≥8), consider if story needs to be split",
                "uncertainty": "If multiple 'coffee cup' (uncertain) votes, need more information"
            },
            "tips": [
                "Start with reference stories of known size",
                "Estimate relative to other stories, not absolute hours",
                "When in doubt, round up (uncertainty = higher estimate)",
                "Don't average estimates - reach consensus through discussion",
                "Track velocity over sprints to improve accuracy"
            ]
        },
        "complexity_scoring": {
            "technical_complexity": "How hard to implement? (1=trivial, 10=very hard)",
            "business_value": "How important? (1=nice-to-have, 10=critical)",
            "risk_level": "How risky? (1=no risk, 10=very risky)",
            "uncertainty": "How clear? (1=very clear, 10=very unclear)",
            "dependencies": "How many? (0=none, 10=many)"
        },
        "anti_patterns": [
            "❌ Treating story points as hours (they're not!)",
            "❌ Comparing velocity between teams (each team is different)",
            "❌ Using story points for individual performance (team metric only)",
            "❌ Re-estimating completed stories (estimate is fixed at planning)",
            "❌ Estimating bugs (just fix them!)"
        ]
    }


@router.get("/story-points/health")
async def story_points_health_check() -> Dict[str, str]:
    """Health check endpoint for Story Point estimator"""
    return {
        "status": "healthy",
        "service": "Story Point Estimator",
        "version": "1.0.0",
        "method": "Fibonacci + PERT + Complexity Analysis"
    }
