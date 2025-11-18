import React, { useState, useEffect } from 'react';
import { notesAPI } from '../services/api';
import type { Note } from '../services/api';
import './CreateNote.css';

interface UpdateNoteProps {
  noteId: string;
  onBack: () => void;
  onSaved: () => void;
}

export const UpdateNote: React.FC<UpdateNoteProps> = ({ noteId, onBack, onSaved }) => {
  const [title, setTitle] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [originalTitle, setOriginalTitle] = useState<string>('');
  const [originalContent, setOriginalContent] = useState<string>('');
  const [image, setImage] = useState<string | null>(null);
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [noteType, setNoteType] = useState<'text' | 'image'>('text');
  const contentRef = React.useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const loadNote = async () => {
      try {
        const notesList = await notesAPI.list();
        const note = notesList.find((n: Note) => n.id === noteId);
        if (note) {
          // Detect if image or text note - kiểm tra files thay vì content
          if (note.files && note.files.length > 0) {
            setNoteType('image');
            setImage(note.files[0].url || null);
            setOriginalImage(note.files[0].url || null);
          } else {
            setNoteType('text');
            const noteTitle = note.title || '';
            const noteContent = note.content || '';
            setTitle(noteTitle);
            setContent(noteContent);
            setOriginalTitle(noteTitle);
            setOriginalContent(noteContent);
          }
        }
      } catch {
        alert('Không thể tải ghi chú');
        onBack();
      } finally {
        setLoading(false);
      }
    };
    loadNote();
  }, [noteId, onBack]);

  // Auto-resize textarea after content loads
  useEffect(() => {
    if (contentRef.current && content) {
      setTimeout(() => {
        if (contentRef.current) {
          contentRef.current.style.height = 'auto';
          contentRef.current.style.height = contentRef.current.scrollHeight + 'px';
        }
      }, 0);
    }
  }, [content]);

  const hasChanges = () => {
    if (noteType === 'text') {
      return title !== originalTitle || content !== originalContent;
    } else {
      return image !== originalImage;
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (noteType === 'text') {
        await notesAPI.update(noteId, title || null, content.trim() || null);
      } else {
        await notesAPI.update(noteId, 'Ghi chú hình ảnh', image);
      }
      onSaved();
      onBack();
    } catch {
      alert('Không thể lưu ghi chú');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="create-note-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="create-note-container">
      <header className="create-note-header">
        <button onClick={onBack} className="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        {noteType === 'text' && (
          <button 
            onClick={handleSave} 
            className="save-btn"
            disabled={saving || !hasChanges()}
          >
            {saving ? 'Đang lưu...' : 'Lưu'}
          </button>
        )}
      </header>

      <main className="create-note-main">
        {noteType === 'text' ? (
          <div className="text-editor">
            <textarea
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  contentRef.current?.focus();
                }
              }}
              placeholder="Tiêu đề"
              className="note-line-input title-line"
              autoFocus
              rows={1}
              style={{ resize: 'none', overflow: 'hidden' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = target.scrollHeight + 'px';
              }}
            />
            <textarea
              ref={contentRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Ghi chú"
              className="note-line-input content-line"
              rows={1}
              style={{ resize: 'none', overflow: 'hidden' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = target.scrollHeight + 'px';
              }}
            />
          </div>
        ) : (
          <div className="image-editor">
            <div className="image-preview-container">
              {image ? (
                <img src={image} alt="Note image" className="image-preview" />
              ) : (
                <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                  Không thể tải ảnh
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
