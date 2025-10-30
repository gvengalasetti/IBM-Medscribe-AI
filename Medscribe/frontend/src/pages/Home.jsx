import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/Button';
import Card from '../components/Card';

export default function Home() {
  const { user } = useAuth();

  return (
    <div>
      <section style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr',
        gap: 24,
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ fontSize: 44, lineHeight: 1.1, margin: 0 }}>Agentic AI scribe for clinicians.</h1>
          <p style={{ color: 'var(--muted)', marginTop: 12, fontSize: 18 }}>
            Medscribe turns raw clinical notes into concise, citation-backed insights and suggested orders.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 18 }}>
            {user ? (
              <Link to="/chat" className="btn btn-primary">Open Chat</Link>
            ) : (
              <>
                <Link to="/signin" className="btn btn-primary">Get Started</Link>
                <a href="#features" className="btn">View Demo</a>
              </>
            )}
          </div>
        </div>
        <Card id="features">
          <div style={{ color: 'var(--muted)', marginBottom: 8 }}>What it can do</div>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            <li>Summarize chief complaint, history, assessment, plan</li>
            <li>Suggest labs, imaging, medications, and consults</li>
            <li>Show evidence sentences and support scores</li>
            <li>Display model, mode, and provenance</li>
          </ul>
        </Card>
      </section>
    </div>
  );
}