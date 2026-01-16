'use client';

import { useState } from 'react';
import { exportEntries, importEntries } from '@/app/config/storage';

interface Props {
  goalId: string;
  onImport?: () => void;
}

export function ExportImport({ goalId, onImport }: Props) {
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const handleExport = async () => {
    const json = exportEntries(goalId);
    try {
      await navigator.clipboard.writeText(json);
      setMessage('Copied to clipboard!');
    } catch {
      setMessage('Copy failed - check console');
      console.log(json);
    }
    setTimeout(() => setMessage(null), 2000);
  };

  const handleImport = () => {
    try {
      importEntries(goalId, importText);
      setMessage('Imported successfully!');
      setShowImport(false);
      setImportText('');
      onImport?.();
    } catch (e) {
      setMessage(`Import failed: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-4">
        <button
          type="button"
          onClick={handleExport}
          className="text-sm text-blue-600 hover:underline"
        >
          Export JSON
        </button>
        <button
          type="button"
          onClick={() => setShowImport(!showImport)}
          className="text-sm text-blue-600 hover:underline"
        >
          Import JSON
        </button>
      </div>
      {message && <p className="text-sm text-green-600">{message}</p>}
      {showImport && (
        <div className="space-y-2">
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            placeholder="Paste JSON here..."
          />
          <button
            type="button"
            onClick={handleImport}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Import
          </button>
        </div>
      )}
    </div>
  );
}
