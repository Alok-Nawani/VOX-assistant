import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, History, Settings, User, Globe, Volume2, Shield, Bell, Trash2, Cpu, Database, Camera, Upload } from 'lucide-react';

const SystemOverlays = ({ type, isOpen, onClose, user, onLanguageChange, currentLanguage, onToneChange, currentTone }) => {
  const [history, setHistory] = useState([]);
  const [facts, setFacts] = useState({});
  const [loading, setLoading] = useState(false);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      if (type === 'history') fetchHistory();
      if (type === 'profile') fetchFacts();
      if (type === 'settings') {
        const synth = window.speechSynthesis;
        const loadVoices = () => {
          const v = synth.getVoices();
          if (v.length > 0) setVoices(v);
        };
        loadVoices();
        // Fallback for browsers where onvoiceschanged is finicky
        setTimeout(loadVoices, 500);
        if (synth.onvoiceschanged !== undefined) {
          synth.onvoiceschanged = loadVoices;
        }
      }
    }
  }, [isOpen, type]);

  const handlePurgeHistory = async () => {
    if (!window.confirm("Purge all neural logs? This action is irreversible.")) return;
    try {
      const token = localStorage.getItem('vox_token');
      await fetch('/api/history/clear', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setHistory([]);
      alert("Neural buffer purged.");
    } catch (e) {
      console.error("Failed to purge history");
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('vox_token');
      const response = await fetch('/api/history', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setHistory(Array.isArray(data) ? data.reverse() : []);
    } catch (e) {
      console.error("Failed to fetch history");
    } finally {
      setLoading(false);
    }
  };

  const fetchFacts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('vox_token');
      const response = await fetch('/api/facts', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setFacts(data || {});
    } catch (e) {
      console.error("Failed to fetch facts");
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64String = reader.result;
      setAvatarUrl(base64String);
      
      try {
        const token = localStorage.getItem('vox_token');
        await fetch('/api/user/avatar', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ avatar_url: base64String })
        });
        
        // Update local storage user object
        const savedUser = JSON.parse(localStorage.getItem('vox_user'));
        savedUser.avatar_url = base64String;
        localStorage.setItem('vox_user', JSON.stringify(savedUser));
      } catch (err) {
        console.error("Failed to sync avatar");
      }
    };
    reader.readAsDataURL(file);
  };

  const overlayVariants = {
    hidden: { x: '100%', opacity: 0 },
    visible: { x: 0, opacity: 1, transition: { type: 'spring', damping: 25, stiffness: 200 } },
    exit: { x: '100%', opacity: 0 }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div 
          className="system-overlay-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div 
            className="system-overlay-content"
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="overlay-header">
              <div className="overlay-title">
                {type === 'history' && <><History size={20} /> Neural Logs</>}
                {type === 'settings' && <><Settings size={20} /> Kernel Configuration</>}
                {type === 'profile' && <><User size={20} /> Biometric Profile</>}
              </div>
              <button className="overlay-close" onClick={onClose}><X size={24} /></button>
            </div>

            <div className="overlay-body">
              {type === 'history' && (
                <div className="history-list">
                  {loading ? (
                    <div className="loader">Synchronizing temporal logs...</div>
                  ) : history.length === 0 ? (
                    <div className="empty-state">Neural buffer is currently clear.</div>
                  ) : (
                    history.map((log, i) => (
                      <div key={i} className={`history-item ${log.role}`}>
                        <div className="item-meta">{log.role === 'user' ? 'ALOK' : 'VOX'} // {new Date().toLocaleTimeString()}</div>
                        <div className="item-content">{log.content}</div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {type === 'profile' && (
                <div className="profile-details">
                  <div className="profile-header">
                    <div className="avatar-uploader-container">
                      <div className="profile-avatar-large">
                        {avatarUrl ? (
                          <img src={avatarUrl} alt="Avatar" className="avatar-img-round" />
                        ) : (
                          user?.full_name?.charAt(0).toUpperCase() || 'A'
                        )}
                      </div>
                      <button className="upload-btn-mini" onClick={() => fileInputRef.current.click()}>
                        <Camera size={14} />
                      </button>
                      <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        accept="image/*"
                        onChange={handleAvatarUpload}
                      />
                    </div>
                    <h2>{user?.full_name || 'System Operator'}</h2>
                    <p className="profile-id">IDENTITY: {user?.username || 'GUEST'}</p>
                  </div>
                  
                  <div className="section-title"><Database size={16} /> Pattern Recognition (Facts)</div>
                  <div className="facts-grid">
                    {loading ? (
                      <div className="loader">Accessing memory bank...</div>
                    ) : Object.entries(facts).length > 0 ? (
                      Object.entries(facts).map(([k, v]) => (
                        <div key={k} className="fact-card">
                          <div className="fact-key">{k.replace(/_/g, ' ').toUpperCase()}</div>
                          <div className="fact-value">{v}</div>
                        </div>
                      ))
                    ) : (
                      <div className="empty-state">No persistent patterns detected yet.</div>
                    )}
                  </div>
                </div>
              )}

              {type === 'settings' && (
                <div className="settings-options">
                  <div className="setting-group">
                    <label><Globe size={18} /> Neural Language Link</label>
                    <select value={currentLanguage} onChange={(e) => onLanguageChange(e.target.value)}>
                      <option value="en">English (Default)</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                      <option value="de">Deutsch</option>
                      <option value="hi">Hindi</option>
                    </select>
                  </div>

                  <div className="setting-group">
                    <label><Cpu size={18} /> Personality Matrix (Tone)</label>
                    <select value={currentTone} onChange={(e) => onToneChange(e.target.value)}>
                      <option value="Jarvis">Jarvis (Precise)</option>
                      <option value="Friendly">Friendly (Warm)</option>
                      <option value="Direct">Direct (Efficient)</option>
                      <option value="Sarcastic">Sarcastic (Witty)</option>
                      <option value="Professional">Professional (Formal)</option>
                    </select>
                  </div>

                  <div className="setting-group">
                    <label><Volume2 size={18} /> Synthetic Voice Module</label>
                    <select value={selectedVoice} onChange={(e) => setSelectedVoice(e.target.value)}>
                      {voices.map(voice => (
                        <option key={voice.name} value={voice.name}>{voice.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="setting-group">
                    <label><Shield size={18} /> Memory Integrity</label>
                    <button className="danger-btn" onClick={handlePurgeHistory}>
                    <Trash2 size={16} /> Purge Neural Buffer
                  </button>
                  </div>

                  <div className="system-info">
                    <div className="info-row">
                      <Cpu size={14} /> <span>VOX_KERNEL_V2</span>
                    </div>
                    <div className="info-row">
                      <Database size={14} /> <span>DATABASE_UPLINK_SECURE</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SystemOverlays;
