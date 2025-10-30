import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  return (
    <header className="navbar">
      <nav className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, paddingBottom: 12 }}>
        <Link to="/" className="brand">
          <span className="brand-badge">M</span>
          Medscribe
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <NavLink to="/" style={({ isActive }) => ({
            padding: '6px 10px', borderRadius: 8, textDecoration: 'none',
            color: isActive ? '#fff' : '#9ca3af', background: isActive ? '#111827' : 'transparent', border: '1px solid var(--border)'
          })}>Home</NavLink>

          <NavLink to="/chat" style={({ isActive }) => ({
            padding: '6px 10px', borderRadius: 8, textDecoration: 'none',
            color: isActive ? '#fff' : '#9ca3af', background: isActive ? '#111827' : 'transparent', border: '1px solid var(--border)'
          })}>Chat</NavLink>

          {user ? (
            <button onClick={handleSignOut} className="btn" style={{ marginLeft: 8 }}>
              Sign out
            </button>
          ) : (
            <NavLink to="/signin" className="btn btn-primary" style={{ marginLeft: 8 }}>Sign in</NavLink>
          )}
        </div>
      </nav>
    </header>
  );
}


