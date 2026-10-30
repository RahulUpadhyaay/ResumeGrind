import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Flame, HeartHandshake, Briefcase, Globe, Sparkles, ArrowRight, ShieldAlert, Cpu, Target, FileText } from 'lucide-react';

const LANGUAGES = [
  { id: 'en', name: 'English', flag: '🇬🇧', desc: 'Standard technical English' },
  { id: 'hi', name: 'Hindi / Hinglish', flag: '🇮🇳', desc: 'Natural Hindi/English tech mix' },
  { id: 'es', name: 'Español', flag: '🇪🇸', desc: 'Spanish technical interview' },
  { id: 'fr', name: 'Français', flag: '🇫🇷', desc: 'French technical interview' },
  { id: 'de', name: 'Deutsch', flag: '🇩🇪', desc: 'German technical interview' },
];

const PERSONAS = [
  {
    id: 'strict_roast',
    name: 'Strict Professor (Scolding Roast)',
    badge: 'Popular & Brutal',
    badgeColor: 'bg-red-500/20 text-red-400 border-red-500/30',
    icon: Flame,
    iconColor: 'text-red-400 bg-red-500/10 border-red-500/20',
    description: 'An authoritative Computer Science professor who scolds buzzwords, calls out superficial answers, and tests your real engineering depth like a teacher reprimanding an unprepared student.',
    quote: '"What kind of careless answer is that? Did you even read the documentation before speaking? Listen carefully!"'
  },
  {
    id: 'friendly',
    name: 'Friendly Mentor',
    badge: 'Supportive & Educational',
    badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    icon: HeartHandshake,
    iconColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    description: 'An empathetic engineering lead who coaches you, celebrates good design thinking, and guides you with warm constructive hints.',
    quote: '"Great attempt! Let\'s think about how we can optimize this further together."'
  },
  {
    id: 'professional',
    name: 'Standard FAANG',
    badge: 'Formal & Objective',
    badgeColor: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
    icon: Briefcase,
    iconColor: 'text-teal-300 bg-teal-500/10 border-teal-500/20',
    description: 'A structured, formal technical evaluation focused strictly on algorithmic complexity, latency metrics, and architectural trade-offs.',
    quote: '"What is the algorithmic complexity and worst-case memory profile?"'
  }
];

export default function InterviewConfigModal({ onStart, onBack }) {
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedPersona, setSelectedPersona] = useState('strict_roast');
  const [selectedProvider, setSelectedProvider] = useState('gemini');
  const [targetRole, setTargetRole] = useState('Senior Software Engineer');
  const [targetJD, setTargetJD] = useState('');

  const handleStart = () => {
    onStart({
      language: selectedLang,
      persona: selectedPersona,
      provider: selectedProvider,
      target_role: targetRole,
      target_job_description: targetJD
    });
  };


  return (
    <div className="max-w-4xl mx-auto w-full p-4 md:p-6 pb-12">
      <div className="text-center mb-8">
        <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 inline-block mb-3">
          Configure Your Session
        </span>
        <h2 className="text-3xl font-extrabold text-white tracking-tight mb-2">
          Customize Your Interview Experience
        </h2>
        <p className="text-slate-400 text-sm max-w-lg mx-auto">
          Select your interview language and interviewer personality. The AI voice, cross-questioning style, and feedback will adapt to your choices.
        </p>
      </div>

      {/* Language Selection */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 mb-6 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Globe className="w-4 h-4 text-emerald-400" />
          1. Select Interview Language
        </h3>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {LANGUAGES.map((lang) => {
            const isSelected = selectedLang === lang.id;
            return (
              <button
                key={lang.id}
                onClick={() => setSelectedLang(lang.id)}
                className={`p-3.5 rounded-xl border text-left transition-all relative ${
                  isSelected
                    ? 'bg-emerald-500/15 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400'
                }`}
              >
                <div className="text-2xl mb-1.5">{lang.flag}</div>
                <div className={`font-semibold text-xs ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                  {lang.name}
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5">{lang.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Persona Selection */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 mb-6 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          2. Choose Interviewer Persona
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PERSONAS.map((p) => {
            const isSelected = selectedPersona === p.id;
            const Icon = p.icon;

            return (
              <div
                key={p.id}
                onClick={() => setSelectedPersona(p.id)}
                className={`cursor-pointer p-5 rounded-2xl border transition-all flex flex-col justify-between relative ${
                  isSelected
                    ? 'bg-slate-800/90 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.15)] ring-1 ring-emerald-400'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2.5 rounded-xl border ${p.iconColor}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${p.badgeColor}`}>
                      {p.badge}
                    </span>
                  </div>

                  <h4 className="font-bold text-white text-base mb-1">{p.name}</h4>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">{p.description}</p>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 text-[11px] text-slate-300 italic">
                  {p.quote}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Model Provider Selection */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          3. Select AI Model Engine (Strategy Gateway)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { id: 'gemini', name: 'Google Gemini 3.6 Flash', speed: 'Standard Cloud', icon: '🧠', badge: 'Default', color: 'border-cyan-500/30' },
            { id: 'groq', name: 'Groq (Llama 3.3 70B)', speed: 'Ultra-Fast 200ms', icon: '⚡', badge: 'High Speed', color: 'border-amber-500/30' },
            { id: 'ollama_local', name: 'ResumeGrind Custom Model', speed: 'Local Fine-Tuned Llama3', icon: '🏆', badge: '100% Privacy', color: 'border-emerald-500/30' },
          ].map((provider) => {
            const isSelected = selectedProvider === provider.id;
            return (
              <div
                key={provider.id}
                onClick={() => setSelectedProvider(provider.id)}
                className={`cursor-pointer p-4 rounded-xl border transition-all text-left ${
                  isSelected
                    ? 'bg-cyan-500/15 border-cyan-400 ring-1 ring-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xl">{provider.icon}</span>
                  <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
                    {provider.badge}
                  </span>
                </div>
                <div className="font-bold text-white text-xs mb-0.5">{provider.name}</div>
                <div className="text-[10px] text-cyan-400 font-mono">{provider.speed}</div>
              </div>
            );
          })}
        </div>
      </div>


      {/* Target Role & Job Description Alignment */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
          <Target className="w-4 h-4 text-emerald-400" />
          4. Target Role & Job Description (ATS & Alignment Gap)
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Tailor interview cross-examination directly against the expectations of your dream job.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Target Position / Level
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Backend Engineer (L5), Staff ML Engineer, Full Stack Architect"
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
              <span>Paste Job Description (Optional)</span>
              <span className="text-[10px] text-slate-500">Enables dynamic gap analysis</span>
            </label>
            <textarea
              rows={3}
              value={targetJD}
              onChange={(e) => setTargetJD(e.target.value)}
              placeholder="Paste key requirements or responsibilities from the job posting (e.g., Go, Kubernetes, high-throughput streaming systems, Redis caching)..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 resize-none font-mono"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-xs text-slate-500 hover:text-slate-300 px-4 py-2 transition-colors font-medium"
        >
          ← Back to Links
        </button>

        <button
          onClick={handleStart}
          className="flex items-center space-x-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-8 py-4 rounded-xl text-base transition-all shadow-[0_0_25px_rgba(16,185,129,0.3)] hover:-translate-y-0.5"
        >
          <span>Launch AI Interview Studio</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
