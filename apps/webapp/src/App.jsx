import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, Plus } from 'lucide-react';
import JarvisHUD from './components/JarvisHUD';
import VoxOrb from './components/VoxOrb';
import ControlPanel from './components/ControlPanel';
import TranscriptArea from './components/TranscriptArea';
import AuthScreens from './components/AuthScreens';
import SideNav from './components/SideNav';
import SystemOverlays from './components/SystemOverlays';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [activeOverlay, setActiveOverlay] = useState(null); 
  const [telemetry, setTelemetry] = useState({ cpu: 0, ram: 0, battery: 100, is_charging: true });
  const [appState, setAppState] = useState('idle'); 
  const [messages, setMessages] = useState([]);
  const [audioLevel, setAudioLevel] = useState(0);
  const [voiceOnly, setVoiceOnly] = useState(false);
  const [language, setLanguage] = useState('en');
  const [tone, setTone] = useState('Jarvis');
  const [isMuted, setIsMuted] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs
  const recognitionRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('vox_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
      fetchHistory();
    }
    setIsInitialized(true);
    setupSpeechRecognition();
    startTelemetry();
    return () => stopAudioAnalyzer();
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('vox_token');
      const response = await fetch('/api/history', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (Array.isArray(data)) {
        setMessages(data.map(h => ({
          role: h.role,
          content: h.content,
          data: h.image ? { type: 'image_generation', image_url: h.image } : null,
          timestamp: h.timestamp ? new Date(h.timestamp) : new Date()
        })));
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const setupSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = language;

    recognition.onstart = () => setAppState('listening');
    recognition.onend = () => {
      if (appState === 'listening') setAppState('idle');
    };
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      processCommand(text);
    };

    recognitionRef.current = recognition;
  };

  const startTelemetry = () => {
    setInterval(() => {
      setTelemetry({
        cpu: parseFloat((Math.random() * 30 + 40).toFixed(1)),
        ram: parseFloat((Math.random() * 20 + 70).toFixed(1)),
        battery: Math.max(0, 100 - (Date.now() % 100000) / 1000).toFixed(0),
        is_charging: true
      });
    }, 3000);
  };

  const startAudioAnalyzer = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      analyserRef.current = analyser;
      audioContextRef.current = audioContext;

      const updateAnalyzer = () => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        setAudioLevel(average / 128);
        animationFrameRef.current = requestAnimationFrame(updateAnalyzer);
      };
      updateAnalyzer();
    } catch (err) {
      console.error("Audio analyzer failed", err);
    }
  };

  const stopAudioAnalyzer = () => {
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    if (audioContextRef.current) audioContextRef.current.close();
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const processCommand = async (text) => {
    if (!text.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: new Date() }]);
    setAppState('processing');
    
    try {
      const token = localStorage.getItem('vox_token');
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ text, language, tone })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { 
        role: 'vox', 
        content: data.response, 
        data: data.data,
        timestamp: new Date() 
      }]);
      
      speak(data.response);
      setAppState('responding');
    } catch (error) {
      setMessages(prev => [...prev, { role: 'vox', content: "Neural uplink failed. Check logs." }]);
      setAppState('idle');
    }
  };

  useEffect(() => {
    if (isMuted) {
      window.speechSynthesis.cancel();
    }
  }, [isMuted]);

  const speak = (text) => {
    if (isMuted) {
      setAppState('idle');
      return;
    }
    window.speechSynthesis.cancel(); // Stop any previous speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.onend = () => setAppState('idle');
    window.speechSynthesis.speak(utterance);
  };

  const toggleListen = () => {
    if (appState === 'listening') {
      recognitionRef.current?.stop();
      setAppState('idle');
    } else {
      setAppState('listening');
      recognitionRef.current?.start();
      startAudioAnalyzer();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('vox_token');
    localStorage.removeItem('vox_user');
    setUser(null);
    setIsNavOpen(false);
  };

  if (!isInitialized) return null;
  if (!user) return <AuthScreens onAuthComplete={setUser} />;

  return (
    <div className="app-container">
      <div className="bg-grid"></div>
      
      <header className="compact-header">
        <button className="nav-toggle-btn" onClick={() => setIsNavOpen(true)}>
          <Menu size={24} />
        </button>
        <button className="new-chat-minimal" onClick={handleNewChat}>
          <Plus size={18} /> New Chat
        </button>
      </header>

      <JarvisHUD telemetry={telemetry} />
      
      <VoxOrb state={appState} audioLevel={audioLevel} />
      
      <TranscriptArea 
        messages={messages}
        voiceOnly={voiceOnly} 
      />
      
      <ControlPanel 
        isListening={appState === 'listening'}
        onToggleListen={toggleListen}
        voiceOnly={voiceOnly}
        onToggleVoiceOnly={() => setVoiceOnly(!voiceOnly)}
        isMuted={isMuted}
        onToggleMute={() => setIsMuted(!isMuted)}
        language={language}
        onLanguageChange={setLanguage}
        onTextSubmit={processCommand}
      />

      <SideNav 
        user={user} 
        isOpen={isNavOpen} 
        onClose={() => setIsNavOpen(false)} 
        onLogout={handleLogout}
        onOpenOverlay={(type) => {
          setActiveOverlay(type);
          setIsNavOpen(false);
        }}
      />

      <SystemOverlays 
        type={activeOverlay}
        isOpen={!!activeOverlay}
        onClose={() => setActiveOverlay(null)}
        user={user}
        onLanguageChange={setLanguage}
        currentLanguage={language}
        onToneChange={setTone}
        currentTone={tone}
      />
    </div>
  );
}

export default App;
