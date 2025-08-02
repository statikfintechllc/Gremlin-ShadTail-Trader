import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Alert, AlertDescription } from './ui/alert';
import {
  Activity,
  Brain,
  TrendingUp,
  Clock,
  Settings,
  Play,
  Pause,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  BarChart3,
  Zap,
  Target,
  Shield,
  Eye,
  Cpu,
  Database,
  DollarSign,
  Search,
  Cog,
  Users,
  BookOpen,
  Timer,
  LineChart,
  PieChart,
  Calendar,
  Network,
  Bot,
  ChevronUp,
  ChevronDown,
  Calculator
} from 'lucide-react';

// Agent configuration with detailed metadata
const AGENT_CONFIGS = {
  memory_agent: {
    name: 'Memory Agent',
    icon: Brain,
    color: 'purple',
    category: 'Core',
    description: 'Manages pattern recognition, historical data analysis, and learning algorithms',
    status: 'active',
    controls: {
      learningRate: { type: 'slider', min: 0.01, max: 1.0, default: 0.1 },
      memoryRetention: { type: 'number', min: 7, max: 365, default: 30 },
      patternThreshold: { type: 'slider', min: 0.1, max: 1.0, default: 0.8 },
      maxPatterns: { type: 'number', min: 1000, max: 100000, default: 10000 }
    }
  },
  timing_agent: {
    name: 'Market Timing Agent',
    icon: Clock,
    color: 'blue',
    category: 'Analysis',
    description: 'Optimizes entry and exit timing based on market conditions and volatility',
    status: 'active',
    controls: {
      timeframes: { type: 'multiselect', options: ['1m', '5m', '15m', '1h', '4h', '1d'], default: ['5m', '15m', '1h'] },
      volatilityThreshold: { type: 'slider', min: 0.1, max: 5.0, default: 2.0 },
      lookbackPeriod: { type: 'number', min: 5, max: 100, default: 20 },
      timingConfidence: { type: 'slider', min: 0.5, max: 1.0, default: 0.75 }
    }
  },
  strategy_agent: {
    name: 'Strategy Agent',
    icon: TrendingUp,
    color: 'green',
    category: 'Trading',
    description: 'Executes trading strategies and generates buy/sell signals',
    status: 'active',
    controls: {
      primaryStrategy: { type: 'select', options: ['mean_reversion', 'momentum', 'breakout', 'scalping'], default: 'momentum' },
      riskLevel: { type: 'select', options: ['conservative', 'moderate', 'aggressive'], default: 'moderate' },
      takeProfitPercent: { type: 'slider', min: 1, max: 50, default: 8 },
      stopLossPercent: { type: 'slider', min: 0.5, max: 20, default: 3 }
    }
  },
  signal_generator: {
    name: 'Signal Generator',
    icon: Zap,
    color: 'yellow',
    category: 'Trading',
    description: 'Generates trading signals based on technical analysis and market patterns',
    status: 'active',
    controls: {
      signalStrength: { type: 'slider', min: 0.1, max: 1.0, default: 0.7 },
      technicalIndicators: { type: 'multiselect', options: ['RSI', 'MACD', 'Bollinger', 'SMA', 'EMA'], default: ['RSI', 'MACD'] },
      signalFrequency: { type: 'select', options: ['high', 'medium', 'low'], default: 'medium' },
      confirmationRequired: { type: 'boolean', default: true }
    }
  },
  rule_set_agent: {
    name: 'Rule Set Agent',
    icon: Shield,
    color: 'orange',
    category: 'Risk',
    description: 'Enforces trading rules and risk management protocols',
    status: 'active',
    controls: {
      maxPositions: { type: 'number', min: 1, max: 20, default: 5 },
      maxPositionSize: { type: 'slider', min: 1, max: 25, default: 5 },
      dailyLossLimit: { type: 'slider', min: 0.5, max: 10, default: 2 },
      emergencyStop: { type: 'boolean', default: true }
    }
  },
  rules_engine: {
    name: 'Rules Engine',
    icon: Cog,
    color: 'red',
    category: 'Risk',
    description: 'Processes and validates trading rules in real-time',
    status: 'active',
    controls: {
      ruleValidation: { type: 'select', options: ['strict', 'moderate', 'flexible'], default: 'strict' },
      ruleOverride: { type: 'boolean', default: false },
      customRules: { type: 'textarea', default: '' },
      alertLevel: { type: 'select', options: ['critical', 'warning', 'info'], default: 'warning' }
    }
  },
  runtime_agent: {
    name: 'Runtime Agent',
    icon: Cpu,
    color: 'cyan',
    category: 'System',
    description: 'Monitors system performance and resource utilization',
    status: 'active',
    controls: {
      cpuThreshold: { type: 'slider', min: 50, max: 95, default: 80 },
      memoryThreshold: { type: 'slider', min: 50, max: 95, default: 85 },
      logLevel: { type: 'select', options: ['debug', 'info', 'warning', 'error'], default: 'info' },
      autoRestart: { type: 'boolean', default: true }
    }
  },
  stock_scraper: {
    name: 'Stock Scraper',
    icon: Search,
    color: 'indigo',
    category: 'Data',
    description: 'Scrapes and processes real-time market data from multiple sources',
    status: 'active',
    controls: {
      dataSources: { type: 'multiselect', options: ['yahoo', 'alpha_vantage', 'polygon', 'finnhub'], default: ['yahoo'] },
      scrapeInterval: { type: 'number', min: 5, max: 300, default: 30 },
      symbols: { type: 'textarea', default: 'BTC,ETH,SOL,MATIC,ADA' },
      dataQuality: { type: 'select', options: ['high', 'medium', 'low'], default: 'high' }
    }
  },
  market_data_service: {
    name: 'Market Data Service',
    icon: Database,
    color: 'emerald',
    category: 'Data',
    description: 'Manages real-time market data feeds and historical data storage',
    status: 'active',
    controls: {
      dataProvider: { type: 'select', options: ['live', 'delayed', 'historical'], default: 'live' },
      cacheSize: { type: 'number', min: 100, max: 10000, default: 1000 },
      updateFrequency: { type: 'number', min: 100, max: 5000, default: 1000 },
      dataValidation: { type: 'boolean', default: true }
    }
  },
  simple_market_service: {
    name: 'Simple Market Service',
    icon: BarChart3,
    color: 'teal',
    category: 'Data',
    description: 'Provides simplified market data for testing and development',
    status: 'active',
    controls: {
      simulationMode: { type: 'boolean', default: true },
      dataDelay: { type: 'number', min: 0, max: 60, default: 15 },
      priceVariance: { type: 'slider', min: 0.01, max: 0.1, default: 0.02 },
      volumeMultiplier: { type: 'slider', min: 0.5, max: 2.0, default: 1.0 }
    }
  },
  portfolio_tracker: {
    name: 'Portfolio Tracker',
    icon: PieChart,
    color: 'pink',
    category: 'Monitoring',
    description: 'Tracks portfolio performance, positions, and P&L in real-time',
    status: 'active',
    controls: {
      trackingPrecision: { type: 'select', options: ['high', 'medium', 'low'], default: 'high' },
      updateInterval: { type: 'number', min: 1, max: 60, default: 5 },
      includeUnrealized: { type: 'boolean', default: true },
      rebalanceAlert: { type: 'boolean', default: true }
    }
  },
  tool_control_agent: {
    name: 'Tool Control Agent',
    icon: Settings,
    color: 'slate',
    category: 'System',
    description: 'Manages and coordinates all trading tools and external integrations',
    status: 'active',
    controls: {
      toolTimeout: { type: 'number', min: 5, max: 300, default: 30 },
      maxConcurrentTools: { type: 'number', min: 1, max: 10, default: 3 },
      errorRetries: { type: 'number', min: 0, max: 5, default: 2 },
      healthCheckInterval: { type: 'number', min: 10, max: 300, default: 60 }
    }
  },
  tax_estimator: {
    name: 'Tax Estimator',
    icon: Calculator,
    color: 'amber',
    category: 'Financial',
    description: 'Calculates tax implications and optimizes tax-efficient trading strategies',
    status: 'active',
    controls: {
      taxStrategy: { type: 'select', options: ['minimize', 'defer', 'optimize'], default: 'optimize' },
      holdingPeriod: { type: 'number', min: 1, max: 365, default: 365 },
      washSaleRules: { type: 'boolean', default: true },
      taxBracket: { type: 'select', options: ['low', 'medium', 'high'], default: 'medium' }
    }
  },
  ibkr_trader: {
    name: 'IBKR API Trader',
    icon: Network,
    color: 'violet',
    category: 'Execution',
    description: 'Executes trades through Interactive Brokers API',
    status: 'inactive',
    controls: {
      paperTrading: { type: 'boolean', default: true },
      orderType: { type: 'select', options: ['market', 'limit', 'stop'], default: 'limit' },
      maxOrderSize: { type: 'number', min: 1, max: 10000, default: 100 },
      connectionTimeout: { type: 'number', min: 5, max: 60, default: 30 }
    }
  },
  kalshi_trader: {
    name: 'Kalshi API Trader',
    icon: Bot,
    color: 'rose',
    category: 'Execution',
    description: 'Executes prediction market trades through Kalshi API',
    status: 'inactive',
    controls: {
      maxRisk: { type: 'slider', min: 1, max: 100, default: 10 },
      marketTypes: { type: 'multiselect', options: ['politics', 'economics', 'weather', 'sports'], default: ['economics'] },
      autoExecute: { type: 'boolean', default: false },
      confidenceThreshold: { type: 'slider', min: 0.6, max: 0.95, default: 0.8 }
    }
  }
};

