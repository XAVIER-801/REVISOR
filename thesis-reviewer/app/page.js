'use client';

import { useState, useCallback } from 'react';
import { 
  Upload, FileText, CheckCircle, AlertCircle, XCircle, 
  RotateCcw, Download, Layout, Type, AlignLeft, 
  BookOpen, ChevronRight, GraduationCap, BarChart3
} from 'lucide-react';

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
    if (droppedFile && (droppedFile.name.toLowerCase().endsWith('.docx') || droppedFile.name.toLowerCase().endsWith('.pdf'))) {
      setFile(droppedFile);
      uploadFile(droppedFile);
    } else {
      setError('Solo se aceptan archivos .docx (Word) o .pdf');
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
      setProgressText('Verificando reglas de formato UNAP 2025...');

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error al procesar el documento');
      }

      setResults(data.results);
      setAnnotatedBase64(data.annotatedBase64);
      setAnnotatedFileName(data.annotatedFileName);

      setProgress(100);
      setProgressText('¡Análisis completado!');

      await new Promise(resolve => setTimeout(resolve, 500));
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
    const isPdf = annotatedFileName.toLowerCase().endsWith('.pdf');
    const blob = new Blob([byteArray], { type: isPdf ? 'application/pdf' : 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = annotatedFileName || (isPdf ? 'tesis_revisada.pdf' : 'tesis_revisada.docx');
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
  };

  const getFilteredResults = () => {
    if (!results) return [];
    let items = results.results || [];
    if (activeFilter === 'errors') return items.filter(r => r.status === 'error');
    if (activeFilter === 'warnings') return items.filter(r => r.status === 'warning');
    if (activeFilter === 'passed') return items.filter(r => r.status === 'passed');
    return items;
  };

  const groupByCategory = (items) => {
    return items.reduce((groups, item) => {
      const cat = item.category;
      if (!groups[cat]) groups[groups.findIndex?.(g => g.name === cat) || -1] ? null : groups[cat] = [];
      groups[cat].push(item);
      return groups;
    }, {});
  };

  // ===== RENDER: UPLOAD =====
  if (!results && !uploading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-6 sm:p-24">
        <div className="w-full max-w-4xl space-y-12 text-center">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-emerald-400 text-sm font-semibold mb-4">
              <GraduationCap size={16} />
              UNAP VRI-SCANNER 2.0
            </div>
            <h1 className="text-5xl sm:text-7xl font-bold tracking-tight">
              Valida tu <span className="text-emerald-500">Tesis</span><br />
              en segundos.
            </h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Optimizado para la nueva <span className="text-emerald-400 font-semibold">Guía de Formato 2025</span>. 
              Soporte completo para Microsoft Word y PDF.
            </p>
          </div>

          <div
            className={`glass p-12 cursor-pointer border-2 border-dashed transition-all duration-300 relative overflow-hidden group
              ${dragOver ? 'border-emerald-500 bg-emerald-500/10 scale-[1.02]' : 'border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800/30'}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
          >
            <div className="relative z-10 space-y-6">
              <div className="w-20 h-20 bg-emerald-500/10 rounded-2xl flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                <Upload className="text-emerald-500" size={40} />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold text-white">Sube tu documento</h3>
                <p className="text-slate-400">Arrastra y suelta o haz clic para explorar</p>
              </div>
              <div className="flex justify-center gap-3">
                <span className="category-pill bg-slate-800 text-emerald-400 border border-emerald-500/30">.DOCX</span>
                <span className="category-pill bg-slate-800 text-emerald-400 border border-emerald-500/30">.PDF</span>
              </div>
            </div>
            <input id="file-input" type="file" accept=".docx,.pdf" onChange={handleFileSelect} className="hidden" />
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3 justify-center animate-shake">
              <XCircle size={20} />
              <span className="font-semibold">{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-slate-500">
            {[
              { icon: Layout, text: "Márgenes 3.5cm" },
              { icon: Type, text: "TNR 12 Ptos" },
              { icon: BookOpen, text: "Estructura" },
              { icon: AlignLeft, text: "APA 7 / Vanc" }
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 justify-center">
                <item.icon size={18} className="text-slate-700" />
                <span className="text-sm font-medium">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  // ===== RENDER: PROCESSING =====
  if (uploading) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md space-y-8 text-center glass p-8">
          <div className="relative w-24 h-24 mx-auto">
            <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-emerald-500 rounded-full border-t-transparent animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <FileText className="text-emerald-500" size={32} />
            </div>
          </div>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold">Escaneando Tesis...</h2>
            <p className="text-slate-400 font-medium">{progressText}</p>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // ===== RENDER: RESULTS =====
  const filtered = getFilteredResults();
  const grouped = groupByCategory(filtered);

  return (
    <main className="min-h-screen p-6 sm:p-12 lg:p-24 bg-slate-950">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header Results */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold">Reporte de Validación</h1>
            <p className="text-slate-400 flex items-center gap-2">
              <FileText size={16} /> {file?.name}
            </p>
          </div>
          <div className="flex gap-4">
            <button onClick={handleDownload} className="btn-primary flex items-center gap-2">
              <Download size={20} /> Descargar Revisado
            </button>
            <button onClick={handleReset} className="p-3 rounded-xl border border-slate-700 text-slate-400 hover:bg-slate-800 transition-colors">
              <RotateCcw size={20} />
            </button>
          </div>
        </div>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-4 glass p-8 flex flex-col items-center justify-center space-y-6">
            <div className="score-radial" style={{ '--score': results.score }}>
              <div className="score-content">
                <span className="score-value">{results.score}</span>
                <span className="score-label">Puntos</span>
              </div>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-bold">Puntaje de Formato</h3>
              <p className="text-slate-400 text-sm">Basado en la Guía de Tesis 2025</p>
            </div>
          </div>

          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              { label: "Aprobados", val: results.passedCount, icon: CheckCircle, color: "text-emerald-400", bg: "bg-emerald-500/10" },
              { label: "Errores Críticos", val: results.errorCount, icon: XCircle, color: "text-red-400", bg: "bg-red-500/10" },
              { label: "Advertencias", val: results.warningCount, icon: AlertCircle, color: "text-amber-400", bg: "bg-amber-500/10" }
            ].map((stat, i) => (
              <div key={i} className="glass p-6 space-y-4">
                <div className={`w-12 h-12 ${stat.bg} rounded-xl flex items-center justify-center ${stat.color}`}>
                  <stat.icon size={24} />
                </div>
                <div>
                  <div className="text-3xl font-bold">{stat.val}</div>
                  <div className="text-slate-400 text-sm font-medium">{stat.label}</div>
                </div>
              </div>
            ))}
            <div className="sm:col-span-3 glass p-6 flex items-center justify-between">
               <div className="flex items-center gap-4">
                 <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400">
                   <BarChart3 size={24} />
                 </div>
                 <div>
                   <div className="text-sm text-slate-400">Total de Reglas Analizadas</div>
                   <div className="text-xl font-bold">{results.totalRules} criterios verificados</div>
                 </div>
               </div>
               <ChevronRight className="text-slate-600" />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          {[
            { id: 'all', label: 'Todas las Reglas' },
            { id: 'errors', label: 'Errores Críticos' },
            { id: 'warnings', label: 'Advertencias' },
            { id: 'passed', label: 'Aprobados' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveFilter(tab.id)}
              className={`px-6 py-2.5 rounded-xl font-semibold transition-all duration-300 border
                ${activeFilter === tab.id 
                  ? 'bg-emerald-500 text-white border-emerald-400 shadow-lg shadow-emerald-500/20' 
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Detailed Results */}
        <div className="space-y-12">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="space-y-6">
              <h2 className="text-xl font-bold flex items-center gap-3 text-slate-200">
                <span className="w-1.5 h-6 bg-emerald-500 rounded-full"></span>
                {category}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {items.map((item, idx) => (
                  <div key={idx} className={`glass p-6 card-result status-${item.status}`}>
                    <div className="flex gap-4">
                      <div className={`mt-1 shrink-0 ${
                        item.status === 'passed' ? 'text-emerald-400' : 
                        item.status === 'error' ? 'text-red-400' : 'text-amber-400'
                      }`}>
                        {item.status === 'passed' ? <CheckCircle size={20} /> : 
                         item.status === 'error' ? <XCircle size={20} /> : <AlertCircle size={20} />}
                      </div>
                      <div className="space-y-3 w-full">
                        <div className="flex justify-between items-start">
                          <h4 className="font-bold text-white leading-tight">{item.rule}</h4>
                          {item.page && item.page > 0 && (
                            <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-400">PÁG. {item.page}</span>
                          )}
                        </div>
                        <p className="text-slate-400 text-sm leading-relaxed">{item.message}</p>
                        
                        {(item.expected || item.actual) && (
                          <div className="pt-3 flex gap-4 border-t border-slate-800/50">
                            {item.expected && (
                              <div className="space-y-0.5">
                                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Esperado</div>
                                <div className="text-xs text-emerald-400 font-semibold">{item.expected}</div>
                              </div>
                            )}
                            {item.actual && (
                              <div className="space-y-0.5">
                                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Encontrado</div>
                                <div className="text-xs text-red-400 font-semibold">{item.actual}</div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
