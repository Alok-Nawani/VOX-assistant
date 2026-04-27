import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, User, Lock, Loader2 } from 'lucide-react';
import VoxOrb from './VoxOrb';

export default function AuthScreens({ onAuthComplete }) {
  const [screen, setScreen] = useState('launch'); // launch, welcome, name, account, transition
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [mode, setMode] = useState('signup'); // signup, login

  // 1. Launch Screen Auto-transition
  useEffect(() => {
    if (screen === 'launch') {
      const timer = setTimeout(() => setScreen('welcome'), 2000);
      return () => clearTimeout(timer);
    }
  }, [screen]);

  const handleAuth = async () => {
    setLoading(true);
    setError('');
    const endpoint = mode === 'signup' ? '/api/auth/signup' : '/api/auth/login';
    
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username, 
          password, 
          full_name: mode === 'signup' ? name : undefined 
        })
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Authentication failed');
      
      if (mode === 'signup') {
        // Store user name as a fact in the background
        await fetch('/api/chat', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${data.access_token}`
          },
          body: JSON.stringify({ text: `My name is ${name}.` })
        });
      }

      localStorage.setItem('vox_token', data.access_token);
      localStorage.setItem('vox_user', JSON.stringify(data.user));
      
      if (mode === 'signup') {
        setScreen('transition');
        setTimeout(() => onAuthComplete(data.user), 3000);
      } else {
        onAuthComplete(data.user);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const containerVariants = {
    exit: { opacity: 0, scale: 0.95, transition: { duration: 0.5 } },
    enter: { opacity: 1, scale: 1, transition: { duration: 0.5 } }
  };

  return (
    <div className="auth-overlay">
      <AnimatePresence mode="wait">
        {screen === 'launch' && (
          <motion.div 
            key="launch"
            variants={containerVariants}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit="exit"
            className="auth-screen centered"
          >
            <div className="launch-logo">VOX</div>
            <div className="launch-sub">KERNEL INITIALIZING...</div>
          </motion.div>
        )}

        {screen === 'welcome' && (
          <motion.div 
            key="welcome"
            variants={containerVariants}
            initial="exit"
            animate="enter"
            exit="exit"
            className="auth-screen centered"
          >
            <div className="auth-bot-container">
              <img src="/assets/cute_bot.png" alt="Vox Bot" className="auth-bot-img" />
              <div className="bot-glow"></div>
            </div>
            <h1 className="auth-title">Hi, I'm Vox.</h1>
            <p className="auth-subtitle">Your personal voice assistant.</p>
            <div className="auth-welcome-actions">
              <button className="auth-btn primary" onClick={() => { setMode('signup'); setScreen('name'); }}>
                Get Started <ArrowRight size={20} />
              </button>
              <button className="auth-link-btn" onClick={() => { setMode('login'); setScreen('account'); }}>
                Already have an account? Log in
              </button>
            </div>
          </motion.div>
        )}

        {screen === 'name' && (
          <motion.div 
            key="name"
            variants={containerVariants}
            initial="exit"
            animate="enter"
            exit="exit"
            className="auth-screen"
          >
            <h2 className="auth-question">What should I call you?</h2>
            <div className="auth-input-wrapper">
              <User className="input-icon" />
              <input 
                autoFocus
                type="text" 
                placeholder="Alok"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && name.trim() && setScreen('account')}
              />
            </div>
            <button 
              className="auth-btn" 
              disabled={!name.trim()}
              onClick={() => setScreen('account')}
            >
              Next
            </button>
          </motion.div>
        )}

        {screen === 'account' && (
          <motion.div 
            key="account"
            variants={containerVariants}
            initial="exit"
            animate="enter"
            exit="exit"
            className="auth-screen"
          >
            <h2 className="auth-question">
              {mode === 'signup' ? 'Choose a username & password' : 'Log in to your account'}
            </h2>
            <div className="auth-input-wrapper">
              <User className="input-icon" />
              <input 
                type="text" 
                placeholder="alok_vox"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="auth-input-wrapper">
              <Lock className="input-icon" />
              <input 
                type="password" 
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <p className="auth-note">Used to save your preferences and history</p>
            {error && <p className="auth-error">{error}</p>}
            <button 
              className="auth-btn primary" 
              disabled={!username.trim() || !password.trim() || loading}
              onClick={handleAuth}
            >
              {loading ? <Loader2 className="animate-spin" /> : mode === 'signup' ? "Complete Sync" : "Access Kernel"}
            </button>
            <button className="auth-link-btn" onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')}>
              {mode === 'signup' ? 'Already have an account? Log in' : 'New here? Create account'}
            </button>
          </motion.div>
        )}

        {screen === 'transition' && (
          <motion.div 
            key="transition"
            variants={containerVariants}
            initial="exit"
            animate="enter"
            className="auth-screen centered"
          >
            <div className="auth-bot-container mini">
              <img src="/assets/cute_bot.png" alt="Vox Bot" className="auth-bot-img" />
              <div className="bot-glow"></div>
            </div>
            <h1 className="auth-welcome">Welcome, {name}.</h1>
            <p className="auth-subtitle">Neural link established.</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
