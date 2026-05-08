'use client';

import { useState, useCallback, useEffect } from 'react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [results, setResults] = useState(null);
  const [annotatedBase64, setAnnotatedBase64] = useState(null);
  const [annotatedFileName, setAnnotatedFileName] = useState('');
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('results');
  const [previewLoading, setPreviewLoading] = useState(false);

  // Effect to render DOCX preview when results change
  const renderDocxPreview = useCallback(async (base64Data) => {
    if (!base64Data || typeof window === 'undefined') return;
    
    setPreviewLoading(true);
    try {
      const { renderAsync } = await import('docx-preview');
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      
      const container = document.getElementById('document-viewer-container');
      if (container) {
        container.innerHTML = '';
        await renderAsync(blob, container, null, {
          className: 'docx-preview',
          inWrapper: false,
          ignoreWidth: false,
          ignoreHeight: false,
          debug: false,
          useCustomFormat: true
        });
        console.log("Preview rendered successfully");
      } else {
        console.warn("Container not found for preview");
      }
    } catch (err) {
      console.error('Error rendering preview:', err);
      setError("Error al generar la vista previa. El documento revisado puede descargarse normalmente.");
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  // UseEffect to trigger preview after state updates
  useEffect(() => {
    if (annotatedBase64) {
      renderDocxPreview(annotatedBase64);
    }
  }, [annotatedBase64, renderDocxPreview]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.docx')) {
      setFile(droppedFile);
      uploadFile(droppedFile);
    } else {
      setError('Solo se aceptan archivos .docx (Word)');
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      uploadFile(selectedFile);
    }
  }, []);

  const uploadFile = async (fileToUpload) => {
    setUploading(true);
    setError(null);
    setProgress(10);
    setProgressText('Subiendo archivo...');

    try {
      const formData = new FormData();
      formData.append('file', fileToUpload);

      setProgress(30);
      setProgressText('Analizando estructura del documento...');

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      setProgress(70);
      setProgressText('Verificando reglas de formato...');

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al procesar el documento');
      }

      setProgress(90);
      setProgressText('Generando documento anotado...');

      setResults(data.results);
      setAnnotatedBase64(data.annotatedBase64);
      setAnnotatedFileName(data.annotatedFileName);

      setProgress(100);
      setProgressText('¡Análisis completado!');

      await new Promise(resolve => setTimeout(resolve, 300));
      setUploading(false);

    } catch (err) {
      setError(err.message);
      setUploading(false);
      setProgress(0);
    }
  };

  const handleDownload = () => {
    if (!annotatedBase64) return;
    const byteCharacters = atob(annotatedBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = annotatedFileName || 'tesis_revisada.docx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setFile(null);
    setResults(null);
    setAnnotatedBase64(null);
    setAnnotatedFileName('');
    setError(null);
    setProgress(0);
    setUploading(false);
    setActiveFilter('all');
    
    const container = document.getElementById('document-viewer-container');
    if (container) container.innerHTML = '';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const getFilteredResults = () => {
    if (!results) return [];
    switch (activeFilter) {
      case 'errors': return results.errors;
      case 'warnings': return results.warnings;
      case 'passed': return results.passed;
      default: return [...results.errors, ...results.warnings, ...results.passed];
    }
  };

  const groupByCategory = (items) => {
    return items.reduce((groups, item) => {
      const cat = item.category;
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(item);
      return groups;
    }, {});
  };

  // ===== UPLOAD PAGE =====
  if (!results && !uploading) {
    return (
      <div className="upload-page">
        <div className="upload-hero animate-fade-in">
          <h1>Revisa tu <span>Tesis</span> al instante</h1>
          <p>
            Sistema automatizado de verificación de formato según la Guía de Presentación 
            de Tesis 2.0 del Repositorio Institucional de la UNA Puno.
          </p>
        </div>

        <div
          id="dropzone"
          className={`dropzone animate-slide-up ${dragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <div className="dropzone-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className="dropzone-text">
            <h3>Arrastra tu tesis aquí</h3>
            <p>o haz clic para seleccionar el archivo</p>
            <div className="file-types">
              <span className="file-type-badge">.DOCX</span>
              <span className="file-type-badge">Word</span>
            </div>
          </div>
          <input
            id="file-input"
            type="file"
            accept=".docx"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>

        {error && (
          <div className="progress-container animate-fade-in" style={{ borderColor: 'var(--accent-red)' }}>
            <p style={{ color: 'var(--accent-red)', fontWeight: 600 }}>❌ {error}</p>
          </div>
        )}

        <div className="features-grid animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="feature-item">
            <span className="feature-icon">📏</span>
            <span className="feature-text">Márgenes y formato</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔤</span>
            <span className="feature-text">Fuentes y tamaños</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📑</span>
            <span className="feature-text">Estructura completa</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📝</span>
            <span className="feature-text">Resumen y Abstract</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">✏️</span>
            <span className="feature-text">Documento anotado</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⬇️</span>
            <span className="feature-text">Descarga revisado</span>
          </div>
        </div>
      </div>
    );
  }

  // ===== PROGRESS STATE =====
  if (uploading) {
    return (
      <div className="upload-page">
        <div className="progress-container animate-fade-in">
          <div className="progress-header">
            <div className="progress-spinner"></div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '15px' }}>Analizando tesis...</div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{file?.name}</div>
            </div>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="progress-status">{progressText}</div>
        </div>
      </div>
    );
  }

  // ===== RESULTS PAGE =====
  const scoreColor = getScoreColor(results.score);
  const circumference = 2 * Math.PI * 58;
  const strokeDashoffset = circumference - (results.score / 100) * circumference;
  const filteredResults = getFilteredResults();
  const grouped = groupByCategory(filteredResults);

  return (
    <div className="results-page animate-fade-in">
      {/* LEFT PANEL */}
      <div>
        {/* Score Card */}
        <div className="score-card">
          <div className="score-gauge">
            <div className="score-circle">
              <svg width="140" height="140">
                <circle className="score-circle-bg" cx="70" cy="70" r="58" />
                <circle
                  className="score-circle-fill"
                  cx="70" cy="70" r="58"
                  stroke={scoreColor}
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  style={{ filter: `drop-shadow(0 0 8px ${scoreColor}60)` }}
                />
              </svg>
              <span className="score-value" style={{ color: scoreColor }}>
                {results.score}
              </span>
            </div>
            <span className="score-label">Puntuación de formato</span>

            <div className="score-stats">
              <div className="stat-item">
                <span className="stat-value passed">{results.passedCount}</span>
                <span className="stat-label">Aprobados</span>
              </div>
              <div className="stat-item">
                <span className="stat-value errors">{results.errorCount}</span>
                <span className="stat-label">Errores</span>
              </div>
              <div className="stat-item">
                <span className="stat-value warnings">{results.warningCount}</span>
                <span className="stat-label">Avisos</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <button className="btn btn-success" onClick={handleDownload} style={{ flex: 1 }}>
            ⬇️ Descargar con observaciones
          </button>
          <button className="btn btn-new" onClick={handleReset}>
            🔄 Nueva
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="filter-tabs">
          <button
            className={`filter-tab ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            Todos <span className="count">{results.totalRules}</span>
          </button>
          <button
            className={`filter-tab ${activeFilter === 'errors' ? 'active' : ''}`}
            onClick={() => setActiveFilter('errors')}
          >
            ❌ Errores <span className="count">{results.errorCount}</span>
          </button>
          <button
            className={`filter-tab ${activeFilter === 'warnings' ? 'active' : ''}`}
            onClick={() => setActiveFilter('warnings')}
          >
            ⚠️ Avisos <span className="count">{results.warningCount}</span>
          </button>
          <button
            className={`filter-tab ${activeFilter === 'passed' ? 'active' : ''}`}
            onClick={() => setActiveFilter('passed')}
          >
            ✅ Aprobados <span className="count">{results.passedCount}</span>
          </button>
        </div>

        {/* Results List */}
        <div className="results-panel">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="category-group">
              <div className="category-header">
                {category === 'Márgenes' && '📏'}
                {category === 'Tipografía' && '🔤'}
                {category === 'Estructura' && '📑'}
                {category === 'Resumen' && '📝'}
                {category === 'Abstract' && '🌐'}
                {category === 'Espaciado' && '↕️'}
                {category === 'Formato de Párrafo' && '¶'}
                {' '}{category}
              </div>
              {items.map((item, idx) => (
                <div key={`${item.id}-${idx}`} className={`error-card ${item.status}`}>
                  <div className="error-card-header">
                    <div className={`error-card-icon ${item.status}`}>
                      {item.status === 'error' && '✕'}
                      {item.status === 'warning' && '!'}
                      {item.status === 'passed' && '✓'}
                    </div>
                    <div>
                      <div className="error-card-title">{item.rule}</div>
                      <div className="error-card-message">{item.message}</div>
                      {(item.expected || item.actual) && (
                        <div className="error-card-meta">
                          {item.expected && (
                            <span className="error-card-meta-item">
                              <strong>Esperado:</strong> {item.expected}
                            </span>
                          )}
                          {item.actual && (
                            <span className="error-card-meta-item">
                              <strong>Encontrado:</strong> {item.actual}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* RIGHT PANEL - Document Viewer */}
      <div className="viewer-container">
        <div className="viewer-toolbar">
          <div className="viewer-toolbar-left">
            <span style={{ fontSize: '18px' }}>📄</span>
            <span className="viewer-filename">{annotatedFileName || file?.name}</span>
          </div>
          <div className="viewer-toolbar-actions">
            <button className="btn btn-primary" onClick={handleDownload}>
              ⬇️ Descargar .docx revisado
            </button>
          </div>
        </div>
        <div className="viewer-body" id="document-viewer">
          {previewLoading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
              <div className="progress-spinner" style={{ marginBottom: '16px' }}></div>
              <p>Preparando vista previa del documento...</p>
            </div>
          )}
          <div id="document-viewer-container" style={{ 
            minHeight: '100%',
            backgroundColor: '#fff',
            display: previewLoading ? 'none' : 'block'
          }}></div>
        </div>
      </div>
    </div>
  );
}
