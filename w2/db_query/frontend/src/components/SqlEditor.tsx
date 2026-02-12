import React from 'react';
import Editor from '@monaco-editor/react';
import type { editor } from 'monaco-editor';

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
  readOnly?: boolean;
  height?: string;
}

export const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  onExecute,
  readOnly = false,
  height = '300px',
}) => {
  const handleEditorChange = (value: string | undefined) => {
    onChange(value || '');
  };

  const handleEditorMount = (editor: editor.IStandaloneCodeEditor) => {
    // Add Ctrl+Enter keyboard shortcut for query execution
    if (onExecute) {
      editor.addCommand(
        // Ctrl+Enter or Cmd+Enter
        monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
        () => {
          onExecute();
        }
      );
    }
  };

  return (
    <Editor
      height={height}
      defaultLanguage="sql"
      value={value}
      onChange={handleEditorChange}
      onMount={handleEditorMount}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 2,
        wordWrap: 'on',
        theme: 'vs-dark',
      }}
    />
  );
};
