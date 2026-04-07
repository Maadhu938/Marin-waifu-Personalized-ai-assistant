import React, { useRef, useEffect } from 'react';

const ChatMessage = ({ msg }) => {
  const isUser = msg.role === 'user';
  const isSystem = msg.role === 'system';

  if (isSystem) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', margin: '1rem 0', opacity: 0.5, fontSize: '0.75rem' }}>
        System: {msg.content}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', marginBottom: '1rem', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', margin: '0 0.5rem' }}>
        {isUser ? 'You' : 'Marin'} {msg.emotion && !isUser && <span style={{ opacity: 0.7 }}>({msg.emotion})</span>}
      </div>
      
      <div 
        style={{
          maxWidth: '85%',
          padding: '0.75rem 1rem',
          borderRadius: '1rem',
          backgroundColor: isUser ? 'var(--user-msg-bg)' : 'var(--marin-msg-bg)',
          border: `1px solid ${isUser ? 'var(--user-msg-border)' : 'var(--marin-msg-border)'}`,
          borderTopRightRadius: isUser ? '0.125rem' : '1rem',
          borderTopLeftRadius: isUser ? '1rem' : '0.125rem',
          color: isUser ? '#ffffff' : 'var(--text-primary)',
          boxShadow: isUser ? '0 4px 20px rgba(255, 107, 157, 0.1)' : '0 4px 20px rgba(0, 0, 0, 0.2)',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap'
        }}
      >
        <p>{msg.content}</p>
        
        {msg.isThinking && (
          <span style={{ display: 'inline-block', width: '0.5rem', height: '0.5rem', marginLeft: '0.25rem', backgroundColor: '#fff', borderRadius: '50%', animation: 'pulse 1s infinite' }}></span>
        )}
      </div>
    </div>
  );
};

export default function ChatPanel({ messages, onSendMessage, isConnected, isRecording }) {
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputRef.current) return;
    
    const text = inputRef.current.value.trim();
    if (text && isConnected) {
      onSendMessage(text);
      inputRef.current.value = '';
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', maxWidth: '42rem', margin: '0 auto', overflow: 'hidden', position: 'relative' }}>
      <div 
        ref={scrollRef}
        className="scrollbar-hide"
        style={{ flex: 1, overflowY: 'auto', padding: '1rem 1.5rem', scrollBehavior: 'smooth' }}
      >
        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}
      </div>
      
      <div style={{ padding: '1rem', borderTop: '1px solid var(--panel-border)', backgroundColor: 'rgba(0,0,0,0.2)' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <div style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'center', opacity: isRecording ? 0.5 : 1, pointerEvents: isRecording ? 'none' : 'auto', transition: 'all 0.3s' }}>
                <input 
                    ref={inputRef}
                    type="text" 
                    placeholder="Type a message..." 
                    style={{
                        width: '100%',
                        backgroundColor: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '9999px',
                        padding: '0.75rem 1.25rem',
                        color: '#fff',
                        outline: 'none',
                        transition: 'all 0.3s'
                    }}
                    onFocus={(e) => { e.target.style.borderColor = 'var(--accent-color)'; e.target.style.backgroundColor = 'rgba(255,255,255,0.1)'; }}
                    onBlur={(e) => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; e.target.style.backgroundColor = 'rgba(255,255,255,0.05)'; }}
                />
            </div>
            
            <button 
                type="submit" 
                disabled={!isConnected || isRecording}
                style={{
                    padding: '0.75rem',
                    borderRadius: '9999px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: isConnected ? 'var(--accent-color)' : 'rgba(255,255,255,0.1)',
                    color: isConnected ? '#fff' : 'rgba(255,255,255,0.5)',
                    border: 'none',
                    cursor: isConnected && !isRecording ? 'pointer' : 'not-allowed',
                    boxShadow: isConnected ? '0 0 15px var(--accent-glow)' : 'none',
                    transition: 'all 0.3s'
                }}
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </form>
      </div>
    </div>
  );
}
