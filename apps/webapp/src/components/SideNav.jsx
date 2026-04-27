import React from 'react';
import { motion } from 'framer-motion';
import { X, History, Settings, User, LogOut } from 'lucide-react';

const SideNav = ({ user, isOpen, onClose, onLogout, onOpenOverlay }) => {
  if (!isOpen) return null;

  return (
    <div className="side-nav-overlay" onClick={onClose}>
      <motion.div 
        className="side-nav"
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="side-nav-header">
          <div className="user-profile">
            <div className="user-avatar">
              {user?.full_name?.charAt(0).toUpperCase() || user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="user-info">
              <div className="user-name">{user?.full_name || 'Vox User'}</div>
              <div className="user-email">{user?.username}</div>
              <div className="user-status">Online</div>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="side-nav-links">
          <button className="nav-link" onClick={() => onOpenOverlay('profile')}>
            <User size={20} /> Profile
          </button>
          <button className="nav-link" onClick={() => onOpenOverlay('history')}>
            <History size={20} /> History
          </button>
          <button className="nav-link" onClick={() => onOpenOverlay('settings')}>
            <Settings size={20} /> Settings
          </button>
        </div>

        <div className="side-nav-footer">
          <button className="nav-link logout" onClick={onLogout}>
            <LogOut size={20} /> Logout
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default SideNav;
