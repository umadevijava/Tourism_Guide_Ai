import { X, Trash2, MessageCircle, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import type { HistoryItem } from "@/services/history"
import { formatTimestamp, groupHistoryByDate } from "@/services/history"

interface HistoryPanelProps {
  history: HistoryItem[]
  isOpen: boolean
  isLoading?: boolean
  onClose: () => void
  onSelectItem: (item: HistoryItem) => void
  onClearHistory: () => void
  onRemoveItem: (id: string) => void
}

export function HistoryPanel({
  history,
  isOpen,
  isLoading,
  onClose,
  onSelectItem,
  onClearHistory,
  onRemoveItem,
}: HistoryPanelProps) {
  const groupedHistory = groupHistoryByDate(history)
  const hasHistory = history.length > 0

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          "fixed top-0 left-0 h-screen w-80 bg-background border-r border-border/50 shadow-lg z-50 transition-transform duration-300 flex flex-col",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border/30">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <MessageCircle size={20} />
            History
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X size={18} />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-3 border-b border-border/30">
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={onClose}
          >
            <Plus size={16} />
            New Chat
          </Button>
        </div>

        {/* History List */}
        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center h-40 text-muted-foreground">
              Loading history...
            </div>
          ) : !hasHistory ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground text-sm p-4">
              <MessageCircle size={32} className="opacity-20 mb-2" />
              <p>No chat history yet</p>
              <p className="text-xs opacity-75 mt-2">Start a new conversation to see it here</p>
            </div>
          ) : (
            <div className="p-2 space-y-4">
              {Object.entries(groupedHistory).map(([date, items]) => (
                items.length > 0 && (
                  <div key={date}>
                    <div className="px-3 py-2">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        {date}
                      </p>
                    </div>
                    <div className="space-y-2">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="group flex items-start gap-2 p-3 rounded-lg hover:bg-accent/50 cursor-pointer transition-colors relative"
                          onClick={() => {
                            onSelectItem(item)
                            onClose()
                          }}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm line-clamp-2 break-words">
                              {item.query}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {formatTimestamp(item.timestamp)}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              onRemoveItem(item.id)
                            }}
                          >
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        {hasHistory && (
          <div className="border-t border-border/30 p-4">
            <Button
              variant="outline"
              size="sm"
              className="w-full text-destructive hover:text-destructive"
              onClick={() => {
                if (window.confirm('Clear all chat history? This cannot be undone.')) {
                  onClearHistory()
                }
              }}
            >
              <Trash2 size={14} className="mr-2" />
              Clear All
            </Button>
          </div>
        )}
      </div>
    </>
  )
}
