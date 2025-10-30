import React from 'react';

export default function ChatMessage({ role, children }) {
  return (
    <div style={{
      marginBottom: 10,
      display: 'flex',
      justifyContent: role === 'user' ? 'flex-end' : 'flex-start'
    }}>
      <div className={`bubble ${role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
        {children}
      </div>
    </div>
  );
}


