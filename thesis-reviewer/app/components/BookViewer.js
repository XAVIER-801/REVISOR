'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  ChevronLeft, ChevronRight, X, ExternalLink, Loader2, BookOpen, Book, ZoomIn, ZoomOut
} from 'lucide-react';

export default function BookViewer({ onClose, pdfUrl }) {
  const [pdf, setPdf] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isSinglePage, setIsSinglePage] = useState(false);
  const [zoomPercent, setZoomPercent] = useState(100);
  
  const canvasLeftRef = useRef(null);
  const canvasRightRef = useRef(null);

  // Cargar PDF.js desde CDN e inicializar el PDF
  useEffect(() => {
    const scriptId = 'pdfjs-cdn-script';
    let script = document.getElementById(scriptId);

    const loadAndInitPDF = () => {
      if (!window.pdfjsLib) return;
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

      window.pdfjsLib.getDocument(pdfUrl).promise.then(
        (loadedPdf) => {
          setPdf(loadedPdf);
          setTotalPages(loadedPdf.numPages);
          setLoading(false);
        },
        (error) => {
          console.error("Error al cargar el PDF:", error);
          setLoading(false);
        }
      );
    };

    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
      script.onload = loadAndInitPDF;
      document.body.appendChild(script);
    } else {
      if (window.pdfjsLib) {
        loadAndInitPDF();
      } else {
        script.onload = loadAndInitPDF;
      }
    }
  }, [pdfUrl]);

  // Renderizar las páginas izquierda y derecha cuando cambie la página o se cargue el PDF
  useEffect(() => {
    if (!pdf) return;

    const renderPageToCanvas = (pageNum, canvasRef) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      
      // Limpiar canvas anterior
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (pageNum > totalPages || pageNum < 1) {
        // Dibujar página en blanco si está fuera del rango
        canvas.width = 400;
        canvas.height = 560;
        ctx.fillStyle = '#0A0D10';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Texto indicador de fin de documento
        ctx.fillStyle = '#475569';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Fin de la Guía Oficial', canvas.width / 2, canvas.height / 2);
        return;
      }

      pdf.getPage(pageNum).then((page) => {
        // Escala adaptada de 2.0 para una excelente definición del texto
        const viewport = page.getViewport({ scale: 2.0 });
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: ctx,
          viewport: viewport,
        };
        page.render(renderContext);
      });
    };

    renderPageToCanvas(pageNumber, canvasLeftRef);
    if (!isSinglePage) {
      renderPageToCanvas(pageNumber + 1, canvasRightRef);
    }

  }, [pdf, pageNumber, totalPages, isSinglePage]);

  const nextPage = () => {
    if (isSinglePage) {
      if (pageNumber + 1 <= totalPages) {
        setPageNumber(pageNumber + 1);
      }
    } else {
      if (pageNumber + 2 <= totalPages) {
        setPageNumber(pageNumber + 2);
      }
    }
  };

  const prevPage = () => {
    if (isSinglePage) {
      if (pageNumber - 1 >= 1) {
        setPageNumber(pageNumber - 1);
      }
    } else {
      if (pageNumber - 2 >= 1) {
        setPageNumber(pageNumber - 2);
      }
    }
  };

  const zoomIn = () => {
    setZoomPercent(prev => Math.min(200, prev + 25));
  };

  const zoomOut = () => {
    setZoomPercent(prev => Math.max(100, prev - 25));
  };

  const getPageIndicatorText = () => {
    if (loading) return '';
    if (isSinglePage) {
      return `Página ${pageNumber} de ${totalPages}`;
    } else {
      return `Páginas ${pageNumber} - ${Math.min(pageNumber + 1, totalPages)} de ${totalPages}`;
    }
  };

  const jumpToPage = (targetPage) => {
    // Asegurar que salte a un número de página impar (inicio de par de hojas)
    const normalizedPage = targetPage % 2 === 0 ? targetPage - 1 : targetPage;
    setPageNumber(Math.max(1, Math.min(normalizedPage, totalPages)));
  };

  return (
    <div className="modal-overlay animate-reveal" onClick={onClose} style={{ zIndex: 3000 }}>
      <div className="modal-content card-elite book-modal-container" onClick={e => e.stopPropagation()}>
        
        {/* CABECERA */}
        <div className="book-modal-header">
          <div className="flex items-center gap-4">
            <div className="ocr-pulse"></div>
            <h3 className="font-black text-sm uppercase tracking-widest text-slate-300">Base Guía de Tesis Sincronizada</h3>
          </div>
          
          <div className="flex items-center gap-4">
            <a href={pdfUrl} target="_blank" className="nav-link flex items-center gap-1 btn-pdf-link">
              <ExternalLink size={14} /> Abrir PDF Original
            </a>
            <button onClick={onClose} className="p-2 text-slate-500 hover:text-white transition-all">
              <X size={28} />
            </button>
          </div>
        </div>

        {/* VISOR DE HOJAS CONSECUTIVAS */}
        <div className="book-viewport">
          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 size={48} className="text-accent animate-spin" />
              <p className="text-slate-400 font-bold text-sm">Cargando guía oficial en formato libro...</p>
            </div>
          ) : (
            <div 
              className="book-container-3d"
              style={{ 
                width: `${zoomPercent}%`, 
                height: `${zoomPercent}%`,
                maxWidth: zoomPercent > 100 ? 'none' : '1500px',
                transition: 'width 0.2s ease, height 0.2s ease'
              }}
            >
              {/* Página Izquierda (o Página Única) */}
              <div className={`book-page ${isSinglePage ? 'book-page-single' : 'book-page-left-side'}`}>
                <canvas ref={canvasLeftRef} className="pdf-canvas" />
                <div className="page-corner-fold-left"></div>
              </div>

              {/* Lomo Central del Libro (solo en vista doble) */}
              {!isSinglePage && <div className="book-spine"></div>}

              {/* Página Derecha (solo en vista doble) */}
              {!isSinglePage && (
                <div className="book-page book-page-right-side">
                  <canvas ref={canvasRightRef} className="pdf-canvas" />
                  <div className="page-corner-fold-right"></div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* CONTROLES */}
        <div className="book-controls">
          {/* NAVEGACIÓN */}
          <div className="flex items-center gap-2">
            <button 
              onClick={prevPage} 
              disabled={pageNumber === 1 || loading}
              className="book-control-btn"
              title="Página Anterior"
            >
              <ChevronLeft size={16} /> <span className="hidden sm:inline">Anterior</span>
            </button>
            
            <button 
              onClick={nextPage} 
              disabled={loading || (isSinglePage ? pageNumber >= totalPages : pageNumber + 1 >= totalPages)}
              className="book-control-btn"
              title="Página Siguiente"
            >
              <span className="hidden sm:inline">Siguiente</span> <ChevronRight size={16} />
            </button>
          </div>
          
          {/* INDICADOR CENTRAL */}
          <div className="book-page-indicator">
            {getPageIndicatorText()}
          </div>
          
          {/* VISTA & ZOOM CONTROLS */}
          <div className="flex items-center gap-3">
            {/* Toggle Vista */}
            <button 
              onClick={() => {
                setIsSinglePage(!isSinglePage);
                // Si cambiamos a doble página, asegurar que sea un número impar para mantener el formato de libro
                if (isSinglePage) {
                  const oddPage = pageNumber % 2 === 0 ? pageNumber - 1 : pageNumber;
                  setPageNumber(Math.max(1, oddPage));
                }
              }}
              className="book-control-btn"
              title={isSinglePage ? "Vista de Doble Página" : "Vista de Una Sola Página"}
            >
              {isSinglePage ? (
                <div className="flex items-center gap-1">
                  <BookOpen size={16} /> <span className="hidden md:inline">Vista Doble</span>
                </div>
              ) : (
                <div className="flex items-center gap-1">
                  <Book size={16} /> <span className="hidden md:inline">Vista Simple</span>
                </div>
              )}
            </button>

            {/* Controles de Zoom */}
            <div className="flex items-center bg-white/5 border border-white/10 rounded-xl p-0.5">
              <button 
                onClick={zoomOut}
                disabled={zoomPercent <= 100 || loading}
                className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Alejar"
              >
                <ZoomOut size={16} />
              </button>
              <span className="text-[10px] font-black tracking-tighter px-2 text-slate-300 min-w-[45px] text-center">
                {zoomPercent}%
              </span>
              <button 
                onClick={zoomIn}
                disabled={zoomPercent >= 200 || loading}
                className="p-1.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
                title="Acercar"
              >
                <ZoomIn size={16} />
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* ESTILOS OPTIMIZADOS PARA EL RENDERIZADO DEL PDF EN CANVAS */}
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(4, 6, 8, 0.85) !important;
          backdrop-filter: blur(12px) !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          z-index: 3000 !important;
          padding: 1.5rem !important;
        }

        .book-modal-container {
          height: 96vh !important;
          width: 96vw !important;
          max-width: 1650px !important;
          background: #06080A !important;
          padding: 0 !important;
          display: flex;
          flex-direction: column;
          border: 1px solid rgba(69, 245, 229, 0.25) !important;
          box-shadow: 0 0 60px rgba(69, 245, 229, 0.15) !important;
          overflow: hidden;
          border-radius: 20px !important;
        }

        .book-modal-header {
          padding: 1rem 2rem;
          border-bottom: 1px solid rgba(255,255,255,0.06);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(10, 13, 16, 0.75);
          backdrop-filter: blur(10px);
        }

        .quick-nav-tabs {
          display: flex;
          background: rgba(255,255,255,0.03);
          padding: 0.25rem;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.05);
          margin-right: 1.5rem;
        }

        .quick-nav-tabs .tab-btn {
          background: transparent;
          border: none;
          color: #94A3B8;
          padding: 0.4rem 0.9rem;
          font-size: 0.65rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s;
        }

        .quick-nav-tabs .tab-btn:hover {
          color: white;
        }

        .quick-nav-tabs .tab-btn.active {
          background: var(--accent);
          color: #06080A;
          font-weight: 900;
        }

        .btn-pdf-link {
          background: rgba(255,255,255,0.03);
          padding: 0.4rem 0.8rem;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.06);
        }

        .btn-pdf-link:hover {
          background: rgba(255,255,255,0.08);
        }

        /* COMPONENTE DE PÁGINAS HORIZONTALES */
        .book-viewport {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: radial-gradient(circle, #0e1217 0%, #06080a 100%);
          padding: 1.5rem;
          overflow: auto !important; /* Permitir scroll cuando hay zoom */
        }

        .book-viewport::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        .book-viewport::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.2);
        }

        .book-viewport::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
        }

        .book-viewport::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .book-container-3d {
          position: relative;
          display: flex;
          width: 100%;
          height: 100%;
          max-width: 1500px;
          justify-content: center;
          align-items: center;
        }

        .book-page {
          width: 48%;
          height: 98%;
          background: #ffffff;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 20px 40px rgba(0,0,0,0.5);
          overflow: hidden;
          border-radius: 4px;
        }

        .book-page-single {
          width: 60%;
          max-width: 780px;
          height: 98%;
          background: #ffffff;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 25px 50px rgba(0,0,0,0.6);
          overflow: hidden;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .pdf-canvas {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
          background: #ffffff;
        }

        .book-page-left-side {
          margin-right: 2px;
          border-top-left-radius: 8px;
          border-bottom-left-radius: 8px;
          box-shadow: -15px 20px 30px rgba(0,0,0,0.4);
        }

        .book-page-right-side {
          margin-left: 2px;
          border-top-right-radius: 8px;
          border-bottom-right-radius: 8px;
          box-shadow: 15px 20px 30px rgba(0,0,0,0.4);
        }

        .book-spine {
          position: absolute;
          left: 50%;
          top: 1%;
          transform: translateX(-50%);
          width: 16px;
          height: 98%;
          background: linear-gradient(90deg, 
            rgba(0,0,0,0.4) 0%, 
            rgba(255,255,255,0.08) 50%, 
            rgba(0,0,0,0.4) 100%
          );
          border-left: 1px solid rgba(255,255,255,0.05);
          border-right: 1px solid rgba(255,255,255,0.05);
          z-index: 10;
          box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }

        /* CONTROLES */
        .book-controls {
          padding: 1rem 2.5rem;
          border-top: 1px solid rgba(255,255,255,0.06);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(10, 13, 16, 0.7);
        }

        .book-control-btn {
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.06);
          color: white;
          padding: 0.6rem 1.2rem;
          border-radius: 10px;
          font-size: 0.75rem;
          font-weight: 800;
          display: flex;
          align-items: center;
          gap: 0.4rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .book-control-btn:hover:not(:disabled) {
          background: rgba(255,255,255,0.08);
          border-color: rgba(255,255,255,0.15);
          transform: translateY(-1px);
        }

        .book-control-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .book-page-indicator {
          font-size: 0.75rem;
          font-weight: 900;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
      `}</style>
    </div>
  );
}
