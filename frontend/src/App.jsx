import React from 'react';
import { BrowserRouter, Routes as ReactRoutes, Route as ReactRoute, Link as ReactLink, useLocation as useReactLocation } from 'react-router-dom';
import SafetyMap from './SafetyMap';
import LinkAnalyzer from './LinkAnalyzer';
import NearMe from './NearMe';
import UserCrawler from './UserCrawler';
import { Shield, Map as MapIcon, Link as LinkIcon, Navigation, Activity } from 'lucide-react';

function NavLinks() {
  const location = useReactLocation();
  return (
    <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <ReactLink to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
        <MapIcon size={20} />
        Safety Map
      </ReactLink>
      <ReactLink to="/analyze" className={`nav-link ${location.pathname === '/analyze' ? 'active' : ''}`}>
        <LinkIcon size={20} />
        Link Analyzer
      </ReactLink>
      <ReactLink to="/near-me" className={`nav-link ${location.pathname === '/near-me' ? 'active' : ''}`}>
        <Navigation size={20} />
        Near Me
      </ReactLink>
      <ReactLink to="/crawler" className={`nav-link ${location.pathname === '/crawler' ? 'active' : ''}`}>
        <Activity size={20} />
        Active Crawler
      </ReactLink>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        {/* Sidebar */}
        <aside className="sidebar glass-panel" style={{ borderRadius: 0, borderRight: '1px solid rgba(255,255,255,0.1)' }}>
          <div className="sidebar-logo">
            <Shield size={28} color="var(--primary-color)" />
            SafeSpace AI
          </div>

          <NavLinks />

          <div style={{ marginTop: 'auto', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <p>MVP Version 1.0</p>
            <p>Analyzing localized threats automatically.</p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <ReactRoutes>
            <ReactRoute path="/" element={<SafetyMap />} />
            <ReactRoute path="/analyze" element={<LinkAnalyzer />} />
            <ReactRoute path="/near-me" element={<NearMe />} />
            <ReactRoute path="/crawler" element={<UserCrawler />} />
          </ReactRoutes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
