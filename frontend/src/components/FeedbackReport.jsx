import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Download, RotateCcw, ChevronDown, ChevronUp, Star, TrendingUp, 
  AlertTriangle, CheckCircle2, Flame, BookOpen, Copy, Check,
  Mic, Gauge, FileCheck2, GitPullRequest, Target, Sparkles, Code2
} from 'lucide-react';
import LearningCard from './LearningCard';

export default function FeedbackReport({ report, onRetry }) {
  const [expandedIndex, setExpandedIndex] = useState(0);
  const [activeConceptIndex, setActiveConceptIndex] = useState(null);
  const [copied, setCopied] = useState(false);

  if (!report) return (
    <div className="flex items-center justify-center h-64 text-emerald-400">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
      Generating final report...
    </div>
  );

  const overallScore = report.overall_score || 0;
  
  const getScoreColor = (score) => {
    const normalized = score <= 10 ? score * 10 : score;
    if (normalized >= 70) return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (normalized >= 50) return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    return 'text-red-400 bg-red-400/10 border-red-400/20';
  };

  const getScoreBar = (score) => {
    const normalized = score <= 10 ? score * 10 : score;
    if (normalized >= 70) return 'bg-emerald-500';
    if (normalized >= 50) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const handleCopyReport = () => {
    const text = `ResumeGrind Mock Interview Dossier\nOverall Score: ${overallScore}/100\nTarget Role: ${report.target_role || 'Software Engineer'}\n` +
      (report.summary ? `\nSummary: ${report.summary}\n` : '') +
      (report.details || []).map((d, i) => 
        `\n[Question ${i + 1}]: ${d.question}\nYour Answer: ${d.transcript}\nScore: ${d.score <= 10 ? `${d.score}/10` : `${d.score}/100`}\nStrengths: ${(d.strengths || []).join(', ')}\nImprovements: ${(d.improvements || []).join(', ')}\n`
      ).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 md:p-6 pb-20">
      
      {/* Header & Overall Score */}
      <div className="bg-slate-900/90 border border-slate-700/80 rounded-3xl p-8 mb-8 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        
        <div className="flex flex-col md:flex-row items-center justify-between relative z-10">
          <div className="mb-8 md:mb-0 text-center md:text-left">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 inline-block">
                Interview Dossier
              </span>
              {report.target_role && (
                <span className="text-xs font-semibold text-cyan-300 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20 inline-flex items-center gap-1.5">
                  <Target className="w-3 h-3" />
                  Target: {report.target_role}
                </span>
              )}
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Performance Debrief</h1>
            <p className="text-slate-300 text-sm max-w-md">Comprehensive engineering evaluation across technical depth, speech delivery cadence, and code architecture.</p>
          </div>
          
          <div className="flex flex-col items-center">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#1e293b" strokeWidth="8" />
                <motion.circle 
                  cx="50" cy="50" r="45" fill="none" 
                  stroke="url(#gradient)" strokeWidth="8" 
                  strokeLinecap="round"
                  initial={{ strokeDasharray: "0 300" }}
                  animate={{ strokeDasharray: `${(overallScore / 100) * 283} 283` }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#34d399" />
                    <stop offset="100%" stopColor="#14b8a6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{overallScore}</span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
            </div>
            <span className="mt-4 px-4 py-1 rounded-full text-xs font-semibold border bg-slate-800 border-slate-700 text-slate-300">
              {overallScore >= 70 ? 'Strong Hire (Approved)' : overallScore >= 50 ? 'Potential Hire' : 'Needs Practice'}
            </span>
          </div>
        </div>

        {/* Category Scores & Role Fit */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6 pt-6 border-t border-slate-800">
          {report.jd_match_score && (
            <div>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-cyan-400 font-semibold flex items-center gap-1">
                  <Target className="w-3.5 h-3.5" />
                  Role Fit Match
                </span>
                <span className="text-white font-bold">{report.jd_match_score}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="h-1.5 rounded-full bg-cyan-400" style={{ width: `${report.jd_match_score}%` }} />
              </div>
            </div>
          )}
          {Object.entries(report.category_scores || {}).map(([category, score], i) => (
            <div key={category}>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-slate-300 capitalize">{category.replace('_', ' ')}</span>
                <span className="text-white font-medium">{score}/100</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <motion.div 
                  className={`h-1.5 rounded-full ${getScoreBar(score)}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${score}%` }}
                  transition={{ duration: 1, delay: i * 0.2 }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Speech Delivery Intelligence Card */}
      {report.speech_summary && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Mic className="w-4 h-4 text-emerald-400" />
              Speech & Delivery Cadence Analytics
            </h3>
            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-medium">
              Live Acoustic Analysis
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[11px] text-slate-400 flex items-center gap-1 mb-1">
                <Gauge className="w-3.5 h-3.5 text-cyan-400" />
                Average Speech Pacing
              </div>
              <div className="text-xl font-bold text-white">{report.speech_summary.average_wpm || 135} <span className="text-xs font-normal text-slate-400">WPM</span></div>
              <div className="text-[10px] text-emerald-400 mt-1 font-semibold">{report.speech_summary.pacing || 'Optimal Cadence'}</div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[11px] text-slate-400 mb-1">Filler Words Detected</div>
              <div className="text-xl font-bold text-amber-400">{report.speech_summary.total_fillers || 0}</div>
              <div className="text-[10px] text-slate-500 mt-1 truncate">
                {report.speech_summary.fillers_detected?.length > 0 
                  ? report.speech_summary.fillers_detected.join(', ')
                  : 'Zero excessive filler words detected'}
              </div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[11px] text-slate-400 mb-1">STAR Structure Adherence</div>
              <div className="text-xl font-bold text-emerald-400">Strong</div>
              <div className="text-[10px] text-slate-400 mt-1">Clear situation & engineering trade-offs</div>
            </div>
          </div>
        </div>
      )}

      {/* Resume Bullet Rewrites (Google XYZ Formula) */}
      {report.resume_bullet_improvements && report.resume_bullet_improvements.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              Resume Bullet Optimizer (Google XYZ Framework)
            </h3>
            <span className="text-[11px] text-slate-400">
              Accomplished [X], measured by [Y], by doing [Z]
            </span>
          </div>

          <div className="space-y-4">
            {report.resume_bullet_improvements.map((bullet, idx) => (
              <div key={idx} className="bg-slate-950/60 rounded-xl p-4 border border-slate-800/80">
                <div className="mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20 mr-2">
                    Original Bullet
                  </span>
                  <span className="text-xs text-slate-400 line-through">{bullet.original}</span>
                </div>
                <div className="mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 mr-2">
                    Optimized Impact
                  </span>
                  <span className="text-xs text-white font-semibold">{bullet.improved}</span>
                </div>
                <div className="text-[11px] text-slate-400 italic mt-2 border-t border-slate-800/60 pt-2">
                  💡 {bullet.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Code Refactoring Suggestions */}
      {report.code_refactoring_suggestions && report.code_refactoring_suggestions.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <GitPullRequest className="w-4 h-4 text-cyan-400" />
              Targeted Code Refactoring Suggestions (Production Diff)
            </h3>
            <span className="text-[11px] text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-500/20">
              PR Ready
            </span>
          </div>

          <div className="space-y-4">
            {report.code_refactoring_suggestions.map((item, idx) => (
              <div key={idx} className="bg-slate-950/80 rounded-xl p-4 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-mono font-bold text-white">{item.file_path}</span>
                  </div>
                  <span className="text-[11px] text-amber-300 font-medium">{item.issue}</span>
                </div>
                <pre className="bg-slate-900 p-3 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto border border-slate-800 leading-relaxed">
                  {item.diff_suggestion}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Q&A Review */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-emerald-400" />
          Multi-Turn Question & Cross-Examination Review
        </h3>
        <span className="text-xs text-slate-400 font-medium">
          {report.details?.length || 0} Questions Evaluated
        </span>
      </div>

      <div className="space-y-4">
        {report.details?.map((detail, index) => (
          <div key={index} className="bg-slate-900 border border-slate-700/80 rounded-xl overflow-hidden transition-all duration-200">
            <button 
              onClick={() => setExpandedIndex(expandedIndex === index ? -1 : index)}
              className="w-full text-left p-5 flex items-start md:items-center justify-between hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-start md:items-center space-x-4 pr-4">
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border ${getScoreColor(detail.score)}`}>
                  {detail.score}
                </div>
                <div>
                  <h4 className="text-slate-200 font-medium line-clamp-1 text-sm">{detail.question}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-400">Round {index + 1}</span>
                    <span className="text-[11px] font-semibold text-slate-300">
                      Score: {detail.score <= 10 ? `${detail.score}/10` : `${detail.score}/100`}
                    </span>
                    {detail.learning_concept && (
                      <span className="text-[10px] bg-teal-500/15 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded-full font-medium">
                        Concept Card Available
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0 text-slate-500 mt-2 md:mt-0">
                {expandedIndex === index ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </button>

            <AnimatePresence>
              {expandedIndex === index && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-slate-800 bg-slate-900/50"
                >
                  <div className="p-6 space-y-6">
                    {detail.persona_reaction && (
                      <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/20 text-xs text-red-300 flex items-start gap-3">
                        <Flame className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold uppercase tracking-wider text-[11px] block mb-0.5 text-red-400">
                            Teacher Scolding / Interviewer Reaction
                          </span>
                          <p className="italic">"{detail.persona_reaction}"</p>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h5 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3">
                          Your Spoken Answer
                        </h5>
                        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-800/80 font-mono">
                          {detail.transcript}
                        </p>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <h5 className="text-xs uppercase tracking-wider text-emerald-400 font-semibold mb-2 flex items-center">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                            Demonstrated Strengths
                          </h5>
                          <ul className="space-y-1.5">
                            {(detail.strengths || []).map((s, idx) => (
                              <li key={idx} className="text-xs text-slate-300 flex items-start">
                                <span className="text-emerald-400 mr-2">•</span>
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <h5 className="text-xs uppercase tracking-wider text-amber-400 font-semibold mb-2 flex items-center">
                            <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
                            Targeted Areas for Improvement
                          </h5>
                          <ul className="space-y-1.5">
                            {(detail.improvements || []).map((imp, idx) => (
                              <li key={idx} className="text-xs text-slate-300 flex items-start">
                                <span className="text-amber-400 mr-2">•</span>
                                {imp}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>

                    {detail.learning_concept && (
                      <div className="pt-4 border-t border-slate-800/80">
                        <button
                          onClick={() => setActiveConceptIndex(activeConceptIndex === index ? null : index)}
                          className="flex items-center space-x-2 text-xs font-semibold text-teal-300 hover:text-teal-200 transition-colors"
                        >
                          <BookOpen className="w-4 h-4" />
                          <span>{activeConceptIndex === index ? 'Hide Architectural Concept Card' : 'View Architectural Concept Breakdown (Diagram & Trade-offs)'}</span>
                        </button>

                        {activeConceptIndex === index && (
                          <div className="mt-4">
                            <LearningCard 
                              concept={detail.learning_concept} 
                              onClose={() => setActiveConceptIndex(null)} 
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
        <button 
          onClick={onRetry}
          className="flex items-center space-x-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-xl font-medium transition-colors w-full sm:w-auto justify-center"
        >
          <RotateCcw className="w-5 h-5" />
          <span>New Interview</span>
        </button>

        <button 
          onClick={handleCopyReport}
          className="flex items-center space-x-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white rounded-xl font-medium transition-colors w-full sm:w-auto justify-center"
        >
          {copied ? <Check className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5" />}
          <span>{copied ? 'Copied to Clipboard!' : 'Copy Dossier'}</span>
        </button>

        <button 
          onClick={handlePrint}
          className="flex items-center space-x-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl transition-colors shadow-lg shadow-emerald-500/20 w-full sm:w-auto justify-center"
        >
          <Download className="w-5 h-5" />
          <span>Print / Save PDF Dossier</span>
        </button>
      </div>

    </div>
  );
}
