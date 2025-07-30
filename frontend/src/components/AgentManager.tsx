import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Play, 
  Pause, 
  Square, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Activity,
  Cpu,
  MemoryStick,
  Clock,
  TrendingUp,
  Target
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  cpu: number;
  memory: string;
  uptime: string;
  lastActivity: string;
  description: string;
  performance?: {
    accuracy: number;
    signalsGenerated: number;
    tradesExecuted: number;
    winRate: number;
  };
  error?: string;
}

const AgentManager: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'trade-agent-1',
      name: 'Trade Execution Agent',
      type: 'trading',
      status: 'running',
      cpu: 15.2,
      memory: '256MB',
      uptime: '2h 15m',
      lastActivity: '30s ago',
      description: 'Executes trades based on signals from strategy agents',
      performance: {
        accuracy: 87.5,
        signalsGenerated: 0,
        tradesExecuted: 23,
        winRate: 65.2
      }
    },
    {
      id: 'strategy-agent-1',
      name: 'Signal Generator Agent',
      type: 'strategy',
      status: 'running',
      cpu: 8.7,
      memory: '512MB',
      uptime: '2h 15m',
      lastActivity: '5s ago',
      description: 'Generates trading signals using AI analysis',
      performance: {
        accuracy: 92.1,
        signalsGenerated: 156,
        tradesExecuted: 0,
        winRate: 0
      }
    },
    {
      id: 'risk-agent-1',
      name: 'Risk Management Agent',
      type: 'risk',
      status: 'running',
      cpu: 3.1,
      memory: '128MB',
      uptime: '2h 15m',
      lastActivity: '10s ago',
      description: 'Monitors and manages trading risk exposure',
      performance: {
        accuracy: 95.8,
        signalsGenerated: 45,
        tradesExecuted: 0,
        winRate: 0
      }
    },
    {
      id: 'market-agent-1',
      name: 'Market Data Agent',
      type: 'data',
      status: 'error',
      cpu: 0,
      memory: '64MB',
      uptime: '0m',
      lastActivity: '5m ago',
      description: 'Collects and processes real-time market data',
      error: 'API connection timeout'
    }
  ]);

  const [isLoading, setIsLoading] = useState(false);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'stopped':
        return <Square className="w-4 h-4 text-gray-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'starting':
      case 'stopping':
        return <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'stopped':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-300 border-red-500/30';
      case 'starting':
      case 'stopping':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      default:
        return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
    }
  };

  const handleAgentAction = async (agentId: string, action: 'start' | 'stop' | 'restart') => {
    setIsLoading(true);
    
    // Update agent status optimistically
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { 
            ...agent, 
            status: action === 'stop' ? 'stopping' : 'starting' as any
          }
        : agent
    ));

    // Simulate API call
    setTimeout(() => {
      setAgents(prev => prev.map(agent => 
        agent.id === agentId 
          ? { 
              ...agent, 
              status: action === 'stop' ? 'stopped' : 'running' as any,
              error: action === 'stop' ? undefined : agent.error
            }
          : agent
      ));
      setIsLoading(false);
    }, 2000);
  };

  const refreshAgents = async () => {
    setIsLoading(true);
    // Simulate API call to refresh agent status
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Agent Manager</h2>
          <p className="text-gray-400">Monitor and control trading agents</p>
        </div>
        <Button 
          onClick={refreshAgents}
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <Card key={agent.id} className="bg-gray-900 border-gray-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(agent.status)}
                  <div>
                    <CardTitle className="text-white">{agent.name}</CardTitle>
                    <CardDescription className="text-gray-400">
                      {agent.description}
                    </CardDescription>
                  </div>
                </div>
                <Badge className={getStatusColor(agent.status)}>
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {agent.error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    <span className="text-red-400 text-sm">{agent.error}</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-blue-400" />
                  <span className="text-gray-300">CPU: {agent.cpu}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MemoryStick className="w-4 h-4 text-green-400" />
                  <span className="text-gray-300">RAM: {agent.memory}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-yellow-400" />
                  <span className="text-gray-300">Uptime: {agent.uptime}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-purple-400" />
                  <span className="text-gray-300">Last: {agent.lastActivity}</span>
                </div>
              </div>

              {agent.performance && (
                <div className="p-3 bg-gray-800 rounded-lg">
                  <h4 className="text-sm font-medium text-white mb-2">Performance</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Accuracy:</span>
                      <span className="text-green-400">{agent.performance.accuracy}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Win Rate:</span>
                      <span className="text-blue-400">{agent.performance.winRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Signals:</span>
                      <span className="text-yellow-400">{agent.performance.signalsGenerated}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Trades:</span>
                      <span className="text-purple-400">{agent.performance.tradesExecuted}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex space-x-2">
                {agent.status === 'running' ? (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAgentAction(agent.id, 'stop')}
                      disabled={isLoading}
                      className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                    >
                      <Pause className="w-3 h-3 mr-1" />
                      Stop
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAgentAction(agent.id, 'restart')}
                      disabled={isLoading}
                      className="border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10"
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Restart
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleAgentAction(agent.id, 'start')}
                    disabled={isLoading}
                    className="border-green-500/30 text-green-400 hover:bg-green-500/10"
                  >
                    <Play className="w-3 h-3 mr-1" />
                    Start
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AgentManager;
