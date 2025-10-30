import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';

export default function SignIn() {
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const ok = await signIn({ email });
      if (ok) navigate('/chat');
    } catch (err) {
      setError('Sign in failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: '60vh' }}>
      <Card style={{ width: 420 }}>
        <h1 style={{ fontSize: 28, marginBottom: 8 }}>Sign in</h1>
        <p style={{ color: 'var(--muted)', marginBottom: 16 }}>Use your email to continue.</p>
        <form onSubmit={onSubmit}>
          <label htmlFor="email" style={{ display: 'block', fontWeight: 600, marginBottom: 8 }}>Email</label>
          <input
            id="email"
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 10,
              border: '1px solid var(--border)',
              background: 'var(--panel-2)',
              color: 'var(--text)',
              marginBottom: 12
            }}
          />
          {error ? <div style={{ color: '#ef4444', marginBottom: 8 }}>{error}</div> : null}
          <button
            type="submit"
            disabled={busy}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            {busy ? 'Signing in...' : 'Continue'}
          </button>
        </form>
      </Card>
    </div>
  );
}


