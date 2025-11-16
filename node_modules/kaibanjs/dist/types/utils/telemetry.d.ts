/**
 * Telemetry Utility Module.
 *
 * This module integrates TelemetryDeck to help improve our project by:
 * 1. Identifying and diagnosing technical issues more efficiently
 * 2. Measuring the performance of different parts of the application
 * 3. Guiding our efforts in optimizing and enhancing the codebase
 *
 * We strictly limit data collection to anonymous, non-personal information
 * such as error occurrences and performance metrics. This approach allows
 * us to make informed decisions for improving the project's stability and
 * performance without compromising privacy.
 *
 * Users can opt out of telemetry by setting the KAIBAN_TELEMETRY_OPT_OUT
 * environment variable to any value.
 *
 * @module telemetry
 */
/** Interface for telemetry instance */
export interface TelemetryInstance {
    /** Send a signal to telemetry */
    signal: (eventName: string, payload?: Record<string, unknown>) => void;
}
/**
 * Initializes the telemetry system
 * @param appID - TelemetryDeck application ID
 * @param clientUser - Client user identifier
 * @returns Telemetry instance
 */
export declare function initializeTelemetry(appID?: string, clientUser?: string): TelemetryInstance;
/**
 * Gets the current telemetry instance
 * @throws Error if telemetry has not been initialized
 * @returns Telemetry instance
 */
export declare function getTelemetryInstance(): TelemetryInstance;
