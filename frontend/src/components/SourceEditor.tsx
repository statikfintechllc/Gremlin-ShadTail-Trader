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
      setIsLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/source/files`);
      if (response.ok) {
        const data = await response.json();
        setFileTree(data.files || []);
      } else {
        console.error('Failed to load file tree: HTTP', response.status);
        setFileTree([]); // Show empty instead of fake data
      }
    } catch (error) {
      console.error('Failed to load file tree:', error);
      setFileTree([]); // Show empty instead of fake data
    } finally {
      setIsLoading(false);
    }
  };

  const checkAgentStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/agents/status`);
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data.status === 'running' ? 'running' : 'stopped');
      } else {
        setAgentStatus('error');
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
      } else {
        console.error('Failed to load file:', response.status);
        setFileContent(`// Error: Could not load file ${filePath}\n// Status: ${response.status}`);
        setSelectedFile(filePath);
        setIsDirty(false);
      }
    } catch (error) {
      console.error('Failed to load file content:', error);
      setFileContent(`// Error: Network error loading ${filePath}\n// ${error}`);
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
    <div className="flex h-full bg-gray-900 text-white overflow-hidden">
      {/* File Explorer */}
      <div className="w-64 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
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
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
              <span className="ml-2 text-sm text-gray-400">Loading files...</span>
            </div>
          ) : fileTree.length > 0 ? (
            renderFileTree(fileTree)
          ) : (
            <div className="text-center py-8">
              <Folder className="w-12 h-12 text-gray-500 mx-auto mb-2" />
              <p className="text-sm text-gray-400">No files found</p>
              <button 
                onClick={loadFileTree}
                className="mt-2 text-xs text-blue-400 hover:text-blue-300"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
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
        <div className="flex-1 overflow-hidden">
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
                <p className="text-sm text-gray-500 mt-2">
                  Files will load from the Gremlin-ShadTail-Trader project
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}