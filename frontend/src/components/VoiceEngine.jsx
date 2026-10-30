import React from 'react';
import { Mic, MicOff, Volume2, AlertCircle, Edit3, ShieldCheck, RotateCcw, Activity, Loader2, Send, Terminal } from 'lucide-react';

/**
 * VoiceEngine Component
 * 
 * WHY: Provides microphone input with real-time hardware volume meter,
 * live speech transcription streaming, editable answer box, submission validation,
 * and clear status alerts.
 */
export default function VoiceEngine({ 
  isListening, 
  isSpeaking, 
  transcript, 
  setTranscript,
  startListening, 
  stopListening,
  onSubmitAnswer,
  isSubmitting = false,
  clearTranscript,
  phase,
  speechError,
  micPermission,
  requestMicPermission,
  audioLevel = 0
}) {
  const isEvaluating = phase === 'evaluating' || isSubmitting;

  const handleSubmitClick = () => {
    if (isEvaluating) return;
    if (onSubmitAnswer) {
      onSubmitAnswer();
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-5 relative overflow-hidden shadow-xl">
      {/* Top Border Indicator */}
      <div className={`absolute top-0 left-0 w-full h-1 transition-all duration-500 ${
        isSpeaking ? 'bg-teal-400 shadow-[0_0_20px_rgba(20,184,166,0.8)]' :
        isListening ? 'bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.8)]' :
        isEvaluating ? 'bg-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.8)]' :
        'bg-slate-800'
      }`} />

      {/* Permission Request Alert if not granted yet */}
      {micPermission !== 'granted' && (
        <div className="mb-4 p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
              <Mic className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">Microphone Permission Required</h4>
              <p className="text-[11px] text-slate-400">Allow microphone access to enable real-time speech recognition.</p>
            </div>
          </div>
          <button
            onClick={requestMicPermission}
            className="flex items-center space-x-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2 rounded-lg text-xs transition-all shadow-md"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Allow Microphone</span>
          </button>
        </div>
      )}

      {/* Header with audio state & live volume meter */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="relative">
            {isSpeaking ? (
              <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center">
                <Volume2 className="w-5 h-5 text-teal-300 animate-pulse" />
              </div>
            ) : isListening ? (
              <div className={`w-10 h-10 rounded-xl border flex items-center justify-center transition-all ${
                audioLevel > 10 ? 'bg-emerald-500/30 border-emerald-400' : 'bg-emerald-500/10 border-emerald-500/30'
              }`}>
                <Mic className="w-5 h-5 text-emerald-400" />
                <div className="absolute inset-0 border-2 border-emerald-500 rounded-xl animate-ping opacity-25"></div>
              </div>
            ) : isEvaluating ? (
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                <MicOff className="w-5 h-5 text-slate-400" />
              </div>
            )}
          </div>
          
          <div>
            <h3 className="font-semibold text-sm text-white flex items-center gap-2">
              {isSpeaking ? 'AI is speaking question aloud...' : 
               isListening ? (audioLevel > 5 ? '🎙️ Voice Detected — Listening...' : 'Listening for your voice...') : 
               isEvaluating ? 'Evaluating and recording your response...' :
               'Microphone Ready'}
            </h3>
            <p className="text-xs text-slate-400">
              {isSpeaking ? 'Listen carefully to the question before speaking' : 
               isListening ? 'Speak naturally — your audio volume meter is shown on the right' : 
               isEvaluating ? 'Please wait while your answer is evaluated...' :
               'Click "Start Answering (Mic)" or type directly in the box below'}
            </p>
          </div>
        </div>

        {/* Live Audio Visualizer (Uses real physical decibel volume when listening!) */}
        <div className="flex items-center space-x-1 h-7">
          {[1, 2, 3, 4, 5, 6].map((i) => {
            const barHeight = isSpeaking 
              ? Math.min(28, 8 + (i % 3) * 8) 
              : isListening 
                ? Math.min(28, Math.max(6, (audioLevel / 100) * 28 * (1 + (i % 3) * 0.2)))
                : 6;

            return (
              <div 
                key={i}
                className={`w-1.5 rounded-full transition-all duration-75 ${
                  isSpeaking ? 'bg-teal-400' : 
                  isListening && audioLevel > 5 ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
                  isListening ? 'bg-emerald-500/50' : 
                  'bg-slate-800'
                }`}
                style={{ height: `${barHeight}px` }}
              />
            );
          })}
        </div>
      </div>

      {/* Permission or Speech Error Banner */}
      {speechError && (
        <div className="mb-3 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start text-red-400 text-xs space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold">Notice: </span>
            {speechError}
          </div>
        </div>
      )}

      {/* Quick Cockpit Directives / Commands */}
      <div className="flex items-center gap-1.5 mb-2.5 overflow-x-auto pb-1 text-[11px] scrollbar-none">
        <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1 mr-1">
          <Terminal className="w-3 h-3 text-indigo-400" />
          Directives:
        </span>
        <button 
          type="button"
          disabled={isEvaluating}
          onClick={() => onSubmitAnswer && onSubmitAnswer("COMMAND: Let's move on to DSA")}
          className="px-2.5 py-1 bg-indigo-500/15 hover:bg-indigo-500/25 disabled:opacity-50 text-indigo-300 border border-indigo-500/30 rounded-lg font-medium transition-all flex items-center gap-1 shadow-sm whitespace-nowrap active:scale-95"
          title="Switch immediately to live DSA coding assessment"
        >
          💻 Switch to DSA
        </button>
        <button 
          type="button"
          disabled={isEvaluating}
          onClick={() => onSubmitAnswer && onSubmitAnswer("COMMAND: Let's move to System Design")}
          className="px-2.5 py-1 bg-purple-500/15 hover:bg-purple-500/25 disabled:opacity-50 text-purple-300 border border-purple-500/30 rounded-lg font-medium transition-all flex items-center gap-1 shadow-sm whitespace-nowrap active:scale-95"
          title="Switch directly to High-Scale Distributed System Design"
        >
          🏗️ System Design
        </button>
        <button 
          type="button"
          disabled={isEvaluating}
          onClick={() => onSubmitAnswer && onSubmitAnswer("COMMAND: Next Question")}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 border border-slate-700 rounded-lg font-medium transition-all flex items-center gap-1 shadow-sm whitespace-nowrap active:scale-95"
          title="Gracefully advance to next engineering domain"
        >
          ⏭️ Next Topic
        </button>
      </div>

      {/* Live Transcript / Input Area */}
      <div className="bg-slate-950/80 rounded-xl p-3 border border-slate-800 relative">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Edit3 className="w-3 h-3 text-slate-500" />
            Your Answer (Spoken or Typed)
          </span>
          <div className="flex items-center space-x-3">
            {transcript && !isEvaluating && (
              <button
                onClick={clearTranscript}
                className="text-[10px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors font-medium"
                title="Clear and restart answer"
              >
                <RotateCcw className="w-2.5 h-2.5" />
                <span>Reset Box</span>
              </button>
            )}
            {isListening && (
              <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Microphone Active
              </span>
            )}
          </div>
        </div>

        <textarea 
          value={transcript}
          disabled={isEvaluating}
          onChange={(e) => setTranscript && setTranscript(e.target.value)}
          placeholder={isListening ? "Listening... speak now! Your words are appearing in real-time." : "Click 'Start Answering (Mic)' to speak, or type your answer directly into this editor."}
          rows={3}
          className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 focus:outline-none resize-none leading-relaxed disabled:opacity-50"
        />
      </div>

      {/* Action Controls */}
      <div className="mt-3.5 flex items-center justify-between">
        <span className="text-xs text-slate-300">
          {isListening ? (
            <span className="text-emerald-400 flex items-center gap-1 font-medium">
              <Activity className="w-3 h-3 animate-pulse" /> Recording your voice...
            </span>
          ) : isEvaluating ? (
            <span className="text-amber-400 flex items-center gap-1 font-medium">
              <Loader2 className="w-3 h-3 animate-spin" /> Saving answer & evaluating...
            </span>
          ) : (
            'Ready to answer question'
          )}
        </span>

        <div className="flex items-center space-x-2.5">
          {isListening ? (
            <button 
              onClick={handleSubmitClick}
              disabled={isEvaluating}
              className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl font-semibold text-xs transition-all shadow-md shadow-red-500/20"
            >
              <div className="w-2 h-2 rounded-full bg-white animate-ping"></div>
              <span>Stop & Submit Answer</span>
            </button>
          ) : (
            <button 
              onClick={startListening}
              disabled={isEvaluating}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition-all ${
                isEvaluating
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-emerald-500 text-slate-950 hover:bg-emerald-400 shadow-md shadow-emerald-500/20 hover:-translate-y-0.5'
              }`}
            >
              <Mic className="w-4 h-4" />
              <span>Start Answering (Mic)</span>
            </button>
          )}

          {!isListening && (
            <button 
              onClick={handleSubmitClick}
              disabled={isEvaluating || !transcript || !transcript.trim()}
              className={`flex items-center space-x-1.5 px-5 py-2.5 rounded-xl font-bold text-xs transition-all shadow-md ${
                isEvaluating || !transcript || !transcript.trim()
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/25 hover:-translate-y-0.5'
              }`}
            >
              {isEvaluating ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Answer</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
