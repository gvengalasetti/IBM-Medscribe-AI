import React, { useRef, useState } from 'react';
import Button from '../components/Button';
import Card from '../components/Card';
import ChatMessage from '../components/ChatMessage';

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! Paste or type a clinical note and hit Send.' }
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const listRef = useRef(null);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    });
  };

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    setInput('');
    const next = [...messages, { role: 'user', content: text }];
    setMessages(next);
    scrollToBottom();

    // If note is short, just echo to keep UX snappy
    if (text.length < 5) {
      const echo = [...next, { role: 'assistant', content: 'Please provide a longer note (≥5 chars).' }];
      setMessages(echo);
      scrollToBottom();
      return;
    }

    setBusy(true);
    try {
      const res = await fetch('http://localhost:5001/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note_text: text,
          patient_context: { patient_id: 'demo-001' }
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || 'Request failed');

      const summary = data?.summary;
      const orders = data?.suggested_orders;
      const model = data?.model_info;

      if (Array.isArray(data?.summary_bullets) || Array.isArray(orders) || data?.id_to_sentence) {
        const structured = {
          summaryBullets: Array.isArray(data?.summary_bullets) ? data.summary_bullets : null,
          suggestedOrders: Array.isArray(orders) ? orders : null,
          idToSentence: data?.id_to_sentence || null,
          modelInfo: model || null
        };
        setMessages(prev => [...prev, { role: 'assistant', structured }]);
      } else {
        const lines = [];
        if (summary) {
          if (summary.text) lines.push(`Summary: ${summary.text}`);
          if (summary.chief_complaint) lines.push(`Chief complaint: ${summary.chief_complaint}`);
          if (summary.history) lines.push(`History: ${summary.history}`);
          if (summary.assessment) lines.push(`Assessment: ${summary.assessment}`);
          if (summary.plan) lines.push(`Plan: ${summary.plan}`);
        }
        if (Array.isArray(orders) && orders.length) {
          lines.push('Suggested orders:');
          for (const o of orders) {
            const row = `• [${o.type}] ${o.name} — ${o.rationale || o.reason || ''}`.trim();
            lines.push(row);
          }
        }
        if (model) {
          lines.push(`\nModel: ${model.provider} - ${model.model} (${model.mode})`);
        }
        const content = lines.join('\n');
        setMessages(prev => [...prev, { role: 'assistant', content }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setBusy(false);
      scrollToBottom();
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const renderStructuredMessage = (m) => {
    const s = m.structured;
    if (!s) return m.content;
    const sentenceFor = (id) => {
      const txt = s.idToSentence ? s.idToSentence[String(id)] || s.idToSentence[id] : '';
      return txt || '';
    };
    return (
      <div style={{ display: 'grid', gap: 16 }}>
        {Array.isArray(s.summaryBullets) && s.summaryBullets.length > 0 && (
          <section>
            <div className="section-title">Summary</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {s.summaryBullets.map((b, idx) => (
                <li key={idx} style={{ marginBottom: 6 }}>
                  <span>{b.text}</span>
                  {b.support_score != null && (
                    <span style={{ color: 'var(--muted)', marginLeft: 6 }}>{`(support ${b.support_score.toFixed(2)})`}</span>
                  )}
                  {(b.citations || []).map((cid) => (
                    <span key={cid} className="chip" title={sentenceFor(cid)} style={{ marginLeft: 6 }}>#{cid}</span>
                  ))}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <div className="section-title">Treatment recommendations</div>
          {Array.isArray(s.suggestedOrders) && s.suggestedOrders.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {s.suggestedOrders.map((o, idx) => (
                <li key={idx} style={{ marginBottom: 10 }}>
                  <span className="badge-type">{o.type}</span>
                  <span style={{ fontWeight: 600 }}>{o.name}</span>
                  {o.reason && <span>{` — ${o.reason}`}</span>}
                  {o.support_score != null && (
                    <span style={{ color: 'var(--muted)', marginLeft: 6 }}>{`(support ${o.support_score.toFixed(2)})`}</span>
                  )}
                  {(o.citations || []).map((cid) => (
                    <span key={cid} className="chip" title={sentenceFor(cid)} style={{ marginLeft: 6 }}>#{cid}</span>
                  ))}
                  {Array.isArray(o.external_citations) && o.external_citations.length > 0 && (
                    <ul style={{ marginTop: 6, paddingLeft: 18, color: 'var(--muted)' }}>
                      {o.external_citations.map((c, j) => (
                        <li key={j}>
                          <a href={c.url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>{c.title}</a>
                          {c.year ? ` (${c.year})` : ''}
                          {c.snippet ? ` — ${c.snippet}` : ''}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ color: 'var(--muted)' }}>No treatment recommendations returned for this note.</div>
          )}
        </section>

        {s.idToSentence && (
          <section>
            <div className="section-title">Evidence sentences</div>
            <div style={{
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
              background: '#0b1220',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: 12,
              whiteSpace: 'pre-wrap'
            }}>
              {Object.keys(s.idToSentence)
                .map(n => parseInt(n, 10))
                .sort((a, b) => a - b)
                .map(i => `${i}. ${s.idToSentence[i]}`)
                .join('\n')}
            </div>
          </section>
        )}

        {s.modelInfo && (
          <div style={{ color: 'var(--muted)' }}>{`Model: ${s.modelInfo.provider} - ${s.modelInfo.model} (${s.modelInfo.mode})`}</div>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
      <aside className="sidebar glass" style={{ padding: 12 }}>
        <div style={{ fontWeight: 700, marginBottom: 10 }}>Conversations</div>
        <Button style={{ width: '100%', marginBottom: 10 }}>New chat</Button>
        <div style={{ color: 'var(--muted)', fontSize: 14 }}>No recent chats</div>
      </aside>

      <section className="chat-main">
        <Card style={{ padding: 12, overflow: 'auto' }}>
          <div ref={listRef}>
            {messages.map((m, i) => (
              <ChatMessage key={i} role={m.role}>
                {m.structured ? renderStructuredMessage(m) : m.content}
              </ChatMessage>
            ))}
          </div>
        </Card>

        <div className="input-dock">
          <div style={{ display: 'flex', gap: 8 }}>
            <textarea
              className="textarea"
              placeholder="Paste or type a clinical note..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={3}
            />
            <Button variant="primary" onClick={send} disabled={busy}>
              {busy ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}


