import React, { useState, useEffect, Suspense } from 'react';
import { logger } from '../utils/logger';
import GrokChat from './GrokChat';
import SourceEditor from './SourceEditor';
// Monaco Editor - dynamically imported to handle SSR
const MonacoEditor = React.lazy(() => import('./MonacoEditor'));
import SettingsComponent from './Settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { MessageCircle, Code, TrendingUp, Settings, Users, BarChart3, Activity, DollarSign, Zap, Target } from 'lucide-react';

interface AgentStatus {
  trading_agents: {
    [key: string]: {
      name: string;
      status: string;
      cpu: number;
      gpu: number;
      memory: string;
      uptime: string;
      last_signal: string;
      last_trade: string;
      error?: string;
      performance?: {
        win_rate: number;
        avg_profit: number;
        avg_loss: number;
        total_trades: number;
      };
    };
  };
  system_status: {
    cpu_usage: number;
    memory: string;
    connections: number;
    uptime: string;
  };
  performance: {
    signals_per_hour: number;
    accuracy: number;
    latency: number;
    queue: number;
  };
}

interface FeedItem {
  symbol: string;
  price: number;
  up_pct: number;
  volume?: number;
  signal_types?: string[];
  confidence?: number;
  risk_score?: number;
  rsi?: number;
  vwap?: number;
  rotation?: number;
  data_source?: string;
  error?: string;
}

interface MarketOverview {
  indices?: Record<string, { price: number; change_pct: number }>;
  vix?: number;
  market_sentiment?: string;
  timestamp?: string;
}

interface Settings {
  scanInterval: number;
  symbols: string[];
}

type TabType = 'trading' | 'chat' | 'source' | 'agents' | 'settings';

// Settings Component
const SettingsComponent: React.FC<{
  settings: Settings;
  onUpdateSettings: (settings: Settings) => void;
}> = ({ settings, onUpdateSettings }) => {
  const [config, setConfig] = useState(settings);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdateSettings(config);
      
      // Save to backend via Electron API if available
      if (window.electronAPI) {
        await window.electronAPI.saveConfig(config);
      }
      
      // Success feedback could be added here
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const renderExchangeSettings = () => (
    <Card className="bg-trading-gray-200/10 border-trading-gray-300">
      <CardHeader>
        <CardTitle className="text-trading-gold flex items-center">
          <DollarSign className="w-5 h-5 mr-2" />
          Exchange Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-trading-bronze text-sm">API Key</label>
            <input
              type="password"
              value={config.exchange.apiKey || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                exchange: { ...prev.exchange, apiKey: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
              placeholder="Enter API Key"
            />
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Secret Key</label>
            <input
              type="password"
              value={config.exchange.secretKey || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                exchange: { ...prev.exchange, secretKey: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
              placeholder="Enter Secret Key"
            />
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Exchange</label>
            <select
              value={config.exchange.name}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                exchange: { ...prev.exchange, name: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            >
              <option value="binance">Binance</option>
              <option value="coinbase">Coinbase Pro</option>
              <option value="kraken">Kraken</option>
              <option value="bybit">Bybit</option>
            </select>
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Environment</label>
            <select
              value={config.exchange.environment}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                exchange: { ...prev.exchange, environment: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            >
              <option value="sandbox">Sandbox</option>
              <option value="production">Production</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.exchange.testMode || false}
            onChange={(e) => setConfig(prev => ({
              ...prev,
              exchange: { ...prev.exchange, testMode: e.target.checked }
            }))}
            className="rounded border-trading-gray-300"
          />
          <label className="text-trading-bronze">Test Mode (Paper Trading)</label>
        </div>
      </CardContent>
    </Card>
  );

  const renderRiskSettings = () => (
    <Card className="bg-trading-gray-200/10 border-trading-gray-300">
      <CardHeader>
        <CardTitle className="text-trading-gold flex items-center">
          <Shield className="w-5 h-5 mr-2" />
          Risk Management
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-trading-bronze text-sm">Max Position Size (%)</label>
            <input
              type="number"
              min="1"
              max="100"
              value={config.risk.maxPositionSize || 10}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                risk: { ...prev.risk, maxPositionSize: parseFloat(e.target.value) }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            />
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Max Daily Loss (%)</label>
            <input
              type="number"
              min="1"
              max="50"
              value={config.risk.maxDailyLoss || 5}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                risk: { ...prev.risk, maxDailyLoss: parseFloat(e.target.value) }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            />
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Stop Loss (%)</label>
            <input
              type="number"
              min="0.1"
              max="20"
              step="0.1"
              value={config.risk.stopLossPercent || 2}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                risk: { ...prev.risk, stopLossPercent: parseFloat(e.target.value) }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.risk.emergencyStop || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                risk: { ...prev.risk, emergencyStop: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Emergency Stop</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.risk.portfolioRebalancing || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                risk: { ...prev.risk, portfolioRebalancing: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Auto Rebalancing</label>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderNotificationSettings = () => (
    <Card className="bg-trading-gray-200/10 border-trading-gray-300">
      <CardHeader>
        <CardTitle className="text-trading-gold flex items-center">
          <Bell className="w-5 h-5 mr-2" />
          Notifications
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.notifications.tradeAlerts || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                notifications: { ...prev.notifications, tradeAlerts: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Trade Alerts</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.notifications.riskAlerts || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                notifications: { ...prev.notifications, riskAlerts: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Risk Alerts</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.notifications.systemAlerts || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                notifications: { ...prev.notifications, systemAlerts: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">System Alerts</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.notifications.emailNotifications || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                notifications: { ...prev.notifications, emailNotifications: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Email Notifications</label>
          </div>
        </div>
        
        {config.notifications.emailNotifications && (
          <div>
            <label className="text-trading-bronze text-sm">Email Address</label>
            <input
              type="email"
              value={config.notifications.email || ''}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                notifications: { ...prev.notifications, email: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
              placeholder="Enter email address"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderSystemSettings = () => (
    <Card className="bg-trading-gray-200/10 border-trading-gray-300">
      <CardHeader>
        <CardTitle className="text-trading-gold flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          System Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-trading-bronze text-sm">Log Level</label>
            <select
              value={config.system.logLevel || 'info'}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                system: { ...prev.system, logLevel: e.target.value }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            >
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warn">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          <div>
            <label className="text-trading-bronze text-sm">Update Frequency (ms)</label>
            <input
              type="number"
              min="100"
              max="10000"
              step="100"
              value={config.system.updateFrequency || 1000}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                system: { ...prev.system, updateFrequency: parseInt(e.target.value) }
              }))}
              className="w-full p-2 rounded bg-trading-gray-100/20 border border-trading-gray-300 text-trading-gold"
            />
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.system.autoStart || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                system: { ...prev.system, autoStart: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Auto-start on Launch</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.system.darkMode || true}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                system: { ...prev.system, darkMode: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Dark Mode</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.system.enableTelemetry || false}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                system: { ...prev.system, enableTelemetry: e.target.checked }
              }))}
              className="rounded border-trading-gray-300"
            />
            <label className="text-trading-bronze">Enable Telemetry</label>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {renderExchangeSettings()}
        {renderRiskSettings()}
        {renderNotificationSettings()}
        {renderSystemSettings()}
      </div>
      
      {/* Save Button */}
      <div className="border-t border-trading-gray-300 p-4 bg-trading-gray-200/10">
        <div className="flex justify-end space-x-4">
          <button
            onClick={() => setConfig(settings)}
            className="px-6 py-2 rounded border border-trading-gray-300 text-trading-bronze hover:text-trading-gold hover:border-trading-gold transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 rounded bg-trading-gold text-trading-black hover:bg-trading-bronze transition-colors disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('trading');
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [marketOverview, setMarketOverview] = useState<MarketOverview>({});
  const [settings, setSettings] = useState<Settings>({ scanInterval: 300, symbols: [] });
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
    setIsClient(true);
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Always use real agent data from /api/feed (agent-generated signals)
        const feedResponse = await fetch(`${API_BASE}/feed`);
        if (!feedResponse.ok) throw new Error('Failed to fetch feed');
        const feedData = await feedResponse.json();
        setFeed(feedData);
        
        // Fetch market overview
        try {
          const overviewResponse = await fetch(`${API_BASE}/market/overview`);
          if (overviewResponse.ok) {
            const overviewData = await overviewResponse.json();
            setMarketOverview(overviewData);
          }
        } catch (overviewError) {
          logger.warn('Market overview failed to load:', overviewError);
        }
        
        // Fetch settings
        const settingsResponse = await fetch(`${API_BASE}/settings`);
        if (!settingsResponse.ok) throw new Error('Failed to fetch settings');
        const settingsData = await settingsResponse.json();
        setSettings(settingsData);

        // Fetch agent status
        try {
          const agentResponse = await fetch(`${API_BASE}/agents/status`);
          if (agentResponse.ok) {
            const agentData = await agentResponse.json();
            setAgentStatus(agentData);
          }
        } catch (agentError) {
          console.warn('Agent status failed to load:', agentError);
        }
        
        logger.info('Dashboard data loaded successfully (REAL AGENT DATA)');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        logger.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Auto-refresh data
    const interval = setInterval(fetchData, settings.scanInterval * 1000);
    return () => clearInterval(interval);
  }, [settings.scanInterval]);

  const updateSettings = async (newSettings: Partial<Settings>) => {
    try {
      const response = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings),
      });
      
      if (!response.ok) throw new Error('Failed to update settings');
      const updatedSettings = await response.json();
      setSettings(updatedSettings);
      logger.info('Settings updated successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update settings';
      setError(errorMessage);
      logger.error('Settings update failed:', errorMessage);
    }
  };

  const renderTradingTab = () => (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardHeader>
            <CardTitle className="text-destructive text-lg">System Error</CardTitle>
            <CardDescription className="text-destructive/80">{error}</CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-900/20 to-green-800/20 border-green-800/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-300">Portfolio</CardTitle>
            <DollarSign className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">+12.5%</div>
            <p className="text-xs text-green-300/70">+2.4% from yesterday</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-900/20 to-blue-800/20 border-blue-800/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-300">Active Signals</CardTitle>
            <Activity className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-400">{feed.length}</div>
            <p className="text-xs text-blue-300/70">Live market signals</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-900/20 to-purple-800/20 border-purple-800/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-300">Open Positions</CardTitle>
            <Target className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-400">3</div>
            <p className="text-xs text-purple-300/70">Currently active</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-900/20 to-orange-800/20 border-yellow-800/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-yellow-300">Win Rate</CardTitle>
            <Zap className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">85%</div>
            <p className="text-xs text-yellow-300/70">Last 30 trades</p>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      {marketOverview.indices && (
        <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-700/50 mb-6">
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <TrendingUp className="w-5 h-5 mr-2 text-blue-400" />
              Market Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(marketOverview.indices).map(([index, data]) => (
                <div key={index} className="text-center">
                  <div className="text-xs text-muted-foreground">{index.replace('^', '')}</div>
                  <div className="font-bold">{data.price.toFixed(2)}</div>
                  <div className={`text-sm ${data.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {data.change_pct >= 0 ? '+' : ''}{data.change_pct.toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>
            {marketOverview.vix && (
              <div className="mt-4 pt-4 border-t border-border/50">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">VIX (Fear Index):</span>
                  <span className="font-bold">{marketOverview.vix}</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    marketOverview.market_sentiment === 'bullish' ? 'bg-green-500/20 text-green-400' :
                    marketOverview.market_sentiment === 'bearish' ? 'bg-red-500/20 text-red-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {marketOverview.market_sentiment}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Trading Feed */}
      <Card className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
            Live Trading Feed
            <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">AGENT DATA</span>
          </CardTitle>
          <CardDescription>
            Real-time trading signals from trading agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-muted-foreground">Loading market data...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="text-red-400 mb-4">
                  <Activity className="w-12 h-12 mx-auto mb-2" />
                  <p>Error loading market data</p>
                  <p className="text-sm text-muted-foreground">{error}</p>
                </div>
                <Button 
                  onClick={() => window.location.reload()} 
                  variant="outline" 
                  size="sm"
                >
                  Retry
                </Button>
              </div>
            ) : feed.length > 0 ? (
              feed.map((item, index) => (
                <Card key={index} className="bg-card/50 border-border/50 hover:bg-card/80 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-bold text-lg text-foreground flex items-center">
                          {item.symbol}
                          {item.data_source && (
                            <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 px-1 py-0.5 rounded">
                              {item.data_source.includes('real') ? 'LIVE' : 'DEMO'}
                            </span>
                          )}
                          {item.error && (
                            <span className="ml-2 text-xs bg-red-500/20 text-red-400 px-1 py-0.5 rounded">
                              ERROR
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          ${item.price.toFixed(2)}
                        </div>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                          {item.volume && (
                            <div>
                              <span className="text-muted-foreground">Vol:</span>
                              <span className="ml-1">{(item.volume / 1000000).toFixed(1)}M</span>
                            </div>
                          )}
                          {item.rsi && (
                            <div>
                              <span className="text-muted-foreground">RSI:</span>
                              <span className={`ml-1 ${
                                item.rsi > 70 ? 'text-red-400' : 
                                item.rsi < 30 ? 'text-green-400' : 
                                'text-yellow-400'
                              }`}>
                                {item.rsi.toFixed(1)}
                              </span>
                            </div>
                          )}
                          {item.rotation && (
                            <div>
                              <span className="text-muted-foreground">Rotation:</span>
                              <span className="ml-1">{item.rotation.toFixed(1)}x</span>
                            </div>
                          )}
                          {item.confidence && (
                            <div>
                              <span className="text-muted-foreground">Confidence:</span>
                              <span className="ml-1">{(item.confidence * 100).toFixed(0)}%</span>
                            </div>
                          )}
                        </div>
                        {item.signal_types && item.signal_types.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {item.signal_types.map((signal, i) => (
                              <span key={i} className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
                                {signal}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className={`text-right ${
                        item.up_pct > 0 
                          ? 'text-green-400' 
                          : item.up_pct < 0 
                          ? 'text-red-400' 
                          : 'text-gray-400'
                      }`}>
                        <div className="text-xl font-bold">
                          {item.up_pct > 0 ? '+' : ''}{item.up_pct.toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {item.up_pct > 5 ? 'Strong Bull' : 
                           item.up_pct > 0 ? 'Bullish' : 
                           item.up_pct < -5 ? 'Strong Bear' :
                           item.up_pct < 0 ? 'Bearish' : 'Neutral'}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No trading signals available</p>
                <p className="text-sm text-muted-foreground/70">
                  Agent signals will appear here when available
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
        </div>
      </div>
    </div>
  );

  // Agent control functions
  const controlAgent = async (agent: string, action: string) => {
    try {
      const response = await fetch(`${API_BASE}/agents/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent }),
      });
      
      if (!response.ok) throw new Error(`Failed to ${action} ${agent}`);
      
      // Refresh agent status after action
      const agentResponse = await fetch(`${API_BASE}/agents/status`);
      if (agentResponse.ok) {
        const agentData = await agentResponse.json();
        setAgentStatus(agentData);
      }
      
      logger.info(`${agent} ${action} completed successfully`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `Failed to ${action} ${agent}`;
      setError(errorMessage);
      logger.error(`Agent control error:`, errorMessage);
    }
  };

  const renderAgentsTab = () => (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Fixed header */}
      <div className="flex-shrink-0 p-6 pb-4 border-b border-trading-gray-300">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-trading-gold">Agent Control Center</h2>
            <p className="text-sm text-trading-bronze mt-1">Individual control panels for each autonomous trading agent</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${agentStatus ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-xs text-trading-gold font-medium">
              {agentStatus ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
            </span>
          </div>
        </div>
      </div>
      
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
      <Card className="bg-gradient-to-br from-trading-black to-trading-gray-200 border-trading-gray-300">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <Users className="w-5 h-5 mr-2 text-trading-gold" />
            Agent Control Center
            <span className="ml-2 text-xs bg-trading-gold/20 text-trading-gold px-2 py-1 rounded">
              {agentStatus ? 'LIVE' : 'OFFLINE'}
            </span>
          </CardTitle>
          <CardDescription className="text-trading-bronze">Individual control panels for each autonomous trading agent</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trading-gold"></div>
              <p className="ml-4 text-trading-bronze">Loading agent controls...</p>
            </div>
          ) : !agentStatus ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Unable to connect to agent system</p>
              <p className="text-sm text-muted-foreground/70">Check if backend is running</p>
              <Button 
                onClick={() => window.location.reload()} 
                variant="outline" 
                size="sm"
                className="mt-4"
              >
                Retry Connection
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Dynamic Agent Control Panels */}
              {agentStatus.trading_agents && Object.entries(agentStatus.trading_agents).map(([agentKey, agent]) => {
                const agentConfig = {
                  scanner_agent: { color: 'blue', icon: '🔍', description: 'Market scanning and opportunity detection' },
                  strategy_agent: { color: 'purple', icon: '⚡', description: 'Trading strategy execution and signal generation' },
                  risk_agent: { color: 'orange', icon: '🛡️', description: 'Portfolio protection and risk assessment' },
                  memory_agent: { color: 'green', icon: '🧠', description: 'Knowledge retention and pattern learning' }
                }[agentKey] || { color: 'gray', icon: '🤖', description: 'Agent control panel' };

                const isActive = agent.status === 'active' || agent.status === 'monitoring';
                
                return (
                  <Card key={agentKey} className={`bg-gradient-to-br from-${agentConfig.color}-900/20 to-${agentConfig.color}-800/20 border-${agentConfig.color}-800/50`}>
                    <CardHeader>
                      <CardTitle className={`flex items-center justify-between text-lg text-${agentConfig.color}-300`}>
                        <span>{agentConfig.icon} {agent.name}</span>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 bg-${agentConfig.color}-500 rounded-full ${isActive ? 'animate-pulse' : ''}`}></div>
                          <span className={`text-xs text-${agentConfig.color}-400 uppercase`}>
                            {agent.status}
                          </span>
                        </div>
                      </CardTitle>
                      <CardDescription className="text-sm text-trading-bronze">{agentConfig.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <span className="text-trading-bronze">CPU:</span>
                          <span className={`ml-2 text-${agentConfig.color}-400`}>{agent.cpu}%</span>
                        </div>
                        <div>
                          <span className="text-trading-bronze">Memory:</span>
                          <span className={`ml-2 text-${agentConfig.color}-400`}>{agent.memory}</span>
                        </div>
                        <div>
                          <span className="text-trading-bronze">Uptime:</span>
                          <span className={`ml-2 text-${agentConfig.color}-400`}>{agent.uptime}</span>
                        </div>
                        <div>
                          <span className="text-trading-bronze">Status:</span>
                          <span className={`ml-2 text-${agentConfig.color}-400`}>{agent.status}</span>
                        </div>
                      </div>
                      
                      {/* Agent-specific controls */}
                      {agentKey === 'scanner_agent' && (
                        <div className="space-y-3 pt-3 border-t border-trading-gray-300">
                          <h4 className="text-sm font-semibold text-trading-gold">📊 Scanner Configuration</h4>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Scan Interval (sec)</label>
                              <input 
                                type="number" 
                                defaultValue={30} 
                                min={5} 
                                max={300}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" 
                                title="Time between market scans"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Market Depth</label>
                              <select 
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Order book analysis depth"
                              >
                                <option value="5">Level 1 (Top 5)</option>
                                <option value="10">Level 2 (Top 10)</option>
                                <option value="20">Level 3 (Top 20)</option>
                              </select>
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-xs text-trading-bronze block mb-1">Active Symbols</label>
                            <input 
                              type="text" 
                              defaultValue="BTC,ETH,SOL,MATIC,ADA"
                              className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                              placeholder="Comma-separated symbols"
                              title="Trading symbols to monitor"
                            />
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Min Volume (24h)</label>
                              <input 
                                type="number" 
                                defaultValue={1000000} 
                                min={10000}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Minimum 24h volume filter"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Price Change %</label>
                              <input 
                                type="number" 
                                defaultValue={3} 
                                min={0.1} 
                                max={50} 
                                step={0.1}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Minimum price change to trigger"
                              />
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Volume Analysis</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Price Patterns</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" className="mr-1" />
                              <span className="text-trading-bronze">Bollinger Bands</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">RSI Signals</span>
                            </label>
                          </div>
                        </div>
                      )}
                      
                      {agentKey === 'strategy_agent' && (
                        <div className="space-y-3 pt-3 border-t border-trading-gray-300">
                          <h4 className="text-sm font-semibold text-trading-gold">⚡ Strategy Configuration</h4>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Primary Strategy</label>
                              <select 
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Main trading strategy"
                              >
                                <option>Mean Reversion</option>
                                <option>Momentum</option>
                                <option>Breakout</option>
                                <option>Scalping</option>
                                <option>Grid Trading</option>
                                <option>DCA (Dollar Cost Average)</option>
                              </select>
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Risk Level</label>
                              <select 
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Overall risk tolerance"
                              >
                                <option>Conservative</option>
                                <option>Moderate</option>
                                <option>Aggressive</option>
                                <option>Extreme</option>
                              </select>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Take Profit %</label>
                              <input 
                                type="number" 
                                defaultValue={8} 
                                min={1} 
                                max={100} 
                                step={0.1}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Take profit percentage"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Stop Loss %</label>
                              <input 
                                type="number" 
                                defaultValue={3} 
                                min={0.1} 
                                max={20} 
                                step={0.1}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Stop loss percentage"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Signal Threshold</label>
                              <input 
                                type="number" 
                                defaultValue={0.7} 
                                min={0.1} 
                                max={1} 
                                step={0.05}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Minimum signal confidence"
                              />
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-xs text-trading-bronze block mb-1">Trading Timeframes</label>
                            <div className="flex flex-wrap gap-2">
                              <label className="flex items-center text-xs">
                                <input type="checkbox" className="mr-1" />
                                <span className="text-trading-bronze">1m</span>
                              </label>
                              <label className="flex items-center text-xs">
                                <input type="checkbox" defaultChecked className="mr-1" />
                                <span className="text-trading-bronze">5m</span>
                              </label>
                              <label className="flex items-center text-xs">
                                <input type="checkbox" defaultChecked className="mr-1" />
                                <span className="text-trading-bronze">15m</span>
                              </label>
                              <label className="flex items-center text-xs">
                                <input type="checkbox" defaultChecked className="mr-1" />
                                <span className="text-trading-bronze">1h</span>
                              </label>
                              <label className="flex items-center text-xs">
                                <input type="checkbox" className="mr-1" />
                                <span className="text-trading-bronze">4h</span>
                              </label>
                              <label className="flex items-center text-xs">
                                <input type="checkbox" className="mr-1" />
                                <span className="text-trading-bronze">1d</span>
                              </label>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {agentKey === 'risk_agent' && (
                        <div className="space-y-3 pt-3 border-t border-trading-gray-300">
                          <h4 className="text-sm font-semibold text-trading-gold">🛡️ Risk Management</h4>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Max Position Size (%)</label>
                              <input 
                                type="number" 
                                defaultValue={5} 
                                min={1} 
                                max={25} 
                                step={0.5}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum position size as % of portfolio"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Daily Loss Limit (%)</label>
                              <input 
                                type="number" 
                                defaultValue={2} 
                                min={0.5} 
                                max={10} 
                                step={0.1}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum daily loss percentage"
                              />
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Max Positions</label>
                              <input 
                                type="number" 
                                defaultValue={5} 
                                min={1} 
                                max={20}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum concurrent positions"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Risk Score Max</label>
                              <input 
                                type="number" 
                                defaultValue={7} 
                                min={1} 
                                max={10}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum acceptable risk score"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Correlation Limit</label>
                              <input 
                                type="number" 
                                defaultValue={0.7} 
                                min={0.1} 
                                max={1} 
                                step={0.05}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum asset correlation"
                              />
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Auto Stop Loss</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Portfolio Rebalancing</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" className="mr-1" />
                              <span className="text-trading-bronze">Emergency Exit</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Drawdown Protection</span>
                            </label>
                          </div>
                        </div>
                      )}
                      
                      {agentKey === 'memory_agent' && (
                        <div className="space-y-3 pt-3 border-t border-trading-gray-300">
                          <h4 className="text-sm font-semibold text-trading-gold">🧠 Memory & Learning</h4>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Learning Rate</label>
                              <select 
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Speed of pattern learning"
                              >
                                <option>Fast</option>
                                <option>Normal</option>
                                <option>Slow</option>
                                <option>Conservative</option>
                              </select>
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Memory Retention (days)</label>
                              <input 
                                type="number" 
                                defaultValue={30} 
                                min={7} 
                                max={365}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="How long to keep learned patterns"
                              />
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Pattern Threshold</label>
                              <input 
                                type="number" 
                                defaultValue={0.8} 
                                min={0.1} 
                                max={1} 
                                step={0.05}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Minimum pattern confidence"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Max Patterns</label>
                              <input 
                                type="number" 
                                defaultValue={10000} 
                                min={1000} 
                                max={100000} 
                                step={1000}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Maximum stored patterns"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-trading-bronze block mb-1">Similarity Score</label>
                              <input 
                                type="number" 
                                defaultValue={0.75} 
                                min={0.1} 
                                max={1} 
                                step={0.05}
                                className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded"
                                title="Pattern similarity threshold"
                              />
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Pattern Recognition</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Market Memory</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" className="mr-1" />
                              <span className="text-trading-bronze">Adaptive Learning</span>
                            </label>
                            <label className="flex items-center text-xs">
                              <input type="checkbox" defaultChecked className="mr-1" />
                              <span className="text-trading-bronze">Historical Analysis</span>
                            </label>
                          </div>
                        </div>
                      )}
                      
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => controlAgent(agentKey, 'start')}
                          className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded"
                        >
                          START
                        </button>
                        <button 
                          onClick={() => controlAgent(agentKey, 'stop')}
                          className="flex-1 px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded"
                        >
                          STOP
                        </button>
                        <button 
                          onClick={() => controlAgent(agentKey, 'restart')}
                          className={`flex-1 px-3 py-1 text-xs bg-${agentConfig.color}-600 hover:bg-${agentConfig.color}-500 text-white rounded`}
                        >
                          RESTART
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Global Agent Controls */}
      <Card className="bg-gradient-to-br from-trading-black to-trading-gray-200 border-trading-gray-300">
        <CardHeader>
          <CardTitle className="text-xl text-trading-gold">Global Agent Controls</CardTitle>
          <CardDescription className="text-trading-bronze">Master controls for all agents</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <button 
              onClick={() => controlAgent('all', 'start')}
              className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium"
            >
              START ALL AGENTS
            </button>
            <button 
              onClick={() => controlAgent('all', 'stop')}
              className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium"
            >
              STOP ALL AGENTS
            </button>
            <button 
              onClick={() => controlAgent('all', 'restart')}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium"
            >
              RESTART ALL AGENTS
            </button>
            <button 
              onClick={() => controlAgent('all', 'emergency_stop')}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium"
            >
              EMERGENCY STOP
            </button>
            <button 
              onClick={async () => {
                try {
                  const response = await fetch(`${API_BASE}/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings),
                  });
                  if (response.ok) {
                    logger.info('Configuration saved successfully');
                  }
                } catch (err) {
                  logger.error('Failed to save configuration:', err);
                }
              }}
              className="px-6 py-2 bg-trading-gold hover:bg-trading-gold/80 text-black rounded-lg font-medium"
            >
              SAVE CONFIGURATION
            </button>
          </div>
          
          {/* System Status Display */}
          {agentStatus?.system_status && (
            <div className="mt-6 p-4 bg-trading-gray-400/20 rounded-lg">
              <h4 className="text-sm font-medium text-trading-gold mb-3">System Status</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-trading-bronze">CPU Usage:</span>
                  <span className="ml-2 text-trading-gold">{agentStatus.system_status.cpu_usage}%</span>
                </div>
                <div>
                  <span className="text-trading-bronze">Memory:</span>
                  <span className="ml-2 text-trading-gold">{agentStatus.system_status.memory}</span>
                </div>
                <div>
                  <span className="text-trading-bronze">Connections:</span>
                  <span className="ml-2 text-trading-gold">{agentStatus.system_status.connections}</span>
                </div>
                <div>
                  <span className="text-trading-bronze">Uptime:</span>
                  <span className="ml-2 text-trading-gold">{agentStatus.system_status.uptime}</span>
                </div>
              </div>
              
              {agentStatus.performance && (
                <div className="mt-4 pt-4 border-t border-trading-gray-300/20">
                  <h5 className="text-xs font-medium text-trading-gold mb-2">Performance Metrics</h5>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                    <div>
                      <span className="text-trading-bronze">Signals/Hour:</span>
                      <span className="ml-2 text-green-400">{agentStatus.performance.signals_per_hour}</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Accuracy:</span>
                      <span className="ml-2 text-green-400">{agentStatus.performance.accuracy}%</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Latency:</span>
                      <span className="ml-2 text-yellow-400">{agentStatus.performance.latency}ms</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Queue:</span>
                      <span className="ml-2 text-blue-400">{agentStatus.performance.queue}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-trading-black text-trading-gold">
      {/* Header */}
      <header className="border-b border-trading-gray-300 bg-trading-gray-100/50 backdrop-blur-sm">
        <div className="flex items-center justify-between p-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-trading-gold via-trading-red to-trading-bronze bg-clip-text text-transparent">
            Gremlin ShadTail Trader
          </h1>
          <div className="text-sm text-trading-bronze">
            AI-Powered Trading Platform
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabType)} className="flex-1 flex flex-col">
        <div className="border-b border-trading-gray-300 bg-trading-gray-200/30">
          <TabsList className="grid w-full grid-cols-5 bg-transparent p-1">
            <TabsTrigger 
              value="trading" 
              className="flex items-center space-x-2 data-[state=active]:bg-trading-gold/20 data-[state=active]:text-trading-gold text-trading-bronze hover:text-trading-gold"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Trading</span>
            </TabsTrigger>
            <TabsTrigger 
              value="chat" 
              className="flex items-center space-x-2 data-[state=active]:bg-trading-gold/20 data-[state=active]:text-trading-gold text-trading-bronze hover:text-trading-gold"
            >
              <MessageCircle className="w-4 h-4" />
              <span>Grok Chat</span>
            </TabsTrigger>
            <TabsTrigger 
              value="source" 
              className="flex items-center space-x-2 data-[state=active]:bg-trading-gold/20 data-[state=active]:text-trading-gold text-trading-bronze hover:text-trading-gold"
            >
              <Code className="w-4 h-4" />
              <span>Source</span>
            </TabsTrigger>
            <TabsTrigger 
              value="agents" 
              className="flex items-center space-x-2 data-[state=active]:bg-trading-gold/20 data-[state=active]:text-trading-gold text-trading-bronze hover:text-trading-gold"
            >
              <Users className="w-4 h-4" />
              <span>Agents</span>
            </TabsTrigger>
            <TabsTrigger 
              value="settings" 
              className="flex items-center space-x-2 data-[state=active]:bg-trading-gold/20 data-[state=active]:text-trading-gold text-trading-bronze hover:text-trading-gold"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          <TabsContent value="trading" className="h-full m-0 overflow-y-auto">
            {renderTradingTab()}
          </TabsContent>
          
          <TabsContent value="chat" className="h-full m-0">
            <GrokChat apiBaseUrl="http://localhost:8000" />
          </TabsContent>
          
          <TabsContent value="source" className="h-full m-0">
            {isClient ? (
              <Suspense fallback={
                <div className="flex items-center justify-center h-full">
                  <div className="text-gray-400">Loading Monaco Editor...</div>
                </div>
              }>
                <MonacoEditor theme="vs-dark" />
              </Suspense>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-gray-400">Initializing Editor...</div>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="agents" className="h-full m-0">
            {renderAgentsTab()}
          </TabsContent>
          
          <TabsContent value="settings" className="h-full m-0">
            <SettingsComponent 
              settings={settings} 
              onUpdateSettings={updateSettings} 
            />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};

export default Dashboard;