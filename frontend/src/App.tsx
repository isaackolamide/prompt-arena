import { useState } from 'react';

interface AuthUser {
  email: string;
}

export default function App() {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [step, setStep] = useState<'request-otp' | 'verify-otp'>('request-otp');
  const [status, setStatus] = useState('Welcome to Prompt Arena');
  const [user, setUser] = useState<AuthUser | null>(null);

  const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleRequestOtp = async (email: string): Promise<void> => {
    setStatus('Sending magic link...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      if (response.ok) {
        setStatus('Magic link sent successfully. Please check your inbox.');
        setStep('verify-otp');
      } else {
        setStatus(`Error: ${data.detail || 'Failed to send magic link'}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${msg}`);
    }
  };

  const handleVerifyOtp = async (email: string, token: string): Promise<void> => {
    setStatus('Verifying OTP...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, token }),
      });

      const data = await response.json();
      if (response.ok) {
        setUser({ email });
        setStatus(`Logged in as ${email}`);
      } else {
        setStatus(`Error: ${data.detail || 'OTP verification failed'}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${msg}`);
    }
  };

  const getStatusStyles = () => {
    if (status.startsWith('Error:')) {
      return {
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        color: '#f87171',
      };
    }
    const isSuccess =
      status.startsWith('Magic link sent successfully') ||
      status.startsWith('Logged in as');
    if (isSuccess) {
      return {
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        border: '1px solid rgba(16, 185, 129, 0.2)',
        color: '#34d399',
      };
    }
    return {
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      border: '1px solid rgba(59, 130, 246, 0.2)',
      color: '#60a5fa',
    };
  };

  return (
    <div style={{
      fontFamily: 'Inter, sans-serif',
      background: 'linear-gradient(135deg, #1e1e24 0%, #111115 100%)',
      color: '#f3f4f6',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        padding: '2.5rem',
        width: '100%',
        maxWidth: '480px',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        textAlign: 'center'
      }}>
        <h1 style={{
          margin: '0 0 0.5rem 0',
          fontSize: '2.5rem',
          fontWeight: 700,
          background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Prompt Arena
        </h1>
        <p id="welcome-message" style={{
          color: '#9ca3af',
          margin: '0 0 2rem 0'
        }}>
          Welcome to Prompt Arena
        </p>
        
        <div id="auth-status" style={{
          padding: '1rem',
          borderRadius: '8px',
          ...getStatusStyles(),
          marginBottom: '2rem',
          fontWeight: 500,
          wordBreak: 'break-all'
        }}>
          {status}
        </div>

        {user ? (
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
              Welcome, {user.email}!
            </h2>
            <button 
              id="logout-button"
              onClick={() => {
                setUser(null);
                setEmail('');
                setToken('');
                setStep('request-otp');
                setStatus('Welcome to Prompt Arena');
              }}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: 'none',
                background: '#ef4444',
                color: 'white',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}
            >
              Log Out
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
            {step === 'request-otp' ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleRequestOtp(email);
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  textAlign: 'left'
                }}
              >
                <h3 style={{
                  margin: 0,
                  fontSize: '1.25rem',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  paddingBottom: '0.5rem'
                }}>
                  Sign In
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <label htmlFor="email-input" style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                    Email
                  </label>
                  <input
                    id="email-input"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '8px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      backgroundColor: 'rgba(0, 0, 0, 0.2)',
                      color: 'white',
                      outline: 'none'
                    }}
                  />
                </div>
                <button
                  id="submit-email-button"
                  type="submit"
                  style={{
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(90deg, #3b82f6, #2563eb)',
                    color: 'white',
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginTop: '0.5rem'
                  }}
                >
                  Send Magic Link
                </button>
              </form>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleVerifyOtp(email, token);
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  textAlign: 'left'
                }}
              >
                <h3 style={{
                  margin: 0,
                  fontSize: '1.25rem',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  paddingBottom: '0.5rem'
                }}>
                  Verify OTP
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <label htmlFor="otp-input" style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                    One-Time Password / Token
                  </label>
                  <input
                    id="otp-input"
                    type="text"
                    required
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '8px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      backgroundColor: 'rgba(0, 0, 0, 0.2)',
                      color: 'white',
                      outline: 'none'
                    }}
                  />
                </div>
                <button
                  id="submit-otp-button"
                  type="submit"
                  style={{
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(90deg, #8b5cf6, #7c3aed)',
                    color: 'white',
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginTop: '0.5rem'
                  }}
                >
                  Verify OTP
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setStep('request-otp');
                    setToken('');
                    setStatus('Welcome to Prompt Arena');
                  }}
                  style={{
                    padding: '0.5rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    background: 'transparent',
                    color: '#9ca3af',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    transition: 'color 0.2s'
                  }}
                >
                  Back to Sign In
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
