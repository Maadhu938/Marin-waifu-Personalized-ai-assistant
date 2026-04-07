import { useState, useEffect, useRef } from 'react'
import AvatarEngine from './components/AvatarEngine'
import ChatPanel from './components/ChatPanel'
import './index.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hey! I\'m Marin. Welcome to the new setup~ ✨', emotion: 'excited' }
  ])
  const [emotion, setEmotion] = useState('happy')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    // Connect to WebSocket
    // Adjust URL as needed for deployment
    const wsUrl = `ws://localhost:8005/ws/chat`;
    
    const connect = () => {
        ws.current = new WebSocket(wsUrl);
        
        ws.current.onopen = () => {
            setIsConnected(true);
            console.log('Connected to Marin');
        };
        
        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'stream') {
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        const lastMsg = newMsgs[newMsgs.length - 1];
                        
                        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isThinking) {
                            lastMsg.content += data.content;
                        } else {
                            newMsgs.push({ role: 'assistant', content: data.content, emotion: data.emotion || 'happy', isThinking: true });
                        }
                        
                        if (data.emotion) setEmotion(data.emotion);
                        setIsSpeaking(true);
                        
                        return newMsgs;
                    });
                } else if (data.type === 'done') {
                    setIsSpeaking(false);
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        const lastMsg = newMsgs[newMsgs.length - 1];
                        if (lastMsg && lastMsg.role === 'assistant') {
                            lastMsg.isThinking = false;
                        }
                        return newMsgs;
                    });
                } else if (data.type === 'emotion') {
                    setEmotion(data.emotion);
                } else if (data.type === 'action') {
                    if (data.action === 'open_url') {
                        window.open(data.payload.url, '_blank');
                    }
                }
            } catch (e) {
                console.error("Failed to parse WS message", e, event.data);
            }
        };
        
        ws.current.onclose = () => {
            setIsConnected(false);
            setIsSpeaking(false);
            setTimeout(connect, 3000); // Reconnect
        };
    };
    
    connect();
    
    return () => {
        if (ws.current) ws.current.close();
    };
  }, []);

  const handleSendMessage = (text) => {
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    if (ws.current && isConnected) {
        ws.current.send(text);
        
        // Add a temporary thinking message
        setMessages(prev => [...prev, { role: 'assistant', content: '', emotion: 'curious', isThinking: true }]);
    }
  };

  return (
    <div style={{ 
        display: 'flex', 
        flexDirection: 'row', 
        height: '100vh', 
        width: '100vw',
        padding: '2rem',
        gap: '2rem',
        boxSizing: 'border-box'
    }}>
        {/* Left Side: Avatar */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <div style={{ width: '100%', height: '100%', maxWidth: '600px', maxHeight: '800px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <AvatarEngine emotion={emotion} isSpeaking={isSpeaking} />
            </div>
        </div>

        {/* Right Side: Chat interface */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <ChatPanel 
                messages={messages} 
                onSendMessage={handleSendMessage} 
                isConnected={isConnected} 
                isRecording={false} 
            />
        </div>
    </div>
  )
}

export default App
