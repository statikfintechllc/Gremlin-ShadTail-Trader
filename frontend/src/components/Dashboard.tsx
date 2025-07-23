import React, { useState, useEffect } from 'react';
import { logger } from '../utils/logger';

interface FeedItem {
  symbol: string;
  price: number;
  up_pct: number;
}

interface Settings {
  scanInterval: number;
  symbols: string[];
}

const Dashboard: React.FC = () => {
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
    
    // Set up auto-refresh
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Gremlin ShadTail Trader
        </h1>
        <p className="text-center text-gray-400 mt-2">
          AI-Powered Trading Dashboard
        </p>
      </header>

      {error && (
        <div className="bg-red-600 text-white p-4 rounded-lg mb-6">
          <p className="font-semibold">Error:</p>
          <p>{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Trading Feed */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Trading Feed</h2>
          <div className="space-y-3">
            {feed.length > 0 ? (
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

        {/* Settings Panel */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Settings</h2>
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
      </div>

      <footer className="mt-12 text-center text-gray-500">
        <p>© 2025 Gremlin ShadTail Trader - Powered by FastAPI, Astro, and React</p>
      </footer>
    </div>
  );
};

export default Dashboard;