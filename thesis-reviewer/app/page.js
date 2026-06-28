'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { 
  Upload, FileText, CheckCircle, AlertCircle, XCircle, 
  RotateCcw, Download, Layout, Type, AlignLeft, 
  BookOpen, ChevronRight, GraduationCap, BarChart3,
  ArrowRight, ShieldCheck, Zap, Globe, File, Eye, X, ExternalLink, Cpu, Activity, TrendingUp, MousePointer2
} from 'lucide-react';
import BookViewer from './components/BookViewer';

export default function Home() {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [annotatedBase64, setAnnotatedBase64] = useState(null);
  const [annotatedFileName, setAnnotatedFileName] = useState('');
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [showPreview, setShowPreview] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard', 'table', 'preview'
  const [elapsedTime, setElapsedTime] = useState(0);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    let timer;
    if (uploading) {
      timer = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [uploading]);

  const getLoadingMessage = () => {
    if (elapsedTime < 3) return "Extrayendo contenido del documento...";
    if (elapsedTime < 7) return "Analizando estructura y configuración de página...";
    if (elapsedTime < 13) return "Auditando niveles de títulos y formato de párrafos...";
    if (elapsedTime < 18) return "Revisando tablas, figuras y ortografía...";
    if (elapsedTime < 26) return "Verificando observaciones con Inteligencia Artificial...";
    if (elapsedTime < 35) return "Filtrando falsos positivos y generando resumen...";
    return "Consolidando documento anotado. ¡Ya casi listo!...";
  };

  const getGroupedStats = () => {
    if (!results || !results.results) return [];
    
    const groupedData = [
      { name: 'Estructura y Capítulos', total: 0, passed: 0 },
      { name: 'Formato de Contenido', total: 0, passed: 0 },
      { name: 'Tablas y Figuras', total: 0, passed: 0 },
      { name: 'Redacción y Estilo', total: 0, passed: 0 }
    ];

    results.results.forEach(r => {
      const cat = (r.category || '').toLowerCase();
      // Ignorar categorías secundarias en las tarjetas (siguen saliendo en la tabla)
      if (cat.includes('ocr') || cat.includes('jurado') || cat.includes('anexo') || cat.includes('preliminar') || cat.includes('cuadro') || cat.includes('acrónimo') || cat.includes('portada')) return;

      let groupIndex = 1; // 1: Formato (por defecto)
      if (cat.includes('nivel') || cat.includes('jerarquía') || cat.includes('viñeta') || cat.includes('capítulo') || cat.includes('índice')) {
        groupIndex = 0;
      } else if (cat.includes('tabla') || cat.includes('figura')) {
        groupIndex = 2;
      } else if (cat.includes('estilo') || cat.includes('ortografía') || cat.includes('escritura') || cat.includes('redacción')) {
        groupIndex = 3;
      }

      groupedData[groupIndex].total++;
      if (r.status === 'passed' || r.ai_rejected === true) {
        groupedData[groupIndex].passed++;
      }
    });

    return groupedData.filter(g => g.total > 0).map(g => {
      const score = Math.round((g.passed / g.total) * 100);
      return { ...g, score, status: score >= 80 ? 'passed' : score >= 50 ? 'warning' : 'error' };
    });
  };

  const pdfUrl = "/guia.pdf";

  const uploadFile = async (fileToUpload) => {
    if (!fileToUpload) return;
    setUploading(true);
    setElapsedTime(0);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', fileToUpload);
      const response = await fetch('/api/upload', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Error al procesar');
      setResults(data.results);
      setAnnotatedBase64(data.annotatedBase64);
      setAnnotatedFileName(data.annotatedFileName);
      setUploading(false);
    } catch (err) {
      setError(err.message);
      setUploading(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      uploadFile(droppedFile);
    }
  }, []);

  const handleDownload = () => {
    if (!annotatedBase64) return;
    const byteCharacters = atob(annotatedBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) byteNumbers[i] = byteCharacters.charCodeAt(i);
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = annotatedFileName || 'tesis_auditada.docx';
    a.click();
  };

  if (!results && !uploading) {
    return (
      <main className="container-crypto animate-reveal" style={{ paddingTop: '6rem', paddingBottom: '6rem' }}>
        {/* HERO SECTION - PERFECTLY CENTERED */}
        <section style={{ textAlign: 'center', marginBottom: '8rem' }}>
          <div className="animate-float" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(69, 245, 229, 0.08)', padding: '0.7rem 1.75rem', borderRadius: '50px', marginBottom: '3.5rem', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
             <Activity size={18} className="text-accent" />
             <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#45F5E5', textTransform: 'uppercase', letterSpacing: '0.2em' }}>Auditoría Digital Sincronizada UNAP</span>
          </div>
          
          <h1 style={{ fontSize: '5.5rem', fontWeight: 900, letterSpacing: '-0.06em', lineHeight: '1', marginBottom: '2.5rem' }}>
             Auditoría de <span className="text-gradient">Tesis.</span><br />
             <span style={{ fontSize: '3.5rem', opacity: 0.9 }}>Pregrado & Posgrado.</span>
          </h1>
          
          <p style={{ fontSize: '1.2rem', color: '#94A3B8', maxWidth: '850px', margin: '0 auto 5rem', fontWeight: 500, lineHeight: '1.8', opacity: 0.8 }}>
             Validación técnica instantánea para Pregrado, Posgrado y Segundas Especialidades. <br />
             Optimizado para el Repositorio Institucional UNAP.
          </p>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem' }}>
             <button className="btn-crypto animate-glow" style={{ padding: '1.4rem 4rem', fontSize: '1.1rem' }} onClick={() => document.getElementById('file-input').click()}>
                Subir Tesis <Upload size={24} />
             </button>
             <button className="btn-crypto" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', padding: '1.4rem 4rem', fontSize: '1.1rem' }} onClick={() => setShowPreview(true)}>
                Base Guía que se Auditará
             </button>
          </div>
          {/* Input oculto necesario para que funcione el botón de arriba */}
          <input id="file-input" type="file" accept=".docx,.pdf" className="hidden-input" onChange={(e) => uploadFile(e.target.files[0])} />
        </section>

        {/* ACADEMIC LEVELS - GRID */}
        <section style={{ marginBottom: '8rem' }}>
           <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
              {[
                { title: "Pregrado", sub: "Tesis & Suficiencia", status: "Activo", color: "#45F5E5" },
                { title: "Posgrado", sub: "Maestría & Doctorado", status: "Sincronizado", color: "#9D50FF" },
                { title: "Especialidades", sub: "Segunda Especialidad", status: "Activo", color: "#3772FF" }
              ].map((lvl, i) => (
                <div key={i} className="academic-level-card" style={{ padding: '2rem' }}>
                   <div className="flex flex-col gap-1">
                      <span style={{ fontSize: '1.3rem', fontWeight: 900 }}>{lvl.title}</span>
                      <span style={{ fontSize: '0.8rem', color: '#64748B', fontWeight: 700 }}>{lvl.sub}</span>
                   </div>
                   <span className="status-tag" style={{ color: lvl.color, borderColor: `${lvl.color}40`, background: `${lvl.color}10`, padding: '0.5rem 1.2rem', borderRadius: '50px', fontSize: '0.7rem', fontWeight: 900, border: '1px solid' }}>{lvl.status}</span>
                </div>
              ))}
           </div>
        </section>

        {showPreview && (
          <BookViewer onClose={() => setShowPreview(false)} pdfUrl={pdfUrl} />
        )}

        {error && (
          <div className="error-banner animate-reveal" style={{ marginTop: '2rem', background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.2)', padding: '1.5rem', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '1rem', color: '#FF4D4D' }}>
             <XCircle size={24} />
             <div style={{ textAlign: 'left' }}>
                <div style={{ fontWeight: 900, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>Error de Procesamiento</div>
                <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>{error}</div>
             </div>
             <button onClick={() => setError(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#FF4D4D', cursor: 'pointer' }}><X size={20}/></button>
          </div>
        )}
      </main>
    );
  }

  if (uploading) {
    return (
      <main className="container-crypto flex items-center justify-center py-40 animate-reveal" style={{ minHeight: '100vh' }}>
         <div className="card-elite max-w-lg w-full text-center py-16 px-10">
            <div className="w-32 h-32 border-4 border-white/5 border-t-accent rounded-full animate-spin mx-auto mb-10 shadow-[0_0_60px_rgba(69,245,229,0.3)] flex items-center justify-center">
               <span style={{ fontSize: '1.5rem', fontWeight: 900, color: 'white', transform: 'rotate(-360deg)', display: 'block', animation: 'spin 1s linear infinite reverse' }}>
                 {elapsedTime}s
               </span>
            </div>
            <h2 className="text-3xl font-black tracking-tighter mb-4 text-white">Analizando Tesis</h2>
            
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginBottom: '1.5rem' }}>
              <div style={{ fontSize: '0.9rem', color: '#94A3B8', fontWeight: 600, minHeight: '1.5rem' }}>
                 {getLoadingMessage()}
              </div>
            </div>

            <div className="flex justify-center gap-3">
               <div className="ocr-pulse"></div>
               <span className="text-xs font-bold text-accent uppercase tracking-wider">Por favor, no cierre esta ventana</span>
            </div>
         </div>
       </main>
    );
  }

  if (results) {
    return (
    <main className="animate-reveal" style={{ minHeight: '100vh', padding: '2rem 0' }}>
       <div className="tech-grid"></div>
       
       <div className="container-crypto">
          {/* HEADER PANEL */}
          <div className="header-panel flex-between">
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <div>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontSize: '0.65rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.3em', marginBottom: '0.4rem' }}>
                      <Activity size={14} /> Auditoría Finalizada
                   </div>
                   <h2 style={{ fontSize: '1.8rem', fontWeight: 900, letterSpacing: '-0.04em' }}>
                      {file?.name.length > 40 ? file?.name.substring(0, 40) + '...' : file?.name}
                      <span style={{ marginLeft: '1rem', padding: '0.2rem 0.6rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.65rem', color: '#64748B', fontWeight: 800, border: '1px solid rgba(255,255,255,0.05)' }}>DOCX</span>
                       {results.engine && (
                         <span style={{ 
                           marginLeft: '0.5rem', 
                           padding: '0.2rem 0.6rem', 
                           background: results.engine === 'python-hifi' ? 'rgba(69, 245, 229, 0.1)' : 'rgba(255, 193, 7, 0.1)', 
                           borderRadius: '6px', 
                           fontSize: '0.6rem', 
                           color: results.engine === 'python-hifi' ? '#45F5E5' : '#FFC107', 
                           fontWeight: 900, 
                           border: `1px solid ${results.engine === 'python-hifi' ? 'rgba(69, 245, 229, 0.2)' : 'rgba(255, 193, 7, 0.2)'}`,
                           textTransform: 'uppercase',
                           letterSpacing: '0.1em'
                         }}>
                           {results.engine === 'python-hifi' ? 'Motor Alta Fidelidad (Python)' : 'Motor de Respaldo (JS)'}
                         </span>
                       )}
                   </h2>
                </div>
             </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ display: 'flex', background: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <button onClick={() => setViewMode('dashboard')} style={{ padding: '0.6rem 1.2rem', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 800, transition: '0.3s', background: viewMode === 'dashboard' ? 'var(--accent)' : 'transparent', color: viewMode === 'dashboard' ? 'black' : '#94A3B8', border: 'none', cursor: 'pointer' }}>
                    <BarChart3 size={16} style={{ marginBottom: '-3px', marginRight: '6px' }} /> Dashboard
                  </button>
                  <button onClick={() => setViewMode('table')} style={{ padding: '0.6rem 1.2rem', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 800, transition: '0.3s', background: viewMode === 'table' ? 'var(--accent)' : 'transparent', color: viewMode === 'table' ? 'black' : '#94A3B8', border: 'none', cursor: 'pointer' }}>
                    <Layout size={16} style={{ marginBottom: '-3px', marginRight: '6px' }} /> Tabla
                  </button>
                  <button onClick={() => setViewMode('preview')} style={{ padding: '0.6rem 1.2rem', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 800, transition: '0.3s', background: viewMode === 'preview' ? 'var(--accent)' : 'transparent', color: viewMode === 'preview' ? 'black' : '#94A3B8', border: 'none', cursor: 'pointer' }}>
                    <Eye size={16} style={{ marginBottom: '-3px', marginRight: '6px' }} /> Preview
                  </button>
                </div>
                <button onClick={() => setResults(null)} className="btn-crypto" style={{ background: 'transparent', border: '1px solid rgba(255, 255, 255, 0.2)', color: 'white' }}>
                    <RotateCcw size={20} /> Nueva Auditoría
                </button>
                <button onClick={handleDownload} className="btn-crypto">
                    <Download size={20} /> Descargar Reporte
                </button>
              </div>
          </div>

          <div className="grid-audit">
             
             {/* SIDEBAR */}
             <aside>
                <div className="sidebar-summary shadow-2xl">
                   <div className="score-circle-wrap" style={{ position: 'relative', margin: '0 auto 2.5rem', width: '220px', height: '220px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                      <div style={{ position: 'absolute', width: '100%', height: '100%', borderRadius: '50%', background: results.score >= 80 ? 'transparent' : results.score >= 60 ? 'var(--warning)' : 'var(--error)', filter: 'blur(40px)', opacity: 0.15 }}></div>
                      <svg width="220" height="220" viewBox="0 0 220 220" style={{ transform: 'rotate(-90deg)', position: 'absolute', zIndex: 5 }}>
                         <circle cx="110" cy="110" r="100" stroke="rgba(255,255,255,0.05)" strokeWidth="12" fill="transparent" />
                         <circle cx="110" cy="110" r="100" stroke={results.score >= 80 ? 'var(--text-main)' : results.score >= 60 ? 'var(--warning)' : 'var(--error)'} strokeWidth="12" fill="transparent" strokeDasharray="628.3" strokeDashoffset={628.3 * (1 - results.score / 100)} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)' }} />
                      </svg>
                      <div className="score-text" style={{ position: 'absolute', textAlign: 'center', zIndex: 10 }}>
                         <div style={{ fontSize: '5rem', fontWeight: 900, lineHeight: '1', color: 'white', textShadow: `0 0 20px ${results.score >= 80 ? 'transparent' : results.score >= 60 ? 'var(--warning)' : 'var(--error)'}60` }}>{results.score}</div>
                         <div style={{ fontSize: '0.75rem', fontWeight: 900, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.25em', marginTop: '0.5rem' }}>Puntaje Global</div>
                      </div>
                   </div>

                   <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                      <span className={`badge ${results.score >= 80 ? '' : results.score >= 60 ? 'badge-warning' : 'badge-error'}`}>
                         {results.score >= 80 ? 'Excelente' : results.score >= 60 ? 'Aceptable' : 'Estado Crítico'}
                      </span>
                   </div>

                   <div className="stats-list">
                      {[
                        { label: "Validaciones OK", val: results.passedCount, color: "var(--text-main)", bg: "rgba(255, 255, 255, 0.05)", icon: <CheckCircle size={16}/> },
                        { label: "Errores Críticos", val: results.errorCount, color: "var(--error)", bg: "rgba(255, 77, 77, 0.05)", icon: <XCircle size={16}/> },
                        { label: "Advertencias", val: results.warningCount, color: "var(--warning)", bg: "rgba(255, 193, 7, 0.05)", icon: <AlertCircle size={16}/> }
                      ].map((s, i) => (
                        <div key={i} className="stat-row">
                           <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                              <div style={{ color: s.color, background: s.bg, width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyCenter: 'center' }}>{s.icon}</div>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94A3B8' }}>{s.label}</span>
                           </div>
                           <span style={{ fontSize: '1.25rem', fontWeight: 900, color: s.color }}>{s.val}</span>
                        </div>
                      ))}
                   </div>
                   
                   <div style={{ marginTop: '2.5rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.05)', fontSize: '0.6rem', color: '#475569', textAlign: 'center', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                      <ShieldCheck size={14} style={{ marginBottom: '0.5rem', display: 'block', margin: '0 auto 0.5rem' }} />
                      Auditoría Protegida UNAP
                   </div>
                </div>
             </aside>

              {/* MAIN CONTENT AREA */}
              <div className="main-audit-content">
                {viewMode === 'dashboard' && (
                  <div className="animate-reveal">
                    <div style={{ marginBottom: '2rem' }}>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 900, marginBottom: '0.5rem' }}>Estado por Categorías</h3>
                      <p style={{ color: '#94A3B8', fontSize: '0.8rem' }}>Análisis detallado del cumplimiento normativo institucional.</p>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
                      {getGroupedStats().map((cat, i) => (
                        <div key={i} className="category-card">
                          <div className="flex-between" style={{ marginBottom: '1rem' }}>
                            <span style={{ fontWeight: 800, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{cat.name}</span>
                            <span style={{ fontWeight: 900, fontSize: '1.1rem', color: cat.score >= 50 ? 'var(--warning)' : 'var(--error)' }}>{cat.score}%</span>
                          </div>
                          <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ 
                              width: `${cat.score}%`, 
                              background: cat.score >= 50 ? 'var(--warning)' : 'var(--error)',
                              boxShadow: `0 0 10px ${cat.score >= 80 ? 'var(--success)' : cat.score >= 50 ? 'var(--warning)' : 'var(--error)'}40`
                            }}></div>
                          </div>
                          <div className="flex-between" style={{ marginTop: '1rem', fontSize: '0.65rem', color: '#64748B', fontWeight: 700 }}>
                            <span>{cat.passed} de {cat.total} pasados</span>
                            <span style={{ textTransform: 'uppercase' }}>{cat.score >= 80 ? 'Óptimo' : cat.score >= 50 ? 'Regular' : 'Crítico'}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="card-elite" style={{ marginTop: '2.5rem', padding: '2rem' }}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                          <div style={{ background: 'rgba(69, 245, 229, 0.1)', padding: '1.5rem', borderRadius: '20px' }}>
                             <TrendingUp size={32} className="text-accent" />
                          </div>
                          <div>
                             <h4 style={{ fontSize: '1.1rem', fontWeight: 900, marginBottom: '0.3rem' }}>Recomendación del Auditor Neural</h4>
                             <p style={{ color: '#94A3B8', fontSize: '0.85rem', lineHeight: '1.6' }}>
                                {results.score >= 80 
                                  ? "Tu tesis cumple con la mayoría de los estándares institucionales. Revisa los detalles menores antes de la entrega final."
                                  : "Se detectaron inconsistencias críticas en el formato. Te recomendamos usar la función de descarga para ver las anotaciones en Word y corregir los puntos señalados."}
                             </p>
                          </div>
                       </div>
                    </div>
                  </div>
                )}

                {viewMode === 'table' && (
                  <div className="animate-reveal">
                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
                      {['all', 'error', 'warning', 'passed'].map((f) => (
                        <button 
                          key={f}
                          onClick={() => setActiveFilter(f)}
                          style={{ 
                            padding: '0.7rem 1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)',
                            fontSize: '0.65rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em',
                            cursor: 'pointer', transition: '0.3s',
                            background: activeFilter === f ? 'white' : 'rgba(255,255,255,0.03)',
                            color: activeFilter === f ? 'black' : '#94A3B8'
                          }}
                        >
                          {f === 'all' ? 'Ver Todos' : f === 'error' ? 'Críticos' : f === 'warning' ? 'Alertas' : 'Correctos'}
                        </button>
                      ))}
                    </div>

                    <div className="audit-table-container">
                      <table className="audit-table">
                          <thead>
                            <tr>
                                <th style={{ width: '50px', textAlign: 'center' }}>#</th>
                                <th>Área y Regla</th>
                                <th>Hallado</th>
                                <th>Requerido</th>
                                <th style={{ textAlign: 'center' }}>Pág</th>
                                <th style={{ textAlign: 'right' }}>Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {results.results
                              .filter(item => activeFilter === 'all' || item.status === activeFilter)
                              .map((item, idx) => (
                                <React.Fragment key={idx}>
                                <tr key={idx}>
                                  <td style={{ textAlign: 'center', color: '#475569', fontWeight: 800 }}>{idx + 1}</td>
                                  <td>
                                      <div style={{ fontWeight: 800, marginBottom: '0.25rem', fontSize: '0.9rem' }}>{item.rule}</div>
                                      <div style={{ fontSize: '0.6rem', color: '#64748B', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: item.status === 'error' ? 'var(--error)' : item.status === 'warning' ? 'var(--warning)' : 'transparent' }}></div>
                                        {item.category || 'REGLA'}
                                      </div>
                                  </td>
                                  <td style={{ fontWeight: 700, fontSize: '0.8rem', color: 'var(--text-main)' }}>{item.actual || '—'}</td>
                                  <td style={{ color: '#94A3B8', fontSize: '0.8rem' }}>{item.expected || '—'}</td>
                                  <td style={{ textAlign: 'center' }}>
                                      {item.paragraphIndex !== undefined ? (
                                        <span style={{ padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', fontSize: '0.7rem', color: '#64748B', fontWeight: 800 }}>
                                          {Math.floor(item.paragraphIndex / 20) + 1}
                                        </span>
                                      ) : '—'}
                                  </td>
                                  <td style={{ textAlign: 'right' }}>
                                      <span className={`badge ${item.status === 'error' ? 'badge-error' : item.status === 'warning' ? 'badge-warning' : ''}`}>
                                        {item.status}
                                      </span>
                                  </td>
                                </tr>
                                <tr>
                                  <td colSpan="6" style={{ padding: '0', border: 'none' }}>
                                    <div
                                      onClick={() => setExpandedRow(expandedRow === `${idx}` ? null : `${idx}`)}
                                      style={{
                                        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem',
                                        padding: '0.4rem 1rem', fontSize: '0.65rem', fontWeight: 700,
                                        color: '#64748B', borderTop: '1px solid rgba(255,255,255,0.03)',
                                        userSelect: 'none',
                                      }}
                                    >
                                      <ChevronRight size={12} style={{
                                        transition: 'transform 0.2s',
                                        transform: expandedRow === `${idx}` ? 'rotate(90deg)' : 'rotate(0deg)',
                                      }} />
                                      {expandedRow === `${idx}` ? 'Ocultar descripción' : 'Ver descripción'}
                                    </div>
                                    {expandedRow === `${idx}` && (
                                      <div style={{
                                        padding: '0.5rem 1rem 0.8rem 1rem', fontSize: '0.75rem',
                                        color: '#94A3B8', lineHeight: '1.6', borderTop: '1px solid rgba(255,255,255,0.03)',
                                      }}>
                                        <strong>Área:</strong> {item.category}<br/>
                                        <strong>Hallado:</strong> {item.actual || '—'}<br/>
                                        <strong>Requerido:</strong> {item.expected || '—'}<br/>
                                        <strong>Descripción:</strong> {item.message}
                                      </div>
                                    )}
                                  </td>
                                </tr>
                                </React.Fragment>
                            ))}
                          </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {viewMode === 'preview' && (
                  <div className="animate-reveal">
                    <div style={{ marginBottom: '2rem' }}>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 900, marginBottom: '0.5rem' }}>Visor de Hallazgos</h3>
                      <p style={{ color: '#94A3B8', fontSize: '0.8rem' }}>Explora el contexto real de cada observación detectada.</p>
                    </div>

                    <div className="preview-pane no-scrollbar">
                      {results.results
                        .filter(r => r.status !== 'passed' && r.paragraphText)
                        .map((item, idx) => (
                          <div key={idx} className={`preview-item status-${item.status}`}>
                            <div className="flex-between" style={{ marginBottom: '1rem' }}>
                               <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                                  <div style={{ padding: '0.4rem 0.8rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '0.6rem', fontWeight: 900, color: 'var(--accent)' }}>
                                     OBS #{(idx + 1).toString().padStart(2, '0')}
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 800, fontSize: '0.85rem' }}>{item.rule}</div>
                                    <div style={{ fontSize: '0.6rem', color: '#64748B', fontWeight: 700, marginTop: '0.15rem' }}>{item.category}</div>
                                  </div>
                               </div>
                               <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 800 }}>PÁGINA {Math.floor(item.paragraphIndex / 20) + 1}</span>
                            </div>

                            <div className="highlight-box" style={{ marginBottom: '0.75rem' }}>
                               <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#475569', marginBottom: '0.5rem', fontWeight: 800 }}>Fragmento detectado:</div>
                               "{item.paragraphText}"
                            </div>

                            <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                               <div style={{ fontSize: '0.7rem', color: 'var(--error)', fontWeight: 700 }}>HALLADO: {item.actual}</div>
                               <div style={{ fontSize: '0.7rem', color: 'white', opacity: 0.5, fontWeight: 700 }}>REQUERIDO: {item.expected}</div>
                            </div>

                            <div
                              onClick={() => setExpandedRow(expandedRow === `preview-${idx}` ? null : `preview-${idx}`)}
                              style={{
                                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem',
                                padding: '0.4rem 0', fontSize: '0.65rem', fontWeight: 700,
                                color: '#64748B', userSelect: 'none',
                              }}
                            >
                              <ChevronRight size={12} style={{
                                transition: 'transform 0.2s',
                                transform: expandedRow === `preview-${idx}` ? 'rotate(90deg)' : 'rotate(0deg)',
                              }} />
                              {expandedRow === `preview-${idx}` ? 'Ocultar descripción' : 'Ver descripción'}
                            </div>
                            {expandedRow === `preview-${idx}` && (
                              <div style={{
                                marginTop: '0.5rem', padding: '0.75rem', borderRadius: '8px',
                                background: 'rgba(255,255,255,0.03)', fontSize: '0.75rem',
                                color: '#94A3B8', lineHeight: '1.6',
                              }}>
                                {item.message}
                              </div>
                            )}
                          </div>
                      ))}
                      {results.results.filter(r => r.status !== 'passed' && r.paragraphText).length === 0 && (
                        <div style={{ textAlign: 'center', padding: '10rem 0' }}>
                           <ShieldCheck size={64} className="text-accent" style={{ opacity: 0.1, margin: '0 auto 2rem' }} />
                           <h4 style={{ fontWeight: 900, opacity: 0.5 }}>¡Sin observaciones críticas!</h4>
                           <p style={{ fontSize: '0.8rem', opacity: 0.3 }}>El documento goza de excelente salud técnica.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="flex-between" style={{ marginTop: '1.5rem', padding: '0 1rem', fontSize: '0.65rem', fontWeight: 800, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                   <div>Total Validaciones: {results.totalRules || results.results.length}</div>
                   <div>v2.0 Sincronizado | © 2025 VRI UNAP</div>
                </div>
              </div>
          </div>
       </div>
    </main>
  );
}
}
