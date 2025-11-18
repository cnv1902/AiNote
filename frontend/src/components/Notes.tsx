import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { notesAPI } from '../services/api';
import type { Note } from '../services/api';
import './Notes.css';

export const Notes: React.FC = () => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    const loadNotes = async () => {
      try {
        const data = await notesAPI.list();
        setNotes(data);
      } catch {
        console.error('Không thể tải ghi chú');
      }
    };

    loadNotes();
  }, []);

  const navigateTo = useCallback((hash: string) => {
    // Safe navigation helper
    window.location.href = hash;
  }, []);

  const handleCreateNote = useCallback((type: 'text' | 'image') => {
    setShowCreateMenu(false);
    navigateTo(`#/create/${type}`);
  }, [navigateTo]);

  const handleViewNote = useCallback((noteId: string) => {
    navigateTo(`#/note/${noteId}`);
  }, [navigateTo]);

  const handleDeleteNote = async (noteId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notesAPI.delete(noteId);
      setNotes(notes.filter(n => n.id !== noteId));
    } catch {
      alert('Không thể xóa ghi chú');
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    const element = e.currentTarget as HTMLElement;
    element.dataset.touchStartX = touch.clientX.toString();
    element.dataset.touchStartTime = Date.now().toString();
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    const element = e.currentTarget as HTMLElement;
    const startX = parseFloat(element.dataset.touchStartX || '0');
    const currentX = touch.clientX;
    const diff = startX - currentX;

    if (diff > 0 && diff <= 100) {
      element.style.transform = `translateX(-${diff}px)`;
      element.style.transition = 'none';
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const element = e.currentTarget as HTMLElement;
    const startX = parseFloat(element.dataset.touchStartX || '0');
    const startTime = parseFloat(element.dataset.touchStartTime || '0');
    const endX = e.changedTouches[0].clientX;
    const diff = startX - endX;
    const duration = Date.now() - startTime;

    element.style.transition = 'transform 0.3s ease';

    if (diff > 80 || (diff > 30 && duration < 300)) {
      element.style.transform = 'translateX(-80px)';
    } else {
      element.style.transform = 'translateX(0)';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Hôm nay';
    } else if (diffDays < 30) {
      return `${diffDays} ngày trước`;
    } else {
      return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: '2-digit' });
    }
  };

  const groupNotesByDate = (notes: Note[]) => {
    const groups: { [key: string]: Note[] } = {};
    
    notes.forEach(note => {
      const date = new Date(note.created_at);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      let group = '';
      if (diffDays < 30) {
        group = '30 ngày trước';
      } else if (diffDays < 60) {
        group = '60 ngày trước';
      } else {
        group = 'Cũ hơn';
      }
      
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(note);
    });
    
    return groups;
  };

  const filteredNotes = notes.filter(note => {
    const searchLower = searchQuery.toLowerCase();
    return (
      note.title?.toLowerCase().includes(searchLower) ||
      note.content?.toLowerCase().includes(searchLower)
    );
  });

  const groupedNotes = groupNotesByDate(filteredNotes);

  return (
    <div className="notes-container-mobile">
      <header className="notes-header-mobile">
        <div className="header-top">
          <h1 className="page-title">Ghi chú</h1>
          <button onClick={logout} className="logout-btn">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <polyline points="16 17 21 12 16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        <div className="search-container">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="8" stroke="#9ca3af" strokeWidth="2"/>
            <path d="M21 21l-4.35-4.35" stroke="#9ca3af" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <input
            type="text"
            placeholder="Tìm kiếm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button className="voice-search-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke="#9ca3af" strokeWidth="2"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" stroke="#9ca3af" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </header>

      <main className="notes-main-mobile">
        {Object.keys(groupedNotes).length === 0 ? (
          <div className="empty-state-mobile">
            <p>Chưa có ghi chú nào</p>
          </div>
        ) : (
          <div className="notes-list-mobile">
            {Object.entries(groupedNotes).map(([group, groupNotes]) => (
              <div key={group} className="notes-group">
                <h2 className="group-title">{group}</h2>
                {groupNotes.map((note) => (
                  <div key={note.id} className="note-item-wrapper">
                    <div
                      className="note-item"
                      onClick={() => handleViewNote(note.id)}
                      onTouchStart={handleTouchStart}
                      onTouchMove={handleTouchMove}
                      onTouchEnd={handleTouchEnd}
                    >
                      <div className="note-content">
                        <h3 className="note-title-mobile">
                          {note.title || 'Không có tiêu đề'}
                        </h3>
                        {note.files && note.files.length > 0 ? (
                          <img 
                            src={note.files[0].url || ''} 
                            alt={note.title || 'Note image'} 
                            className="note-image-preview"
                          />
                        ) : note.content ? (
                          <p className="note-preview">{note.content.substring(0, 100)}</p>
                        ) : null}
                      </div>
                      <span className="note-date-mobile">{formatDate(note.created_at)}</span>
                    </div>
                    <button
                      className="delete-action"
                      onClick={(e) => handleDeleteNote(note.id, e)}
                      aria-label="Xóa ghi chú"
                    >
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </main>

      <div className="fab-container">
        {showCreateMenu && (
          <div className="fab-menu">
            <button 
              className="fab-menu-item"
              onClick={() => handleCreateNote('image')}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                <path d="M21 15l-5-5L5 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Hình ảnh</span>
            </button>
            <button 
              className="fab-menu-item"
              onClick={() => handleCreateNote('text')}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Văn bản</span>
            </button>
          </div>
        )}
        <button 
          className="fab"
          onClick={() => setShowCreateMenu(!showCreateMenu)}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ transform: showCreateMenu ? 'rotate(45deg)' : 'none', transition: 'transform 0.2s' }}>
            <path d="M20 14.66V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5.34" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M18 2l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M7.5 20.5L22 6l-4-4L3.5 16.5l-1.5 5.5 5.5-1.5z" fill="currentColor"/>
          </svg>
        </button>
      </div>

      <div className="bottom-info">
        <span>{filteredNotes.length} ghi chú</span>
      </div>
    </div>
  );
};
