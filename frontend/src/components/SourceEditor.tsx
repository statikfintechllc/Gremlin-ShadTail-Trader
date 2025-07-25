import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Editor } from '@monaco-editor/react';
import { FolderOpen, Save, Play, Square, FileText, Folder, ChevronRight, ChevronDown } from 'lucide-react';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  size?: number;
  modified?: string;
}

interface SourceEditorProps {
  apiBaseUrl?: string;
}

export default function SourceEditor({ apiBaseUrl = 'http://localhost:8000' }: SourceEditorProps) {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [agentStatus, setAgentStatus] = useState<'stopped' | 'running' | 'error'>('stopped');
  const editorRef = useRef<any>(null);

  useEffect(() => {
    loadFileTree();
    checkAgentStatus();
  }, []);

  const loadFileTree = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/source/files`);
      if (response.ok) {
        const data = await response.json();
        setFileTree(data.files || []);
      }
    } catch (error) {
      console.error('Failed to load file tree:', error);
      // Fallback mock data
      setFileTree([
        {
          name: 'backend',
          path: '/backend',
          type: 'directory',
          children: [
            { name: 'server.py', path: '/backend/server.py', type: 'file', size: 15234 },
            { name: 'Gremlin_Trade_Core', path: '/backend/Gremlin_Trade_Core', type: 'directory' }
          ]
        },
        {
          name: 'frontend',
          path: '/frontend',
          type: 'directory',
          children: [
            { name: 'src', path: '/frontend/src', type: 'directory' }
          ]
        }
      ]);
    }
  };

  const checkAgentStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/agents/status`);
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data.status === 'running' ? 'running' : 'stopped');
      }
    } catch (error) {
      console.error('Failed to check agent status:', error);
      setAgentStatus('error');
    }
  };

  const loadFileContent = async (filePath: string) => {
    if (isDirty && selectedFile) {
      const confirmDiscard = window.confirm('You have unsaved changes. Discard them?');
      if (!confirmDiscard) return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/source/file?path=${encodeURIComponent(filePath)}`);
      if (response.ok) {
        const data = await response.json();
        setFileContent(data.content || '');
        setSelectedFile(filePath);
        setIsDirty(false);
      }
    } catch (error) {
      console.error('Failed to load file content:', error);
      // Mock content for demonstration
      setFileContent(`# File: ${filePath}
# This is a mock file content for development

def example_function():
    """Example function"""
    return "Hello from ${filePath}"

if __name__ == "__main__":
    print(example_function())
`);
      setSelectedFile(filePath);
      setIsDirty(false);
    } finally {
      setIsLoading(false);
    }
  };

  const saveFile = async () => {
    if (!selectedFile || !isDirty) return;

    try {
      const response = await fetch(`${apiBaseUrl}/api/source/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: selectedFile,
          content: fileContent
        }),
      });

      if (response.ok) {
        setIsDirty(false);
        console.log('File saved successfully');
      }
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };

  const startAgents = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/agents/start`, {
        method: 'POST',
      });
      if (response.ok) {
        setAgentStatus('running');
      }
    } catch (error) {
      console.error('Failed to start agents:', error);
      setAgentStatus('error');
    }
  };

  const stopAgents = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/agents/stop`, {
        method: 'POST',
      });
      if (response.ok) {
        setAgentStatus('stopped');
      }
    } catch (error) {
      console.error('Failed to stop agents:', error);
      setAgentStatus('error');
    }
  };

  const handleEditorChange = useCallback((value: string | undefined) => {
    setFileContent(value || '');
    setIsDirty(true);
  }, []);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
    // Configure editor settings
    editor.updateOptions({
      fontSize: 14,
      lineNumbers: 'on',
      roundedSelection: false,
      scrollBeyondLastLine: false,
      automaticLayout: true,
    });
  };

  const toggleDirectory = (path: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedDirs(newExpanded);
  };

  const renderFileTree = (nodes: FileNode[], level = 0): JSX.Element[] => {
    return nodes.map((node) => (
      <div key={node.path} style={{ marginLeft: `${level * 16}px` }}>
        <div
          className={`flex items-center space-x-2 p-1 hover:bg-gray-700 cursor-pointer rounded ${
            selectedFile === node.path ? 'bg-blue-600' : ''
          }`}
          onClick={() => {
            if (node.type === 'directory') {
              toggleDirectory(node.path);
            } else {
              loadFileContent(node.path);
            }
          }}
        >
          {node.type === 'directory' ? (
            <>
              {expandedDirs.has(node.path) ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <Folder className="w-4 h-4 text-yellow-400" />
            </>
          ) : (
            <>
              <div className="w-4" />
              <FileText className="w-4 h-4 text-blue-400" />
            </>
          )}
          <span className="text-sm">{node.name}</span>
        </div>
        {node.type === 'directory' && 
         expandedDirs.has(node.path) && 
         node.children && 
         renderFileTree(node.children, level + 1)}
      </div>
    ));
  };

  const getLanguageFromPath = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return 'python';
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'tsx': return 'typescript';
      case 'jsx': return 'javascript';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'html': return 'html';
      case 'css': return 'css';
      case 'sh': return 'shell';
      default: return 'plaintext';
    }
  };

  return (
    <div className="flex h-full bg-gray-900 text-white">
      {/* File Explorer */}
      <div className="w-64 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold mb-2">Source Explorer</h3>
          <div className="flex space-x-2">
            <button
              onClick={loadFileTree}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
              title="Refresh"
            >
              <FolderOpen className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {renderFileTree(fileTree)}
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">
              {selectedFile || 'No file selected'}
            </span>
            {isDirty && <span className="text-yellow-400 text-sm">●</span>}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={saveFile}
              disabled={!isDirty}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded text-sm"
            >
              <Save className="w-4 h-4" />
              <span>Save</span>
            </button>
            <div className="border-l border-gray-600 pl-2 ml-2">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-400">Agents:</span>
                <div className={`w-2 h-2 rounded-full ${
                  agentStatus === 'running' ? 'bg-green-400' : 
                  agentStatus === 'error' ? 'bg-red-400' : 'bg-gray-400'
                }`} />
                {agentStatus === 'running' ? (
                  <button
                    onClick={stopAgents}
                    className="flex items-center space-x-1 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                  >
                    <Square className="w-3 h-3" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={startAgents}
                    className="flex items-center space-x-1 px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                  >
                    <Play className="w-3 h-3" />
                    <span>Start</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1">
          {selectedFile ? (
            <Editor
              height="100%"
              language={getLanguageFromPath(selectedFile)}
              value={fileContent}
              onChange={handleEditorChange}
              onMount={handleEditorDidMount}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: 'on',
                wrappingIndent: 'indent',
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select a file to start editing</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}