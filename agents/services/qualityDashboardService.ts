/**
 * Quality Dashboard Service
 *
 * Provides data aggregation and API endpoints for the Quality Dashboard
 * Week 12 Day 3-4 - Quality Dashboard integration
 */

import QualityGateService, { QualityGateResult } from './qualityGateService';
import * as fs from 'fs';
import * as path from 'path';

export interface DashboardMetrics {
  overallScore: number;
  totalViolations: number;
  criticalViolations: number;
  highViolations: number;
  mediumViolations: number;
  lowViolations: number;
  filesChecked: number;
  timestamp: string;
}

export interface CategoryScores {
  'SIG-TOP-10': number;
  'SOLID': number;
  'GRASP': number;
  'TDD': number;
  'Testing Patterns': number;
  'Design Patterns': number;
  'Clean Code': number;
  'Law of Demeter': number;
}

export interface HistoricalDataPoint {
  date: string;
  score: number;
  violations: number;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  categoryScores: CategoryScores;
  historicalData: HistoricalDataPoint[];
  recentFindings: Array<{
    severity: string;
    title: string;
    location: string;
    description: string;
    recommendation: string;
    category: string;
  }>;
  checksEnabled: number;
  checksTotal: number;
}

export class QualityDashboardService {
  private qualityGateService: QualityGateService;
  private historyFile: string;
  private maxHistoryDays: number;

  constructor() {
    this.qualityGateService = new QualityGateService();
    this.historyFile = path.join(__dirname, '../data/quality-history.json');
    this.maxHistoryDays = 30;

    // Ensure data directory exists
    const dataDir = path.dirname(this.historyFile);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
  }

  /**
   * Get current dashboard data
   */
  async getDashboardData(): Promise<DashboardData> {
    // Run quality check on full codebase
    const qualityResult = await this.qualityGateService.checkPostImplementation({
      scope: 'full_codebase'
    });

    // Extract metrics
    const metrics = this.extractMetrics(qualityResult);
    const categoryScores = this.extractCategoryScores(qualityResult);
    const recentFindings = this.extractRecentFindings(qualityResult);

    // Get historical data
    const historicalData = this.getHistoricalData();

    // Save current metrics to history
    await this.saveToHistory(metrics);

    return {
      metrics,
      categoryScores,
      historicalData,
      recentFindings,
      checksEnabled: this.countEnabledChecks(),
      checksTotal: 28  // Total checks across all categories
    };
  }

