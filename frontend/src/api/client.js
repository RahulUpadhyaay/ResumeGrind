import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload-resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const inspectLinks = async (urls) => {
  const response = await api.post('/inspect-links', { urls });
  return response.data;
};

export const startInterview = async (resumeAnalysis, inspectionResult, config) => {
  const response = await api.post('/start-interview', {
    resume_analysis: resumeAnalysis,
    inspection_result: inspectionResult,
    config: config || { language: 'en', persona: 'strict_roast' }
  });
  return response.data;
};

export const submitAnswer = async (sessionId, transcript) => {
  const response = await api.post('/submit-answer', {
    session_id: sessionId,
    transcript: transcript
  });
  return response.data;
};

export const teachConcept = async (topic, sessionId = null, questionText = null) => {
  const response = await api.post('/teach-concept', { 
    topic,
    session_id: sessionId,
    question_text: questionText
  });
  return response.data;
};

export const getSessionReport = async (sessionId) => {
  const response = await api.get(`/session-report/${sessionId}`);
  return response.data;
};

export const executeCode = async (code, language = 'python') => {
  const response = await api.post('/execute-code', { code, language });
  return response.data;
};

export default api;

