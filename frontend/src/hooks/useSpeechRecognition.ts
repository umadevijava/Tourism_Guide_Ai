import { useState, useRef, useCallback, useEffect } from 'react';

interface SpeechRecognitionState {
  isListening: boolean;
  transcript: string;
  error: string | null;
  isBrowserSupported: boolean;
}

interface UseSpeechRecognitionReturn extends SpeechRecognitionState {
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  toggleListening: () => void;
  setOnTranscriptReady: (callback: (transcript: string) => void) => void;
}

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [state, setState] = useState<SpeechRecognitionState>({
    isListening: false,
    transcript: '',
    error: null,
    isBrowserSupported: true, // Assume supported initially
  });

  const recognitionRef = useRef<any>(null);
  const isInitializedRef = useRef(false);
  const isListeningRef = useRef(false);
  const finalTranscriptRef = useRef('');
  const interimTranscriptRef = useRef('');
  const onTranscriptReadyRef = useRef<(transcript: string) => void | null>(null);

  // Initialize speech recognition ONCE on mount
  useEffect(() => {
    console.log('[useSpeechRecognition] Initializing...');
    
    if (isInitializedRef.current) {
      console.log('[useSpeechRecognition] Already initialized, skipping');
      return;
    }

    // Check browser support
    const SpeechRecognitionAPI =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      console.error('[useSpeechRecognition] Speech Recognition NOT supported');
      setState({
        isListening: false,
        transcript: '',
        error: 'Speech Recognition not supported in this browser',
        isBrowserSupported: false,
      });
      return;
    }

    console.log('[useSpeechRecognition] Speech Recognition API found');

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.language = 'en-US';

    // ====== EVENT HANDLERS ======

    recognition.onstart = () => {
      console.log('[onstart] Recording started');
      isListeningRef.current = true;
      finalTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      setState((prev) => ({ ...prev, isListening: true, error: null, transcript: '' }));
    };

    recognition.onresult = (event: any) => {
      console.log('[onresult] Result event received:', {
        resultIndex: event.resultIndex,
        resultsLength: event.results.length,
      });

      let interimTranscript = '';
      
      // Collect ALL results from resultIndex to end
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPart = event.results[i][0].transcript;
        
        console.log(`[onresult] Result[${i}]:`, {
          transcript: transcriptPart,
          isFinal: event.results[i].isFinal,
          confidence: event.results[i][0].confidence,
        });

        if (event.results[i].isFinal) {
          // Accumulate final results (NO extra spaces)
          finalTranscriptRef.current += transcriptPart;
        } else {
          // Show interim results
          interimTranscript = transcriptPart;
        }
      }

      // Build display text: final + interim (for live preview)
      const displayText = (finalTranscriptRef.current + ' ' + interimTranscript).trim();
      console.log('[onresult] Display text (with interim):', displayText);
      console.log('[onresult] Final transcript so far:', finalTranscriptRef.current.trim());
      
      setState((prev) => ({ ...prev, transcript: displayText }));
    };

    recognition.onerror = (event: any) => {
      console.error('[onerror] Speech recognition error:', event.error);
      let errorMessage = 'Speech recognition error';

      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'No microphone found. Ensure that it is connected.';
          break;
        case 'network':
          errorMessage = 'Network error. Please check your connection.';
          break;
        case 'permission-denied':
          errorMessage = 'Microphone permission denied. Please check your browser settings.';
          break;
        case 'not-allowed':
          errorMessage = 'Speech recognition not allowed. Please check your permissions.';
          break;
        default:
          errorMessage = `Speech recognition error: ${event.error}`;
      }

      isListeningRef.current = false;
      setState((prev) => ({
        ...prev,
        error: errorMessage,
        isListening: false,
      }));
    };

    recognition.onend = () => {
      console.log('[onend] Recording stopped');
      isListeningRef.current = false;
      
      // Get the final transcript (without interim results)
      const finalTranscript = finalTranscriptRef.current.trim();
      console.log('[onend] Final transcript captured:', finalTranscript);
      
      // Update state with only final transcript (no interim)
      setState((prev) => ({
        ...prev,
        isListening: false,
        transcript: finalTranscript,
      }));

      // Call the callback if registered (for auto-send or direct handling)
      if (onTranscriptReadyRef.current && finalTranscript) {
        console.log('[onend] Calling onTranscriptReady callback with:', finalTranscript);
        onTranscriptReadyRef.current(finalTranscript);
      }
    };

    recognitionRef.current = recognition;
    isInitializedRef.current = true;
    console.log('[useSpeechRecognition] Initialization complete');

    // Cleanup on unmount
    return () => {
      console.log('[useSpeechRecognition] Cleaning up');
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (err) {
          console.error('Error during cleanup:', err);
        }
      }
    };
  }, []);

  const startListening = useCallback(() => {
    console.log('[startListening] Called');
    console.log('[startListening] isListeningRef:', isListeningRef.current);
    console.log('[startListening] recognitionRef:', recognitionRef.current ? 'exists' : 'null');

    if (!recognitionRef.current) {
      console.error('[startListening] Recognition not initialized yet');
      return;
    }

    if (isListeningRef.current) {
      console.log('[startListening] Already listening, ignoring');
      return;
    }

    try {
      console.log('[startListening] Calling recognition.start()');
      finalTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      recognitionRef.current.start();
      console.log('[startListening] recognition.start() succeeded');
    } catch (err) {
      console.error('[startListening] Error starting speech recognition:', err);
      setState((prev) => ({
        ...prev,
        error: 'Failed to start speech recognition: ' + String(err),
      }));
    }
  }, []);

  const stopListening = useCallback(() => {
    console.log('[stopListening] Called');
    console.log('[stopListening] isListeningRef:', isListeningRef.current);

    if (!recognitionRef.current) {
      console.error('[stopListening] Recognition not initialized');
      return;
    }

    if (!isListeningRef.current) {
      console.log('[stopListening] Not currently listening, ignoring');
      return;
    }

    try {
      console.log('[stopListening] Calling recognition.stop()');
      recognitionRef.current.stop();
      console.log('[stopListening] recognition.stop() succeeded');
    } catch (err) {
      console.error('[stopListening] Error stopping speech recognition:', err);
    }
  }, []);

  const resetTranscript = useCallback(() => {
    console.log('[resetTranscript] Called');
    setState((prev) => ({ ...prev, transcript: '', error: null }));
    finalTranscriptRef.current = '';
    interimTranscriptRef.current = '';
  }, []);

  const toggleListening = useCallback(() => {
    console.log('[toggleListening] Called, isListening:', isListeningRef.current);
    
    if (isListeningRef.current) {
      console.log('[toggleListening] Stopping listening');
      stopListening();
    } else {
      console.log('[toggleListening] Starting listening');
      startListening();
    }
  }, [startListening, stopListening]);

  const setOnTranscriptReady = useCallback((callback: (transcript: string) => void) => {
    console.log('[setOnTranscriptReady] Callback registered');
    onTranscriptReadyRef.current = callback;
  }, []);

  return {
    isListening: state.isListening,
    transcript: state.transcript,
    error: state.error,
    isBrowserSupported: state.isBrowserSupported,
    startListening,
    stopListening,
    resetTranscript,
    toggleListening,
    setOnTranscriptReady,
  };
}
