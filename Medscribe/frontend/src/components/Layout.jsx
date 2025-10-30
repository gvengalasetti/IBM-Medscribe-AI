import React from 'react';
import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <div style={{ minHeight: '100dvh' }}>
      <Navbar />
      <main className="container">
        {children}
      </main>
      <footer style={{
        marginTop: 40,
        padding: '24px 16px',
        borderTop: '1px solid var(--border)',
        color: 'var(--muted)',
        textAlign: 'center'
      }}>
        © {new Date().getFullYear()} Medscribe · AI Agentic Scribe
      </footer>
    </div>
  );
}


