import React, { useState } from 'react';

export default function Home() {

    const [note, setNote] = useState('');
    const [message, setMessage] = useState('');
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('Submitting...');
        setResult(null);
      
        try {
          console.log('Submitting note of length:', note.length);
          const res = await fetch('http://localhost:5001/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              note_text: note,
              patient_context: { patient_id: 'demo-001' }
            })
          });
      
          console.log('Response status:', res.status);
          const data = await res.json();
          console.log('Response JSON:', data);
          if (!res.ok) {
            setMessage(data?.error || 'Request failed');
            return;
          }
          setResult(data);
          setMessage('Received analysis.');
        } catch (err) {
          console.error(err);
          setMessage('Network error. Is the Flask server running on port 5001?');
        }
      };

    const handleClickBox = () => {
        setMessage('Box clicked! This is a simple onClick example.');
    };

  

    return (
        <div style={{ maxWidth: 900, margin: '0 auto', padding: 24 }}>
            <h1>Medscribe - Home</h1>

            <form onSubmit={handleSubmit}>
                <label htmlFor="note" style={{ display: 'block', fontWeight: 600, marginBottom: 8 }}>
                    Clinical Note
                </label>
                <textarea
                    id="note"
                    rows={10}
                    style={{ width: '100%', padding: 8, fontFamily: 'inherit' }}
                    placeholder="Paste clinical note here..."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                />

                <div style={{ marginTop: 12 }}>
                    <button type="submit" disabled={note.trim().length < 5}>
                        Submit
                    </button>
                </div>

                <div style={{ marginTop: 12 }}>
                    <button type = "button" onClick = {handleClickBox}>Upload File
                    </button>
                </div>

                <div style={{ marginTop: 12 }}>
                    <button type = "button" onClick = {handleClickBox}>Speak
                    </button>
                </div>


            </form>

            <div
                onClick={handleClickBox}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => (e.key === 'Enter' ? handleClickBox() : null)}
                style={{
                    marginTop: 16,
                    padding: 16,
                    border: '1px solid #ccc',
                    borderRadius: 8,
                    cursor: 'pointer',
                    background: '#fafafa',
                }}
            >
                Click this box (onClick example)
            </div>

            {message && (
                <div style={{ marginTop: 12, color: '#0a6' }}>
                    {message}
                </div>
            )}

            {result && (
                <pre style={{ marginTop: 12, background: '#f7f7f7', padding: 12 }}>
                    {JSON.stringify(result, null, 2)}
                </pre>
            )}
        </div>
    );
}