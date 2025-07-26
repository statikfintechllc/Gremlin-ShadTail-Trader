// Electron API type definitions
export interface TailscaleStatus {
  connected: boolean;
  ip: string | null;
  hostname: string | null;
}

export interface ElectronAPI {
  // App info
  getAppVersion: () => Promise<string>;
  
  // Backend control
  restartBackend: () => Promise<string>;
  
  // Tailscale control
  tailscaleStatus: () => Promise<TailscaleStatus>;
  tailscaleStart: (authKey?: string) => Promise<TailscaleStatus>;
  tailscaleStop: () => Promise<TailscaleStatus>;
  tailscaleQRCode: () => Promise<{ url?: string }>;
  
  // Configuration
  getConfig: () => Promise<any>;
  saveConfig: (config: any) => Promise<{ success: boolean }>;
  
  // Logging
  logToMain: (level: string, message: string, data?: any) => void;
  
  // Platform info
  platform: string;
  isDev: boolean;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    windowAPI?: {
      minimize: () => void;
      maximize: () => void;
      close: () => void;
    };
  }
}

export {};