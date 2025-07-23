export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  data?: any;
}

class Logger {
  private logLevel: LogLevel = LogLevel.INFO;
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;

  setLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  private log(level: LogLevel, message: string, data?: any): void {
    if (level >= this.logLevel) {
      const entry: LogEntry = {
        timestamp: new Date(),
        level,
        message,
        data,
      };

      this.logs.push(entry);
      
      // Keep only the most recent logs
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs);
      }

      // Output to console
      const timestamp = entry.timestamp.toISOString();
      const levelStr = LogLevel[level];
      const logMessage = `[${timestamp}] ${levelStr}: ${message}`;
      
      switch (level) {
        case LogLevel.DEBUG:
          console.debug(logMessage, data);
          break;
        case LogLevel.INFO:
          console.info(logMessage, data);
          break;
        case LogLevel.WARN:
          console.warn(logMessage, data);
          break;
        case LogLevel.ERROR:
          console.error(logMessage, data);
          break;
      }
    }
  }

  debug(message: string, data?: any): void {
    this.log(LogLevel.DEBUG, message, data);
  }

  info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  warn(message: string, data?: any): void {
    this.log(LogLevel.WARN, message, data);
  }

  error(message: string, data?: any): void {
    this.log(LogLevel.ERROR, message, data);
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs(): void {
    this.logs = [];
  }
}

export const logger = new Logger();

// Set log level based on environment
if (typeof window !== 'undefined') {
  // Browser environment
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  logger.setLevel(isDev ? LogLevel.DEBUG : LogLevel.INFO);
} else {
  // Node environment
  logger.setLevel(LogLevel.INFO);
}