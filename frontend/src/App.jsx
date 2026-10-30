import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers } from 'lucide-react';

import ResumeUploader from './components/ResumeUploader';
import LinkDashboard from './components/LinkDashboard';
import InterviewConfigModal from './components/InterviewConfigModal';
import InterviewCockpit from './components/InterviewCockpit';
import FeedbackReport from './components/FeedbackReport';
import ErrorBoundary from './components/ErrorBoundary';
import { useInterview } from './hooks/useInterview';

function App() {
  const [appPhase, setAppPhase] = useState('UPLOAD'); // UPLOAD, INSPECT, CONFIG, INTERVIEW, REPORT
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const [inspectionResult, setInspectionResult] = useState(null);
  
  const interview = useInterview();

  const handleUploadComplete = (data) => {
    setResumeAnalysis(data);
    setAppPhase('INSPECT');
  };

  const handleInspectionComplete = (data) => {
    setInspectionResult(data);
    setAppPhase('CONFIG');
  };

  const handleStartInterview = async (config) => {
    try {
      setAppPhase('INTERVIEW');
      await interview.initSession(resumeAnalysis, inspectionResult, config);
    } catch (e) {
      console.error("Failed to start interview:", e);
      alert("Failed to start interview. Backend might be down.");
      setAppPhase('CONFIG');
    }
  };

  const handleInterviewComplete = async () => {
    setAppPhase('REPORT');
    await interview.getReport();
  };

  const handleRetry = () => {
    setAppPhase('UPLOAD');
    setResumeAnalysis(null);
    setInspectionResult(null);
  };

  // Header / Navigation
  const steps = [
    { id: 'UPLOAD', name: 'Upload Resume' },
    { id: 'INSPECT', name: 'Analyze Links' },
    { id: 'CONFIG', name: 'Setup Interview' },
    { id: 'INTERVIEW', name: 'Mock Interview' },
    { id: 'REPORT', name: 'Feedback' },
  ];

  const currentStepIndex = steps.findIndex(s => s.id === appPhase);

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-emerald-500/30">
      
      {/* Top Navbar */}
      <header className="flex-shrink-0 border-b border-slate-700/80 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 via-teal-400 to-amber-400 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/10">
              <Layers className="w-5 h-5 text-slate-950" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">ResumeGrind</span>
          </div>

          {/* Stepper */}
          <div className="hidden md:flex items-center space-x-2">
            {steps.map((step, index) => {
              const isActive = index === currentStepIndex;
              const isPast = index < currentStepIndex;
              return (
                <React.Fragment key={step.id}>
                  <div className="flex items-center">
                    <div className={`w-2.5 h-2.5 rounded-full transition-colors ${
                      isActive ? 'bg-emerald-400 ring-4 ring-emerald-400/20' :
                      isPast ? 'bg-emerald-500/50' : 'bg-slate-700'
                    }`} />
                    <span className={`ml-2 text-sm font-medium transition-colors ${
                      isActive ? 'text-white' : 
                      isPast ? 'text-slate-400' : 'text-slate-500'
                    }`}>
                      {step.name}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-8 h-px mx-2 ${isPast ? 'bg-emerald-500/30' : 'bg-slate-800'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content Area with Error Boundary */}
      <main className="flex-1 flex flex-col items-center justify-center relative">
        <ErrorBoundary onReset={handleRetry}>
          <AnimatePresence mode="wait">
            {appPhase === 'UPLOAD' && (
              <motion.div 
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="w-full flex-1 flex items-center"
              >
                <ResumeUploader onUploadComplete={handleUploadComplete} />
              </motion.div>
            )}

            {appPhase === 'INSPECT' && (
              <motion.div 
                key="inspect"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="w-full flex-1 py-12"
              >
                <LinkDashboard 
                  resumeAnalysis={resumeAnalysis} 
                  onInspectionComplete={handleInspectionComplete} 
                />
              </motion.div>
            )}

            {appPhase === 'CONFIG' && (
              <motion.div 
                key="config"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="w-full flex-1 py-8"
              >
                <InterviewConfigModal 
                  onStart={handleStartInterview}
                  onBack={() => setAppPhase('INSPECT')}
                />
              </motion.div>
            )}

            {appPhase === 'INTERVIEW' && (
              <motion.div 
                key="interview"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05 }}
                className="w-full flex-1"
              >
                {interview.isLoading && interview.phase === 'generating' ? (
                  <div className="h-full flex flex-col items-center justify-center space-y-4 min-h-[350px]">
                    <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-emerald-400 font-medium">AI is generating your custom interview...</p>
                  </div>
                ) : (
                  <InterviewCockpit 
                    interview={interview} 
                    onComplete={handleInterviewComplete} 
                  />
                )}
              </motion.div>
            )}

            {appPhase === 'REPORT' && (
              <motion.div 
                key="report"
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -50 }}
                className="w-full flex-1 py-12"
              >
                <FeedbackReport report={interview.report} onRetry={handleRetry} />
              </motion.div>
            )}
          </AnimatePresence>
        </ErrorBoundary>
      </main>
      
    </div>
  );
}

export default App;
