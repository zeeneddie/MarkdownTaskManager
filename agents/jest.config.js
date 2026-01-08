/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>'],
  testMatch: [
    '**/__tests__/**/*.test.ts',
    '**/*.test.ts'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  collectCoverageFrom: [
    'commands/**/*.ts',
    'workflows/**/*.ts',
    'types/**/*.ts',
    '!**/__tests__/**',
    '!**/node_modules/**',
    '!**/dist/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  verbose: true,
  testTimeout: 30000, // 30 seconds for agent execution
  // Transform files with ts-jest
  transform: {
    '^.+\\.ts$': 'ts-jest'
  },
  // Module name mapper for absolute imports (if needed)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1'
  }
};