  /**
   * Extract key metrics from quality gate result
   */
  private extractMetrics(result: QualityGateResult): DashboardMetrics {
    return {
      overallScore: result.bestPracticeScore.totalScore,
      totalViolations: result.summary.totalViolations,
      criticalViolations: result.summary.criticalViolations,
      highViolations: result.summary.highViolations,
      mediumViolations: result.summary.mediumViolations,
      lowViolations: result.summary.lowViolations,
      filesChecked: 0,  // TODO: Add filesAnalyzed to metadata
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Extract category scores
   */
  private extractCategoryScores(result: QualityGateResult): CategoryScores {
    return {
      'SIG-TOP-10': result.bestPracticeScore.sigCompliance.overall,
      'SOLID': result.bestPracticeScore.solidCompliance.overall,
      'GRASP': result.bestPracticeScore.graspCompliance.overall,
      'TDD': result.bestPracticeScore.tddCompliance.overall,
      'Testing Patterns': result.bestPracticeScore.testingPatternsCompliance.overall,
      'Design Patterns': result.bestPracticeScore.designPatternsCompliance.overall,
      'Clean Code': result.bestPracticeScore.cleanCodeCompliance.overall,
      'Law of Demeter': 100 - (result.bestPracticeScore.lawOfDemeter.violations * 5)
    };
  }

  /**
   * Extract recent findings (top 10 by severity)
   */
  private extractRecentFindings(result: QualityGateResult) {
    // Sort by severity: critical > high > medium > low
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

    return result.findings
      .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
      .slice(0, 10)
      .map(finding => ({
        severity: finding.severity,
        title: finding.title,
        location: finding.location,
        description: finding.description,
        recommendation: finding.recommendation,
        category: finding.bestPractice
      }));
  }

  /**
   * Get historical quality data
   */
  private getHistoricalData(): HistoricalDataPoint[] {
    try {
      if (!fs.existsSync(this.historyFile)) {
        return [];
      }

      const data = fs.readFileSync(this.historyFile, 'utf-8');
      const history = JSON.parse(data);

      // Return last N days
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.maxHistoryDays);

      return history
        .filter((point: HistoricalDataPoint) => new Date(point.date) >= cutoffDate)
        .sort((a: HistoricalDataPoint, b: HistoricalDataPoint) =>
          new Date(a.date).getTime() - new Date(b.date).getTime()
        );
    } catch (error) {
      console.error('Error reading quality history:', error);
      return [];
    }
  }

  /**
   * Save current metrics to history
   */
  private async saveToHistory(metrics: DashboardMetrics): Promise<void> {
    try {
      let history: HistoricalDataPoint[] = this.getHistoricalData();

      const today = new Date().toISOString().split('T')[0];

      // Check if today's entry already exists
      const todayIndex = history.findIndex(point => point.date === today);

      const newPoint: HistoricalDataPoint = {
        date: today,
        score: metrics.overallScore,
        violations: metrics.totalViolations
      };

      if (todayIndex >= 0) {
        // Update existing entry
        history[todayIndex] = newPoint;
      } else {
        // Add new entry
        history.push(newPoint);
      }

      // Keep only last N days
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.maxHistoryDays);
      history = history.filter(point => new Date(point.date) >= cutoffDate);

      // Save to file
      fs.writeFileSync(this.historyFile, JSON.stringify(history, null, 2), 'utf-8');
    } catch (error) {
      console.error('Error saving quality history:', error);
    }
  }

  /**
   * Count enabled checks
   */
  private countEnabledChecks(): number {
    // This would normally check the QualityGateService configuration
    // For now, assuming all 28 checks are enabled
    return 28;
  }

  /**
   * Export dashboard data as JSON
   */
  async exportAsJson(): Promise<string> {
    const data = await this.getDashboardData();
    return JSON.stringify(data, null, 2);
  }

  /**
   * Export dashboard data as CSV
   */
  async exportAsCsv(): Promise<string> {
    const data = await this.getDashboardData();

    let csv = 'Category,Score,Violations\n';

    // Add category scores
    Object.entries(data.categoryScores).forEach(([category, score]) => {
      csv += `${category},${score},\n`;
    });

    // Add summary
    csv += '\nSummary\n';
    csv += `Overall Score,${data.metrics.overallScore}\n`;
    csv += `Total Violations,${data.metrics.totalViolations}\n`;
    csv += `Critical,${data.metrics.criticalViolations}\n`;
    csv += `High,${data.metrics.highViolations}\n`;
    csv += `Medium,${data.metrics.mediumViolations}\n`;
    csv += `Low,${data.metrics.lowViolations}\n`;

    return csv;
  }

  /**
   * Get quality trend (improvement or decline)
   */
  getTrend(): 'improving' | 'declining' | 'stable' {
    const history = this.getHistoricalData();

    if (history.length < 2) {
      return 'stable';
    }

    const recent = history.slice(-7);  // Last 7 days
    const average = recent.reduce((sum, point) => sum + point.score, 0) / recent.length;
    const previousAverage = history.slice(-14, -7).reduce((sum, point) => sum + point.score, 0) / 7;

    if (average > previousAverage + 2) {
      return 'improving';
    } else if (average < previousAverage - 2) {
      return 'declining';
    }
    return 'stable';
  }

  /**
   * Get compliance status
   */
  getComplianceStatus(): 'excellent' | 'good' | 'needs_improvement' | 'critical' {
    const history = this.getHistoricalData();

    if (history.length === 0) {
      return 'needs_improvement';
    }

    const latest = history[history.length - 1];

    if (latest.score >= 90) return 'excellent';
    if (latest.score >= 80) return 'good';
    if (latest.score >= 70) return 'needs_improvement';
    return 'critical';
  }
}

export default QualityDashboardService;
