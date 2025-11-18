import React, { useState, useRef } from 'react';
import { notesAPI } from '../services/api';
import './CreateNote.css';

interface CreateNoteProps {
  type: 'text' | 'image';
  onBack: () => void;
  onSaved: () => void;
}

export const CreateNote: React.FC<CreateNoteProps> = ({ type, onBack, onSaved }) => {
  const [title, setTitle] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const contentRef = useRef<HTMLTextAreaElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (type === 'text') {
        await notesAPI.create(title || null, content.trim() || null);
      } else {
        if (!imageFile) {
          alert('Vui lòng chọn ảnh');
          return;
        }
        await notesAPI.uploadImage(imageFile, 'Ghi chú hình ảnh');
      }
      onSaved();
      onBack();
    } catch (error) {
      console.error('Error saving note:', error);
      alert('Không thể lưu ghi chú');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="create-note-container">
      <header className="create-note-header">
        <button onClick={onBack} className="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <button 
          onClick={handleSave} 
          className="save-btn"
          disabled={saving || (type === 'text' && !title.trim() && !content.trim()) || (type === 'image' && !image)}
        >
          {saving ? 'Đang lưu...' : 'Lưu'}
        </button>
      </header>

      <main className="create-note-main">
        {type === 'text' ? (
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
            {!image ? (
              <div className="image-upload-options">
                <button 
                  className="upload-option"
                  onClick={() => cameraInputRef.current?.click()}
                >
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2"/>
                    <circle cx="12" cy="13" r="4" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  <span>Chụp ảnh</span>
                </button>
                <button 
                  className="upload-option"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                    <path d="M21 15l-5-5L5 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>Tải ảnh lên</span>
                </button>
                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleImageSelect}
                  style={{ display: 'none' }}
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  style={{ display: 'none' }}
                />
              </div>
            ) : (
              <div className="image-preview-container">
                <img src={image} alt="Preview" className="image-preview" />
                <button 
                  className="change-image-btn"
                  onClick={() => {
                    setImage(null);
                    setImageFile(null);
                  }}
                >
                  Thay đổi ảnh
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
