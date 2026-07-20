// Privacy Policy + Terms shown in a modal (the app has no router, so this mirrors
// the Glossary modal pattern). The site stores no personal data, so the policy is
// short and factual rather than boilerplate.

const SECTIONS = [
  {
    heading: 'Privacy Policy',
    body: [
      'This site does not use analytics, advertising, or tracking cookies, and does not collect, store, or sell personal information.',
      'Score checker: the CRS score you enter is processed entirely in your browser to compare against public draw data. It is never transmitted to or stored on our servers, and it is cleared when you close the page.',
      '"Check now" button: pressing it triggers an anonymous, rate-limited request to the public IRCC feed. We do not record your name, email address, or IP address when you use it.',
      'Third parties: page fonts are served by Google Fonts, which may receive your IP address in order to deliver those files. Draw data is stored in Supabase and contains only public IRCC records, no user data.',
      'Deleting your data: because no personal data is collected or stored, there is nothing for us to delete. Anything you type stays on your device.',
    ],
  },
  {
    heading: 'Terms of Use',
    body: [
      'This dashboard is an independent project and is not affiliated with, endorsed by, or operated by IRCC or the Government of Canada.',
      'Draw figures are sourced from the public IRCC feed and are provided for informational purposes only. The data and any predictions may be delayed, incomplete, or inaccurate, and are not a guarantee of future draw results.',
      'Nothing here is legal or immigration advice. Always confirm details against official IRCC sources before making decisions.',
    ],
  },
];

export default function Legal({ open, onClose }) {
  if (!open) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(16,22,40,.55)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px 16px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Privacy Policy and Terms of Use"
        style={{
          background: '#fff', borderRadius: 14, width: '100%', maxWidth: 560,
          maxHeight: '80vh', display: 'flex', flexDirection: 'column',
          boxShadow: '0 8px 40px rgba(16,22,40,.22)',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 24px 16px', borderBottom: '1px solid #e2ded3', flexShrink: 0,
        }}>
          <div>
            <div style={{ fontSize: 11, letterSpacing: '.14em', textTransform: 'uppercase', color: '#c8362b', fontWeight: 700 }}>
              Express Entry
            </div>
            <h2 style={{ margin: '2px 0 0', fontSize: 20, fontWeight: 800, letterSpacing: '-.02em' }}>Privacy &amp; Terms</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              border: 'none', background: '#f0ede6', borderRadius: 8,
              width: 32, height: 32, cursor: 'pointer', fontSize: 18, lineHeight: 1,
              color: '#5b6172', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ overflowY: 'auto', padding: '18px 24px 22px' }}>
          {SECTIONS.map(({ heading, body }) => (
            <section key={heading} style={{ marginBottom: 22 }}>
              <h3 style={{ margin: '0 0 8px', fontSize: 15, fontWeight: 700, color: '#16223d' }}>{heading}</h3>
              {body.map((p, i) => (
                <p key={i} style={{ margin: '0 0 10px', fontSize: 13.5, color: '#42485a', lineHeight: 1.55 }}>{p}</p>
              ))}
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
