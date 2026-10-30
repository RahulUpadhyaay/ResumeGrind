import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, Loader2, Link as LinkIcon, Code } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { uploadResume } from '../api/client';

export default function ResumeUploader({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (file) => {
    setError('');
    if (!file) return;
    
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a PDF or DOCX file.');
      return;
    }
    
    setFile(file);
    uploadFile(file);
  };

  const uploadFile = async (selectedFile) => {
    setIsUploading(true);
    try {
      const data = await uploadResume(selectedFile);
      // Wait a moment for UX before moving on
      setTimeout(() => {
        onUploadComplete(data);
      }, 1000);
    } catch (err) {
      console.error(err);
      setError('Failed to upload and parse resume. Please try again.');
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto w-full p-6">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-400 to-amber-400">
          Prepare for Reality
        </h1>
        <p className="text-slate-300 text-lg">
          Upload your resume to start an AI-driven mock interview tailored to your experience.
        </p>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
          isDragging 
            ? 'border-emerald-500 bg-emerald-500/10' 
            : file 
              ? 'border-emerald-500/50 bg-slate-800/80' 
              : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/60'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.docx"
        />

        <AnimatePresence mode="wait">
          {!file ? (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mb-6 shadow-lg border border-slate-700">
                <Upload className="w-10 h-10 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Click or drag file to upload</h3>
              <p className="text-slate-300 text-sm">PDF or DOCX (Max 5MB)</p>
            </motion.div>
          ) : (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center"
            >
              <div className="relative mb-6">
                <FileText className={`w-16 h-16 text-emerald-400 ${isUploading ? 'animate-pulse' : ''}`} />
                {isUploading && (
                  <div className="absolute -inset-4 border-2 border-emerald-500 rounded-full animate-ping opacity-20"></div>
                )}
              </div>
              
              <h3 className="text-xl font-medium text-white mb-4">
                {file.name}
              </h3>

              {isUploading ? (
                <div className="flex items-center text-emerald-400 space-x-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Extracting skills and links...</span>
                </div>
              ) : (
                <div className="flex items-center text-emerald-400 space-x-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Analysis Complete!</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-center"
        >
          {error}
        </motion.div>
      )}
    </div>
  );
}
