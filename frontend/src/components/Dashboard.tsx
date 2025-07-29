import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import GrokChat from './GrokChat';
import SourceEditor from './SourceEditor';
import SettingsComponent from './Settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { MessageCircle, Code, TrendingUp, Settings, Users, BarChart3, Activity, DollarSign, Zap, Target } from 'lucide-react';

interface AgentStatus {
  status: string;
  active_agents: string[];
  system_stats: {
    cpu_usage: number;
    memory_usage: string;
    connections: number;
    uptime: string;
  };
  performance: {
    signals_per_hour: number;
    accuracy: number;
    latency: string;
    queue_size: number;
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

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('trading');
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [marketOverview, setMarketOverview] = useState<MarketOverview>({});
  const [settings, setSettings] = useState<Settings>({ scanInterval: 300, symbols: [] });
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
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
  );

  const renderAgentsTab = () => (
    <div className="h-full p-6 space-y-6">
      <Card className="bg-gradient-to-br from-trading-black to-trading-gray-200 border-trading-gray-300">
        <CardHeader>
          <CardTitle className="flex items-center text-xl">
            <Users className="w-5 h-5 mr-2 text-trading-gold" />
            Agent Control Center
            <span className="ml-2 text-xs bg-trading-gold/20 text-trading-gold px-2 py-1 rounded">LIVE</span>
          </CardTitle>
          <CardDescription className="text-trading-bronze">Individual control panels for each autonomous trading agent</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-trading-gold"></div>
              <p className="ml-4 text-trading-bronze">Loading agent controls...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Scanner Agent Control Panel */}
              <Card className="bg-gradient-to-br from-blue-900/20 to-blue-800/20 border-blue-800/50">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg text-blue-300">
                    <span>Scanner Agent</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-blue-400">ACTIVE</span>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-sm text-trading-bronze">Market scanning and opportunity detection</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-trading-bronze">CPU:</span>
                      <span className="ml-2 text-blue-400">12.5%</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Memory:</span>
                      <span className="ml-2 text-blue-400">180MB</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Uptime:</span>
                      <span className="ml-2 text-blue-400">2h 15m</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Scans:</span>
                      <span className="ml-2 text-blue-400">1,247</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Scan Interval (seconds):</label>
                    <input type="number" defaultValue={30} className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Min Volume Filter:</label>
                    <input type="number" defaultValue={100000} className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" />
                  </div>
                  <div className="flex space-x-2">
                    <button className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded">START</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded">STOP</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded">RESTART</button>
                  </div>
                </CardContent>
              </Card>

              {/* Strategy Agent Control Panel */}
              <Card className="bg-gradient-to-br from-purple-900/20 to-purple-800/20 border-purple-800/50">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg text-purple-300">
                    <span>Strategy Agent</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-purple-400">ACTIVE</span>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-sm text-trading-bronze">Trading strategy execution and signal generation</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-trading-bronze">CPU:</span>
                      <span className="ml-2 text-purple-400">8.3%</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Memory:</span>
                      <span className="ml-2 text-purple-400">95MB</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Signals:</span>
                      <span className="ml-2 text-purple-400">342</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Accuracy:</span>
                      <span className="ml-2 text-purple-400">87.2%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Active Strategy:</label>
                    <select className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded">
                      <option>Mean Reversion</option>
                      <option>Momentum</option>
                      <option>Breakout</option>
                      <option>Scalping</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Risk Level:</label>
                    <select className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded">
                      <option>Conservative</option>
                      <option>Moderate</option>
                      <option>Aggressive</option>
                    </select>
                  </div>
                  <div className="flex space-x-2">
                    <button className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded">START</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded">STOP</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-purple-600 hover:bg-purple-500 text-white rounded">OPTIMIZE</button>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Management Agent Control Panel */}
              <Card className="bg-gradient-to-br from-orange-900/20 to-orange-800/20 border-orange-800/50">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg text-orange-300">
                    <span>Risk Management Agent</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-orange-400">MONITORING</span>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-sm text-trading-bronze">Portfolio protection and risk assessment</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-trading-bronze">CPU:</span>
                      <span className="ml-2 text-orange-400">5.1%</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Memory:</span>
                      <span className="ml-2 text-orange-400">45MB</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Risk Score:</span>
                      <span className="ml-2 text-orange-400">3.2/10</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Alerts:</span>
                      <span className="ml-2 text-orange-400">7</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Max Position Size (%):</label>
                    <input type="number" defaultValue={5} max={25} className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Stop Loss (%):</label>
                    <input type="number" defaultValue={2} max={10} step={0.1} className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" />
                  </div>
                  <div className="flex space-x-2">
                    <button className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded">ENABLE</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded">DISABLE</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-orange-600 hover:bg-orange-500 text-white rounded">CONFIG</button>
                  </div>
                </CardContent>
              </Card>

              {/* Memory Agent Control Panel */}
              <Card className="bg-gradient-to-br from-green-900/20 to-green-800/20 border-green-800/50">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg text-green-300">
                    <span>Memory Agent</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400">ACTIVE</span>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-sm text-trading-bronze">Knowledge retention and pattern learning</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-trading-bronze">CPU:</span>
                      <span className="ml-2 text-green-400">15.2%</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Memory:</span>
                      <span className="ml-2 text-green-400">210MB</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">Patterns:</span>
                      <span className="ml-2 text-green-400">8,943</span>
                    </div>
                    <div>
                      <span className="text-trading-bronze">DB Size:</span>
                      <span className="ml-2 text-green-400">2.3GB</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Learning Rate:</label>
                    <select className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded">
                      <option>Fast</option>
                      <option>Normal</option>
                      <option>Slow</option>
                      <option>Conservative</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-trading-bronze">Memory Retention (days):</label>
                    <input type="number" defaultValue={30} min={7} max={365} className="w-full px-2 py-1 text-xs bg-trading-gray-400 border border-trading-gray-300 rounded" />
                  </div>
                  <div className="flex space-x-2">
                    <button className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded">START</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded">CLEAR</button>
                    <button className="flex-1 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded">BACKUP</button>
                  </div>
                </CardContent>
              </Card>
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
            <button className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium">
              START ALL AGENTS
            </button>
            <button className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium">
              STOP ALL AGENTS
            </button>
            <button className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium">
              RESTART ALL AGENTS
            </button>
            <button className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium">
              EMERGENCY STOP
            </button>
            <button className="px-6 py-2 bg-trading-gold hover:bg-trading-gold/80 text-black rounded-lg font-medium">
              SAVE CONFIGURATION
            </button>
          </div>
        </CardContent>
      </Card>
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