import { SignIn, SignUp, useUser, UserButton } from '@clerk/clerk-react';
import { useState } from 'react';
import './AuthWrapper.css';

export function AuthWrapper({ children }) {
  const { isSignedIn, isLoaded, user } = useUser();
  const [showSignUp, setShowSignUp] = useState(false);

  if (!isLoaded) {
    return (
      <div className="auth-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="auth-container">
        <div className="auth-box">
          <h1 className="auth-title">🤝 LLM Council</h1>
          <p className="auth-subtitle">
            Collaborative AI deliberation with multiple language models
          </p>

          <div className="auth-form">
            {showSignUp ? (
              <>
                <SignUp
                  appearance={{
                    elements: {
                      formButtonPrimary: 'clerk-button-primary',
                      card: 'clerk-card'
                    }
                  }}
                />
                <button
                  className="auth-toggle-button"
                  onClick={() => setShowSignUp(false)}
                >
                  Already have an account? Sign in
                </button>
              </>
            ) : (
              <>
                <SignIn
                  appearance={{
                    elements: {
                      formButtonPrimary: 'clerk-button-primary',
                      card: 'clerk-card'
                    }
                  }}
                />
                <button
                  className="auth-toggle-button"
                  onClick={() => setShowSignUp(true)}
                >
                  Don't have an account? Sign up
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <h1 className="header-title">🤝 LLM Council</h1>
          <div className="header-user">
            <span className="user-greeting">Welcome, {user?.firstName || user?.username}!</span>
            <UserButton
              appearance={{
                elements: {
                  avatarBox: 'user-avatar'
                }
              }}
            />
          </div>
        </div>
      </header>
      <div className="app-content">
        {children}
      </div>
    </>
  );
}
