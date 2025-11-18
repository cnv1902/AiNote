import { useState, useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext.tsx';
import { useAuth } from './hooks/useAuth';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { Notes } from './components/Notes';
import { CreateNote } from './components/CreateNote';
import { UpdateNote } from './components/UpdateNote';
import './App.css';

function AppContent() {
  const [showLogin, setShowLogin] = useState(true);
  const [currentView, setCurrentView] = useState<'list' | 'create' | 'update'>('list');
  const [createType, setCreateType] = useState<'text' | 'image'>('text');
  const [editNoteId, setEditNoteId] = useState<string>('');
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#/create/')) {
        const type = hash.split('/')[2] as 'text' | 'image';
        setCreateType(type);
        setCurrentView('create');
      } else if (hash.startsWith('#/note/')) {
        const noteId = hash.split('/')[2];
        setEditNoteId(noteId);
        setCurrentView('update');
      } else {
        setCurrentView('list');
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Đang tải...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return showLogin ? (
      <Login onSwitchToRegister={() => setShowLogin(false)} />
    ) : (
      <Register onSwitchToLogin={() => setShowLogin(true)} />
    );
  }

  if (currentView === 'create') {
    return (
      <CreateNote
        type={createType}
        onBack={() => {
          window.location.hash = '#/';
          setCurrentView('list');
        }}
        onSaved={() => {
          // Refresh notes list
        }}
      />
    );
  }

  if (currentView === 'update') {
    return (
      <UpdateNote
        noteId={editNoteId}
        onBack={() => {
          window.location.hash = '#/';
          setCurrentView('list');
        }}
        onSaved={() => {
          // Refresh notes list
        }}
      />
    );
  }

  return <Notes />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
