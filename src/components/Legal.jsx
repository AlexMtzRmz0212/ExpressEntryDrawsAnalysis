// Privacy Policy + Terms shown in a modal (the app has no router, so this mirrors
// the Glossary modal pattern). Browsing the dashboard collects nothing; the email
// alert list is the one place personal data is involved, so the policy says
// exactly what is stored, why, and how to get rid of it.

const SECTIONS = [
  {
    heading: 'Privacy Policy',
    body: [
      'Browsing this dashboard is anonymous. There are no analytics, no advertising, and no tracking cookies. The only personal data collected is from people who choose to subscribe to draw notifications, described below.',
      'Draw notification emails: if you subscribe, we store your email address, the date and time you signed up, the date and time you confirmed, and the IP address and browser user agent recorded at signup. The address is used solely to send you an email when IRCC publishes a new Express Entry round. The IP address and user agent are kept only as proof that you gave consent, which Canada’s anti-spam legislation requires senders to be able to demonstrate. None of this is sold, rented, or used for advertising or profiling.',
      'Confirming your subscription: signing up does not add you to the list. We send one email with a confirmation link, and only clicking it activates the subscription. If you never confirm, the record is deleted automatically after 7 days.',
      'Deleting your data: every notification email contains a one-click unsubscribe link. Using it stops all email immediately, and your record is deleted within 30 days. You can also request deletion at any time by replying to any notification email, and it will be handled within 10 business days.',
      'Score checker: the CRS score you enter is processed entirely in your browser to compare against public draw data. It is never transmitted to or stored on our servers, and it is cleared when you close the page.',
      '"Check now" button: pressing it triggers an anonymous, rate-limited request to the public IRCC feed. Your name, email address, and IP address are not recorded when you use it.',
      'Third parties: page fonts are served by Google Fonts, which may receive your IP address in order to deliver those files. Draw data and subscriber records are stored in Supabase. Notification emails are delivered by Resend, which processes your address for the sole purpose of delivering the message.',
    ],
  },
  {
    heading: 'Terms of Use',
    body: [
      'This dashboard is an independent project and is not affiliated with, endorsed by, or operated by IRCC or the Government of Canada.',
      'Draw figures are sourced from the public IRCC feed and are provided for informational purposes only. The data and any predictions may be delayed, incomplete, or inaccurate, and are not a guarantee of future draw results.',
      'Email notifications are a free convenience offered on a best-effort basis. Delivery and timing are not guaranteed, messages can be delayed or filtered by your mail provider, and the service may be changed or discontinued at any time. Always confirm draw details against official IRCC sources rather than relying on an email.',
      'Subscribing to notifications is not an application, does not create any relationship with IRCC, and has no effect on your Express Entry profile or ranking.',
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
