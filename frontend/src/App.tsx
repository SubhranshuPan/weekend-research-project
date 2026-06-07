import React, { useState, useEffect, useRef } from 'react';
import { Search, UploadCloud, FileText, BookOpen, Clock, Loader2, FileUp } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [papers, setPapers] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchPapers();
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query) {
        searchPapers(query);
      } else {
        setResults([]);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const fetchPapers = async () => {
    try {
      const res = await axios.get(`${API_URL}/papers`);
      setPapers(res.data.papers);
    } catch (err) {
      console.error('Failed to fetch papers', err);
    }
  };

  const searchPapers = async (q) => {
    setIsSearching(true);
    try {
      const res = await axios.get(`${API_URL}/search?q=${encodeURIComponent(q)}&limit=20`);
      setResults(res.data.results);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFiles(e.target.files);
    }
  };

  const uploadFiles = async (files) => {
    setIsUploading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchPapers();
      if (query) searchPapers(query);
    } catch (err) {
      console.error('Upload failed', err);
    } finally {
      setIsUploading(false);
    }
  };

  const displayItems = query ? results : papers;

  return (
    <div className="app-container">
      <header>
        <div className="brand">
          <BookOpen size={32} color="#3b82f6" />
          <span>ResearchAssistant</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="upload-button" onClick={() => fileInputRef.current?.click()}>
            <FileUp size={18} style={{ marginRight: '0.5rem', display: 'inline' }} />
            Add Papers
          </button>
        </div>
      </header>

      <div className="search-container">
        <Search className="search-icon" size={20} />
        <input 
          type="text" 
          className="search-input" 
          placeholder="Search by keyword, concept, or author..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {isSearching && (
          <Loader2 className="loader" size={20} style={{ position: 'absolute', right: '1.2rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--accent-color)' }} />
        )}
      </div>

      <div className="main-content">
        <main>
          {papers.length === 0 ? (
            <div 
              className={`dropzone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                multiple 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                style={{ display: 'none' }} 
                accept=".pdf,.txt,.docx,.md"
              />
              <UploadCloud size={64} className="dropzone-icon" />
              <h3>Drag and drop your papers here</h3>
              <p style={{ color: 'var(--text-secondary)' }}>Supports PDF, TXT, DOCX, and MD files</p>
              <button className="upload-button" onClick={() => fileInputRef.current?.click()}>
                {isUploading ? 'Uploading & Indexing...' : 'Browse Files'}
              </button>
            </div>
          ) : (
            <>
              <h2 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', color: 'var(--text-secondary)' }}>
                {query ? `Search Results (${results.length})` : 'Your Library'}
              </h2>
              
              <div className="papers-grid">
                {displayItems.map((item, idx) => (
                  <div key={item.id || idx} className="paper-card glass">
                    <div className="paper-title">
                      {item.filename}
                    </div>
                    <div className="paper-meta">
                      <FileText size={14} />
                      <span>{item.filename.split('.').pop().toUpperCase()}</span>
                      {item.score !== undefined && (
                        <span className="paper-score">
                          Match: {(item.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <div className="paper-actions">
                      <button className="action-btn" title="View Details">
                        <BookOpen size={16} />
                      </button>
                      <button className="action-btn" title="AI Summary">
                        <Loader2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
                
                {displayItems.length === 0 && query && !isSearching && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                    No papers found matching "{query}"
                  </div>
                )}
              </div>
            </>
          )}
          
          {/* Hidden input for navbar button */}
          <input 
            type="file" 
            multiple 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            style={{ display: 'none' }} 
            accept=".pdf,.txt,.docx,.md"
          />
        </main>
        
        <aside className="sidebar">
          <div className="sidebar-section glass">
            <h3 className="section-title">Library Stats</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <BookOpen size={18} color="var(--accent-color)" />
              <span>{papers.length} Papers Indexed</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={18} color="var(--accent-color)" />
              <span>Ready for Search</span>
            </div>
          </div>
          
          <div className="sidebar-section glass">
            <h3 className="section-title">Topics</h3>
            <div className="tag-list">
              <span className="tag" onClick={() => setQuery('learning')}>Learning</span>
              <span className="tag" onClick={() => setQuery('machine')}>Machine</span>
              <span className="tag" onClick={() => setQuery('neural')}>Neural</span>
              <span className="tag" onClick={() => setQuery('network')}>Network</span>
              <span className="tag" onClick={() => setQuery('deep')}>Deep</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
