/**
 * Logging Utility.
 *
 * This module sets up and configures the logging system used across the KaibanJS library.
 * It provides a centralized logger that can be imported and used throughout the library,
 * with support for dynamic log level configuration.
 *
 * @module logger
 */
import log from 'loglevel';
/** Valid log levels for the application */
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'silent';
/**
 * Sets the logging level for the application
 * @param level - The desired logging level
 */
export declare const setLogLevel: (level: LogLevel) => void;
/** The main logger instance */
export declare const logger: log.RootLogger;
