/**
 * Logger utility for the frontend application
 * Provides controlled logging with environment-based filtering
 */

type LogLevel = 'log' | 'info' | 'warn' | 'error' | 'debug';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
  sendToMonitoring: boolean;
}

class Logger {
  private config: LoggerConfig;
  private isDevelopment: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
    this.config = {
      enabled: this.isDevelopment,
      level: (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel) || 'info',
      sendToMonitoring: process.env.NEXT_PUBLIC_ENABLE_MONITORING === 'true',
    };
  }

  /**
   * Log general information
   */
  log(message: string, ...args: any[]): void {
    if (this.shouldLog('log')) {
      logger.info(`[LOG] ${message}`, ...args);
    }
  }

  /**
   * Log informational messages
   */
  info(message: string, ...args: any[]): void {
    if (this.shouldLog('info')) {
      logger.info(`[INFO] ${message}`, ...args);
    }
  }

  /**
   * Log warnings
   */
  warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn')) {
      logger.warn(`[WARN] ${message}`, ...args);
    }
  }

  /**
   * Log errors and optionally send to monitoring service
   */
  error(message: string, error?: Error | unknown, ...args: any[]): void {
    if (this.shouldLog('error')) {
      logger.error(`[ERROR] ${message}`, error, ...args);
    }

    // Send to monitoring in production
    if (this.config.sendToMonitoring && error) {
      this.sendErrorToMonitoring(message, error);
    }
  }

  /**
   * Log debug information (development only)
   */
  debug(message: string, ...args: any[]): void {
    if (this.isDevelopment && this.shouldLog('debug')) {
      logger.debug(`[DEBUG] ${message}`, ...args);
    }
  }

  /**
   * Check if logging is enabled for the given level
   */
  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled && level !== 'error') {
      return false;
    }

    const levels: LogLevel[] = ['debug', 'log', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const requestedLevelIndex = levels.indexOf(level);

    return requestedLevelIndex >= currentLevelIndex;
  }

  /**
   * Send error to monitoring service (e.g., Sentry)
   */
  private sendErrorToMonitoring(message: string, error: Error | unknown): void {
    try {
      // In production, you would send to Sentry or similar
      // For now, we'll just prepare the data structure
      const errorData = {
        message,
        error:
          error instanceof Error
            ? {
              name: error.name,
              message: error.message,
              stack: error.stack,
            }
            : error,
        timestamp: new Date().toISOString(),
        userAgent:
          typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
        url: typeof window !== 'undefined' ? window.location.href : 'unknown',
      };

      // TODO: Integrate with monitoring service
      // Example: Sentry.captureException(error, { extra: errorData });

      if (this.isDevelopment) {
        this.debug('[MONITORING] Would send error:', errorData);
      }
    } catch (e) {
      // Silently fail - don't break the app if monitoring fails
      if (this.isDevelopment) {
        this.error('[MONITORING] Failed to send error:', e);
      }
    }
  }

  /**
   * Group related logs together
   */
  group(label: string, collapsed: boolean = false): void {
    if (this.isDevelopment) {
      if (collapsed) {
        console.groupCollapsed(label);
      } else {
        console.group(label);
      }
    }
  }

  /**
   * End a log group
   */
  groupEnd(): void {
    if (this.isDevelopment) {
      console.groupEnd();
    }
  }

  /**
   * Log performance timing
   */
  time(label: string): void {
    if (this.isDevelopment) {
      console.time(label);
    }
  }

  /**
   * End performance timing
   */
  timeEnd(label: string): void {
    if (this.isDevelopment) {
      console.timeEnd(label);
    }
  }

  /**
   * Log table data (development only)
   */
  table(data: any): void {
    if (this.isDevelopment) {
      console.table(data);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export type for convenience
export type { LogLevel };