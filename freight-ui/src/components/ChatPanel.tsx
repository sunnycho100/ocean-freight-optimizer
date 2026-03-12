import React, { useState, useRef, useEffect, useMemo } from 'react';
import { API_BASE } from '../config';
import '../styles/chat-panel.css';

/** Lightweight markdown-ish formatting for bot replies */
function formatMessage(text: string): React.ReactNode {
  const lines = text.split('\n');
  return lines.map((line, i) => {
    // Headings: ### text → styled label
    const headingMatch = line.match(/^#{1,4}\s+(.+)$/);
    if (headingMatch) {
      return (
        <span key={i} className="chat-heading">
          {i > 0 && <br />}
          {headingMatch[1]}
        </span>
      );
    }

    // Bullet: - text → • text
    let processed = line.replace(/^- /, '• ');

    // Bold: **text**
    const parts = processed.split(/(\*\*[^*]+\*\*)/g);
    const formatted = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
    return (
      <span key={i}>
        {i > 0 && <br />}
        {formatted}
      </span>
    );
  });
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: '안녕하세요, PNS 챗봇입니다.\n운임, 경로, 캐리어 비교에 대해 물어봐주세요!' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.filter((m) => m !== messages[0]), // exclude initial greeting
        }),
      });
      const data = await res.json();
      if (data.reply) {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.error || 'Something went wrong.' },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Failed to reach the server. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating chat button */}
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} title="Freight Assistant">
          <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span className="chat-panel-title">PNS 챗봇</span>
            <button className="chat-panel-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          <div className="chat-panel-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg chat-msg--${msg.role}`}>
                <div className="chat-msg-bubble">
                  {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg chat-msg--assistant">
                <div className="chat-msg-bubble chat-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-panel-input">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask about routes, rates..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
