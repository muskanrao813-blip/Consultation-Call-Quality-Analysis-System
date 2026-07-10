import React, { useState } from 'react';
import {
  UploadCloud,
  Loader2,
  Clock,
  CheckCircle2,
  FileCheck2,
  ShieldCheck,
  AlertCircle,
  FileText
} from 'lucide-react';
import { Recording } from '../types';

interface CallUploadViewProps {
  activeQueue: Recording[];
  completedRecordings: Recording[];
  onSelectCall: (id: string) => void;
  onUploadFile: (fileName: string) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CallUploadView({
  activeQueue,
  onUploadFile
}: CallUploadViewProps) {
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [dragOverExcel, setDragOverExcel] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');

  // Handle Drag & Drop events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      onUploadFile(file.name);
    }
  };

  // Handle manual file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadFile(e.target.files[0].name);
    }
  };

  // Handle Excel file upload
  const handleExcelUpload = async (file: File) => {
    setUploading(true);
    setUploadMessage('Uploading Excel file...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/calls/bulk-upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setUploadMessage(`Successfully uploaded! Processed ${data.valid_rows} rows. Batch ID: ${data.batch_id}`);
      setTimeout(() => setUploadMessage(''), 5000);
    } catch (error) {
      setUploadMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => setUploadMessage(''), 5000);
    } finally {
      setUploading(false);
    }
  };

  const handleExcelDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverExcel(true);
  };

  const handleExcelDragLeave = () => {
    setDragOverExcel(false);
  };

  const handleExcelDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverExcel(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        handleExcelUpload(file);
      } else {
        setUploadMessage('Please upload an Excel file (.xlsx or .xls)');
      }
    }
  };

  const handleExcelFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        handleExcelUpload(file);
      } else {
        setUploadMessage('Please upload an Excel file (.xlsx or .xls)');
      }
    }
  };

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar h-full bg-[#F7F3F0] p-8 select-none">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header Block */}
        <section className="border-b border-[#1A1A1A]/10 pb-6">
          <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Ingestion Portal</span>
          <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Upload Clinical Consultation</h2>
          <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
            Securely upload medical audio recordings for automated clinical transcription, compliance auditing, and performance scoring.
          </p>
        </section>

        {/* Dynamic Multi-Pane Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          
          {/* Left Block: Upload Zone */}
          <div className="md:col-span-7 bg-white border border-[#1A1A1A]/10 p-8 space-y-6">
            <div className="border-b border-[#1A1A1A]/5 pb-4">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">Audio Ingestion</h3>
              <p className="text-xs text-[#1A1A1A]/60 mt-1">Select or drag standard therapeutic conversation audio recordings.</p>
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative border border-dashed p-10 text-center transition-all duration-300 cursor-pointer ${
                dragOver 
                  ? 'border-[#8B7E66] bg-[#FAF8F6]' 
                  : 'border-[#1A1A1A]/20 hover:border-[#8B7E66] hover:bg-[#FAF8F6]/40'
              }`}
            >
              <input
                type="file"
                accept=".mp3,.wav,.flac"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              <div className="w-14 h-14 bg-[#FAF8F6] border border-[#1A1A1A]/10 flex items-center justify-center mx-auto mb-4 transition-transform duration-300">
                <UploadCloud className="w-6 h-6 text-[#8B7E66]" />
              </div>

              <h4 className="text-base font-serif italic font-medium text-[#1A1A1A]">Choose Audio File</h4>
              <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5">
                Drag & drop or browse your local system
              </p>
              <p className="text-[9px] text-[#1A1A1A]/40 font-mono mt-2">
                Supported formats: MP3, WAV, FLAC (Max 500MB)
              </p>
            </div>

            {/* Protocol Notice */}
            <div className="bg-[#FAF8F6] border border-[#1A1A1A]/10 p-4 flex gap-3">
              <ShieldCheck className="w-5 h-5 text-[#8B7E66] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h5 className="text-[10px] font-sans font-bold text-[#1A1A1A] uppercase tracking-wider">HIPAA Encryption Protocol</h5>
                <p className="text-xs text-[#1A1A1A]/70 leading-relaxed">
                  All clinical conversations are processed with AES-256 end-to-end encryption. Personally identifiable health identifiers (PHI) are automatically scrubbed during the transcription stage.
                </p>
              </div>
            </div>

            {/* Excel Bulk Upload Section */}
            <div className="border-t border-[#1A1A1A]/5 pt-6">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A] mb-4">Bulk Excel Upload</h3>

              <div className="space-y-3">
                {/* Simple File Input */}
                <div className="bg-white border border-[#1A1A1A]/10 p-4">
                  <input
                    id="excel-file-input"
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleExcelFileChange}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-none file:border-0
                      file:text-sm file:font-semibold
                      file:bg-[#1A1A1A] file:text-white
                      hover:file:bg-[#8B7E66]
                      cursor-pointer"
                  />
                  <p className="text-xs text-[#1A1A1A]/60 mt-2">
                    Supported: XLSX, XLS, CSV files
                  </p>
                </div>

                {/* Drag & Drop Area */}
                <div
                  onDragOver={handleExcelDragOver}
                  onDragLeave={handleExcelDragLeave}
                  onDrop={handleExcelDrop}
                  className={`border border-dashed p-6 text-center transition-all duration-300 ${
                    dragOverExcel
                      ? 'border-[#8B7E66] bg-[#FAF8F6]'
                      : 'border-[#1A1A1A]/20'
                  }`}
                >
                  <FileText className="w-8 h-8 text-[#8B7E66] mx-auto mb-2" />
                  <p className="text-sm text-[#1A1A1A] font-medium">Or drag Excel file here</p>
                </div>

                {/* Status Message */}
                {uploadMessage && (
                  <div className={`p-3 rounded text-sm font-mono ${
                    uploadMessage.includes('Error') || uploadMessage.includes('Please')
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : 'bg-green-50 text-green-700 border border-green-200'
                  }`}>
                    {uploadMessage}
                  </div>
                )}

                {uploading && (
                  <div className="bg-blue-50 border border-blue-200 text-blue-700 p-3 rounded text-sm">
                    Uploading... Please wait
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Block: Process Status Queue */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A1A1A]/10 pb-3">
              <h3 className="text-xs font-sans font-bold uppercase tracking-[0.15em] text-[#1A1A1A]">Ingestion Queue</h3>
              <span className="px-2.5 py-0.5 border border-[#8B7E66]/30 bg-white text-[#8B7E66] text-[10px] font-mono font-bold uppercase tracking-wider">
                {activeQueue.length} Active
              </span>
            </div>

            {activeQueue.length === 0 ? (
              <div className="bg-white border border-[#1A1A1A]/10 p-8 text-center flex flex-col items-center justify-center min-h-[220px]">
                <FileCheck2 className="w-10 h-10 text-[#1A1A1A]/20 mb-3" />
                <h4 className="text-sm font-serif italic font-medium text-[#1A1A1A]">Queue is empty</h4>
                <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5 max-w-[200px] leading-relaxed mx-auto">
                  No active transcriptions are processing. Upload a file to see its live progress.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeQueue.map((item) => (
                  <div 
                    key={item.id} 
                    className="bg-white border border-[#1A1A1A]/10 p-4 space-y-3 shadow-sm hover:border-[#8B7E66] transition-colors"
                  >
                    {/* Header line */}
                    <div className="flex justify-between items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-serif font-semibold text-[#1A1A1A] truncate">{item.name}</p>
                        <p className="text-[9px] font-mono text-[#1A1A1A]/40 mt-0.5 uppercase">ID: {item.id}</p>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-[#8B7E66] shrink-0">
                        {item.status === 'waiting' ? 'QUEUED' : `${item.progress}%`}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/5 h-1.5 overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${
                          item.status === 'waiting' ? 'bg-[#1A1A1A]/20' : 'bg-[#8B7E66]'
                        }`} 
                        style={{ width: `${item.status === 'waiting' ? 10 : item.progress}%` }}
                      ></div>
                    </div>

                    {/* Status Text & Indicator */}
                    <div className="flex items-center justify-between text-[9px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/50">
                      <span className="flex items-center gap-1">
                        {item.status === 'processing' ? (
                          <Loader2 className="w-3 h-3 animate-spin text-[#8B7E66]" />
                        ) : (
                          <Clock className="w-3 h-3 text-[#1A1A1A]/40" />
                        )}
                        <span className="truncate max-w-[180px]">{item.statusText}</span>
                      </span>
                      <span className="text-[#1A1A1A]/40">{item.duration}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Ingestion Guidelines */}
            <div className="border border-[#1A1A1A]/10 p-4 space-y-2 bg-white">
              <div className="flex items-center gap-1.5 text-[#1A1A1A] mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-[#8B7E66]" />
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider">Troubleshooting Ingestion</span>
              </div>
              <ul className="space-y-1 text-[11px] text-[#1A1A1A]/60 leading-relaxed list-disc list-inside">
                <li>Processing times vary by audio length (~10s per minute).</li>
                <li>Ensure speaker clarity to maximize compliance score accuracy.</li>
                <li>Review finished consultations inside the Transcriptions tab.</li>
              </ul>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
