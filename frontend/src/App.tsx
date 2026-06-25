import { useState } from 'react';
import './App.css';

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

  const getStatusClass = () => {
    if (status.startsWith('Error:')) {
      return 'status-box status-error';
    }
    const isSuccess =
      status.startsWith('Magic link sent successfully') ||
      status.startsWith('Logged in as');
    if (isSuccess) {
      return 'status-box status-success';
    }
    return 'status-box status-info';
  };

  return (
    <div className="app-container">
      <div className="bg-blob bg-blob-purple"></div>
      <div className="bg-blob bg-blob-cyan"></div>
      
      <div className="glass-card">
        <h1 className="app-title">
          Prompt Arena
        </h1>
        <p id="welcome-message" className="welcome-msg">
          Welcome to Prompt Arena
        </p>
        
        <div id="auth-status" className={getStatusClass()}>
          {status}
        </div>

        {user ? (
          <div>
            <h2 className="welcome-title">
              Welcome, {user.email}!
            </h2>
            <button 
              id="logout-button"
              className="btn-logout"
              onClick={() => {
                setUser(null);
                setEmail('');
                setToken('');
                setStep('request-otp');
                setStatus('Welcome to Prompt Arena');
              }}
            >
              Log Out
            </button>
          </div>
        ) : (
          <div className="auth-form-wrapper">
            {step === 'request-otp' ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleRequestOtp(email);
                }}
                className="form-container"
              >
                <h3 className="form-title">
                  Sign In
                </h3>
                <div className="input-group">
                  <label htmlFor="email-input" className="input-label">
                    Email
                  </label>
                  <input
                    id="email-input"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="text-input"
                  />
                </div>
                <button
                  id="submit-email-button"
                  type="submit"
                  className="btn-submit btn-email-submit"
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
                className="form-container"
              >
                <h3 className="form-title">
                  Verify OTP
                </h3>
                <div className="input-group">
                  <label htmlFor="otp-input" className="input-label">
                    One-Time Password / Token
                  </label>
                  <input
                    id="otp-input"
                    type="text"
                    required
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    className="text-input"
                  />
                </div>
                <button
                  id="submit-otp-button"
                  type="submit"
                  className="btn-submit btn-otp-verify"
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
                  className="btn-back"
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
