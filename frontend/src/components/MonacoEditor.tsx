import React, { useState, useEffect, useRef } from 'react';
import * as monaco from 'monaco-editor';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { FileText, Save, RefreshCw, Folder, File } from 'lucide-react';

interface FileTreeItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileTreeItem[];
  size?: number;
  modified?: string;
}

interface MonacoEditorProps {
  theme?: 'vs-dark' | 'light';
}

const MonacoEditor: React.FC<MonacoEditorProps> = ({ theme = 'vs-dark' }) => {
  const [editor, setEditor] = useState<monaco.editor.IStandaloneCodeEditor | null>(null);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [projectFiles, setProjectFiles] = useState<FileTreeItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const editorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (editorRef.current && !editor) {
      const monacoEditor = monaco.editor.create(editorRef.current, {
        value: '// Welcome to Gremlin ShadTail Trader Code Editor\n// Select a file from the tree to start editing\n',
        language: 'javascript',
        theme: theme,
        automaticLayout: true,
        fontSize: 14,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        lineNumbers: 'on',
        folding: true,
        lineDecorationsWidth: 10,
        lineNumbersMinChars: 3,
      });

      setEditor(monacoEditor);
      loadProjectFiles();
    }

    return () => {
      if (editor) {
        editor.dispose();
      }
    };
  }, []);

  const loadProjectFiles = async () => {
    if (!window.electronAPI) {
      console.warn('Electron API not available - file system access disabled');
      return;
    }

    setIsLoading(true);
    try {
      const result = await window.electronAPI.getProjectFiles();
      if (result.success) {
        setProjectFiles(result.files);
      } else {
        console.error('Failed to load project files:', result.error);
      }
    } catch (error) {
      console.error('Error loading project files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFile = async (filePath: string) => {
    if (!window.electronAPI) {
      return;
    }

    setIsLoading(true);
    try {
      const result = await window.electronAPI.readFile(filePath);
      if (result.success) {
        setFileContent(result.content);
        setCurrentFile(filePath);
        
        if (editor) {
          editor.setValue(result.content);
          
          // Set language based on file extension
          const extension = filePath.split('.').pop()?.toLowerCase();
          let language = 'plaintext';
          
          switch (extension) {
            case 'js':
            case 'jsx':
              language = 'javascript';
              break;
            case 'ts':
            case 'tsx':
              language = 'typescript';
              break;
            case 'py':
              language = 'python';
              break;
            case 'json':
              language = 'json';
              break;
            case 'html':
              language = 'html';
              break;
            case 'css':
              language = 'css';
              break;
            case 'md':
              language = 'markdown';
              break;
            case 'sh':
              language = 'shell';
              break;
            case 'yml':
            case 'yaml':
              language = 'yaml';
              break;
          }
          
          monaco.editor.setModelLanguage(editor.getModel()!, language);
        }
      } else {
        console.error('Failed to load file:', result.error);
      }
    } catch (error) {
      console.error('Error loading file:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveFile = async () => {
    if (!window.electronAPI || !currentFile || !editor) {
      return;
    }

    setIsLoading(true);
    try {
      const content = editor.getValue();
      const result = await window.electronAPI.writeFile(currentFile, content);
      if (result.success) {
        setFileContent(content);
        console.log('File saved successfully');
      } else {
        console.error('Failed to save file:', result.error);
      }
    } catch (error) {
      console.error('Error saving file:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDirectory = (dirPath: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(dirPath)) {
      newExpanded.delete(dirPath);
    } else {
      newExpanded.add(dirPath);
    }
    setExpandedDirs(newExpanded);
  };

  const renderFileTree = (items: FileTreeItem[], level = 0) => {
    return items.map((item) => (
      <div key={item.path} style={{ paddingLeft: `${level * 16}px` }}>
        <div
          className={`flex items-center p-1 cursor-pointer hover:bg-trading-gray-200/20 rounded ${
            currentFile === item.path ? 'bg-trading-gold/20' : ''
          }`}
          onClick={() => {
            if (item.type === 'directory') {
              toggleDirectory(item.path);
            } else {
              loadFile(item.path);
            }
          }}
        >
          {item.type === 'directory' ? (
            <Folder className="w-4 h-4 mr-2 text-trading-bronze" />
          ) : (
            <File className="w-4 h-4 mr-2 text-trading-gold" />
          )}
          <span className="text-sm text-trading-gold">{item.name}</span>
          {item.type === 'file' && item.size && (
            <span className="ml-auto text-xs text-trading-bronze">
              {(item.size / 1024).toFixed(1)}KB
            </span>
          )}
        </div>
        {item.type === 'directory' && 
         item.children && 
         expandedDirs.has(item.path) && 
         renderFileTree(item.children, level + 1)}
      </div>
    ));
  };

  const hasUnsavedChanges = editor && currentFile && editor.getValue() !== fileContent;

  return (
    <div className="h-full flex bg-trading-black">
      {/* File Tree Sidebar */}
      <div className="w-80 border-r border-trading-gray-300 bg-trading-gray-200/10">
        <Card className="h-full bg-transparent border-0 rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-trading-gold flex items-center justify-between">
              <div className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Project Files
              </div>
              <button
                onClick={loadProjectFiles}
                disabled={isLoading}
                className="p-1 hover:bg-trading-gray-200/20 rounded transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent className="h-full overflow-y-auto p-2">
            {isLoading && projectFiles.length === 0 ? (
              <div className="text-trading-bronze text-center py-4">Loading files...</div>
            ) : projectFiles.length > 0 ? (
              renderFileTree(projectFiles)
            ) : (
              <div className="text-trading-bronze text-center py-4">
                No files found or file system access not available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        {/* Editor Header */}
        <div className="border-b border-trading-gray-300 bg-trading-gray-200/10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-trading-gold font-medium">
                {currentFile || 'No file selected'}
              </span>
              {hasUnsavedChanges && (
                <span className="ml-2 text-trading-red text-sm">● Unsaved changes</span>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={saveFile}
                disabled={!currentFile || isLoading || !hasUnsavedChanges}
                className="flex items-center px-3 py-1 bg-trading-gold text-trading-black rounded hover:bg-trading-bronze transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4 mr-1" />
                Save
              </button>
            </div>
          </div>
        </div>

        {/* Monaco Editor Container */}
        <div className="flex-1">
          <div ref={editorRef} className="w-full h-full" />
        </div>
      </div>
    </div>
  );
};

export default MonacoEditor;
