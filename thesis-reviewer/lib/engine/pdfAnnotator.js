import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';

/**
 * PDF Annotator Elite 2.0 - Total visual compliance report.
 * Supports multi-page summaries, precise spatial highlighting, and non-overlapping labels.
 */
class PdfAnnotator {
  constructor(buffer) {
    this.buffer = buffer;
  }

  async annotate(analysis) {
    const { results, stats } = analysis;
    const pdfDoc = await PDFDocument.load(this.buffer);
    
    const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
    const fontItalic = await pdfDoc.embedFont(StandardFonts.HelveticaOblique);
    const fontRegular = await pdfDoc.embedFont(StandardFonts.Helvetica);

    const clean = (str) => (str || '').replace(/[^\x00-\x7F\xC0-\xFF]/g, '');

    // 1. GENERATE SUMMARY PAGES (Chunked by 15)
    const issues = results.filter(r => r.status !== 'passed');
    const chunkSize = 15;
    
    for (let i = 0; i < Math.max(1, Math.ceil(issues.length / chunkSize)); i++) {
      const summaryPage = pdfDoc.insertPage(i);
      const { width, height } = summaryPage.getSize();
      
      // Header Background
      summaryPage.drawRectangle({
        x: 0, y: height - 100, width: width, height: 100,
        color: rgb(0.06, 0.45, 0.35)
      });

      summaryPage.drawText(`REPOSTYLE: REPORTE DE CUMPLIMIENTO (PAG. ${i + 1})`, {
        x: 50, y: height - 50, size: 20, font: fontBold, color: rgb(1, 1, 1)
      });
      
      let currentY = height - 130;

      // Only show Score and Stats on the FIRST summary page
      if (i === 0) {
        const scoreColor = stats.score > 80 ? rgb(0.1, 0.7, 0.3) : (stats.score > 50 ? rgb(0.9, 0.6, 0.1) : rgb(0.8, 0.1, 0.1));
        summaryPage.drawRectangle({ x: 50, y: currentY - 50, width: width - 100, height: 60, color: rgb(0.95, 0.97, 0.96), borderColor: scoreColor, borderWidth: 1 });
        summaryPage.drawText('PUNTAJE DE FORMATO:', { x: 70, y: currentY - 20, size: 10, font: fontBold, color: rgb(0.3, 0.3, 0.3) });
        summaryPage.drawText(`${stats.score}/100`, { x: 70, y: currentY - 45, size: 22, font: fontBold, color: scoreColor });
        summaryPage.drawText(`${stats.passed} Aprobados | ${stats.errors} Errores | ${stats.warnings} Advertencias`, { x: 250, y: currentY - 35, size: 10, font: fontRegular, color: rgb(0.4, 0.4, 0.4) });
        currentY -= 100;
      }

      summaryPage.drawText('DETALLE DE HALLAZGOS:', { x: 50, y: currentY, size: 12, font: fontBold });
      currentY -= 25;

      const pageIssues = issues.slice(i * chunkSize, (i + 1) * chunkSize);
      pageIssues.forEach((finding, idx) => {
        const globalIdx = i * chunkSize + idx + 1;
        summaryPage.drawText(`${globalIdx}. [${clean(finding.category)}] ${clean(finding.rule)}`, { x: 60, y: currentY, size: 9, font: fontBold });
        currentY -= 11;
        summaryPage.drawText(`   ${clean(finding.message).substring(0, 95)}${finding.page ? ` (Pág. ${finding.page})` : ''}`, { x: 60, y: currentY, size: 8, font: fontRegular, color: rgb(0.3, 0.3, 0.3) });
        
        if (finding.expected) {
          currentY -= 10;
          summaryPage.drawText(`   Esperado: ${clean(finding.expected)} | Encontrado: ${clean(finding.actual) || 'No detectado'}`, { x: 70, y: currentY, size: 7, font: fontItalic, color: rgb(0.5, 0.5, 0.5) });
        }
        currentY -= 15;
      });

      summaryPage.drawText(`Generado por RepoStyle - Auditor de Formato y Estilo.`, { x: width / 2 - 100, y: 30, size: 7, font: fontRegular, color: rgb(0.6, 0.6, 0.6) });
    }

    // 2. SPATIAL ANNOTATIONS ON PAGES
    const labelOffsets = {}; // To stack labels if multiple on one page

    results.forEach(finding => {
      if (finding.status === 'passed') return;
      if (!finding.page || finding.page <= 0) return;

      try {
        const pages = pdfDoc.getPages();
        const targetPage = pages[finding.page - 1];
        if (!targetPage) return;

        const { width, height } = targetPage.getSize();
        if (!labelOffsets[finding.page]) labelOffsets[finding.page] = 0;

        // A. TEXT HIGHLIGHTING (If Y is available)
        if (finding.y !== undefined && finding.y > 0) {
          targetPage.drawRectangle({
            x: 50, 
            y: finding.y - 5,
            width: width - 100,
            height: 15,
            color: finding.status === 'error' ? rgb(0.95, 0.4, 0.4) : rgb(0.95, 0.8, 0.3),
            opacity: 0.1 // Ultra-subtle professional highlight
          });
        }

        // B. MARGIN GUIDELINES
        if (finding.id === 'margin-left') {
          const margin35pts = (3.5 * 72) / 2.54;
          targetPage.drawLine({ start: { x: margin35pts, y: 0 }, end: { x: margin35pts, y: height }, thickness: 1, color: rgb(1, 0, 0), opacity: 0.3, dashArray: [5, 5] });
        }

        // C. STACKED LABELS AT TOP (Subtle background)
        const labelY = height - 25 - (labelOffsets[finding.page] * 12);
        targetPage.drawRectangle({
          x: 20, y: labelY - 2, width: width - 40, height: 10,
          color: finding.status === 'error' ? rgb(0.99, 0.96, 0.96) : rgb(0.99, 0.99, 0.95),
          borderColor: finding.status === 'error' ? rgb(0.9, 0.6, 0.6) : rgb(0.8, 0.7, 0.5),
          borderWidth: 0.2,
          opacity: 0.95
        });

        targetPage.drawText(`[VRI] ${clean(finding.rule).toUpperCase()}: ${clean(finding.message).substring(0, 85)}`, {
          x: 30, y: labelY, size: 6, font: fontBold,
          color: finding.status === 'error' ? rgb(0.6, 0, 0) : rgb(0.5, 0.3, 0)
        });

        labelOffsets[finding.page]++;

      } catch (err) {
        console.error(`Error annotating PDF page ${finding.page}:`, err.message);
      }
    });

    const pdfBytes = await pdfDoc.save();
    return Buffer.from(pdfBytes);
  }
}

export default PdfAnnotator;
