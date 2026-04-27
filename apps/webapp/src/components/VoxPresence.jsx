import React from 'react';
import { motion } from 'framer-motion';

const VoxPresence = ({ state, onClick }) => {
  const isResponding = state === 'responding';
  const isListening = state === 'listening';
  
  return (
    <div className="vox-presence-container" onClick={onClick} title="Click to Wake Vox">
      <motion.div
        className="vox-bot-wrapper"
        animate={{
          y: [0, -15, 0],
          scale: isResponding ? [1, 1.05, 1] : 1,
          rotate: isListening ? [0, 5, -5, 0] : 0
        }}
        transition={{
          y: { duration: 4, repeat: Infinity, ease: "easeInOut" },
          scale: { duration: 0.5, repeat: isResponding ? Infinity : 0 },
          rotate: { duration: 2, repeat: isListening ? Infinity : 0 }
        }}
      >
        <img src="/assets/cute_bot.png" alt="Vox" className="vox-bot-img" />
        {isResponding && (
          <div className="vox-bot-glow" />
        )}
      </motion.div>
      <div className="vox-presence-status">
        <div className={`status-dot ${state}`} />
        <span>VOX_{state.toUpperCase()}</span>
      </div>
      <div className="vox-presence-hint">DIAGNOSTIC_COMPANION_V2</div>
    </div>
  );
};

export default VoxPresence;
