import React from 'react';

export default function JarvisHUD({ telemetry }) {
  const { cpu = 0, ram = 0, battery = 100, is_charging = true } = telemetry || {};

  return (
    <div className="hud-container">
      {/* Massive rotating SVG Rings */}
      <svg className="hud-svg" viewBox="0 0 1000 1000">
        <defs>
          <radialGradient id="glow" cx="50%" cy="50%" r="50%">
            <stop offset="80%" stopColor="transparent" />
            <stop offset="100%" stopColor="rgba(0, 240, 255, 0.2)" />
          </radialGradient>
        </defs>

        {/* Outer Tech Ring */}
        <g className="hud-ring-outer">
          <circle cx="500" cy="500" r="450" fill="none" stroke="rgba(0, 240, 255, 0.3)" strokeWidth="2" strokeDasharray="10 40 50 100" />
          <circle cx="500" cy="500" r="460" fill="none" stroke="rgba(176, 0, 255, 0.4)" strokeWidth="1" strokeDasharray="5 20" />
          <circle cx="500" cy="500" r="440" fill="none" stroke="rgba(0, 240, 255, 0.1)" strokeWidth="10" strokeDasharray="2 10" />
        </g>

        {/* Middle Data Ring */}
        <g className="hud-ring-middle">
          <circle cx="500" cy="500" r="350" fill="none" stroke="rgba(0, 240, 255, 0.2)" strokeWidth="4" strokeDasharray="200 50 50 50" />
          <circle cx="500" cy="500" r="340" fill="none" stroke="rgba(176, 0, 255, 0.3)" strokeWidth="2" strokeDasharray="10 30" />
        </g>

        {/* Inner Target Reticle */}
        <g className="hud-ring-inner">
          <circle cx="500" cy="500" r="250" fill="none" stroke="rgba(0, 240, 255, 0.5)" strokeWidth="1" strokeDasharray="4 8" />
          <line x1="500" y1="230" x2="500" y2="270" stroke="var(--accent-cyan)" strokeWidth="2" />
          <line x1="500" y1="730" x2="500" y2="770" stroke="var(--accent-cyan)" strokeWidth="2" />
          <line x1="230" y1="500" x2="270" y2="500" stroke="var(--accent-cyan)" strokeWidth="2" />
          <line x1="730" y1="500" x2="770" y2="500" stroke="var(--accent-cyan)" strokeWidth="2" />
        </g>
      </svg>

      {/* Telemetry Overlays */}
      <div className="telemetry-panel top-left">
        <div className="telemetry-title">SYS.CORE.CPU</div>
        <div className="telemetry-value">{Number(cpu).toFixed(1)}%</div>
        <div className="telemetry-bar">
          <div className="telemetry-fill" style={{ width: `${cpu}%` }}></div>
        </div>
      </div>

      <div className="telemetry-panel top-right">
        <div className="telemetry-title">SYS.MEM.RAM</div>
        <div className="telemetry-value">{Number(ram).toFixed(1)}%</div>
        <div className="telemetry-bar">
          <div className="telemetry-fill" style={{ width: `${ram}%`, background: 'var(--accent-purple)' }}></div>
        </div>
      </div>

      <div className="telemetry-panel bottom-left">
        <div className="telemetry-title">PWR.BATTERY</div>
        <div className="telemetry-value">{battery}% {is_charging ? '⚡' : ''}</div>
        <div className="telemetry-bar">
          <div className="telemetry-fill" style={{ width: `${battery}%`, background: Number(battery) < 20 && !is_charging ? 'red' : 'var(--accent-cyan)' }}></div>
        </div>
      </div>
      
      <div className="telemetry-panel bottom-right">
        <div className="telemetry-title">VOX.NETWORK</div>
        <div className="telemetry-value">SECURE // UPLINK</div>
        <div className="telemetry-bar animated-bar"></div>
      </div>
    </div>
  );
}
