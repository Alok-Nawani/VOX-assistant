import React, { useState } from 'react';
import { Mic, Globe, Volume2, VolumeX, Send } from 'lucide-react';

export default function ControlPanel({ 
  isListening, 
  onToggleListen, 
  voiceOnly, 
  onToggleVoiceOnly,
  isMuted,
  onToggleMute,
  language,
  onLanguageChange,
  onTextSubmit
}) {
  const [textInput, setTextInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim() && onTextSubmit) {
      onTextSubmit(textInput);
      setTextInput('');
    }
  };

  return (
    <div className="control-panel-container">
      <form className="cli-form" onSubmit={handleSubmit}>
        <span className="cli-prompt">{'>'}</span>
        <input 
          type="text" 
          className="cli-input"
          placeholder="Awaiting command..."
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
        />
        <button type="submit" className="cli-submit-btn" disabled={!textInput.trim()}>
          <Send size={20} />
        </button>
      </form>

      <div className="control-panel">
        <button 
          className={`toggle-btn ${language !== 'en' ? 'active' : ''}`}
          onClick={() => onLanguageChange(language === 'en' ? 'es' : 'en')}
          title="Toggle Language"
        >
          <Globe size={20} /> {language.toUpperCase()}
        </button>

        <button 
          className={`toggle-btn ${isMuted ? 'active' : ''}`}
          onClick={onToggleMute}
          title={isMuted ? "Unmute Vox" : "Mute Vox"}
        >
          {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          {isMuted ? 'Muted' : 'Sound On'}
        </button>

        <button 
          className={`mic-btn ${isListening ? 'active' : ''}`} 
          onClick={onToggleListen}
        >
          <Mic size={32} />
        </button>

        <button 
          className={`toggle-btn ${voiceOnly ? 'active' : ''}`}
          onClick={onToggleVoiceOnly}
          title="Voice Only Mode (Hide UI Text)"
        >
          <Send size={20} /> 
          {voiceOnly ? 'Voice Only' : 'Text On'}
        </button>
      </div>
    </div>
  );
}
