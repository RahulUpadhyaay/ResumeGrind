import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import VoiceEngine from './VoiceEngine';
import CodeInspector from './CodeInspector';
import ProjectPreview from './ProjectPreview';
import LearningCard from './LearningCard';
import { useSpeech } from '../hooks/useSpeech';
import { 
  Flame, 
  HeartHandshake, 
  Briefcase, 
  Sparkles, 
  BookOpen, 
  Flag, 
  CheckCircle2, 
  Volume2, 
  Loader2,
  User,
  Bot,
  MessageSquare,
  AlertTriangle
} from 'lucide-react';

export default function InterviewCockpit({ interview, onComplete }) {
  const { 
    currentQuestion, 
    turnCount, 
    conversationTurns = [],
    phase, 
    setPhase, 
    submitAnswer, 
    lastReaction,
    activeLearningConcept,
    setActiveLearningConcept,
    requestConceptExplanation,
    isTeachingLoading,
    concludeInterview,
    config
  } = interview;

  const currentLang = config?.language || 'en';
  const currentPersona = config?.persona || 'strict_roast';

  const { 
    speak, 
    stopSpeaking, 
    startListening, 
    stopListening, 
    clearTranscript,
    transcript, 
    setTranscript, 
    getTranscript,
    isListening, 
    isSpeaking, 
    speechError,
    micPermission,
    requestMicPermission,
    audioLevel
  } = useSpeech(currentLang);
  
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const lastTurnKeyRef = useRef('');
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom of conversation feed on new messages or typewriter progress
  const scrollToBottom = (smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: smooth ? 'smooth' : 'auto',
        block: 'nearest'
      });
    }
  };

  useEffect(() => {
    scrollToBottom(true);
  }, [conversationTurns, displayedText]);

  // Turn Key uniquely identifies each question instance by turn number & question text
  const currentTurnKey = `${turnCount}_${currentQuestion?.question_text || ''}`;

  // Typewriter effect & speech synthesis for each round
  useEffect(() => {
    if (!currentQuestion || !currentQuestion.question_text) return;

    if (lastTurnKeyRef.current !== currentTurnKey) {
      lastTurnKeyRef.current = currentTurnKey;
      
      const uiText = currentQuestion.question_text || "";
      setDisplayedText(uiText);
      setIsTyping(false);

      // Voice text includes spoken teacher reaction first, followed by question
      const voiceText = currentQuestion.voice_text || currentQuestion.question_text || "";

      // Ensure listening phase is set once voice finishes
      speak(voiceText).finally(() => {
        setPhase('listening');
      });

      // Safety timeout: Guarantee phase is ready within 7s no matter what
      const safetyTimer = setTimeout(() => {
        setPhase('listening');
      }, 7000);

      return () => {
        clearTimeout(safetyTimer);
      };
    }
  }, [currentTurnKey, currentQuestion, speak, setPhase]);

  // Handle phase completion
  useEffect(() => {
    if (phase === 'complete') {
      stopSpeaking();
      stopListening();
      onComplete();
    }
  }, [phase, onComplete, stopSpeaking, stopListening]);

  // Handle submit answer with strict locking & validation to prevent dropped responses
  const handleSubmitAnswer = async (overrideText = null) => {
    if (isSubmitting || phase === 'evaluating') return;

    let text = "";
    if (typeof overrideText === 'string' && overrideText.trim()) {
      text = overrideText.trim();
    } else {
      text = (getTranscript && getTranscript()) || transcript || "";
      if (isListening) {
        const liveText = stopListening();
        text = liveText || text;
      }
      text = (text || "").trim();
    }

    if (!text) {
      alert("Please speak into your microphone or type your answer before clicking Submit.");
      return;
    }

    setIsSubmitting(true);
    try {
      await submitAnswer(text);
      clearTranscript();
    } catch (err) {
      console.error("Submission failed:", err);
      alert("Failed to submit answer. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTeachMe = () => {
    const topic = currentQuestion?.category || currentQuestion?.question_text || "Software Engineering Principles";
    requestConceptExplanation(topic, currentQuestion?.question_text);
  };

  if (!currentQuestion) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        <span>Preparing your interview cockpit...</span>
      </div>
    );
  }

  const context = currentQuestion.visual_context;
  const activeQuestionText = currentQuestion.question_text || "";

  // Last turn evaluation details
  const lastTurn = conversationTurns.length > 0 ? conversationTurns[conversationTurns.length - 1] : null;
  const isLastAnswerApproved = lastTurn && lastTurn.score >= 6;

  // Persona Badge Config (Brighter non-blue styling)
  const personaBadge = currentPersona === 'strict_roast' ? {
    name: 'Strict Professor (Evaluator)',
    icon: Flame,
    color: 'text-amber-400 bg-amber-500/15 border-amber-500/30'
  } : currentPersona === 'friendly' ? {
    name: 'Friendly Mentor',
    icon: HeartHandshake,
    color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30'
  } : {
    name: 'Standard FAANG',
    icon: Briefcase,
    color: 'text-teal-400 bg-teal-500/15 border-teal-500/30'
  };
  const PersonaIcon = personaBadge.icon;

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-120px)] max-w-[1600px] mx-auto w-full gap-6 p-4 md:p-6">
      
      {/* Left Panel - Question, Conversation & Voice Studio */}
      <div className="flex-1 lg:w-[58%] flex flex-col space-y-4">
        
        {/* Top Status & Controls Bar */}
        <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-4 shadow-lg flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200 bg-slate-800 px-3 py-1 rounded-lg border border-slate-700">
              Round {turnCount}
            </span>
            <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg border text-xs font-semibold ${personaBadge.color}`}>
              <PersonaIcon className="w-3.5 h-3.5" />
              <span>{personaBadge.name}</span>
            </div>
            {currentQuestion.is_cross_question && (
              <span className="text-xs text-amber-300 bg-amber-500/15 px-2.5 py-1 rounded-lg border border-amber-500/30 font-semibold flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                Cross-Exam
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleTeachMe}
              disabled={isTeachingLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/40 rounded-xl text-xs font-semibold transition-all shadow-sm"
              title="Get a targeted answer hint grounded in your resume projects"
            >
              {isTeachingLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span>Take a Hint</span>
            </button>

            <button
              onClick={concludeInterview}
              className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl text-xs font-medium transition-colors"
              title="End interview and view feedback report"
            >
              <Flag className="w-3.5 h-3.5 text-slate-400" />
              <span>Conclude</span>
            </button>
          </div>
        </div>

        {/* Live Conversational Chat Feed (Chronological AI Questions + Candidate Answers + Teacher Feedback) */}
        <div 
          ref={chatContainerRef}
          className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-2xl p-4 md:p-5 flex flex-col space-y-4 overflow-y-auto max-h-[440px] min-h-[320px] shadow-xl scrollbar-custom"
        >
          {conversationTurns.length === 0 && (
            <div className="text-center py-2 text-xs text-slate-400 flex items-center justify-center gap-1.5 border-b border-slate-800/80 pb-3">
              <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
              <span>Live interview session active. Answer the opening question below:</span>
            </div>
          )}

          {/* Past Conversation Turns */}
          {conversationTurns.map((turn, idx) => {
            const isApproved = turn.score >= 7;
            const isHarsh = turn.score <= 4;
            return (
              <div key={idx} className="space-y-3 pt-1">
                
                {/* AI Question Bubble (Left) */}
                <div className="flex flex-col items-start max-w-[90%]">
                  <div className="flex items-center gap-1.5 mb-1 text-[11px] font-semibold text-slate-400">
                    <Bot className="w-3.5 h-3.5 text-emerald-400" />
                    <span>AI Interviewer · Round {turn.turnIndex}</span>
                  </div>
                  <div className="bg-slate-800/90 border border-slate-700 text-slate-100 text-sm p-3.5 rounded-2xl rounded-tl-sm shadow-sm leading-relaxed">
                    {turn.questionText}
                  </div>
                </div>

                {/* Candidate Answer Bubble (Right) */}
                <div className="flex flex-col items-end self-end max-w-[90%] ml-auto">
                  <div className="flex items-center gap-2 mb-1 text-[11px]">
                    <span className={`px-2 py-0.5 rounded font-semibold text-[10px] border ${
                      isApproved 
                        ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' 
                        : isHarsh
                          ? 'bg-red-500/15 text-red-300 border-red-500/30'
                          : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                    }`}>
                      Score: {turn.score}/10 {isApproved ? '★ Excellent (Friendly)' : isHarsh ? '⚠️ Careless (Harsh)' : '⚡ Fair (Needs Depth)'}
                    </span>
                    <span className="font-semibold text-emerald-400 flex items-center gap-1">
                      <User className="w-3 h-3" />
                      You (Candidate)
                    </span>
                  </div>
                  <div className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-100 text-sm p-3.5 rounded-2xl rounded-tr-sm shadow-sm leading-relaxed text-left">
                    {turn.candidateAnswer}
                  </div>
                </div>

                {/* Teacher / Interviewer Reaction Banner (Dynamically styled to tone) */}
                {turn.personaReaction && (
                  <div className={`p-3 rounded-xl border text-xs leading-relaxed max-w-[92%] ${
                    isApproved 
                      ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200' 
                      : isHarsh
                        ? 'bg-red-950/40 border-red-500/30 text-red-200'
                        : 'bg-amber-950/30 border-amber-500/30 text-amber-200'
                  }`}>
                    <div className="font-bold uppercase tracking-wider mb-0.5 flex items-center gap-1.5 text-[10px]">
                      {isApproved ? (
                        <>
                          <HeartHandshake className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Friendly Mentor Praise & Validation</span>
                        </>
                      ) : isHarsh ? (
                        <>
                          <AlertTriangle className="w-3 h-3 text-red-400" />
                          <span>Harsh Scolding & Strict Roast</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-3 h-3 text-amber-400" />
                          <span>Firm Reality-Check & Constructive Critique</span>
                        </>
                      )}
                    </div>
                    <p className="italic">"{turn.personaReaction}"</p>
                  </div>
                )}

              </div>
            );
          })}

          {/* Active Current Question (Left - Highlighted) */}
          <div className="flex flex-col items-start max-w-[94%] pt-2">
            <div className="flex items-center justify-between w-full mb-1">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <Bot className="w-3.5 h-3.5" />
                <span>AI Interviewer · Round {turnCount} (Active Question)</span>
              </div>
              {isSpeaking && (
                <span className="text-[10px] text-emerald-300 bg-emerald-500/15 px-2 py-0.5 rounded-full border border-emerald-500/30 font-medium animate-pulse flex items-center gap-1">
                  <Volume2 className="w-3 h-3" />
                  Voicing aloud...
                </span>
              )}
            </div>

            <div className="bg-slate-800/95 border-2 border-emerald-500/40 text-white text-sm md:text-base p-4 rounded-2xl rounded-tl-sm shadow-lg leading-relaxed w-full">
              {displayedText || activeQuestionText}
              {isTyping && <span className="inline-block w-2 h-4 ml-1 bg-emerald-400 animate-pulse align-middle"></span>}
            </div>

            {context && (
              <div className="lg:hidden mt-2 p-2 bg-slate-800/80 rounded-lg border border-slate-700 flex items-center justify-between text-[11px] text-slate-300 w-full">
                <span>Repository context linked</span>
                <span className="text-emerald-400 font-semibold">View below ↓</span>
              </div>
            )}
          </div>

          <div ref={messagesEndRef} />
        </div>

        {/* Voice Studio / Microphone Engine */}
        <div className="flex-shrink-0">
          <VoiceEngine 
            isListening={isListening}
            isSpeaking={isSpeaking}
            transcript={transcript}
            setTranscript={setTranscript}
            startListening={startListening}
            stopListening={stopListening}
            onSubmitAnswer={handleSubmitAnswer}
            isSubmitting={isSubmitting}
            clearTranscript={clearTranscript}
            phase={phase}
            speechError={speechError}
            micPermission={micPermission}
            requestMicPermission={requestMicPermission}
            audioLevel={audioLevel}
          />
        </div>

      </div>

      {/* Right Panel - Interactive Split Screen (Code Inspector / Learning Card) */}
      <div className="w-full lg:w-[42%] min-h-[480px] lg:min-h-0 flex-shrink-0 flex flex-col">
        <AnimatePresence mode="wait">
          {activeLearningConcept ? (
            <LearningCard
              key="learning"
              concept={activeLearningConcept}
              onClose={() => setActiveLearningConcept(null)}
            />
          ) : !context ? (
            <motion.div 
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full bg-slate-900/60 border border-slate-700/80 rounded-2xl flex flex-col items-center justify-center text-center p-8 min-h-[400px]"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500/20 to-slate-800 border border-amber-500/30 flex items-center justify-center mb-4 shadow-xl">
                <Sparkles className="w-8 h-8 text-amber-400" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">Technical Interview Cockpit</h3>
              <p className="text-slate-300 text-xs max-w-sm leading-relaxed mb-6">
                Need guidance on how to answer this question using the projects listed on your resume? Click below to generate a tailored hint.
              </p>
              <button
                onClick={handleTeachMe}
                disabled={isTeachingLoading}
                className="px-4 py-2.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-amber-500/10"
              >
                {isTeachingLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 text-amber-400" />
                )}
                <span>Take a Hint (Resume Project Grounded)</span>
              </button>
            </motion.div>
          ) : context.type === 'github_code' ? (
            <CodeInspector key="code" context={context} onSubmitCode={handleSubmitAnswer} isSubmittingParent={isSubmitting} />
          ) : context.type === 'live_project' ? (
            <ProjectPreview key="project" context={context} />
          ) : null}
        </AnimatePresence>
      </div>

    </div>
  );
}
