import React from 'react';

export default function VoxOrb({ state, audioLevel = 0 }) {
  // state can be: 'idle', 'listening', 'processing', 'responding'
  
  let statusText = "System Online";
  if (state === 'listening') statusText = "Listening...";
  if (state === 'processing') statusText = "Processing Data...";
  if (state === 'responding') statusText = "Transmitting...";

  // Calculate dynamic scale based on audio volume when listening
  const isListening = state === 'listening';
  // audioLevel is 0-1. Max scale expansion of +0.4
  const dynamicScale = isListening ? 1 + (audioLevel * 0.4) : 1;
  const dynamicGlow = isListening ? 0.3 + (audioLevel * 0.7) : null;

  return (
    <div className="vox-orb-wrapper">
      <div 
        className={`vox-orb-container ${state}`}
        style={{
          transform: isListening ? `scale(${dynamicScale})` : undefined,
          transition: isListening ? 'transform 0.05s ease-out' : 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }}
      >
        <div 
          className="vox-orb-aura"
          style={{
            opacity: isListening ? dynamicGlow : undefined,
            filter: isListening ? `blur(${20 + (audioLevel * 20)}px)` : undefined,
            transition: isListening ? 'none' : 'all 0.5s ease'
          }}
        ></div>
        <div className="vox-orb-core"></div>
        <div className="vox-orb-ring-1"></div>
        <div className="vox-orb-ring-2"></div>
        <div className="vox-orb-ring-3"></div>
      </div>
      <div className={`status-text ${state !== 'idle' ? 'visible' : ''}`}>
        {statusText}
      </div>
    </div>
  );
}
