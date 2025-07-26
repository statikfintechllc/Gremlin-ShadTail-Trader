import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Wifi, 
  WifiOff, 
  Power, 
  PowerOff, 
  QrCode, 
  RefreshCw, 
  Save,
  AlertCircle,
  CheckCircle,
  Download,
  Upload
} from 'lucide-react';

interface TailscaleStatus {
  connected: boolean;
  ip: string | null;
  hostname: string | null;
}

interface FullSpecConfig {
  api_keys: {
    grok: { api_key: string; base_url: string; model: string; max_tokens: number };
    ibkr: { username: string; password: string; paper_username: string; paper_password: string };
  };
  other_logins: {
    tailscale: { auth_key: string; hostname: string; tags: string[] };
  };
  system_config: {
    enable_tailscale_tunnel: boolean;
    pwa_publishing: {
      enabled: boolean;
      tunnel_name: string;
      qr_code_enabled: boolean;
    };
    plugins: {
      grok: { enabled: boolean };
      source_editor: { enabled: boolean };
    };
  };
}

interface SettingsProps {
  settings: { scanInterval: number; symbols: string[] };
  onUpdateSettings: (newSettings: Partial<{ scanInterval: number; symbols: string[] }>) => void;
}

export default function Settings({ settings, onUpdateSettings }: SettingsProps) {
  const [tailscaleStatus, setTailscaleStatus] = useState<TailscaleStatus>({ connected: false, ip: null, hostname: null });
  const [config, setConfig] = useState<FullSpecConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
    checkTailscaleStatus();
  }, []);

  const loadConfig = async () => {
    try {
      if (window.electronAPI) {
        const configData = await window.electronAPI.getConfig();
        setConfig(configData);
      } else {
        // Fallback for web environment
        const response = await fetch('http://localhost:8000/api/config');
        if (response.ok) {
          const configData = await response.json();
          setConfig(configData);
        }
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const saveConfig = async () => {
    if (!config) return;
    
    setSaveStatus('saving');
    try {
      if (window.electronAPI) {
        await window.electronAPI.saveConfig(config);
      } else {
        // Fallback for web environment
        const response = await fetch('http://localhost:8000/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config),
        });
        if (!response.ok) throw new Error('Failed to save config');
      }
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Failed to save config:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const checkTailscaleStatus = async () => {
    try {
      if (window.electronAPI) {
        const status = await window.electronAPI.tailscaleStatus();
        setTailscaleStatus(status);
      }
    } catch (error) {
      console.error('Failed to check Tailscale status:', error);
    }
  };

  const toggleTailscale = async () => {
    setIsLoading(true);
    try {
      if (window.electronAPI) {
        if (tailscaleStatus.connected) {
          await window.electronAPI.tailscaleStop();
        } else {
          const authKey = config?.other_logins?.tailscale?.auth_key;
          await window.electronAPI.tailscaleStart(authKey);
        }
        await checkTailscaleStatus();
      }
    } catch (error) {
      console.error('Failed to toggle Tailscale:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateQRCode = async () => {
    try {
      if (window.electronAPI && tailscaleStatus.connected) {
        const result = await window.electronAPI.tailscaleQRCode();
        setQrCodeUrl(result.url || null);
      }
    } catch (error) {
      console.error('Failed to generate QR code:', error);
    }
  };

  const updateConfig = (path: string, value: any) => {
    if (!config) return;
    
    const newConfig = { ...config };
    const pathParts = path.split('.');
    let current = newConfig;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      current = current[pathParts[i] as keyof typeof current] as any;
    }
    
    current[pathParts[pathParts.length - 1] as keyof typeof current] = value;
    setConfig(newConfig);
  };

  if (!config) {
    return (
      <div className="h-full bg-gray-900 text-white p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading configuration...</span>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-900 text-white p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold flex items-center">
          <SettingsIcon className="w-6 h-6 mr-2" />
          System Settings
        </h2>
        <button
          onClick={saveConfig}
          disabled={saveStatus === 'saving'}
          className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
            saveStatus === 'saved' ? 'bg-green-600' : 
            saveStatus === 'error' ? 'bg-red-600' : 
            'bg-blue-600 hover:bg-blue-700'
          } disabled:opacity-50`}
        >
          {saveStatus === 'saving' ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : saveStatus === 'saved' ? (
            <CheckCircle className="w-4 h-4 mr-2" />
          ) : saveStatus === 'error' ? (
            <AlertCircle className="w-4 h-4 mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          {saveStatus === 'saving' ? 'Saving...' : 
           saveStatus === 'saved' ? 'Saved!' : 
           saveStatus === 'error' ? 'Error!' : 'Save Config'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Configuration */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Trading Configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Scan Interval (seconds)
              </label>
              <input
                type="number"
                value={settings.scanInterval}
                onChange={(e) => onUpdateSettings({ scanInterval: parseInt(e.target.value) })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                min="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Symbols (comma-separated)
              </label>
              <input
                type="text"
                value={settings.symbols.join(', ')}
                onChange={(e) => onUpdateSettings({ 
                  symbols: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="GPRO, IXHL, AAPL"
              />
            </div>
          </div>
        </div>

        {/* Plugin Settings */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Plugin Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Grok Chat Plugin</span>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.system_config.plugins.grok.enabled}
                  onChange={(e) => updateConfig('system_config.plugins.grok.enabled', e.target.checked)}
                  className="w-4 h-4"
                />
                <div className={`w-3 h-3 rounded-full ${config.system_config.plugins.grok.enabled ? 'bg-green-500' : 'bg-gray-500'}`}></div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>Source Editor Plugin</span>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.system_config.plugins.source_editor.enabled}
                  onChange={(e) => updateConfig('system_config.plugins.source_editor.enabled', e.target.checked)}
                  className="w-4 h-4"
                />
                <div className={`w-3 h-3 rounded-full ${config.system_config.plugins.source_editor.enabled ? 'bg-green-500' : 'bg-gray-500'}`}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Tailscale Configuration */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            {tailscaleStatus.connected ? (
              <Wifi className="w-5 h-5 mr-2 text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 mr-2 text-red-400" />
            )}
            Tailscale Network
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <div>
                <div className="font-medium">Connection Status</div>
                <div className="text-sm text-gray-400">
                  {tailscaleStatus.connected ? (
                    <>
                      Connected as {tailscaleStatus.hostname}
                      {tailscaleStatus.ip && <div>IP: {tailscaleStatus.ip}</div>}
                    </>
                  ) : (
                    'Disconnected'
                  )}
                </div>
              </div>
              <button
                onClick={toggleTailscale}
                disabled={isLoading}
                className={`p-2 rounded transition-colors ${
                  tailscaleStatus.connected 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-green-600 hover:bg-green-700'
                } disabled:opacity-50`}
              >
                {isLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : tailscaleStatus.connected ? (
                  <PowerOff className="w-4 h-4" />
                ) : (
                  <Power className="w-4 h-4" />
                )}
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Auth Key</label>
              <input
                type="password"
                value={config.other_logins.tailscale.auth_key}
                onChange={(e) => updateConfig('other_logins.tailscale.auth_key', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="tskey-auth-..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Hostname</label>
              <input
                type="text"
                value={config.other_logins.tailscale.hostname}
                onChange={(e) => updateConfig('other_logins.tailscale.hostname', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="gremlin-trader"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.system_config.enable_tailscale_tunnel}
                onChange={(e) => updateConfig('system_config.enable_tailscale_tunnel', e.target.checked)}
                className="w-4 h-4"
              />
              <label className="text-sm">Auto-start Tailscale on launch</label>
            </div>
          </div>
        </div>

        {/* PWA Publishing */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Upload className="w-5 h-5 mr-2" />
            PWA Publishing
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.system_config.pwa_publishing.enabled}
                onChange={(e) => updateConfig('system_config.pwa_publishing.enabled', e.target.checked)}
                className="w-4 h-4"
              />
              <label className="text-sm">Enable PWA publishing via Tailscale</label>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Tunnel Name</label>
              <input
                type="text"
                value={config.system_config.pwa_publishing.tunnel_name}
                onChange={(e) => updateConfig('system_config.pwa_publishing.tunnel_name', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="gremlin-trader"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.system_config.pwa_publishing.qr_code_enabled}
                onChange={(e) => updateConfig('system_config.pwa_publishing.qr_code_enabled', e.target.checked)}
                className="w-4 h-4"
              />
              <label className="text-sm">Enable QR code for mobile access</label>
            </div>

            {tailscaleStatus.connected && config.system_config.pwa_publishing.enabled && (
              <div className="mt-4">
                <button
                  onClick={generateQRCode}
                  className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                >
                  <QrCode className="w-4 h-4 mr-2" />
                  Generate Mobile QR Code
                </button>
                
                {qrCodeUrl && (
                  <div className="mt-3 p-4 bg-gray-700 rounded text-center">
                    <img src={qrCodeUrl} alt="QR Code" className="mx-auto mb-2" />
                    <p className="text-sm text-gray-400">
                      Scan with your mobile device to access the trading platform
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* API Configuration */}
        <div className="bg-gray-800 rounded-lg p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Grok AI</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">API Key</label>
                  <input
                    type="password"
                    value={config.api_keys.grok.api_key}
                    onChange={(e) => updateConfig('api_keys.grok.api_key', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                    placeholder="xai-..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Model</label>
                  <input
                    type="text"
                    value={config.api_keys.grok.model}
                    onChange={(e) => updateConfig('api_keys.grok.model', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  />
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-3">IBKR Trading</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Username</label>
                  <input
                    type="text"
                    value={config.api_keys.ibkr.username}
                    onChange={(e) => updateConfig('api_keys.ibkr.username', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Paper Username</label>
                  <input
                    type="text"
                    value={config.api_keys.ibkr.paper_username}
                    onChange={(e) => updateConfig('api_keys.ibkr.paper_username', e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}