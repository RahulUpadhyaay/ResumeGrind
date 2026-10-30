import { useState, useRef, useCallback, useEffect } from 'react';

// Maps app language codes to browser Speech Recognition locales
const LANGUAGE_LOCALE_MAP = {
  en: 'en-US',
  hi: 'hi-IN',
  es: 'es-ES',
  fr: 'fr-FR',
  de: 'de-DE',
};

/**
 * useSpeech Hook
 * 
 * MULTI-LANGUAGE & GLITCH-FREE VOICE ENGINE:
 * 1. Supports English, Hindi/Hinglish, Spanish, French, and German.
 * 2. Dynamic SpeechRecognition and SpeechSynthesis localization.
 * 3. Fresh instance creation on start to prevent Chrome inactive pipeline bugs.
 * 4. Real-time physical Web Audio volume level analyzer (0-100%).
 * 5. Clean buffer reset for seamless question-to-question transitions.
 */
export const useSpeech = (language = 'en') => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscriptState] = useState('');
  const [speechError, setSpeechError] = useState(null);
  const [micPermission, setMicPermission] = useState('prompt');
  const [audioLevel, setAudioLevel] = useState(0);

  const recognitionRef = useRef(null);
  const isListeningRef = useRef(false);
  const currentTranscriptRef = useRef('');
  const restartTimerRef = useRef(null);
  const voicesRef = useRef([]);

  const setTranscript = useCallback((val) => {
    currentTranscriptRef.current = val;
    setTranscriptState(val);
  }, []);

  const targetLocale = LANGUAGE_LOCALE_MAP[language] || 'en-US';

  // Audio Context refs for volume visualization
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const animFrameRef = useRef(null);

  // Load available speech synthesis voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const loadVoices = () => {
        voicesRef.current = window.speechSynthesis.getVoices();
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Check microphone permissions
  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: 'microphone' })
        .then((status) => {
          setMicPermission(status.state);
          status.onchange = () => {
            setMicPermission(status.state);
            if (status.state === 'granted') setSpeechError(null);
          };
        })
        .catch(() => {});
    }
  }, []);

  // Cleanup audio tracks on unmount
  useEffect(() => {
    return () => {
      isListeningRef.current = false;
      if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Real-time AudioContext volume analyzer
  const startVolumeAnalyzer = useCallback((stream) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;

      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
      }

      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.5;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateVolume = () => {
        if (!isListeningRef.current) {
          setAudioLevel(0);
          return;
        }

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const average = sum / dataArray.length;
        const normalized = Math.min(100, Math.round((average / 128) * 100));
        setAudioLevel(normalized);

        animFrameRef.current = requestAnimationFrame(updateVolume);
      };

      updateVolume();
    } catch (err) {
      console.warn('Volume meter analyzer notice:', err);
    }
  }, []);

  const requestMicPermission = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setSpeechError('Microphone API not supported in this browser.');
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicPermission('granted');
      setSpeechError(null);
      return true;
    } catch (err) {
      console.warn('Microphone permission denied:', err);
      setMicPermission('denied');
      setSpeechError('Microphone permission denied. Please allow microphone in your browser URL bar.');
      return false;
    }
  }, []);

  // Text-to-speech adapted to target language
  const speak = useCallback((text) => {
    return new Promise((resolve) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        resolve();
        return;
      }

      window.speechSynthesis.cancel();

      if (!text || !text.trim()) {
        resolve();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.lang = targetLocale;

      window.__activeUtterance = utterance;

      const voices = voicesRef.current.length ? voicesRef.current : window.speechSynthesis.getVoices();
      const langPrefix = targetLocale.split('-')[0];
      const matchedVoice = voices.find((v) => v.lang.startsWith(targetLocale)) ||
                           voices.find((v) => v.lang.startsWith(langPrefix)) ||
                           voices.find((v) => v.lang.startsWith('en'));

      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }

      let isResolved = false;
      const finish = () => {
        if (!isResolved) {
          isResolved = true;
          setIsSpeaking(false);
          window.__activeUtterance = null;
          resolve();
        }
      };

      const safetyTime = Math.max(6000, (text.length / 14) * 1000);
      const timer = setTimeout(finish, safetyTime);

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        clearTimeout(timer);
        finish();
      };
      utterance.onerror = () => {
        clearTimeout(timer);
        finish();
      };

      try {
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        clearTimeout(timer);
        finish();
      }
    });
  }, [targetLocale]);

  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  // Start listening with fresh SpeechRecognition configured for target language
  const startListening = useCallback(async () => {
    // 1. Cancel speech synthesis
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);

    // 2. Request mic stream directly
    let stream = null;
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStreamRef.current = stream;
        setMicPermission('granted');
        setSpeechError(null);
      }
    } catch (err) {
      console.warn('Microphone permission denied:', err);
      setMicPermission('denied');
      setSpeechError('Microphone permission denied. Please allow microphone in your browser URL bar.');
      return;
    }

    // 3. Start audio volume visualizer
    isListeningRef.current = true;
    setIsListening(true);
    if (stream) {
      startVolumeAnalyzer(stream);
    }

    // 4. Create fresh SpeechRecognition pipeline
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = targetLocale;

      recognition.onstart = () => {
        setIsListening(true);
        isListeningRef.current = true;
        setSpeechError(null);
      };

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = 0; i < event.results.length; i++) {
          const text = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += text + ' ';
          } else {
            interimTranscript += text;
          }
        }

        const fullText = `${finalTranscript} ${interimTranscript}`.replace(/\s+/g, ' ').trim();
        if (fullText) {
          currentTranscriptRef.current = fullText;
          setTranscriptState(fullText);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          setMicPermission('denied');
          setSpeechError('Microphone permission blocked. Please allow mic access in your browser.');
          setIsListening(false);
          isListeningRef.current = false;
        } else if (event.error === 'network') {
          setSpeechError('Chrome Speech Network Notice: Google speech service issue detected. Voice meter is active — speak or type your answer.');
        } else if (event.error === 'no-speech') {
          // Normal pause in speech, will auto-restart in onend
        }
      };

      recognition.onend = () => {
        if (isListeningRef.current) {
          restartTimerRef.current = setTimeout(() => {
            if (isListeningRef.current && recognitionRef.current) {
              try {
                recognitionRef.current.start();
              } catch (e) {}
            }
          }, 150);
        } else {
          setIsListening(false);
        }
      };

      try {
        recognition.start();
        recognitionRef.current = recognition;
      } catch (err) {
        console.warn('Recognition start error:', err);
      }
    } else {
      setSpeechError('Web Speech API is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
    }
  }, [startVolumeAnalyzer, targetLocale]);

  const stopListening = useCallback(() => {
    isListeningRef.current = false;
    setIsListening(false);
    setAudioLevel(0);

    if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    return currentTranscriptRef.current || transcript;
  }, [transcript]);

  const clearTranscript = useCallback(() => {
    currentTranscriptRef.current = '';
    setTranscriptState('');
  }, []);

  return {
    speak,
    stopSpeaking,
    startListening,
    stopListening,
    clearTranscript,
    transcript,
    setTranscript,
    getTranscript: () => currentTranscriptRef.current || transcript,
    isListening,
    isSpeaking,
    speechError,
    micPermission,
    requestMicPermission,
    audioLevel,
    targetLocale
  };
};
