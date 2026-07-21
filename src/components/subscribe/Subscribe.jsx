// Double opt-in signup for new-draw email alerts.
//
// Submitting does NOT subscribe anyone: the API creates a pending record and
// sends a confirmation link, and only clicking that link activates the address.
// The success copy has to say so plainly, or people assume they are done and
// then wonder why no emails arrive.

import { useState } from 'react';

const IDLE = 'idle';
const SENDING = 'sending';
const DONE = 'done';
const FAILED = 'failed';

export default function Subscribe({ onLegal }) {
  const [email, setEmail] = useState('');
  const [website, setWebsite] = useState(''); // honeypot, see the input below
  const [state, setState] = useState(IDLE);
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (state === SENDING) return;

    setState(SENDING);
    setMessage('');

    try {
      const r = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, website }),
      });
      const data = await r.json().catch(() => ({}));

      if (r.ok) {
        setState(DONE);
        setMessage(data.message || 'Check your inbox to confirm.');
        setEmail('');
      } else {
        setState(FAILED);
        setMessage(data.detail || 'Something went wrong. Try again in a moment.');
      }
    } catch {
      setState(FAILED);
      setMessage('Could not reach the server. Check your connection and try again.');
    }
  }

  const sending = state === SENDING;

  return (
    <section
      aria-labelledby="subscribe-heading"
      style={{
        marginTop: 26, background: '#fff', border: '1px solid #e2ded3',
        borderRadius: 12, padding: 22,
      }}
    >
      <div style={{ fontSize: 11.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#c8362b', fontWeight: 700 }}>
        Draw alerts
      </div>
      <h2
        id="subscribe-heading"
        style={{ margin: '4px 0 0', fontSize: 20, fontWeight: 800, letterSpacing: '-.02em', color: '#16223d' }}
      >
        Get an email when the next draw lands
      </h2>
      <p style={{ margin: '8px 0 0', fontSize: 14, color: '#42485a', lineHeight: 1.6, maxWidth: 560 }}>
        Every new round, with the CRS cutoff, the invitation count, how it compares to
        recent rounds in the same category, and the year to date totals. Nothing else.
      </p>

      {state === DONE ? (
        <div
          role="status"
          style={{
            marginTop: 16, padding: '14px 16px', background: '#f1efe9',
            borderLeft: '3px solid #2f8f6b', borderRadius: '0 8px 8px 0',
            fontSize: 14, color: '#16223d', lineHeight: 1.6, fontWeight: 600,
          }}
        >
          {message}
          <div style={{ fontWeight: 400, color: '#5b6172', marginTop: 4 }}>
            You are not subscribed until you click that link. If it does not show up
            within a few minutes, check your spam folder.
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate>
          <label
            htmlFor="subscribe-email"
            style={{
              position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
              overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
            }}
          >
            Email address
          </label>

          {/*
            Honeypot. Positioned offscreen rather than display:none, because some
            bots skip hidden fields but nearly all fill a visible-to-the-DOM input.
            Real users never see or tab into it.
          */}
          <input
            type="text"
            name="website"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            value={website}
            onChange={e => setWebsite(e.target.value)}
            style={{ position: 'absolute', left: '-9999px', width: 1, height: 1, opacity: 0 }}
          />

          <div className="subscribe-row" style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              id="subscribe-email"
              type="email"
              required
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => { setEmail(e.target.value); if (state === FAILED) setState(IDLE); }}
              aria-describedby="subscribe-consent"
              aria-invalid={state === FAILED || undefined}
              disabled={sending}
              style={{
                minWidth: 0, padding: '12px 14px',
                border: `1px solid ${state === FAILED ? '#c8362b' : '#e2ded3'}`,
                borderRadius: 8, fontSize: 14.5, fontFamily: 'inherit', color: '#16223d',
                background: sending ? '#f6f4ef' : '#fff',
              }}
              onFocus={e => e.currentTarget.style.borderColor = '#16223d'}
              onBlur={e => e.currentTarget.style.borderColor = state === FAILED ? '#c8362b' : '#e2ded3'}
            />
            <button
              type="submit"
              disabled={sending}
              style={{
                padding: '12px 22px', border: 'none', borderRadius: 8,
                background: '#16223d', color: '#fff', fontSize: 14.5, fontWeight: 700,
                fontFamily: 'inherit', cursor: sending ? 'default' : 'pointer',
                opacity: sending ? 0.7 : 1, transition: 'opacity .15s',
              }}
            >
              {sending ? 'Sending' : 'Notify me'}
            </button>
          </div>

          <p
            id="subscribe-consent"
            style={{ margin: '10px 0 0', fontSize: 12.5, color: '#5b6172', lineHeight: 1.6, maxWidth: 560 }}
          >
            Roughly two to six emails a month, one per draw. We send a confirmation link
            first, and every email has a one-click unsubscribe. Your address is used only
            for these alerts, never sold or shared for advertising. See the{' '}
            <button
              type="button"
              onClick={onLegal}
              style={{
                border: 'none', background: 'none', padding: 0, font: 'inherit',
                color: '#16223d', fontWeight: 600, textDecoration: 'underline', cursor: 'pointer',
              }}
            >
              Privacy Policy
            </button>.
          </p>

          {state === FAILED && (
            <p role="status" style={{ margin: '10px 0 0', fontSize: 13.5, color: '#c8362b', fontWeight: 600 }}>
              {message}
            </p>
          )}
        </form>
      )}
    </section>
  );
}
