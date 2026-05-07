import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Paperclip, Mic, MicOff } from "lucide-react"
import { ModeToggle, type ChatModes } from "./mode-toggle"
import { DocumentUpload } from "./document-upload"
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition"
import type { DocumentInfo } from "@/services/api"
import type { UploadProgress } from "@/hooks/useDocuments"

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
  modes: ChatModes
  onModesChange: (modes: ChatModes) => void
  documents: DocumentInfo[]
  uploading: UploadProgress | null
  onDocumentsChange: (updater: (prev: DocumentInfo[]) => DocumentInfo[]) => void
  onUploadStart: (filename: string) => void
  onUploadProgress: (filename: string, progress: number) => void
  onUploadEnd: () => void
  onError: (message: string) => void
}

export function ChatInput({
  onSend,
  isLoading,
  modes,
  onModesChange,
  documents,
  uploading,
  onDocumentsChange,
  onUploadStart,
  onUploadProgress,
  onUploadEnd,
  onError,
}: ChatInputProps) {
  const [input, setInput] = useState("")
  const [isDocUploadExpanded, setIsDocUploadExpanded] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // Speech recognition hook
  const { isListening, transcript, error: speechError, isBrowserSupported, toggleListening, resetTranscript, setOnTranscriptReady } = useSpeechRecognition()

  // Log on mount and when browser support changes
  useEffect(() => {
    console.log('[ChatInput] Mounted');
    console.log('[ChatInput] Browser speech support:', isBrowserSupported);
    console.log('[ChatInput] SpeechRecognition API:', (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition ? 'Found' : 'Not Found');
  }, [])

  // Register transcript ready callback - populate input with full transcript
  useEffect(() => {
    const handleTranscriptReady = (finalTranscript: string) => {
      console.log('[ChatInput] Transcript ready callback:', finalTranscript);
      
      // Build the full message by appending to existing input
      const fullMessage = (input.trim() + (input.trim() ? " " : "") + finalTranscript).trim();
      console.log('[ChatInput] Full message (ready to send):', fullMessage);
      
      // Update input field with the full transcript for user to review/edit
      setInput(fullMessage);
      
      // Reset the transcript in the hook
      resetTranscript();
      
      console.log('[ChatInput] Input field populated. User can now review or click Send.');
    };

    setOnTranscriptReady(handleTranscriptReady);
  }, [input, resetTranscript, setOnTranscriptReady])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isLoading) return
    onSend(input.trim())
    setInput("")
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Handle microphone button click
  const handleMicClick = () => {
    console.log('[handleMicClick] Mic button clicked');
    console.log('[handleMicClick] Browser supported:', isBrowserSupported);
    console.log('[handleMicClick] Currently listening:', isListening);
    console.log('[handleMicClick] isLoading:', isLoading);

    if (!isBrowserSupported) {
      console.error('[handleMicClick] Speech Recognition not supported');
      alert('Speech Recognition is not supported in this browser. Please use Google Chrome.');
      return;
    }

    if (isLoading) {
      console.warn('[handleMicClick] Chat is loading, ignoring mic click');
      return;
    }

    console.log('[handleMicClick] Calling toggleListening');
    toggleListening()
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  // Handle speech recognition transcript - just update UI for preview/edit
  // Actual sending is handled by the callback in setOnTranscriptReady
  useEffect(() => {
    if (transcript && !isListening) {
      console.log('[ChatInput] Transcript updated (UI preview):', transcript);
      // Don't auto-send here - it's handled by the callback
      // Just keep the transcript in state for display
    }
  }, [isListening, transcript])

  const hasActiveMode = modes.rag || modes.reasoning || modes.webSearch

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2">
      {/* Document Upload Area */}
      <div className="mb-3">
        <DocumentUpload
          documents={documents}
          uploading={uploading}
          onDocumentsChange={onDocumentsChange}
          onUploadStart={onUploadStart}
          onUploadProgress={onUploadProgress}
          onUploadEnd={onUploadEnd}
          onError={onError}
          isExpanded={isDocUploadExpanded}
          onToggleExpand={() => setIsDocUploadExpanded(!isDocUploadExpanded)}
        />
      </div>

      {/* Glassmorphism Input Container */}
      <form onSubmit={handleSubmit} className="relative">
        <div className={cn(
          "glass rounded-2xl p-1.5 transition-all duration-300",
          hasActiveMode && "ring-1 ring-primary/20"
        )}>
          <div className="flex flex-col">
            {/* Mode Toggles Row */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-border/30">
              <ModeToggle modes={modes} onModesChange={onModesChange} />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setIsDocUploadExpanded(!isDocUploadExpanded)}
                className={cn(
                  "h-8 w-8 transition-colors",
                  documents.length > 0
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Paperclip className="h-4 w-4" />
                {documents.length > 0 && (
                  <span className="absolute -top-1 -right-1 h-4 w-4 text-[10px] font-medium bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                    {documents.length}
                  </span>
                )}
              </Button>
            </div>

            {/* Input Row */}
            <div className="flex items-end gap-2 p-2">
              {/* Microphone Button */}
              <Button
                type="button"
                size="icon"
                variant={isListening ? "default" : "ghost"}
                onClick={handleMicClick}
                disabled={isLoading || !isBrowserSupported}
                className={cn(
                  "h-12 w-12 rounded-xl shrink-0 transition-all duration-200",
                  isListening && "bg-red-500 hover:bg-red-600 animate-pulse",
                  !isBrowserSupported && "opacity-50 cursor-not-allowed"
                )}
                title={isListening ? "Stop recording (Click to stop)" : "Start voice input (Click to speak)"}
              >
                {isListening ? (
                  <MicOff className="h-5 w-5 text-white" />
                ) : (
                  <Mic className="h-5 w-5" />
                )}
                <span className="sr-only">
                  {isListening ? "Stop recording" : "Start voice input"}
                </span>
              </Button>

              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isListening ? "Listening..." : "Ask anything..."}
                disabled={isLoading}
                rows={1}
                className={cn(
                  "flex-1 min-h-[48px] max-h-[200px] resize-none",
                  "bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0",
                  "text-foreground placeholder:text-muted-foreground/60",
                  "py-3 px-2 text-base leading-relaxed"
                )}
              />
              <Button
                type="submit"
                size="icon"
                disabled={!input.trim() || isLoading}
                className={cn(
                  "h-12 w-12 rounded-xl shrink-0 transition-all duration-200",
                  "bg-primary hover:bg-primary/90",
                  "disabled:opacity-40 disabled:cursor-not-allowed",
                  input.trim() && !isLoading && "animate-glow-pulse"
                )}
              >
                <Send className="h-5 w-5" />
                <span className="sr-only">Send message</span>
              </Button>
            </div>

            {/* Status Messages */}
            {isListening && (
              <div className="px-3 py-2 text-xs text-center text-primary font-medium animate-pulse">
                🎤 Listening... Click to stop
              </div>
            )}

            {speechError && (
              <div className="px-3 py-2 text-xs text-center text-red-500 bg-red-50/50 dark:bg-red-950/20 rounded">
                {speechError}
              </div>
            )}
          </div>
        </div>

        {/* Input hint */}
        <p className="text-center text-xs text-muted-foreground/60 mt-2">
          Press Enter to send, Shift + Enter for new line • Click 🎤 for voice input
        </p>
      </form>
    </div>
  )
}
