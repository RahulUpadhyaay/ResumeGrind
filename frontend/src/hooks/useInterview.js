import { useState, useCallback } from 'react';
import { startInterview, submitAnswer, getSessionReport, teachConcept } from '../api/client';

export const useInterview = () => {
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [turnCount, setTurnCount] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  const [lastReaction, setLastReaction] = useState(null);
  const [activeLearningConcept, setActiveLearningConcept] = useState(null);
  const [isTeachingLoading, setIsTeachingLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [phase, setPhase] = useState('idle'); // idle | generating | asking | listening | evaluating | complete
  const [report, setReport] = useState(null);
  const [config, setConfig] = useState({ language: 'en', persona: 'strict_roast' });

  const initSession = async (resumeAnalysis, inspectionResult, userConfig) => {
    setIsLoading(true);
    setPhase('generating');
    const selectedConfig = userConfig || config;
    setConfig(selectedConfig);

    try {
      const response = await startInterview(resumeAnalysis, inspectionResult, selectedConfig);
      setSession(response);
      setCurrentQuestion(response.current_question);
      setTurnCount(1);
      setAnswers([]);
      setFeedbacks([]);
      setLastReaction(null);
      setActiveLearningConcept(null);
      setPhase('asking');
      return response;
    } catch (error) {
      console.error("Error starting interview:", error);
      setPhase('idle');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const [conversationTurns, setConversationTurns] = useState([]);

  const handleAnswerSubmit = async (transcript) => {
    if (!session) return;
    if (isLoading || phase === 'evaluating') {
      console.warn("Submission already in progress. Preventing duplicate submission.");
      return;
    }
    
    setIsLoading(true);
    setPhase('evaluating');

    try {
      const result = await submitAnswer(session.session_id, transcript);
      
      const turnRecord = {
        turnIndex: turnCount,
        questionText: currentQuestion?.question_text || "",
        candidateAnswer: transcript,
        personaReaction: result.persona_reaction,
        score: result.feedback?.score !== undefined ? result.feedback.score : 7,
        speechMetrics: result.feedback?.speech_metrics || null
      };

      setConversationTurns(prev => [...prev, turnRecord]);
      setAnswers(prev => [...prev, transcript]);
      setFeedbacks(prev => [...prev, result.feedback]);
      setLastReaction(result.persona_reaction);

      if (result.learning_concept) {
        setActiveLearningConcept(result.learning_concept);
      }

      if (result.next_question && !result.is_complete) {
        setCurrentQuestion(result.next_question);
        setTurnCount(prev => prev + 1);
        setPhase('asking');
      } else {
        setPhase('complete');
      }

      return result;
    } catch (error) {
      console.error("Error submitting answer:", error);
      setPhase('listening');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const requestConceptExplanation = async (topic, questionText = null) => {
    setIsTeachingLoading(true);
    try {
      const concept = await teachConcept(topic, session?.session_id, questionText);
      setActiveLearningConcept(concept);
      return concept;
    } catch (err) {
      console.error("Error fetching concept explanation:", err);
    } finally {
      setIsTeachingLoading(false);
    }
  };

  const concludeInterview = async () => {
    setPhase('complete');
  };

  const fetchReport = async () => {
    if (!session) return null;
    setIsLoading(true);
    try {
      const data = await getSessionReport(session.session_id);
      setReport(data);
      return data;
    } catch (error) {
      console.error("Error fetching report:", error);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    session,
    currentQuestion,
    currentQuestionIndex: turnCount - 1,
    turnCount,
    conversationTurns,
    answers,
    feedbacks,
    lastReaction,
    activeLearningConcept,
    setActiveLearningConcept,
    requestConceptExplanation,
    isTeachingLoading,
    isLoading,
    phase,
    setPhase,
    report,
    config,
    setConfig,
    initSession,
    submitAnswer: handleAnswerSubmit,
    concludeInterview,
    getReport: fetchReport,
  };
};
