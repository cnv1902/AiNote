import { useEffect, useMemo, useRef, useState } from 'react';
import { qaAPI } from '../services/api';
import './ChatWidget.css';

type Message = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  // Simple greeting once when opening
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: 'greet',
          role: 'assistant',
          content: 'Xin chào! Hãy đặt câu hỏi dựa trên ghi chú của bạn.',
        },
      ]);
    }
  }, [isOpen, messages.length]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  const onSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: `${Date.now()}_u`, role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await qaAPI.ask(text);
      const assistantMsg: Message = {
        id: `${Date.now()}_a`,
        role: 'assistant',
        content: res?.answer ?? 'Xin lỗi, không nhận được phản hồi.',
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}_err`,
          role: 'system',
          content: 'Không thể gửi câu hỏi. Vui lòng đăng nhập và thử lại.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSend();
    }
  };

  return (
    <>
      {/* Floating button */}
      <button
        className={`chat-fab ${isOpen ? 'open' : ''}`}
        aria-label={isOpen ? 'Đóng chatbot' : 'Mở chatbot'}
        onClick={() => setIsOpen((v) => !v)}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="chat-fab-icon"
        >
          <path d="M2 12c0-4.97 4.477-9 10-9s10 4.03 10 9-4.477 9-10 9c-1.33 0-2.596-.23-3.75-.65L2 22l1.24-3.72C2.46 16.79 2 14.96 2 13v-1z" />
        </svg>
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-title">Trợ lý ghi chú</div>
            <button className="chat-close" onClick={() => setIsOpen(false)} aria-label="Đóng">×</button>
          </div>

          <div className="chat-messages" ref={listRef}>
            {messages.map((m) => (
              <div key={m.id} className={`chat-message ${m.role}`}>
                <div className="bubble">
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant">
                <div className="bubble typing">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </div>
              </div>
            )}
          </div>

          <div className="chat-input">
            <textarea
              placeholder="Nhập câu hỏi của bạn..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={2}
            />
            <button className="send-btn" disabled={!canSend} onClick={onSend}>
              Gửi
            </button>
          </div>
        </div>
      )}
    </>
  );
}
