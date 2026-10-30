import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, X, CheckCircle, Table, Cpu, Lightbulb, FileText, Layers } from 'lucide-react';

/**
 * LearningCard Component
 * 
 * WHY: Teaches the user the full technical concept using BOTH comprehensive theory
 * (mechanics, real-world case studies, common interview pitfalls) AND visual charts
 * (ASCII architecture diagrams, comparison tables, and takeaways).
 */
export default function LearningCard({ concept, onClose }) {
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'theory' | 'chart' | 'table' | 'resume'

  if (!concept) return null;

  const { concept_title, summary, theory, table_markdown, diagram_ascii, key_takeaways, resume_project_connection } = concept;

  // Simple Markdown Table parser for clean visual display
  const renderTable = (md) => {
    if (!md) return null;
    const rows = md.trim().split('\n').filter(r => r.includes('|') && !r.includes('---'));
    if (rows.length < 1) return <pre className="text-xs text-slate-300 font-mono">{md}</pre>;

    const headerCells = rows[0].split('|').map(c => c.trim()).filter(c => c);
    const bodyRows = rows.slice(1).map(r => r.split('|').map(c => c.trim()).filter(c => c));

    return (
      <div className="overflow-x-auto rounded-xl border border-slate-700/80 bg-slate-950/90 shadow-inner">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900 border-b border-slate-700 text-slate-200">
              {headerCells.map((h, i) => (
                <th key={i} className="p-3 font-semibold uppercase tracking-wider text-[11px] text-emerald-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {bodyRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-900/60 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="p-3 text-slate-200 font-mono text-xs">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="bg-slate-900/95 border border-slate-700/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden flex flex-col max-h-[85vh] overflow-y-auto scrollbar-custom"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-400 to-amber-400" />

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
              Technical Concept Masterclass
            </span>
            <h3 className="text-xl font-bold text-white mt-1 tracking-tight">{concept_title}</h3>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          title="Close learning card"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 mb-4 text-xs">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            activeTab === 'all' ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          All-In-One
        </button>
        <button
          onClick={() => setActiveTab('theory')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            activeTab === 'theory' ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Core Theory</span>
        </button>
        <button
          onClick={() => setActiveTab('chart')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            activeTab === 'chart' ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Architecture Chart</span>
        </button>
        <button
          onClick={() => setActiveTab('table')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            activeTab === 'table' ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Table className="w-3.5 h-3.5" />
          <span>Trade-Offs Table</span>
        </button>
        {resume_project_connection && (
          <button
            onClick={() => setActiveTab('resume')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
              activeTab === 'resume' ? 'bg-amber-400 text-slate-950' : 'text-amber-300 hover:text-amber-200 hover:bg-amber-950/40 border border-amber-500/30'
            }`}
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Answer with Your Project</span>
          </button>
        )}
      </div>

      {/* Summary */}
      <p className="text-xs text-slate-200 leading-relaxed mb-5 bg-slate-950/80 p-4 rounded-xl border border-slate-800 shadow-sm">
        {summary}
      </p>

      {/* Resume Project Grounded Answer Hint */}
      {resume_project_connection && (
        <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-amber-950/50 via-slate-900 to-emerald-950/40 border border-amber-500/40 shadow-lg">
          <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            💡 How to Answer Using Your Resume Project:
          </h4>
          <p className="text-xs text-amber-100/90 leading-relaxed font-sans whitespace-pre-line">
            {resume_project_connection}
          </p>
        </div>
      )}

      {/* 1. Theory Section */}
      {(activeTab === 'all' || activeTab === 'theory') && (
        <div className="mb-6">
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            1. Theoretical Foundation & Mechanics
          </h4>
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed whitespace-pre-line space-y-3 font-sans">
            {theory || (
              <>
                <p><strong className="text-white">Under the Hood:</strong> {concept_title} balances system state across processing boundaries to guarantee low latency and fault isolation.</p>
                <p><strong className="text-white">Industry Application:</strong> Used extensively in distributed services to prevent bottlenecking and reduce server load.</p>
                <p><strong className="text-white">Common Pitfalls:</strong> Avoid ignoring cache stampedes, stale data, and synchronization latency.</p>
              </>
            )}
          </div>
        </div>
      )}

      {/* 2. ASCII Architecture Diagram */}
      {(activeTab === 'all' || activeTab === 'chart') && diagram_ascii && (
        <div className="mb-6">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            2. System Architecture & Flow Chart
          </h4>
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-emerald-400 leading-relaxed overflow-x-auto whitespace-pre shadow-inner">
            {diagram_ascii}
          </div>
        </div>
      )}

      {/* 3. Comparison Table */}
      {(activeTab === 'all' || activeTab === 'table') && table_markdown && (
        <div className="mb-6">
          <h4 className="text-xs font-bold text-teal-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Table className="w-3.5 h-3.5 text-teal-400" />
            3. Engineering Trade-Offs & Comparison Matrix
          </h4>
          {renderTable(table_markdown)}
        </div>
      )}

      {/* 4. Key Takeaways */}
      {key_takeaways && key_takeaways.length > 0 && (
        <div className="pt-2">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            Key Interview Takeaways
          </h4>
          <ul className="space-y-2">
            {key_takeaways.map((point, idx) => (
              <li key={idx} className="flex items-start text-xs text-slate-200 gap-2.5 bg-slate-950/40 p-2 rounded-lg border border-slate-800/60">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