interface AgentStatus {
  name: string;
  status: 'active' | 'inactive' | 'error' | 'starting' | 'stopping';
  uptime: number;
  cpu: number;
  memory: string;
  lastActivity: string;
  performance: {
    successRate: number;
    totalActions: number;
    avgResponseTime: number;
  };
  health: {
    score: number;
    issues: string[];
  };
}

interface AgentControlPanelProps {
  agentKey: string;
  config: typeof AGENT_CONFIGS[keyof typeof AGENT_CONFIGS];
  status: AgentStatus;
  onAction: (agent: string, action: string, params?: any) => Promise<void>;
}

const AgentControlPanel: React.FC<AgentControlPanelProps> = ({ agentKey, config, status, onAction }) => {
  const [settings, setSettings] = useState<any>({});
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'secondary';
      case 'error': return 'destructive';
      case 'starting': return 'warning';
      case 'stopping': return 'warning';
      default: return 'secondary';
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const handleAction = async (action: string) => {
    setIsLoading(true);
    try {
      await onAction(agentKey, action, settings);
    } finally {
      setIsLoading(false);
    }
  };

  const renderControl = (controlKey: string, controlConfig: any) => {
    const value = settings[controlKey] ?? controlConfig.default;

    switch (controlConfig.type) {
      case 'slider':
        return (
          <div key={controlKey} className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min={controlConfig.min}
                max={controlConfig.max}
                step={controlConfig.step || 0.01}
                value={value}
                onChange={(e) => setSettings(prev => ({ ...prev, [controlKey]: parseFloat(e.target.value) }))}
                className="flex-1"
              />
              <span className="text-xs text-muted-foreground w-16">{value}</span>
            </div>
          </div>
        );

      case 'number':
        return (
          <div key={controlKey} className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
            <input
              type="number"
              min={controlConfig.min}
              max={controlConfig.max}
              value={value}
              onChange={(e) => setSettings(prev => ({ ...prev, [controlKey]: parseInt(e.target.value) }))}
              className="w-full px-2 py-1 text-xs bg-background border border-input rounded"
            />
          </div>
        );

      case 'select':
        return (
          <div key={controlKey} className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
            <select
              value={value}
              onChange={(e) => setSettings(prev => ({ ...prev, [controlKey]: e.target.value }))}
              className="w-full px-2 py-1 text-xs bg-background border border-input rounded"
            >
              {controlConfig.options.map((option: string) => (
                <option key={option} value={option}>{option.replace(/_/g, ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>
        );

      case 'boolean':
        return (
          <div key={controlKey} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => setSettings(prev => ({ ...prev, [controlKey]: e.target.checked }))}
              className="rounded"
            />
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
          </div>
        );

      case 'textarea':
        return (
          <div key={controlKey} className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
            <textarea
              value={value}
              onChange={(e) => setSettings(prev => ({ ...prev, [controlKey]: e.target.value }))}
              className="w-full px-2 py-1 text-xs bg-background border border-input rounded"
              rows={3}
            />
          </div>
        );

      case 'multiselect':
        return (
          <div key={controlKey} className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              {controlKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </label>
            <div className="flex flex-wrap gap-1">
              {controlConfig.options.map((option: string) => {
                const isSelected = Array.isArray(value) ? value.includes(option) : false;
                return (
                  <button
                    key={option}
                    onClick={() => {
                      const currentValue = Array.isArray(value) ? value : [];
                      const newValue = isSelected 
                        ? currentValue.filter(v => v !== option)
                        : [...currentValue, option];
                      setSettings(prev => ({ ...prev, [controlKey]: newValue }));
                    }}
                    className={`px-2 py-1 text-xs rounded border ${
                      isSelected 
                        ? 'bg-primary text-primary-foreground border-primary' 
                        : 'bg-background border-input hover:bg-accent'
                    }`}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const IconComponent = config.icon;

  return (
    <Card className={`bg-gradient-to-br from-${config.color}-900/20 to-${config.color}-800/20 border-${config.color}-800/50`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-${config.color}-500/20`}>
              <IconComponent className={`w-5 h-5 text-${config.color}-400`} />
            </div>
            <div>
              <CardTitle className="text-base font-medium">{config.name}</CardTitle>
              <CardDescription className="text-xs">{config.category}</CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={getStatusColor(status.status) as any}>
              {status.status.toUpperCase()}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground mb-4">{config.description}</p>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Uptime:</span>
            <span>{Math.floor(status.uptime / 3600)}h {Math.floor((status.uptime % 3600) / 60)}m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">CPU:</span>
            <span>{status.cpu}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Memory:</span>
            <span>{status.memory}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Health:</span>
            <span className={getHealthColor(status.health.score)}>{status.health.score}%</span>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Success Rate</span>
            <span>{status.performance.successRate}%</span>
          </div>
          <Progress value={status.performance.successRate} className="h-1" />
        </div>

        {/* Health Issues */}
        {status.health.issues.length > 0 && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription className="text-xs">
              {status.health.issues.join(', ')}
            </AlertDescription>
          </Alert>
        )}

        {/* Control Buttons */}
        <div className="flex space-x-2 mb-4">
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleAction('start')}
            disabled={status.status === 'active' || isLoading}
            className="flex-1"
          >
            <Play className="w-3 h-3 mr-1" />
            Start
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleAction('stop')}
            disabled={status.status === 'inactive' || isLoading}
            className="flex-1"
          >
            <Pause className="w-3 h-3 mr-1" />
            Stop
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleAction('restart')}
            disabled={isLoading}
            className="flex-1"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Restart
          </Button>
        </div>

        {/* Expanded Configuration */}
        {isExpanded && (
          <div className="border-t border-border pt-4 space-y-4">
            <h4 className="text-sm font-medium">Configuration</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(config.controls || {}).map(([key, controlConfig]) =>
                renderControl(key, controlConfig)
              )}
            </div>
            <div className="flex justify-end space-x-2 pt-4">
              <Button size="sm" variant="outline" onClick={() => setSettings({})}>
                Reset
              </Button>
              <Button size="sm" onClick={() => handleAction('configure')}>
                Apply Settings
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const EnhancedAgentDashboard: React.FC = () => {
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemStats, setSystemStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    totalActions: 0,
    systemHealth: 0
  });

  const fetchAgentStatuses = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch('/api/agents/detailed-status');
      if (!response.ok) throw new Error('Failed to fetch agent statuses');
      
      const data = await response.json();
      setAgentStatuses(data.agents || {});
      setSystemStats(data.system || systemStats);
    } catch (err) {
      setError(`Failed to fetch agent data: ${err}`);
      console.error('Error fetching agent statuses:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgentStatuses();
    const interval = setInterval(fetchAgentStatuses, 5000);
    return () => clearInterval(interval);
  }, [fetchAgentStatuses]);

  const handleAgentAction = async (agentKey: string, action: string, params?: any) => {
    try {
      const response = await fetch(`/api/agents/${agentKey}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params || {})
      });
      
      if (!response.ok) throw new Error(`Failed to ${action} ${agentKey}`);
      
      // Refresh status after action
      setTimeout(fetchAgentStatuses, 1000);
    } catch (err) {
      console.error(`Agent action error:`, err);
      setError(`Failed to ${action} ${agentKey}: ${err}`);
    }
  };

  const categories = ['all', ...Array.from(new Set(Object.values(AGENT_CONFIGS).map(config => config.category)))];
  
  const filteredAgents = Object.entries(AGENT_CONFIGS).filter(([key, config]) => 
    selectedCategory === 'all' || config.category === selectedCategory
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading agent dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Enhanced Agent Control Center</h1>
          <p className="text-muted-foreground">Comprehensive control and monitoring for all trading agents</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={fetchAgentStatuses}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(AGENT_CONFIGS).length}</div>
            <p className="text-xs text-muted-foreground">Configured agents</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {Object.values(agentStatuses).filter(status => status?.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Target className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">
              {systemStats.systemHealth || 95}%
            </div>
            <p className="text-xs text-muted-foreground">Overall performance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Actions</CardTitle>
            <Zap className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-500">
              {systemStats.totalActions || 0}
            </div>
            <p className="text-xs text-muted-foreground">Since startup</p>
          </CardContent>
        </Card>
      </div>

      {/* Category Filter */}
      <div className="flex space-x-2">
        {categories.map(category => (
          <Button
            key={category}
            variant={selectedCategory === category ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(category)}
          >
            {category.replace(/^\w/, c => c.toUpperCase())}
          </Button>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredAgents.map(([agentKey, config]) => {
          const status = agentStatuses[agentKey] || {
            name: config.name,
            status: 'inactive' as const,
            uptime: 0,
            cpu: 0,
            memory: '0MB',
            lastActivity: 'Never',
            performance: { successRate: 0, totalActions: 0, avgResponseTime: 0 },
            health: { score: 0, issues: [] }
          };

          return (
            <AgentControlPanel
              key={agentKey}
              agentKey={agentKey}
              config={config}
              status={status}
              onAction={handleAgentAction}
            />
          );
        })}
      </div>

      {/* Global Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Global Agent Controls</CardTitle>
          <CardDescription>System-wide agent management</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button onClick={() => handleAgentAction('all', 'start')} className="bg-green-600 hover:bg-green-700">
              <Play className="w-4 h-4 mr-2" />
              Start All Agents
            </Button>
            <Button onClick={() => handleAgentAction('all', 'stop')} variant="destructive">
              <Pause className="w-4 h-4 mr-2" />
              Stop All Agents
            </Button>
            <Button onClick={() => handleAgentAction('all', 'restart')} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Restart All Agents
            </Button>
            <Button onClick={() => handleAgentAction('all', 'emergency_stop')} variant="destructive">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Emergency Stop
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedAgentDashboard;