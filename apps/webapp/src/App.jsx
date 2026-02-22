import React, { useState, useEffect, useRef } from 'react';
import {
  Mic, Settings, MessageSquare, Activity,
  Terminal, User, Compass, Calendar, Search,
  Battery, Cpu, HardDrive, Wifi, X, LogOut, ImagePlus, Camera, ShieldCheck, Menu
} from 'lucide-react';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('vox_token'));
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('vox_user')));
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [authForm, setAuthForm] = useState({ username: '', password: '' });

  const authenticatedFetch = async (url, options = {}) => {
    const authOptions = {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    };
    const res = await fetch(url, authOptions);
    if (res.status === 401) {
      handleLogout();
      return null;
    }
    return res;
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/signup';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('vox_token', data.access_token);
        localStorage.setItem('vox_user', JSON.stringify(data.user));
      } else {
        alert(data.detail || "Authentication failed");
      }
    } catch (err) { alert("Backend offline"); }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('vox_token');
    localStorage.removeItem('vox_user');
  };

  const [activeTab, setActiveTab] = useState('dashboard');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, sender: 'assistant', text: "Neural link established. System Operator VOX is active. How shall we proceed, Alok?" }
  ]);
  const [systemEvents, setSystemEvents] = useState([
    "Kernel initialization complete",
    "Neural link established on port 8000",
    "Optical sensor standby",
    "Security protocols active"
  ]);

  useEffect(() => {
    const logs = [
      "Accessing local kernel...",
      "Syncing neural weights...",
      "Scanning optical perimeter...",
      "Heartbeat: OK",
      "Analyzing user patterns...",
      "Encryption cycles: ACTIVE"
    ];
    const interval = setInterval(() => {
      const log = logs[Math.floor(Math.random() * logs.length)];
      setSystemEvents(prev => [log, ...prev].slice(0, 10));
    }, 4000);
    return () => clearInterval(interval);
  }, []);
  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const chatEndRef = useRef(null);

  const [isTtsEnabled, setIsTtsEnabled] = useState(true);
  const [personality, setPersonality] = useState('Professional');

  const speak = (text) => {
    if (!isTtsEnabled) return;
    setIsSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    const voices = window.speechSynthesis.getVoices();
    const premiumVoice = voices.find(v => v.name.includes('Samantha') || v.name.includes('Daniel') || v.lang === 'en-US');
    if (premiumVoice) utterance.voice = premiumVoice;
    window.speechSynthesis.speak(utterance);
  };

  const [history, setHistory] = useState([]);
  const [facts, setFacts] = useState({});
  const [calendar, setCalendar] = useState(null);

  const [systemStats, setSystemStats] = useState({
    cpu: 0,
    ram: 0,
    disk: 0,
    battery: 100
  });

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!token) return;
    // Fetch real-time system stats
    const fetchStatus = async () => {
      try {
        const response = await authenticatedFetch('/api/status');
        if (!response) return;
        if (response.ok) {
          const data = await response.json();
          setSystemStats(data);
        }
      } catch (e) { console.log("Stats poll fail"); }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [token]);

  // Fetch tab-specific data and sync chat history
  useEffect(() => {
    if (!token) return;
    const syncData = async () => {
      try {
        if (activeTab === 'conversations' || activeTab === 'dashboard') {
          const res = await authenticatedFetch('/api/history');
          if (!res) return;
          const data = await res.json();
          setHistory(data);

          if (activeTab === 'dashboard') {
            // Map history to chat message format
            const newMessages = data.map((item, index) => ({
              id: `history-${index}`,
              sender: item.role === 'user' ? 'user' : 'assistant',
              text: item.content
            }));

            // Check if there's a new proactive message from Vox to speak
            if (activeTab === 'dashboard' && newMessages.length > messages.length) {
              const lastMsg = newMessages[newMessages.length - 1];
              if (lastMsg.sender === 'assistant' && !messages.some(m => m.text === lastMsg.text)) {
                speak(lastMsg.text);
              }
            }
            setMessages(newMessages);
          }
        }

        if (activeTab === 'schedule') {
          authenticatedFetch('/api/calendar').then(res => res ? res.json() : null).then(setCalendar);
        } else if (activeTab === 'dashboard') {
          authenticatedFetch('/api/facts').then(res => res ? res.json() : null).then(setFacts);
        }
      } catch (e) { console.log("Sync failed"); }
    };

    syncData();
    const interval = setInterval(syncData, 5000); // Poll history every 5s for proactivity
    return () => clearInterval(interval);
  }, [activeTab, messages.length, token]);

  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        processCommand(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => setIsListening(false);
      recognitionRef.current.onerror = () => setIsListening(false);
    }
  }, []);

  const processCommand = async (text) => {
    if (!text.trim() || !token) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text,
      image: selectedImage?.preview
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setSelectedImage(null);

    // Add thinking state
    const thinkingId = Date.now() + 1;
    setMessages(prev => [...prev, { id: thinkingId, sender: 'assistant', text: "Vox is thinking..." }]);

    try {
      const payload = { text };
      if (userMessage.image) {
        payload.image = userMessage.image; // Send base64 image if exists
      }

      const response = await authenticatedFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response) return;
      const data = await response.json();

      let finalResponse = data.response;
      let isCamera = data.data?.action === 'camera_capture';

      if (isCamera) {
        finalResponse = "3....2....1....cheese";
      }

      setMessages(prev => prev.filter(m => m.id !== thinkingId).concat([{
        id: Date.now() + 2,
        sender: 'assistant',
        text: finalResponse
      }]));

      // Make Vox talk!
      speak(finalResponse);

      // Handle System Commands from data payload
      if (isCamera) {
        startCamera();
        let timer = 3;
        setCountdown(timer);
        const interval = setInterval(() => {
          timer -= 1;
          setCountdown(timer);
          if (timer === 0) {
            clearInterval(interval);
            capturePhoto();
            setCountdown(0);
          }
        }, 1000);
      }

    } catch (error) {
      setMessages(prev => prev.filter(m => m.id !== thinkingId).concat([{
        id: Date.now() + 2,
        sender: 'assistant',
        text: "Vox error."
      }]));
    }
  };

  const handleSend = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      processCommand(inputValue);
      setInputValue('');
    }
  };

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else if (recognitionRef.current) {
      recognitionRef.current.start();
      setIsListening(true);
    } else {
      alert("Speech not supported.");
    }
  };
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const inputRef = useRef(null);

  const handleSearchClick = () => {
    inputRef.current?.focus();
    setActiveTab('dashboard');
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage({
          file: file,
          preview: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const startCamera = async () => {
    setIsCameraOpen(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      alert("Camera access denied or not found.");
      setIsCameraOpen(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
    }
    setIsCameraOpen(false);
  };

  const capturePhoto = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/png');

      // Save locally via API
      try {
        const response = await authenticatedFetch('/api/system/save-image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: dataUrl, prefix: "Vox_Capture" })
        });
        const result = await response.json();
        if (result.success) {
          const [loc, realPath] = result.path.split('@');
          const isCloud = loc === 'Cloud Storage';

          setMessages(prev => [...prev, {
            id: Date.now(),
            sender: 'assistant',
            text: isCloud
              ? `Optical data secured in Cloud Sanctuary: ${realPath}`
              : `Optical data secured locally: ${realPath}`,
            image: dataUrl,
            downloadUrl: dataUrl, // Always allow download from browser
            fileName: realPath.split('/').pop()
          }]);
        }
      } catch (err) {
        console.error("Local save failed:", err);
      }

      setSelectedImage({
        file: null,
        preview: dataUrl
      });
      stopCamera();
    }
  };

  if (!token) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="orb-container" style={{ padding: '0 0 2rem 0' }}>
            <div className="orb" style={{ width: '80px', height: '80px' }}></div>
          </div>
          <h2 className="text-gradient" style={{ marginBottom: '0.5rem' }}>{authMode === 'login' ? 'Welcome Back' : 'Join Vox Core'}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
            {authMode === 'login' ? 'Initializing neural links...' : 'Create your digital identity'}
          </p>

          <form onSubmit={handleAuth}>
            <div className="auth-input-group">
              <label>Username</label>
              <input
                type="text"
                className="ai-input"
                placeholder="Ident Code"
                value={authForm.username}
                onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
                required
              />
            </div>
            <div className="auth-input-group">
              <label>Access Key</label>
              <input
                type="password"
                className="ai-input"
                placeholder="••••••••"
                value={authForm.password}
                onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="auth-btn">
              {authMode === 'login' ? 'Authenticate' : 'Initialize Core'}
            </button>
          </form>

          <p className="auth-switch">
            {authMode === 'login' ? "New operative?" : "Already registered?"}
            <span onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>
              {authMode === 'login' ? ' Create Identity' : ' Login'}
            </span>
          </p>
        </div>
      </div>
    );
  }

  const [permissions, setPermissions] = useState({
    camera: 'granted',
    microphone: 'granted',
    files: 'full-access',
    system: 'operator'
  });

  return (
    <div className={`app-container ${isMenuOpen ? 'menu-open' : ''}`}>
      {/* Tactical Image Zoom Overlay */}
      {zoomedImage && (
        <div className="zoom-overlay" onClick={() => setZoomedImage(null)}>
          <div className="zoom-content glass-panel" onClick={e => e.stopPropagation()}>
            <button className="close-zoom btn-icon" onClick={() => setZoomedImage(null)}><X size={24} /></button>
            <img src={zoomedImage} alt="Tactical Zoom" />
          </div>
        </div>
      )}

      {/* Profile Modal Overlay */}
      {isProfileOpen && (
        <div className="glass-panel" style={{
          position: 'absolute', top: '80px', right: '20px', width: '300px',
          zIndex: 1000, padding: '1.5rem', animation: 'fadeIn 0.3s ease'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 className="text-gradient">{user?.username || 'User'}'s Profile</h3>
            <button className="btn-icon" onClick={() => setIsProfileOpen(false)}><X size={16} /></button>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>Memory & Personalization Data</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Object.keys(facts).length > 0 ? Object.entries(facts).map(([k, v]) => (
              <div key={k} style={{ fontSize: '0.8rem', padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--accent-blue)' }}>{k.replace(/_/g, ' ')}:</span> {v}
              </div>
            )) : <p style={{ fontSize: '0.8rem', opacity: 0.5 }}>No deep facts recorded yet.</p>}
          </div>
        </div>
      )}

      {/* Camera Modal */}
      {isCameraOpen && (
        <div className="camera-modal">
          <div className="camera-content glass-panel">
            <div className="camera-header">
              <h3 className="text-gradient">Optical Sensor Link</h3>
              <button className="btn-icon" onClick={stopCamera}><X size={16} /></button>
            </div>
            <video ref={videoRef} autoPlay playsInline className="video-feed" />
            {countdown > 0 && <div className="countdown-overlay">{countdown}</div>}
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <div className="camera-controls">
              <button className="capture-btn" onClick={capturePhoto}>
                <div className="capture-inner"></div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Menu Overlay */}
      {isMenuOpen && <div className="menu-overlay" onClick={() => setIsMenuOpen(false)}></div>}

      {/* Sidebar */}
      <aside className="sidebar glass-panel">
        <div className="panel-header" style={{ textAlign: "center", marginTop: "1rem" }}>
          <h2 className="text-gradient">Vox Core</h2>
          <p>Status: {isListening ? 'Listening...' : 'Active'}</p>
        </div>

        <ul className="nav-menu" style={{ marginTop: "1rem", flex: 1 }}>
          <li className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => { setActiveTab('dashboard'); setIsMenuOpen(false); }}><Compass size={20} /> Dashboard</li>
          <li className={`nav-item ${activeTab === 'conversations' ? 'active' : ''}`} onClick={() => { setActiveTab('conversations'); setIsMenuOpen(false); }}><MessageSquare size={20} /> Conversations</li>
          <li className={`nav-item ${activeTab === 'terminal' ? 'active' : ''}`} onClick={() => { setActiveTab('terminal'); setIsMenuOpen(false); }}><Terminal size={20} /> Terminal</li>
          <li className={`nav-item ${activeTab === 'schedule' ? 'active' : ''}`} onClick={() => { setActiveTab('schedule'); setIsMenuOpen(false); }}><Calendar size={20} /> Schedule</li>
          <li className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => { setActiveTab('settings'); setIsMenuOpen(false); }}><Settings size={20} /> Settings</li>
        </ul>

        {/* User Identity Section */}
        <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            onClick={() => setIsProfileOpen(true)}
            style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '1.2rem', cursor: 'pointer' }}
          >
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => setIsProfileOpen(true)}>
            <p style={{ fontSize: '0.9rem', fontWeight: '600' }}>{user?.username || 'Operative'}</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>View Profile</p>
          </div>
          <button
            className="btn-icon"
            style={{ width: '32px', height: '32px' }}
            onClick={handleLogout}
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Integrated System Stats in Sidebar */}
        <div className="sidebar-stats" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <h4 className="text-gradient" style={{ fontSize: '0.8rem', marginBottom: '1rem', textTransform: 'uppercase' }}>System Telemetry</h4>

          <div className="stat-mini">
            <span>Kernel Hook:</span>
            <span className="status-item"><div className="status-dot online"></div> ACTIVE</span>
          </div>
          <div className="stat-mini">
            <span>Optical Link:</span>
            <span className="status-item"><div className="status-dot online"></div> READY</span>
          </div>

          <div style={{ marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
              <span>Memory</span>
              <span>{systemStats.ram}%</span>
            </div>
            <div className="progress-bar"><div className="progress-fill" style={{ width: `${systemStats.ram}%` }}></div></div>
          </div>

          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '1.5rem', fontStyle: 'italic', opacity: 0.8 }}>
            {Object.keys(facts).length > 0
              ? "Vox is actively learning and adapting to your patterns."
              : "No personal facts learned yet."}
          </p>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="main-content glass-panel">
        <header className="header glass-panel" style={{ borderBottom: '1px solid var(--border-color)', zIndex: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <button className="btn-icon hamburger" onClick={() => setIsMenuOpen(!isMenuOpen)} title="System Menu">
              <Menu size={24} color="var(--accent-blue)" />
            </button>
            <div className="header-title">
              <h2 className="text-gradient" style={{ fontSize: '1.4rem' }}>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
              <p className="operator-text" style={{ fontSize: '0.75rem', marginTop: '-2px' }}>System Logic: OPTIMAL</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn-icon" onClick={() => { /* handle search */ }}><Search size={20} /></button>
            <button className="btn-icon" onClick={() => setIsProfileOpen(!isProfileOpen)}><User size={20} /></button>
          </div>
        </header>

        <div className="chat-container">
          {activeTab === 'dashboard' && (
            <div className="neural-center">
              {/* System Event Ticker Backdrop */}
              <div className="system-ticker">
                {systemEvents.map((ev, i) => (
                  <div key={i} className="ticker-item">
                    <span className="ticker-timestamp">[{new Date().toLocaleTimeString()}]</span> {ev}
                  </div>
                ))}
              </div>

              {/* Central 3D Glowing Ball */}
              <div className="orb-wrapper">
                <div className={`neural-orb ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
                  <div className="inner-glow"></div>
                  <div className="core-light"></div>
                  <div className="energy-rings"></div>
                </div>
              </div>

              <div className="floating-messages">
                {messages.map((msg) => (
                  <div key={msg.id} className={`message ${msg.sender} glass-message`}>
                    {msg.image && (
                      <div className="image-container">
                        <img
                          src={msg.image}
                          alt="Captured Data"
                          className="message-image"
                          style={{ maxWidth: '100%', borderRadius: '8px', marginBottom: '0.5rem', display: 'block', cursor: 'zoom-in' }}
                          onClick={() => setZoomedImage(msg.image)}
                        />
                        <button className="zoom-btn" onClick={() => setZoomedImage(msg.image)}>
                          <Search size={14} /> Full View
                        </button>
                      </div>
                    )}
                    <p>{msg.text}</p>
                    {msg.downloadUrl && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <a
                          href={msg.downloadUrl}
                          download={msg.fileName || 'vox_capture.png'}
                          className="btn-download"
                        >
                          Download Remote Capture
                        </a>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            </div>
          )}

          {activeTab === 'conversations' && (
            <div className="tab-content scroll-v" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '2rem' }}>
              <h3 className="text-gradient">Transmission History</h3>
              {history.map((log, i) => (
                <div key={i} className="glass-panel" style={{ padding: '1rem', borderLeft: log.role === 'user' ? '4px solid var(--accent-blue)' : '4px solid var(--accent-purple)' }}>
                  <strong style={{ fontSize: '0.8rem', opacity: 0.6 }}>{log.role.toUpperCase()}</strong>
                  <p style={{ marginTop: '0.5rem' }}>{log.content}</p>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="tab-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', textAlign: 'center' }}>
              <Calendar size={64} style={{ opacity: 0.1, marginBottom: '2rem' }} />
              <h3 className="text-gradient">Agenda Sync</h3>
              {systemStats.has_google_creds ? (
                <>
                  <p style={{ maxWidth: '400px', margin: '1rem auto', color: 'var(--text-secondary)' }}>
                    Credentials detected. Vox is ready to sync with your digital timeline.
                  </p>
                  <div className="glass-panel" style={{ padding: '1rem', fontSize: '0.9rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
                    Action Required: Ask "Vox, what's on my schedule today?" to authorize the link.
                  </div>
                </>
              ) : (
                <>
                  <p style={{ maxWidth: '400px', margin: '1rem auto', color: 'var(--text-secondary)' }}>
                    Vox can manage your Google Calendar events. To enable this link, place your
                    <code style={{ color: 'var(--accent-blue)' }}> google_credentials.json</code> in the configs directory.
                  </p>
                  <div className="glass-panel" style={{ padding: '1rem', fontSize: '0.8rem', opacity: 0.6 }}>
                    Status: Pending Credentials
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'terminal' && (
            <div className="tab-content" style={{ padding: '2rem' }}>
              <div className="terminal-view">
                <div className="terminal-header">VOX OS KERNEL v2.0.4 [TTY_1]</div>
                <div className="terminal-body" style={{ color: '#00ff00', fontFamily: 'monospace', fontSize: '0.9rem' }}>
                  <p>[OK] CPU: {systemStats.cpu}%</p>
                  <p>[OK] RAM: {systemStats.ram}%</p>
                  <p>[OK] DISK: {systemStats.disk}%</p>
                  <p>[OK] PERIPHERALS: ONLINE</p>
                  <p style={{ marginTop: '1rem' }}>$ vox status</p>
                  <p style={{ color: 'var(--accent-blue)' }}>- All skills operational. Neural link: STABLE.</p>
                  <p style={{ color: 'var(--accent-blue)' }}>- Memory blocks: {Object.keys(facts).length} items recorded.</p>
                  <p style={{ animation: 'pulse 1s infinite', marginTop: '1rem' }}>_</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-panel animate-fade-in">
              <h3 className="text-gradient">Core Configuration</h3>
              <div className="stat-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3>Voice Output</h3>
                  <p style={{ color: 'var(--text-secondary)' }}>{isTtsEnabled ? 'Enabled' : 'Disabled'}</p>
                </div>
                <button
                  className={`btn-icon ${isTtsEnabled ? 'active-mic' : ''}`}
                  onClick={() => setIsTtsEnabled(!isTtsEnabled)}
                  style={{ background: isTtsEnabled ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer' }}
                >
                  {isTtsEnabled ? 'ON' : 'OFF'}
                </button>
              </div>
              <div className="stat-card">
                <h3>Personality Mode</h3>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                  {['Professional', 'Friendly', 'Sarcastic'].map(mode => (
                    <button
                      key={mode}
                      onClick={() => setPersonality(mode)}
                      style={{
                        background: personality === mode ? 'var(--accent-purple)' : 'rgba(255,255,255,0.05)',
                        border: '1px solid var(--border-color)',
                        padding: '0.5rem 1rem',
                        borderRadius: '8px',
                        color: 'white',
                        cursor: 'pointer'
                      }}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {
          activeTab === 'dashboard' && (
            <div className="input-area-wrapper">
              {selectedImage && (
                <div className="image-preview-container">
                  <img src={selectedImage.preview} alt="Preview" className="image-preview" />
                  <button className="clear-image" onClick={() => setSelectedImage(null)}><X size={14} /></button>
                </div>
              )}
              <div className="input-area">
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept="image/*"
                  onChange={handleImageSelect}
                />
                <button
                  className="btn-icon"
                  onClick={startCamera}
                  title="Capture Photo"
                >
                  <Camera size={20} />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => fileInputRef.current?.click()}
                  title="Attach Image"
                >
                  <ImagePlus size={20} />
                </button>
                <input
                  ref={inputRef}
                  type="text"
                  className="ai-input"
                  placeholder="Ask Vox anything..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleSend}
                />
                <button className={`btn-icon ${isListening ? 'active-mic' : ''}`} onClick={toggleListen}>
                  <Mic size={24} />
                </button>
              </div>
            </div>
          )}
      </main>
    </div>
  );
}

export default App;
