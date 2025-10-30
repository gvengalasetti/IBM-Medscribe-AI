import React from 'react';

export default function Button({ variant = 'default', children, style, ...props }) {
  const cls = ['btn'];
  if (variant === 'primary') cls.push('btn-primary');
  return (
    <button className={cls.join(' ')} style={style} {...props}>
      {children}
    </button>
  );
}


