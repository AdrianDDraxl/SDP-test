import { useState, useRef, useCallback } from 'react';
import { X, Link as LinkIcon, Upload, Loader2 } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
  onClone: (url: string) => Promise<void>;
  onUpload: (file: File) => Promise<void>;
}

export default function AddRepoModal({ open, onClose, onClone, onUpload }: Props) {
  const [tab, setTab] = useState<'clone' | 'upload'>('clone');
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleClone = async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      await onClone(url.trim());
      setUrl('');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleFile = useCallback(async (file: File) => {
    setLoading(true);
    try {
      await onUpload(file);
      onClose();
    } finally {
      setLoading(false);
    }
  }, [onUpload, onClose]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.zip')) handleFile(file);
  }, [handleFile]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Add Repository</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setTab('clone')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              tab === 'clone'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <LinkIcon className="mr-2 inline h-4 w-4" />
            Clone URL
          </button>
          <button
            onClick={() => setTab('upload')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              tab === 'upload'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload className="mr-2 inline h-4 w-4" />
            Upload ZIP
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {tab === 'clone' ? (
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Git Repository URL</label>
                <input
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  placeholder="https://github.com/user/repo.git"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  onKeyDown={e => e.key === 'Enter' && handleClone()}
                />
              </div>
              <button
                onClick={handleClone}
                disabled={loading || !url.trim()}
                className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? 'Cloning...' : 'Clone Repository'}
              </button>
            </div>
          ) : (
            <div
              className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors ${
                dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-gray-50'
              }`}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <Upload className="h-10 w-10 text-gray-400" />
              <p className="mt-3 text-sm text-gray-600">
                Drag & drop a <span className="font-medium">.zip</span> file here, or{' '}
                <button
                  onClick={() => fileRef.current?.click()}
                  className="text-blue-600 hover:underline font-medium"
                >
                  browse
                </button>
              </p>
              <input
                ref={fileRef}
                type="file"
                accept=".zip"
                className="hidden"
                onChange={e => {
                  const file = e.target.files?.[0];
                  if (file) handleFile(file);
                }}
              />
              {loading && (
                <div className="mt-4 flex items-center gap-2 text-sm text-blue-600">
                  <Loader2 className="h-4 w-4 animate-spin" /> Uploading...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
