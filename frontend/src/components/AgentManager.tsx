import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
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
  Shield
} from 'lucide-react';

interface CoordinatorOverview {
  coordinator_status: {
    status: string;
    uptime: number;
  };
  coordination_mode: string;
  trading_phase: string;
  performance: {
    total_decisions: number;
    successful_decisions: number;
    accuracy: number;
    total_pnl: number;
  };
  active_watchlist: string[];
  pending_decisions: number;
  executed_decisions: number;
  agent_overviews: {
    timing: any;
    strategy: any;
    rules: any;
    runtime: any;
  };
}

interface ToolOverview {
  agent_status: {
    status: string;
  };
  total_tools: number;
  status_distribution: Record<string, number>;
  performance_summary: {
    success_rate: number;
    total_executions: number;
    average_duration: number;
  };
  top_performing_tools: string[];
  active_executions: number;
}

const AgentManager: React.FC = () => {
  const [coordinatorData, setCoordinatorData] = useState<CoordinatorOverview | null>(null);
  const [toolData, setToolData] = useState<ToolOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchSystemStatus = useCallback(async () => {
    try {
      setError(null);
      
      // Fetch coordinator overview
      const coordResponse = await fetch('/api/coordinator/overview');
      if (coordResponse.ok) {
        const coordData = await coordResponse.json();
        setCoordinatorData(coordData);
      }
      
      // Fetch tool overview
      const toolResponse = await fetch('/api/tools/overview');
      if (toolResponse.ok) {
        const toolData = await toolResponse.json();
        setToolData(toolData);
      }
      
    } catch (err) {
      setError(`Failed to fetch system status: ${err}`);
      console.error('Error fetching system status:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSystemStatus();
  }, [fetchSystemStatus]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchSystemStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchSystemStatus, refreshInterval, autoRefresh]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'inactive':
        return <Pause className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'initializing':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'inactive':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      case 'initializing':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading agent status...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="w-6 h-6" />
          <h1 className="text-2xl font-bold">Agent Manager</h1>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            Auto Refresh
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSystemStatus}
          >
            <RefreshCw className="w-4 h-4" />
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

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Trading Agents</TabsTrigger>
          <TabsTrigger value="tools">Tool Control</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* System Status */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Status</CardTitle>
                <Activity className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {coordinatorData?.coordinator_status?.status || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Uptime: {coordinatorData?.coordinator_status?.uptime ? 
                    formatUptime(coordinatorData.coordinator_status.uptime) : 'N/A'}
                </p>
              </CardContent>
            </Card>

            {/* Trading Mode */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Trading Mode</CardTitle>
                <Target className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {coordinatorData?.coordination_mode || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Phase: {coordinatorData?.trading_phase || 'N/A'}
                </p>
              </CardContent>
            </Card>

            {/* Total Decisions */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Decisions</CardTitle>
                <BarChart3 className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {coordinatorData?.performance?.total_decisions || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Accuracy: {coordinatorData?.performance?.accuracy ? 
                    `${(coordinatorData.performance.accuracy * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </CardContent>
            </Card>

            {/* Total P&L */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
                <TrendingUp className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {coordinatorData?.performance?.total_pnl ? 
                    formatCurrency(coordinatorData.performance.total_pnl) : '$0.00'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Successful: {coordinatorData?.performance?.successful_decisions || 0}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Active Watchlist */}
          <Card>
            <CardHeader>
              <CardTitle>Active Watchlist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {coordinatorData?.active_watchlist?.map((symbol) => (
                  <Badge key={symbol} variant="secondary">
                    {symbol}
                  </Badge>
                )) || <span className="text-muted-foreground">No symbols</span>}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Timing Agent */}
            {coordinatorData?.agent_overviews?.timing && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Clock className="w-5 h-5" />
                    <span>Timing Agent</span>
                  </CardTitle>
                  {getStatusIcon(coordinatorData.agent_overviews.timing.agent_status?.status || 'unknown')}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Status</span>
                      <Badge variant={coordinatorData.agent_overviews.timing.agent_status?.status === 'active' ? 'default' : 'secondary'}>
                        {coordinatorData.agent_overviews.timing.agent_status?.status || 'Unknown'}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Active Analyses</span>
                      <span>{coordinatorData.agent_overviews.timing.active_analyses || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Accuracy</span>
                      <span>{coordinatorData.agent_overviews.timing.timing_accuracy ? 
                        `${(coordinatorData.agent_overviews.timing.timing_accuracy * 100).toFixed(1)}%` : 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Strategy Agent */}
            {coordinatorData?.agent_overviews?.strategy && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5" />
                    <span>Strategy Agent</span>
                  </CardTitle>
                  {getStatusIcon(coordinatorData.agent_overviews.strategy.agent_status?.status || 'unknown')}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Status</span>
                      <Badge variant={coordinatorData.agent_overviews.strategy.agent_status?.status === 'active' ? 'default' : 'secondary'}>
                        {coordinatorData.agent_overviews.strategy.agent_status?.status || 'Unknown'}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Active Strategies</span>
                      <span>{coordinatorData.agent_overviews.strategy.active_strategies || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Performance</span>
                      <span>{coordinatorData.agent_overviews.strategy.performance?.accuracy ? 
                        `${(coordinatorData.agent_overviews.strategy.performance.accuracy * 100).toFixed(1)}%` : 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Rule Set Agent */}
            {coordinatorData?.agent_overviews?.rules && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Shield className="w-5 h-5" />
                    <span>Rule Set Agent</span>
                  </CardTitle>
                  {getStatusIcon(coordinatorData.agent_overviews.rules.agent_status?.status || 'unknown')}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Status</span>
                      <Badge variant={coordinatorData.agent_overviews.rules.agent_status?.status === 'active' ? 'default' : 'secondary'}>
                        {coordinatorData.agent_overviews.rules.agent_status?.status || 'Unknown'}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Active Rules</span>
                      <span>{coordinatorData.agent_overviews.rules.total_rules || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Rule Sets</span>
                      <span>{coordinatorData.agent_overviews.rules.rule_sets || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Runtime Agent */}
            {coordinatorData?.agent_overviews?.runtime && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Settings className="w-5 h-5" />
                    <span>Runtime Agent</span>
                  </CardTitle>
                  {getStatusIcon(coordinatorData.agent_overviews.runtime.agent_status?.status || 'unknown')}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Status</span>
                      <Badge variant={coordinatorData.agent_overviews.runtime.agent_status?.status === 'active' ? 'default' : 'secondary'}>
                        {coordinatorData.agent_overviews.runtime.agent_status?.status || 'Unknown'}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Active Tasks</span>
                      <span>{coordinatorData.agent_overviews.runtime.active_tasks || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>CPU Usage</span>
                      <span>{coordinatorData.agent_overviews.runtime.system_metrics?.cpu_percent ? 
                        `${coordinatorData.agent_overviews.runtime.system_metrics.cpu_percent.toFixed(1)}%` : 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Tool Control Tab */}
        <TabsContent value="tools" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Tools</CardTitle>
                <Zap className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {toolData?.total_tools || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Active: {toolData?.status_distribution?.active || 0}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <CheckCircle className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {toolData?.performance_summary?.success_rate ? 
                    `${(toolData.performance_summary.success_rate * 100).toFixed(1)}%` : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Executions: {toolData?.performance_summary?.total_executions || 0}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Executions</CardTitle>
                <Activity className="w-4 h-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {toolData?.active_executions || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Avg Duration: {toolData?.performance_summary?.average_duration ? 
                    `${toolData.performance_summary.average_duration.toFixed(1)}s` : 'N/A'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Tool Status Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Tool Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {toolData?.status_distribution && Object.entries(toolData.status_distribution).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
                      <span className="capitalize">{status}</span>
                    </div>
                    <span>{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Performing Tools */}
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Tools</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-32">
                <div className="space-y-2">
                  {toolData?.top_performing_tools?.map((tool, index) => (
                    <div key={tool} className="flex items-center justify-between">
                      <span>#{index + 1} {tool}</span>
                      <Badge variant="secondary">Top Performer</Badge>
                    </div>
                  )) || <span className="text-muted-foreground">No data available</span>}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Coordinator Performance */}
            <Card>
              <CardHeader>
                <CardTitle>Coordinator Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Decision Accuracy</span>
                    <span>{coordinatorData?.performance?.accuracy ? 
                      `${(coordinatorData.performance.accuracy * 100).toFixed(1)}%` : 'N/A'}</span>
                  </div>
                  <Progress 
                    value={coordinatorData?.performance?.accuracy ? coordinatorData.performance.accuracy * 100 : 0} 
                    className="h-2"
                  />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Success Rate</span>
                    <span>
                      {coordinatorData?.performance?.total_decisions ? 
                        `${((coordinatorData.performance.successful_decisions / coordinatorData.performance.total_decisions) * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <Progress 
                    value={coordinatorData?.performance?.total_decisions ? 
                      (coordinatorData.performance.successful_decisions / coordinatorData.performance.total_decisions) * 100 : 0} 
                    className="h-2"
                  />
                </div>
              </CardContent>
            </Card>

            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Agent Uptime</span>
                    <span>99.9%</span>
                  </div>
                  <Progress value={99.9} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Memory Efficiency</span>
                    <span>85%</span>
                  </div>
                  <Progress value={85} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Processing Speed</span>
                    <span>92%</span>
                  </div>
                  <Progress value={92} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentManager;
