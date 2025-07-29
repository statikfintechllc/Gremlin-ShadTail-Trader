import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import GrokChat from './GrokChat';
import SourceEditor from './SourceEditor';
import SettingsComponent from './Settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import { MessageCircle, Code, TrendingUp, Settings, Users, BarChart3, Activity, DollarSign, Zap, Target, Database, TestTube } from 'lucide-react';

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

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('trading');
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [marketOverview, setMarketOverview] = useState<MarketOverview>({});
  const [settings, setSettings] = useState<Settings>({ scanInterval: 300, symbols: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useRealData, setUseRealData] = useState(true);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Choose between real and demo data
        const feedEndpoint = useRealData ? `${API_BASE}/feed/real` : `${API_BASE}/feed`;
        
        // Fetch feed data
        const feedResponse = await fetch(feedEndpoint);
        if (!feedResponse.ok) throw new Error('Failed to fetch feed');
        const feedData = await feedResponse.json();
        setFeed(feedData);
        
        // Fetch market overview (only for real data mode)
        if (useRealData) {
          try {
            const overviewResponse = await fetch(`${API_BASE}/market/overview`);
            if (overviewResponse.ok) {
              const overviewData = await overviewResponse.json();
              setMarketOverview(overviewData);
            }
          } catch (overviewError) {
            logger.warn('Market overview failed to load:', overviewError);
          }
        }
        
        // Fetch settings
        const settingsResponse = await fetch(`${API_BASE}/settings`);
        if (!settingsResponse.ok) throw new Error('Failed to fetch settings');
        const settingsData = await settingsResponse.json();
        setSettings(settingsData);
        
        logger.info(`Dashboard data loaded successfully (${useRealData ? 'REAL' : 'DEMO'} data mode)`);
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
  }, [settings.scanInterval, useRealData]);

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
    <div className="h-full p-6 space-y-6">
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

      {/* Data Mode Toggle */}
      <div className="flex items-center space-x-2 mb-4">
        <TestTube className="w-4 h-4" />
        <span className="text-sm">Demo Mode</span>
        <Switch
          checked={useRealData}
          onCheckedChange={setUseRealData}
        />
        <span className="text-sm">Real Data</span>
        <Database className="w-4 h-4" />
        {useRealData && (
          <span className="text-xs text-green-400 ml-2">● Live Market Data</span>
        )}
      </div>

      {/* Market Overview (Real Data Only) */}
      {useRealData && marketOverview.indices && (
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
            {useRealData && <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">REAL DATA</span>}
          </CardTitle>
          <CardDescription>
            {useRealData ? 'Real-time market signals from yfinance' : 'Demo trading signals for testing'}
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
                        {useRealData && (
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
                        )}
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
                  {useRealData ? 'Real market data will appear here when available' : 'Demo signals will appear here'}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderAgentsTab = () => (
    <div className="h-full p-6 space-y-6">
      <Card className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <Users className="w-5 h-5 mr-2 text-purple-400" />
            Agent Control Center
          </CardTitle>
          <CardDescription>Monitor and control autonomous trading agents</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-gradient-to-br from-green-900/20 to-green-800/20 border-green-800/50">
              <CardHeader>
                <CardTitle className="text-lg text-green-300">Trading Agents</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Scanner Agent</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-xs text-green-400">Active</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Strategy Agent</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-xs text-green-400">Active</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Risk Agent</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span className="text-xs text-yellow-400">Monitoring</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-900/20 to-blue-800/20 border-blue-800/50">
              <CardHeader>
                <CardTitle className="text-lg text-blue-300">System Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-sm text-blue-400">45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Memory</span>
                  <span className="text-sm text-blue-400">2.1GB / 4GB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Connections</span>
                  <span className="text-sm text-blue-400">3 Active</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Uptime</span>
                  <span className="text-sm text-blue-400">2h 15m</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-900/20 to-purple-800/20 border-purple-800/50">
              <CardHeader>
                <CardTitle className="text-lg text-purple-300">Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Signals/Hour</span>
                  <span className="text-sm text-purple-400">142</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Accuracy</span>
                  <span className="text-sm text-purple-400">87.3%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Latency</span>
                  <span className="text-sm text-purple-400">12ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Queue</span>
                  <span className="text-sm text-purple-400">0 pending</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center justify-between p-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-blue-600 bg-clip-text text-transparent">
            Gremlin ShadTail Trader
          </h1>
          <div className="text-sm text-muted-foreground">
            AI-Powered Trading Platform
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabType)} className="flex-1 flex flex-col">
        <div className="border-b border-border bg-card/30">
          <TabsList className="grid w-full grid-cols-5 bg-transparent p-1">
            <TabsTrigger 
              value="trading" 
              className="flex items-center space-x-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Trading</span>
            </TabsTrigger>
            <TabsTrigger 
              value="chat" 
              className="flex items-center space-x-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            >
              <MessageCircle className="w-4 h-4" />
              <span>Grok Chat</span>
            </TabsTrigger>
            <TabsTrigger 
              value="source" 
              className="flex items-center space-x-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            >
              <Code className="w-4 h-4" />
              <span>Source</span>
            </TabsTrigger>
            <TabsTrigger 
              value="agents" 
              className="flex items-center space-x-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            >
              <Users className="w-4 h-4" />
              <span>Agents</span>
            </TabsTrigger>
            <TabsTrigger 
              value="settings" 
              className="flex items-center space-x-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          <TabsContent value="trading" className="h-full m-0">
            {renderTradingTab()}
          </TabsContent>
          
          <TabsContent value="chat" className="h-full m-0">
            <GrokChat apiBaseUrl="http://localhost:8000" />
          </TabsContent>
          
          <TabsContent value="source" className="h-full m-0">
            <SourceEditor apiBaseUrl="http://localhost:8000" />
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