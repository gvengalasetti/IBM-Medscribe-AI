import React from 'react';

export default function Card({ children, style }) {
  return (
    <div className="glass" style={{ padding: 16, ...style }}>
      {children}
    </div>
  );
}


