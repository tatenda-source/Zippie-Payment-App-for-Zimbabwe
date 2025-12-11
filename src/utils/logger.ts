/**
 * Logging utility for the application
 * Provides consistent logging across the frontend
 */

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

export interface LoggerConfig {
  level: LogLevel;
  enabled: boolean;
  prefix: string;
}

class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: LogLevel.INFO,
      enabled: process.env.NODE_ENV === 'development',
      prefix: '[Zippie]',
      ...config,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;

    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const messageLevelIndex = levels.indexOf(level);

    return messageLevelIndex >= currentLevelIndex;
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `${this.config.prefix} ${timestamp} [${level.toUpperCase()}] ${message}`;
  }

  debug(message: string, ...args: any[]): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      const formattedMessage = this.formatMessage(LogLevel.DEBUG, message);
      // eslint-disable-next-line no-console
      console.log(formattedMessage, ...args);
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.shouldLog(LogLevel.INFO)) {
      const formattedMessage = this.formatMessage(LogLevel.INFO, message);
      // eslint-disable-next-line no-console
      console.info(formattedMessage, ...args);
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.shouldLog(LogLevel.WARN)) {
      const formattedMessage = this.formatMessage(LogLevel.WARN, message);
      // eslint-disable-next-line no-console
      console.warn(formattedMessage, ...args);
    }
  }

  error(message: string, error?: Error | any, ...args: any[]): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      const formattedMessage = this.formatMessage(LogLevel.ERROR, message);
      if (error instanceof Error) {
        // eslint-disable-next-line no-console
        console.error(formattedMessage, error.message, error.stack, ...args);
      } else {
        // eslint-disable-next-line no-console
        console.error(formattedMessage, error, ...args);
      }
    }
  }

  // Utility methods for common logging scenarios
  apiCall(endpoint: string, method: string = 'GET'): void {
    this.debug(`API Call: ${method} ${endpoint}`);
  }

  apiResponse(endpoint: string, status: number, responseTime?: number): void {
    const message = `API Response: ${endpoint} - Status: ${status}`;
    const details = responseTime ? `${message} (${responseTime}ms)` : message;

    if (status >= 400) {
      this.error(details);
    } else if (status >= 300) {
      this.warn(details);
    } else {
      this.info(details);
    }
  }

  performance(metric: string, value: number, unit: string = 'ms'): void {
    this.info(`Performance: ${metric} = ${value}${unit}`);
  }
}

// Create a singleton instance
export const logger = new Logger({
  level: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.DEBUG,
  enabled: true,
  prefix: '[Zippie]',
});

export default logger;
