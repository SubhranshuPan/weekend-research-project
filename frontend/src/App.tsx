import { useState, useEffect, useRef, type ChangeEvent, type DragEvent, type FormEvent, type MouseEvent } from 'react';
import { Search, UploadCloud, FileText, BookOpen, Loader2, FileUp, X, Copy, Check, Trash2, Settings, MessageSquare, Send, Globe, DownloadCloud, Network, Edit3 } from 'lucide-react';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api').replace(/\/$/, '');

type Paper = {
  id: string;
  filename: string;
  path?: string;
  score?: number;
};

type DiscoverPaper = {
  title: string;
  authors: string[];
  summary: string;
  pdf_url: string;
  published: string;
};

type GraphData = {
  nodes: Array<Record<string, any>>;
  links: Array<Record<string, any>>;
};

type ModalType = 'details' | 'summary' | 'settings' | 'cite' | null;

type PaperMetadata = {
  metadata?: {
    title?: string;
    authors?: string;
    year?: string;
  };
  bibtex?: string;
  error?: string;
} | null;

type ChatMessage = {
  role: 'user' | 'ai';
  text: string;
  sources?: string[];
};

function App() {
  const [currentTab, setCurrentTab] = useState<'library' | 'discover' | 'graph' | 'notebook'>('library');
  
  // Library state
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Paper[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Tags & Folders
  const [tags, setTags] = useState<Record<string, string[]>>({});
  const [folders, setFolders] = useState<Record<string, string[]>>({});
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [isTagging, setIsTagging] = useState<Record<string, boolean>>({});

  // Discover state
  const [discoverQuery, setDiscoverQuery] = useState('');
  const [discoverResults, setDiscoverResults] = useState<DiscoverPaper[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [downloadingUrl, setDownloadingUrl] = useState<string | null>(null);
  
  // Notebook state
  const [notebookText, setNotebookText] = useState('# My Research Draft\n\nStart writing here...\n');
  
  // Graph state
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });

  // Modals state
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [metadata, setMetadata] = useState<PaperMetadata>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoadingModal, setIsLoadingModal] = useState(false);
  const [copied, setCopied] = useState(false);

  // Settings state
  const [geminiApiKey, setGeminiApiKey] = useState('');
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchPapers();
    fetchTags();
    const savedKey = localStorage.getItem('geminiApiKey');
    if (savedKey) setGeminiApiKey(savedKey);
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

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

  useEffect(() => {
    if (currentTab === 'graph') {
      fetchGraph();
    }
  }, [currentTab]);

  const fetchPapers = async () => {
    try {
      const res = await axios.get(`${API_URL}/papers`);
      setPapers(res.data.papers);
    } catch (err) {
      console.error('Failed to fetch papers', err);
    }
  };

  const fetchTags = async () => {
    try {
      const res = await axios.get(`${API_URL}/tags`);
      setTags(res.data.paper_tags);
      setFolders(res.data.folders);
    } catch (err) {
      console.error('Failed to fetch tags', err);
    }
  };

  const fetchGraph = async () => {
    try {
      const res = await axios.get(`${API_URL}/graph`);
      setGraphData(res.data);
    } catch (err) {
      console.error('Failed to fetch graph', err);
    }
  };

  const searchPapers = async (q: string) => {
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

  const autoTag = async (paper: Paper) => {
    if (!geminiApiKey) {
      alert("Please configure your Gemini API Key in Settings to use Auto-Tagging.");
      setModalType('settings');
      return;
    }
    setIsTagging(prev => ({...prev, [paper.id]: true}));
    try {
      await axios.get(`${API_URL}/papers/${paper.id}/auto_tag`, {
        headers: { 'x-gemini-key': geminiApiKey }
      });
      await fetchTags();
    } catch (err) {
      console.error(err);
      alert('Failed to generate tags. Ensure Gemini key is valid and backend is running.');
    } finally {
      setIsTagging(prev => ({...prev, [paper.id]: false}));
    }
  };

  const searchDiscover = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!discoverQuery) return;
    setIsDiscovering(true);
    try {
      const res = await axios.get(`${API_URL}/discover?q=${encodeURIComponent(discoverQuery)}`);
      setDiscoverResults(res.data.results);
    } catch (err) {
      console.error('Discover failed', err);
    } finally {
      setIsDiscovering(false);
    }
  };

  const downloadPaper = async (paper: DiscoverPaper) => {
    setDownloadingUrl(paper.pdf_url);
    try {
      await axios.post(`${API_URL}/discover/download`, {
        title: paper.title,
        pdf_url: paper.pdf_url
      });
      await fetchPapers();
      setCurrentTab('library');
    } catch (err) {
      console.error('Download failed', err);
      alert('Failed to download paper.');
    } finally {
      setDownloadingUrl(null);
    }
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFiles(e.target.files);
    }
  };

  const uploadFiles = async (files: FileList) => {
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

  const deletePaper = async (paperId: string, e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete ${paperId}?`)) return;
    try {
      await axios.delete(`${API_URL}/papers/${paperId}`);
      await fetchPapers();
      await fetchTags();
      if (query) searchPapers(query);
      if (currentTab === 'graph') fetchGraph();
    } catch (err) {
      console.error('Delete failed', err);
    }
  };

  const openDetails = async (paper: Paper) => {
    setSelectedPaper(paper);
    setModalType('details');
    setIsLoadingModal(true);
    try {
      const res = await axios.get(`${API_URL}/papers/${paper.id}/metadata`);
      setMetadata(res.data);
    } catch (err) {
      console.error(err);
      setMetadata({ error: "Failed to load metadata" });
    } finally {
      setIsLoadingModal(false);
    }
  };

  const openSummary = async (paper: Paper) => {
    setSelectedPaper(paper);
    setModalType('summary');
    setIsLoadingModal(true);
    try {
      const res = await axios.get(`${API_URL}/papers/${paper.id}/summary`, {
        headers: { 'x-gemini-key': geminiApiKey }
      });
      setSummary(res.data.summary);
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 401 || err.response?.status === 500) {
        setSummary("Error: " + (err.response?.data?.detail || "Failed to generate summary."));
      } else {
        setSummary("Failed to load summary");
      }
    } finally {
      setIsLoadingModal(false);
    }
  };

  const copyBibtex = () => {
    if (metadata?.bibtex) {
      navigator.clipboard.writeText(metadata.bibtex);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const saveSettings = () => {
    localStorage.setItem('geminiApiKey', geminiApiKey);
    closeModal();
  };

  const insertCitation = async (paper: Paper) => {
    setIsLoadingModal(true);
    try {
      const res = await axios.get(`${API_URL}/papers/${paper.id}/metadata`);
      const bibtex = res.data.bibtex || `Citation for ${paper.filename}`;
      setNotebookText(prev => prev + '\n\n' + bibtex);
      setModalType(null);
    } catch (err) {
      console.error(err);
      alert('Failed to fetch citation.');
    } finally {
      setIsLoadingModal(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || isChatting) return;
    
    if (!geminiApiKey) {
      alert("Please configure your Gemini API Key in Settings first.");
      setModalType('settings');
      return;
    }

    const newMsgs: ChatMessage[] = [...chatMessages, { role: 'user', text: chatInput }];
    setChatMessages(newMsgs);
    setChatInput('');
    setIsChatting(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, { query: chatInput }, {
        headers: { 'x-gemini-key': geminiApiKey }
      });
      
      setChatMessages([...newMsgs, { role: 'ai', text: res.data.answer, sources: res.data.sources }]);
    } catch (err: any) {
      setChatMessages([...newMsgs, { role: 'ai', text: "Error: " + (err.response?.data?.detail || "Failed to get response.") }]);
    } finally {
      setIsChatting(false);
    }
  };

  const closeModal = () => {
    setSelectedPaper(null);
    setModalType(null);
    setMetadata(null);
    setSummary(null);
  };

  const displayItems = (query ? results : papers).filter(item => {
    if (!selectedFolder) return true;
    const paperTags = tags[item.id] || [];
    return paperTags.includes(selectedFolder);
  });

  return (
    <div className="app-container">
      <header>
        <div className="brand">
          <BookOpen size={32} color="#3b82f6" />
          <span>ResearchAssistant</span>
        </div>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${currentTab === 'library' ? 'active' : ''}`}
            onClick={() => setCurrentTab('library')}
          >
            <BookOpen size={18} /> My Library
          </button>
          <button 
            className={`nav-tab ${currentTab === 'discover' ? 'active' : ''}`}
            onClick={() => setCurrentTab('discover')}
          >
            <Globe size={18} /> Discover
          </button>
          <button 
            className={`nav-tab ${currentTab === 'graph' ? 'active' : ''}`}
            onClick={() => setCurrentTab('graph')}
          >
            <Network size={18} /> Knowledge Graph
          </button>
          <button 
            className={`nav-tab ${currentTab === 'notebook' ? 'active' : ''}`}
            onClick={() => setCurrentTab('notebook')}
          >
            <Edit3 size={18} /> Notebook
          </button>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="icon-button" onClick={() => setModalType('settings')} title="Settings">
            <Settings size={18} />
          </button>
          <button className="upload-button" onClick={() => fileInputRef.current?.click()}>
            <FileUp size={18} style={{ marginRight: '0.5rem', display: 'inline' }} />
            Add Papers
          </button>
        </div>
      </header>

      <div className="main-content">
        <main>
          {currentTab === 'library' && (
            <>
              <div className="search-container" style={{ marginBottom: '1.5rem' }}>
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

              {Object.keys(folders).length > 0 && (
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
                  <button 
                    onClick={() => setSelectedFolder(null)}
                    style={{ 
                      padding: '0.4rem 1rem', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', 
                      background: selectedFolder === null ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.05)', 
                      color: selectedFolder === null ? 'white' : 'var(--text-secondary)' 
                    }}
                  >
                    All Papers
                  </button>
                  {Object.keys(folders).map(folder => (
                    <button 
                      key={folder}
                      onClick={() => setSelectedFolder(folder)}
                      style={{ 
                        padding: '0.4rem 1rem', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', 
                        background: selectedFolder === folder ? 'var(--accent-gradient)' : 'rgba(255,255,255,0.05)', 
                        color: selectedFolder === folder ? 'white' : 'var(--text-secondary)' 
                      }}
                    >
                      {folder} ({folders[folder].length})
                    </button>
                  ))}
                </div>
              )}

              {papers.length === 0 ? (
                <div 
                  className={`dropzone ${dragActive ? 'active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
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
                    {selectedFolder ? `Folder: ${selectedFolder} (${displayItems.length})` : (query ? `Search Results (${results.length})` : 'Your Library')}
                  </h2>
                  
                  <div className="papers-grid">
                    {displayItems.map((item, idx) => (
                      <div key={item.id || idx} className="paper-card glass">
                        <div className="paper-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <a 
                            href={`${API_URL}/files/${encodeURIComponent(item.id)}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ color: 'var(--accent-hover)', textDecoration: 'none' }}
                            title="Open paper in new tab"
                          >
                            {item.filename}
                          </a>
                          <button 
                            onClick={(e) => deletePaper(item.id, e)}
                            style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                            title="Delete Paper"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                        <div className="paper-meta">
                          <FileText size={14} />
                          <span>{item.filename.split('.').pop()?.toUpperCase() || 'TXT'}</span>
                          {item.score !== undefined && (
                            <span className="paper-score">
                              Match: {(item.score * 100).toFixed(0)}
                            </span>
                          )}
                        </div>
                        
                        <div className="paper-tags" style={{ display: 'flex', gap: '0.4rem', marginTop: '0.8rem', flexWrap: 'wrap' }}>
                          {tags[item.id] ? tags[item.id].map(tag => (
                            <span key={tag} style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem' }}>
                              {tag}
                            </span>
                          )) : (
                            <button onClick={() => autoTag(item)} style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: '#94a3b8', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              {isTagging[item.id] ? <Loader2 size={12} className="loader" /> : 'Auto-Tag'}
                            </button>
                          )}
                        </div>

                        <div className="paper-actions" style={{ marginTop: '1rem' }}>
                          <button className="action-btn" title="View Details" onClick={() => openDetails(item)}>
                            <BookOpen size={16} style={{ marginRight: '6px' }} /> Details
                          </button>
                          <button className="action-btn" title="AI Summary" onClick={() => openSummary(item)}>
                            <Loader2 size={16} style={{ marginRight: '6px' }} /> Summary
                          </button>
                        </div>
                      </div>
                    ))}
                    
                    {displayItems.length === 0 && !isSearching && (
                      <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                        No papers found in this category.
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}

          {currentTab === 'notebook' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Edit3 size={24} color="var(--accent-color)" /> Smart Notebook
                </h2>
                <button className="upload-button" onClick={() => { setModalType('cite'); setQuery(''); }} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <BookOpen size={16} /> Insert Citation
                </button>
              </div>
              <textarea 
                className="glass"
                value={notebookText}
                onChange={e => setNotebookText(e.target.value)}
                style={{ 
                  flex: 1, width: '100%', padding: '1.5rem', borderRadius: '12px', 
                  background: 'rgba(30, 41, 59, 0.4)', color: 'var(--text-primary)', 
                  border: '1px solid var(--border-color)', fontSize: '1rem', 
                  lineHeight: '1.6', resize: 'vertical', minHeight: '500px',
                  fontFamily: 'inherit'
                }}
                placeholder="Start drafting your research here. Click 'Insert Citation' to search your library and automatically append a BibTeX citation."
              />
            </div>
          )}

          {currentTab === 'discover' && (
            <>
              <div className="search-container" style={{ marginBottom: '2rem' }}>
                <Search className="search-icon" size={20} />
                <form onSubmit={searchDiscover}>
                  <input 
                    type="text" 
                    className="search-input" 
                    placeholder="Search arXiv for latest papers on any topic..." 
                    value={discoverQuery}
                    onChange={(e) => setDiscoverQuery(e.target.value)}
                  />
                  <button type="submit" style={{ display: 'none' }}></button>
                </form>
                {isDiscovering && (
                  <Loader2 className="loader" size={20} style={{ position: 'absolute', right: '1.2rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--accent-color)' }} />
                )}
              </div>

              {!isDiscovering && discoverResults.length === 0 && !discoverQuery && (
                <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                  <Globe size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                  <h3>Discover New Research</h3>
                  <p>Type a topic or keyword above and hit enter to search the arXiv database.</p>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {discoverResults.map((paper, idx) => (
                  <div key={idx} className="glass" style={{ padding: '1.5rem', borderRadius: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                      <h3 style={{ fontSize: '1.2rem', lineHeight: '1.4', marginBottom: '0.5rem', color: 'var(--accent-hover)' }}>
                        {paper.title}
                      </h3>
                      <button 
                        className="upload-button" 
                        onClick={() => downloadPaper(paper)}
                        disabled={downloadingUrl === paper.pdf_url}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', whiteSpace: 'nowrap' }}
                      >
                        {downloadingUrl === paper.pdf_url ? (
                          <><Loader2 size={16} className="loader" /> Indexing...</>
                        ) : (
                          <><DownloadCloud size={16} /> Add to Library</>
                        )}
                      </button>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                      {paper.authors.join(', ')} • {paper.published}
                    </p>
                    <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: '1.6', opacity: 0.8 }}>
                      {paper.summary.length > 300 ? paper.summary.substring(0, 300) + '...' : paper.summary}
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}

          {currentTab === 'graph' && (
            <div className="glass" style={{ height: '600px', borderRadius: '16px', overflow: 'hidden', position: 'relative' }}>
              <h2 style={{ position: 'absolute', top: '1rem', left: '1rem', zIndex: 10, color: 'var(--text-primary)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Network size={20} color="var(--accent-color)" /> Knowledge Graph
              </h2>
              {graphData.nodes.length > 0 ? (
                <ForceGraph2D
                  graphData={graphData}
                  nodeLabel=""
                  linkColor={() => 'rgba(255,255,255,0.2)'}
                  backgroundColor="#0b0f19"
                  nodeRelSize={6}
                  linkWidth={link => link.value * 5}
                  onNodeClick={node => {
                    const paper = papers.find(p => p.id === node.id);
                    if (paper) openDetails(paper);
                  }}
                  nodeCanvasObject={(node, ctx, globalScale) => {
                    const x = node.x ?? 0;
                    const y = node.y ?? 0;

                    // Draw the circle
                    ctx.beginPath();
                    ctx.arc(x, y, 5, 0, 2 * Math.PI, false);
                    ctx.fillStyle = '#3b82f6';
                    ctx.fill();

                    // Draw the text
                    const label = node.name || node.id;
                    const fontSize = Math.max(12 / globalScale, 4);
                    ctx.font = `${fontSize}px Inter, sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    
                    // Optional background for text readability
                    const textWidth = ctx.measureText(label).width;
                    ctx.fillStyle = 'rgba(11, 15, 25, 0.7)';
                    ctx.fillRect(x - textWidth / 2 - 2, y + 7, textWidth + 4, fontSize + 2);
                    
                    ctx.fillStyle = '#e2e8f0';
                    ctx.fillText(label, x, y + 8);
                  }}
                  width={800}
                  height={600}
                />
              ) : (
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                  Not enough papers to build a graph, or semantic search is unavailable.
                </div>
              )}
            </div>
          )}
        </main>
        
        <aside className="sidebar">
          <div className="sidebar-section glass" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1.5rem' }}>
            <h2 style={{ marginBottom: '1rem', color: 'var(--accent-hover)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.2rem' }}>
              <MessageSquare size={20} /> Library Chat
            </h2>
            
            <div className="chat-messages sidebar-chat-messages">
              {chatMessages.length === 0 && (
                <div style={{ color: 'var(--text-secondary)', textAlign: 'center', margin: 'auto', fontSize: '0.9rem' }}>
                  Ask a question about your papers! I will search your library and synthesize an answer.
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  <div>{msg.text}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <strong>Sources:</strong> {msg.sources.join(', ')}
                    </div>
                  )}
                </div>
              ))}
              {isChatting && (
                <div className="chat-message ai">
                  <Loader2 className="loader" size={16} /> Thinking...
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            
            <div className="chat-input-container">
              <input 
                type="text" 
                className="chat-input" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendChatMessage()}
                placeholder="Ask something..."
                style={{ padding: '0.8rem', fontSize: '0.9rem' }}
              />
              <button 
                onClick={sendChatMessage} 
                className="upload-button" 
                disabled={isChatting || !chatInput.trim()}
                style={{ padding: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </aside>
      </div>

      {/* Global Hidden File Input */}
      <input 
        type="file" 
        multiple 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        style={{ display: 'none' }} 
        accept=".pdf,.txt,.docx,.md"
      />

      {/* Modal Overlay */}
      {modalType && (
        <div className="modal-overlay" onClick={closeModal} style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="modal-content glass" onClick={e => e.stopPropagation()} style={{
            width: '90%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto',
            padding: '2rem', borderRadius: '16px', position: 'relative',
            display: 'flex', flexDirection: 'column'
          }}>
            <button onClick={closeModal} style={{
              position: 'absolute', top: '1.5rem', right: '1.5rem',
              background: 'transparent', border: 'none', color: 'var(--text-secondary)',
              cursor: 'pointer'
            }}>
              <X size={24} />
            </button>
            
            {modalType === 'settings' && (
              <div>
                <h2 style={{ marginBottom: '1.5rem', color: 'var(--accent-hover)' }}>Settings</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Gemini API Key</label>
                  <input 
                    type="password" 
                    value={geminiApiKey} 
                    onChange={e => setGeminiApiKey(e.target.value)}
                    className="search-input"
                    placeholder="AIzaSy..."
                    style={{ padding: '0.8rem 1rem' }}
                  />
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Your API key is stored locally in your browser and used only to request AI Summaries and Chat answers.
                  </p>
                  <button onClick={saveSettings} className="upload-button" style={{ alignSelf: 'flex-start', marginTop: '1rem' }}>
                    Save Settings
                  </button>
                </div>
              </div>
            )}

            {modalType === 'details' && (
              <>
                <h2 style={{ marginBottom: '1.5rem', color: 'var(--accent-hover)', paddingRight: '2rem', wordBreak: 'break-word' }}>
                  {selectedPaper?.filename}
                </h2>
                {isLoadingModal ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <Loader2 className="loader" size={32} color="var(--accent-color)" />
                  </div>
                ) : metadata ? (
                  <div>
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>TITLE</h3>
                      <p style={{ fontSize: '1.1rem' }}>{metadata.metadata?.title}</p>
                    </div>
                    <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '2rem' }}>
                      <div>
                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>AUTHORS</h3>
                        <p>{metadata.metadata?.authors}</p>
                      </div>
                      <div>
                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>YEAR</h3>
                        <p>{metadata.metadata?.year}</p>
                      </div>
                    </div>
                    
                    <div style={{ marginTop: '2rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>BIBTEX CITATION</h3>
                        <button onClick={copyBibtex} style={{
                          background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-hover)',
                          border: 'none', padding: '0.4rem 0.8rem', borderRadius: '6px',
                          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem',
                          fontSize: '0.85rem'
                        }}>
                          {copied ? <Check size={14} /> : <Copy size={14} />}
                          {copied ? 'Copied!' : 'Copy BibTeX'}
                        </button>
                      </div>
                      <pre style={{
                        background: 'rgba(15, 23, 42, 0.8)', padding: '1rem', borderRadius: '8px',
                        overflowX: 'auto', fontSize: '0.9rem', border: '1px solid var(--border-color)',
                        color: '#e2e8f0'
                      }}>
                        {metadata.bibtex}
                      </pre>
                    </div>
                  </div>
                ) : <p>Error loading data.</p>}
              </>
            )}

            {modalType === 'summary' && (
              <>
                <h2 style={{ marginBottom: '1.5rem', color: 'var(--accent-hover)', paddingRight: '2rem', wordBreak: 'break-word' }}>
                  {selectedPaper?.filename}
                </h2>
                {isLoadingModal ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <Loader2 className="loader" size={32} color="var(--accent-color)" />
                  </div>
                ) : summary ? (
                  <div>
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>AI SUMMARY</h3>
                    <div style={{ 
                      lineHeight: '1.6', color: 'var(--text-primary)', 
                      background: 'rgba(59, 130, 246, 0.05)', padding: '1.5rem', 
                      borderRadius: '8px', borderLeft: '4px solid var(--accent-color)',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {summary}
                    </div>
                  </div>
                ) : <p>Error loading data.</p>}
              </>
            )}

            {modalType === 'cite' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
                <h2 style={{ marginBottom: '1rem', color: 'var(--accent-hover)' }}>Insert Citation</h2>
                <div className="search-container" style={{ marginBottom: '1rem' }}>
                  <Search className="search-icon" size={20} />
                  <input 
                    type="text" className="search-input" placeholder="Search your library..."
                    value={query} onChange={e => setQuery(e.target.value)}
                  />
                  {isSearching && <Loader2 className="loader" size={20} style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)' }} />}
                </div>
                
                {isLoadingModal ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem', flex: 1, alignItems: 'center' }}>
                    <Loader2 className="loader" size={32} color="var(--accent-color)" />
                    <span style={{ marginLeft: '1rem' }}>Extracting metadata...</span>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', overflowY: 'auto', flex: 1, paddingRight: '0.5rem' }}>
                    {displayItems.map(item => (
                      <div key={item.id} className="glass" style={{ 
                        padding: '1rem', display: 'flex', justifyContent: 'space-between', 
                        alignItems: 'center', transition: 'all 0.2s' 
                      }}>
                        <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingRight: '1rem' }}>
                          {item.filename}
                        </span>
                        <button className="upload-button" onClick={() => insertCitation(item)} style={{ padding: '0.4rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <Check size={14} /> Cite
                        </button>
                      </div>
                    ))}
                    {displayItems.length === 0 && (
                      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem' }}>No papers found.</p>
                    )}
                  </div>
                )}
              </div>
            )}
            
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
