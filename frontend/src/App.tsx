import React, { useState } from 'react';

interface AuthUser {
  email: string;
  username: string;
}

export default function App() {
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const [status, setStatus] = useState('Welcome to Prompt Arena');
  const [user, setUser] = useState<AuthUser | null>(null);

  const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('Registering...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          username: registerUsername,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setStatus('Registration successful');
      } else {
        setStatus(`Error: ${data.detail || 'Registration failed'}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`Error: ${msg}`);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('Logging in...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setUser({ email: data.email, username: data.username });
        setStatus(`Logged in as ${data.email}`);
      } else {
        setStatus(`Error: ${data.detail || 'Login failed'}`);
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
      status.startsWith('Registration successful') ||
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
              Welcome, {user.username || user.email}!
            </h2>
            <button 
              id="logout-button"
              onClick={() => {
                setUser(null);
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
            {/* Login Section */}
            <form
              onSubmit={handleLogin}
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
                <label htmlFor="login-email" style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                  Email
                </label>
                <input
                  id="login-email"
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
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
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label htmlFor="login-password" style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                  Password
                </label>
                <input
                  id="login-password"
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
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
                id="login-submit"
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
                Sign In
              </button>
            </form>

            {/* Register Section */}
            <form
              onSubmit={handleRegister}
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
                Register
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label
                  htmlFor="register-username"
                  style={{ fontSize: '0.875rem', color: '#9ca3af' }}
                >
                  Username
                </label>
                <input
                  id="register-username"
                  type="text"
                  required
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
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
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label
                  htmlFor="register-email"
                  style={{ fontSize: '0.875rem', color: '#9ca3af' }}
                >
                  Email
                </label>
                <input
                  id="register-email"
                  type="email"
                  required
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
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
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label
                  htmlFor="register-password"
                  style={{ fontSize: '0.875rem', color: '#9ca3af' }}
                >
                  Password
                </label>
                <input
                  id="register-password"
                  type="password"
                  required
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
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
                id="register-submit"
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
                Register
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
