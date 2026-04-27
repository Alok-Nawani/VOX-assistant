import React, { useEffect, useRef } from 'react';
import { Copy, Code, Image as ImageIcon } from 'lucide-react';

export default function TranscriptArea({ messages, voiceOnly }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (voiceOnly || messages.length === 0) return null;

  const renderContent = (text) => {
    if (!text) return null;
    const parts = text.split(/(```[\s\S]*?```)/g);
    
    return parts.map((part, i) => {
      if (part.startsWith('```')) {
        const lines = part.split('\n');
        const lang = lines[0].replace('```', '').trim();
        const code = lines.slice(1, -1).join('\n');
        
        return (
          <div key={i} className="code-block-container">
            <div className="code-header">
              <span><Code size={14} /> {lang || 'CODE'}</span>
              <button onClick={() => navigator.clipboard.writeText(code)} title="Copy Code">
                <Copy size={14} />
              </button>
            </div>
            <pre className="code-content">
              <code>{code}</code>
            </pre>
          </div>
        );
      }
      return <p key={i} className="text-paragraph">{part}</p>;
    });
  };

  return (
    <div className="transcript-container animate-fade-in">
      <div className="transcript-header">
        <span>VOX // NEURAL_UPLINK_STABLE</span>
        <div className="pulse-dot" />
      </div>
      
      <div className="transcript-box" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="transcript-user">
                <span className="user-label">UPLINK:</span> {msg.content}
              </div>
            ) : (
              <div className="transcript-vox">
                <div className="vox-text">
                  {renderContent(msg.content)}
                </div>
                
                {msg.data?.type === 'image_generation' && (
                  <div className="generated-image-container">
                    <div className="image-header">
                      <div className="image-header-title">
                        <ImageIcon size={16} /> VISUAL_SYNTHESIS_COMPLETE
                      </div>
                      <div className="image-actions">
                        <button onClick={() => window.open(msg.data.image_url, '_blank')} title="Expand">
                          <ImageIcon size={14} />
                        </button>
                        <a href={msg.data.image_url} download={`vox_art_${Date.now()}.png`} title="Download">
                          <ImageIcon size={14} />
                        </a>
                      </div>
                    </div>
                    <img src={msg.data.image_url} alt={msg.data.prompt} className="generated-image" />
                    <div className="image-caption">PROMPT: {msg.data.prompt}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
