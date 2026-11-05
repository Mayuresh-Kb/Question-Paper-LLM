import React, { useState, useRef, useEffect } from 'react';
import { api, errorMessage } from '../lib/api';
import { useForm } from '../context/formState';
import { Upload, FileText, AlertCircle, X, ArrowRight } from 'lucide-react';



const UploadPage = () => {
  const { handleUploadSuccess } = useForm();
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const [forceOcr, setForceOcr] = useState(false);
  const [ocrAvailable, setOcrAvailable] = useState(null);
  useEffect(() => {
    let active = true;
    api.get('/health').then(({ data }) => { if (active) setOcrAvailable(data.ocr_available); }).catch(() => {});
    return () => { active = false; };
  }, []);

  const allowedExtensions = ['.pdf', '.docx', '.txt'];

  const processFiles = (newFiles) => {
    if (isLoading) return;
    setError(null);
    const selectedFiles = Array.from(newFiles);

    const validFiles = selectedFiles.filter((file) => {
      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
      return allowedExtensions.includes(ext) && file.size > 0 && file.size <= 10 * 1024 * 1024;
    });

    if (validFiles.length !== selectedFiles.length) {
      setError('Some files were skipped. Use nonempty PDF, DOCX or TXT files up to 10 MB each.');
    }

    if (validFiles.length > 0) {
      setFiles((prev) => {
        const existingNames = new Set(prev.map((f) => f.name + f.size));
        const uniqueNew = validFiles.filter(f => { const key=f.name+f.size; if(existingNames.has(key)) return false; existingNames.add(key); return true; });
        const result=[...prev,...uniqueNew];
        if(result.length>12 || result.reduce((sum,f)=>sum+f.size,0)>30*1024*1024) { setError('Use at most 12 files and 30 MB in total.'); return prev; }
        return result;
      });
    }
  };

  const handleFileChange = (event) => {
    if (event.target.files) {
      processFiles(event.target.files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (indexToRemove) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const clearAllFiles = () => {
    setFiles([]);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select or drop at least one question bank file.');
      return;
    }

    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('ocr_mode', forceOcr ? 'force' : 'auto');

    try {
      const response = await api.post('/upload', formData);
      handleUploadSuccess(response.data);
    } catch (err) {
      console.error("Upload error:", err);
      const errorMsg = errorMessage(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-light text-gray-900 mb-2">
          Upload Question Bank Files
        </h2>
        <p className="text-sm text-gray-600">
          One numbered question bank per unit. Upload printed or scanned PDFs, DOCX, or UTF-8 TXT. Scanned PDF pages are read with local OCR.
        </p>
      </div>

      <p className="text-sm text-slate-600 mb-5">Maximum 12 files, 10 MB each and 30 MB total. Questions should start with Q1., 1. or 1). Add [5 Marks], [BTL: 3], and optional [Topic: Trees]. <a href="/examples/unit-1.txt" download className="text-blue-700 underline">Download an example bank</a>.</p>
      <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 mb-5 text-sm text-slate-700 space-y-2">
        <p>OCR stays on this computer. Use clear, upright printed scans; review extracted questions and marks before generating. Up to 20 scanned pages per upload; processing may take up to 90 seconds.</p>
        {ocrAvailable === false && <p role="status" className="text-amber-800">OCR is unavailable on the backend. Install Tesseract with English language data to read scans. Text PDFs, DOCX and TXT still work.</p>}
        <label className="flex gap-2 items-start"><input type="checkbox" className="mt-1" checked={forceOcr} disabled={isLoading || ocrAvailable === false} onChange={e => setForceOcr(e.target.checked)} />Re-read all PDF pages with OCR (use if the existing text layer is garbled)</label>
      </div>
      {/* Drag and Drop Zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Choose question bank files"
        onKeyDown={e => { if(e.key==='Enter' || e.key===' ') { e.preventDefault(); if(!isLoading) fileInputRef.current?.click(); } }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isLoading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
          isDragging
            ? 'border-blue-700 bg-blue-50/50'
            : 'border-gray-300 hover:border-gray-400 bg-white'
        }`}
      >
        <input
          ref={fileInputRef}
          id="file-upload"
          type="file"
          multiple
          disabled={isLoading}
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
          className="hidden"
        />

        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
            <Upload className="w-8 h-8 text-blue-700" />
          </div>

          <div className="text-sm text-gray-600">
            <span className="text-blue-700 font-semibold hover:text-blue-800">
              Click to upload
            </span>{' '}
            or drag and drop
          </div>
          <p className="text-xs text-gray-500 mt-1">
            PDF, DOCX, or TXT files
          </p>
        </div>
      </div>

      {/* Selected Files List */}
      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-gray-900">
              Selected Files ({files.length})
            </p>
            <button
              type="button"
              disabled={isLoading}
              onClick={clearAllFiles}
              className="text-xs text-gray-500 hover:text-red-600 transition-colors cursor-pointer"
            >
              Clear all
            </button>
          </div>

          {files.map((file, index) => (
            <div
              key={`${file.name}-${index}`}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1 mr-3">
                <FileText className="w-5 h-5 text-gray-400 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-900 truncate">
                    Unit {index+1}: {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(index);
                }}
                className="p-1 text-gray-400 hover:text-gray-700 rounded transition-colors cursor-pointer"
                disabled={isLoading}
                aria-label={`Remove ${file.name}`}
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleUpload}
        disabled={isLoading || files.length === 0}
        className="mt-6 w-full flex items-center justify-center gap-2 bg-blue-700 hover:bg-blue-800 text-white font-medium py-3 px-4 rounded disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm"
      >
        {isLoading ? (
          <span role="status">Reading question banks… Scanned pages may take longer.</span>
        ) : (
          <>
            <span>Upload & Proceed</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
};

export default UploadPage;