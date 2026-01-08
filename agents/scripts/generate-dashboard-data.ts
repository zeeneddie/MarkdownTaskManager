#!/usr/bin/env ts-node
/**
 * Generate Dashboard Data
 *
 * Creates JSON data file for the Quality Dashboard
 * Week 12 Day 3-4 - Quality Dashboard data generation
 */

import QualityDashboardService from '../services/qualityDashboardService';
import * as fs from 'fs';
import * as path from 'path';

interface CliOptions {
  output?: string;
  format?: 'json' | 'csv';
  serve?: boolean;
}

/**
 * Generate dashboard data and save to file
 */
async function generateDashboardData(options: CliOptions = {}): Promise<void> {
  const {
    output = path.join(__dirname, '../../data/dashboard-data.json'),
    format = 'json',
    serve = false
  } = options;

  console.log('\n📊 Generating Quality Dashboard Data...\n');

  try {
    const dashboardService = new QualityDashboardService();

    // Get dashboard data
    console.log('🔍 Running quality checks...');
    const data = await dashboardService.getDashboardData();

    console.log('\n✅ Quality Check Complete\n');
    console.log('Metrics:');
    console.log(`  Overall Score: ${data.metrics.overallScore}%`);
    console.log(`  Total Violations: ${data.metrics.totalViolations}`);
    console.log(`  Critical Issues: ${data.metrics.criticalViolations}`);
    console.log(`  Files Checked: ${data.metrics.filesChecked}`);
    console.log();

    console.log('Category Scores:');
    Object.entries(data.categoryScores).forEach(([category, score]) => {
      const icon = score >= 90 ? '✅' : score >= 80 ? '🟢' : score >= 70 ? '🟡' : '🔴';
      console.log(`  ${icon} ${category}: ${score}%`);
    });
    console.log();

    // Ensure output directory exists
    const outputDir = path.dirname(output);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Save data
    if (format === 'json') {
      const jsonData = JSON.stringify(data, null, 2);
      fs.writeFileSync(output, jsonData, 'utf-8');
      console.log(`💾 Saved dashboard data to: ${output}`);
    } else if (format === 'csv') {
      const csvData = await dashboardService.exportAsCsv();
      const csvOutput = output.replace('.json', '.csv');
      fs.writeFileSync(csvOutput, csvData, 'utf-8');
      console.log(`💾 Saved CSV report to: ${csvOutput}`);
    }

    // Display trend
    const trend = dashboardService.getTrend();
    const trendIcon = trend === 'improving' ? '📈' :
                      trend === 'declining' ? '📉' : '➡️';
    console.log(`${trendIcon} Quality Trend: ${trend.toUpperCase()}`);

    // Display compliance status
    const compliance = dashboardService.getComplianceStatus();
    const complianceIcon = compliance === 'excellent' ? '🏆' :
                          compliance === 'good' ? '✅' :
                          compliance === 'needs_improvement' ? '⚠️' : '🚨';
    console.log(`${complianceIcon} Compliance Status: ${compliance.toUpperCase().replace('_', ' ')}`);

    console.log('\n✨ Dashboard data generated successfully!\n');

    if (serve) {
      console.log('📡 Starting simple HTTP server...');
      console.log('Dashboard available at: http://localhost:8080/quality-dashboard.html');
      console.log('Press Ctrl+C to stop\n');
      startSimpleServer();
    }

  } catch (error) {
    console.error('❌ Error generating dashboard data:', error);
    process.exit(1);
  }
}

/**
 * Start a simple HTTP server to serve the dashboard
 */
function startSimpleServer(): void {
  const http = require('http');
  const fs = require('fs');
  const path = require('path');

  const PORT = 8080;
  const FRONTEND_DIR = path.join(__dirname, '../../../frontend');
  const DATA_DIR = path.join(__dirname, '../../data');

  const server = http.createServer((req: any, res: any) => {
    let filePath = '';

    if (req.url === '/' || req.url === '/quality-dashboard.html') {
      filePath = path.join(FRONTEND_DIR, 'quality-dashboard.html');
    } else if (req.url === '/api/dashboard-data') {
      // Serve dashboard data as API endpoint
      filePath = path.join(DATA_DIR, 'dashboard-data.json');
      res.setHeader('Content-Type', 'application/json');
    } else {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }

    fs.readFile(filePath, (err: any, data: any) => {
      if (err) {
        res.writeHead(500);
        res.end('Error loading file');
        return;
      }

      if (!res.getHeader('Content-Type')) {
        res.setHeader('Content-Type', 'text/html');
      }
      res.writeHead(200);
      res.end(data);
    });
  });

  server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
  });
}

// Run if executed directly
if (require.main === module) {
  const args = process.argv.slice(2);

  const options: CliOptions = {
    output: undefined,
    format: 'json',
    serve: false
  };

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--output' || args[i] === '-o') {
      options.output = args[++i];
    } else if (args[i] === '--format' || args[i] === '-f') {
      options.format = args[++i] as 'json' | 'csv';
    } else if (args[i] === '--serve' || args[i] === '-s') {
      options.serve = true;
    } else if (args[i] === '--help' || args[i] === '-h') {
      console.log(`
Usage: ts-node generate-dashboard-data.ts [options]

Options:
  -o, --output <path>   Output file path (default: ../../data/dashboard-data.json)
  -f, --format <type>   Output format: json or csv (default: json)
  -s, --serve           Start HTTP server to serve dashboard
  -h, --help            Show this help message

Examples:
  ts-node generate-dashboard-data.ts
  ts-node generate-dashboard-data.ts --serve
  ts-node generate-dashboard-data.ts --format csv
  ts-node generate-dashboard-data.ts --output /tmp/dashboard.json
      `);
      process.exit(0);
    }
  }

  generateDashboardData(options).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { generateDashboardData };
