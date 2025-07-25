import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';
import GrokChat from './GrokChat';
import SourceEditor from './SourceEditor';
import { MessageCircle, Code, TrendingUp, Settings, Users, BarChart3 } from 'lucide-react';

interface FeedItem {
  symbol: string;
  price: number;
  up_pct: number;
}

interface Settings {
  scanInterval: number;
  symbols: string[];
}

type TabType = 'trading' | 'chat' | 'source' | 'agents' | 'settings';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('trading');
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [settings, setSettings] = useState<Settings>({ scanInterval: 300, symbols: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch feed data
        const feedResponse = await fetch(`${API_BASE}/feed`);
        if (!feedResponse.ok) throw new Error('Failed to fetch feed');
        const feedData = await feedResponse.json();
        setFeed(feedData);
        
        // Fetch settings
        const settingsResponse = await fetch(`${API_BASE}/settings`);
        if (!settingsResponse.ok) throw new Error('Failed to fetch settings');
        const settingsData = await settingsResponse.json();
        setSettings(settingsData);
        
        logger.info('Dashboard data loaded successfully');
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        logger.error('Failed to load dashboard data:', errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up auto-refresh for trading tab
    if (activeTab === 'trading') {
      const interval = setInterval(fetchData, settings.scanInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [settings.scanInterval, activeTab]);

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

  const tabs = [
    { id: 'trading' as TabType, label: 'Trading', icon: TrendingUp },
    { id: 'chat' as TabType, label: 'Grok Chat', icon: MessageCircle },
    { id: 'source' as TabType, label: 'Source', icon: Code },
    { id: 'agents' as TabType, label: 'Agents', icon: Users },
    { id: 'settings' as TabType, label: 'Settings', icon: Settings },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'chat':
        return <GrokChat apiBaseUrl="http://localhost:8000" />;
      
      case 'source':
        return <SourceEditor apiBaseUrl="http://localhost:8000" />;
      
      case 'agents':
        return (
          <div className="h-full bg-gray-900 text-white p-6">
            <h2 className="text-2xl font-semibold mb-4">Agent Control</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">Trading Agents</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span>Scanner Agent</span>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Strategy Agent</span>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Risk Agent</span>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">System Status</h3>
                <div className="space-y-2 text-sm">
                  <div>CPU: 45%</div>
                  <div>Memory: 2.1GB / 4GB</div>
                  <div>Active Connections: 3</div>
                </div>
              </div>
            </div>
          </div>
        );
      
      case 'settings':
        return (
          <div className="h-full bg-gray-900 text-white p-6">
            <h2 className="text-2xl font-semibold mb-6">System Settings</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                      onChange={(e) => updateSettings({ scanInterval: parseInt(e.target.value) })}
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
                      onChange={(e) => updateSettings({ 
                        symbols: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                      })}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      placeholder="GPRO, IXHL, AAPL"
                    />
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Plugin Settings</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Grok Chat Plugin</span>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Source Editor Plugin</span>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Tailscale Integration</span>
                    <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      
      default: // trading
        return (
          <div className="h-full bg-gray-900 text-white p-6">
            {error && (
              <div className="bg-red-600 text-white p-4 rounded-lg mb-6">
                <p className="font-semibold">Error:</p>
                <p>{error}</p>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Trading Feed */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-2xl font-semibold mb-4 flex items-center">
                  <BarChart3 className="w-6 h-6 mr-2" />
                  Trading Feed
                </h2>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {loading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                      <p className="mt-2 text-gray-400">Loading...</p>
                    </div>
                  ) : feed.length > 0 ? (
                    feed.map((item, index) => (
                      <div key={index} className="bg-gray-700 rounded p-4 flex justify-between items-center">
                        <div>
                          <span className="font-bold text-lg">{item.symbol}</span>
                          <div className="text-sm text-gray-400">
                            Price: ${item.price.toFixed(2)}
                          </div>
                        </div>
                        <div className={`text-right ${item.up_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          <div className="text-xl font-bold">
                            {item.up_pct > 0 ? '+' : ''}{item.up_pct.toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-400 text-center py-8">
                      No trading data available
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h2 className="text-2xl font-semibold mb-4">Market Overview</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <div className="text-2xl font-bold text-green-400">+12.5%</div>
                    <div className="text-sm text-gray-400">Portfolio</div>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <div className="text-2xl font-bold text-blue-400">{feed.length}</div>
                    <div className="text-sm text-gray-400">Active Signals</div>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <div className="text-2xl font-bold text-yellow-400">3</div>
                    <div className="text-sm text-gray-400">Open Positions</div>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <div className="text-2xl font-bold text-purple-400">85%</div>
                    <div className="text-sm text-gray-400">Win Rate</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Gremlin ShadTail Trader
          </h1>
          <div className="text-sm text-gray-400">
            AI-Powered Trading Platform
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="flex space-x-0">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 bg-gray-700 text-white'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Tab Content */}
      <main className="flex-1 overflow-hidden">
        {renderTabContent()}
      </main>
    </div>
  );
};

export default Dashboard;