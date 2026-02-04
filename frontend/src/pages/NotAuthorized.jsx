import { Link } from 'react-router-dom';

export default function NotAuthorized() {
    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            textAlign: 'center',
            padding: '20px'
        }}>
            <div style={{
                fontSize: '80px',
                marginBottom: '20px'
            }}>
                🚫
            </div>
            <h1 style={{
                color: '#fff',
                fontSize: '28px',
                marginBottom: '12px'
            }}>
                Not Authorized
            </h1>
            <p style={{
                color: 'rgba(255, 255, 255, 0.6)',
                fontSize: '16px',
                marginBottom: '24px',
                maxWidth: '400px'
            }}>
                You don't have permission to access this page. Please contact your administrator if you believe this is an error.
            </p>
            <Link
                to="/dashboard"
                style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: '#fff',
                    padding: '12px 24px',
                    borderRadius: '10px',
                    textDecoration: 'none',
                    fontWeight: '500',
                    transition: 'transform 0.2s'
                }}
            >
                Go to Dashboard
            </Link>
        </div>
    );
}
