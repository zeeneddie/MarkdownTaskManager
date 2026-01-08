"use strict";
/**
 * Work Type Definitions
 *
 * Shared types for work classification and routing.
 * Extracted to avoid circular dependencies.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkType = void 0;
var WorkType;
(function (WorkType) {
    WorkType["PROJECT_DEFINITION"] = "PROJECT_DEFINITION";
    WorkType["NEW_FEATURE"] = "NEW_FEATURE";
    WorkType["MAINTENANCE"] = "MAINTENANCE";
    WorkType["QUALITY_AUDIT"] = "QUALITY_AUDIT";
    WorkType["BUG"] = "BUG";
    WorkType["ENHANCEMENT"] = "ENHANCEMENT";
    WorkType["MIGRATION"] = "MIGRATION";
    WorkType["QUALITY_IMPROVEMENT"] = "QUALITY_IMPROVEMENT";
    WorkType["TESTING"] = "TESTING";
})(WorkType || (exports.WorkType = WorkType = {}));
