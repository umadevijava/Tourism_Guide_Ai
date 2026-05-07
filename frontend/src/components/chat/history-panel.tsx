import { X, Trash2, MessageCircle, Plus, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { type ChatSessionSummary } from "@/services/api"

interface HistoryPanelProps {
  sessions: ChatSessionSummary[]
  currentSessionId: string | null
  isOpen: boolean
  loading: boolean
  error?: string | null
  onClose: () => void
  onSelectSession: (sessionId: string) => void
  onCreateNew: () => void
  onDeleteSession: (sessionId: string) => void
  onClearHistory: () => void
}

export function HistoryPanel({
  sessions,
  currentSessionId,
  isOpen,
  loading,
  error,
  onClose,
  onSelectSession,
  onCreateNew,
  onDeleteSession,
  onClearHistory,
}: HistoryPanelProps) {
  const hasSessions = sessions.length > 0

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  const handleClearConfirm = () => {
    if (window.confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
      onClearHistory()
    }
  }

  const handleDeleteConfirm = (sessionId: string) => {
    if (window.confirm('Delete this chat session?')) {
      onDeleteSession(sessionId)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={cn(
          "fixed top-0 right-0 h-screen w-full sm:w-96 bg-background border-l border-border/50 shadow-lg z-50 flex flex-col transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="shrink-0 h-16 border-b border-border/30 flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold text-foreground">Chat History</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="shrink-0 px-4 py-2 border-b border-border/30">
          <Button
            onClick={onCreateNew}
            className="w-full"
            variant="default"
            size="sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 px-4 py-4">
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm mb-4">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-muted-foreground text-sm">Loading history...</div>
            </div>
          ) : !hasSessions ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageCircle className="h-12 w-12 text-muted-foreground/30 mb-2" />
              <p className="text-muted-foreground text-sm">No chat history yet</p>
              <p className="text-muted-foreground/70 text-xs mt-1">
                Your chats will appear here
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={cn(
                    "p-3 rounded-lg border transition-all duration-200 cursor-pointer group",
                    currentSessionId === session.session_id
                      ? "bg-primary/10 border-primary/50"
                      : "bg-secondary/50 border-border/30 hover:bg-secondary hover:border-border/50"
                  )}
                  onClick={() => onSelectSession(session.session_id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground line-clamp-2">
                        {session.title || session.last_question || "Untitled Chat"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                      </p>
                      <p className="text-xs text-muted-foreground/70 mt-0.5">
                        {formatDate(session.updated_at)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteConfirm(session.session_id)
                      }}
                      className="shrink-0 p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        {hasSessions && (
          <div className="shrink-0 border-t border-border/30 p-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearConfirm}
              className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All History
            </Button>
          </div>
        )}
      </div>
    </>
  )
}
