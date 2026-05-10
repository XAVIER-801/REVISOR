/**
 * DOCX Annotator Elite - Inserts high-fidelity visual markers and native Word comments.
 * 
 * CRITICAL DESIGN DECISION: This annotator does NOT use xml2js.Builder to rebuild
 * the entire document.xml. Doing so destroys xml:space="preserve" attributes on
 * w:t elements, causing Word to collapse spaces between runs (words get joined).
 * 
 * Instead, we work with the raw XML string using targeted regex insertions,
 * preserving the original document structure perfectly.
 */
const JSZip = require('jszip');
const xml2js = require('xml2js');

class DocxAnnotator {
  constructor(originalBuffer) {
    this.originalBuffer = originalBuffer;
    this.zip = null;
    this.rawDocXml = '';  // We work with the raw XML string
    this.documentObj = null; // Only used for reading paragraph count
  }

  async init() {
    this.zip = await JSZip.loadAsync(this.originalBuffer);
    this.rawDocXml = await this.zip.file('word/document.xml').async('string');
    
    // Parse only to count paragraphs and map indices
    const parser = new xml2js.Parser({ 
      explicitArray: false, 
      preserveChildrenOrder: true,
      attrkey: '$',
      charkey: '_'
    });
    this.documentObj = await parser.parseStringPromise(this.rawDocXml);
  }

  async annotate(analysis) {
    await this.init();
    const { results, stats } = analysis;
    const issues = results.filter(r => r.status !== 'passed');

    // 1. Apply visual markers by modifying the raw XML string
    this._applyVisualMarkersToRawXml(issues);

    // 2. Insert summary block at the beginning of the document
    this._insertSummaryBlockToRawXml(stats, results);

    // 3. Create comments XML
    const commentsXml = this._createCommentsXml(issues);
    this.zip.file('word/comments.xml', commentsXml);

    // 4. Update content types and relationships
    await this._updateContentTypes();
    await this._updateRelationships();

    // 5. Save the modified raw XML (preserving all original formatting)
    this.zip.file('word/document.xml', this.rawDocXml);

    return await this.zip.generateAsync({ type: 'nodebuffer' });
  }

  /**
   * Apply visual markers (shading + left border) to paragraphs with issues.
   * Works by finding the Nth <w:p> in the raw XML and injecting shading into its <w:pPr>.
   */
  _applyVisualMarkersToRawXml(issues) {
    // Build a map of paragraph index -> issues
    const issuesByParagraph = {};
    issues.forEach((issue, idx) => {
      const pIdx = issue.paragraphIndex;
      if (pIdx === undefined || pIdx < 0) return;
      if (!issuesByParagraph[pIdx]) issuesByParagraph[pIdx] = [];
      issuesByParagraph[pIdx].push({ ...issue, commentId: idx });
    });

    // Find all <w:p> positions in the raw XML
    const pPositions = [];
    const pRegex = /<w:p[\s>]/g;
    let match;
    while ((match = pRegex.exec(this.rawDocXml)) !== null) {
      pPositions.push(match.index);
    }

    // Process paragraphs in reverse order (so string positions don't shift)
    const sortedIndices = Object.keys(issuesByParagraph).map(Number).sort((a, b) => b - a);

    for (const pIdx of sortedIndices) {
      if (pIdx >= pPositions.length) continue;
      
      const issuesForP = issuesByParagraph[pIdx];
      const worstStatus = issuesForP.some(i => i.status === 'error') ? 'error' : 'warning';
      const color = worstStatus === 'error' ? 'FFA07A' : 'FFDAB9';
      const bgColor = worstStatus === 'error' ? 'FFF5F0' : 'FFFAEF';

      const pStart = pPositions[pIdx];
      
      // Find where this <w:p> element's content starts (after the opening tag)
      const afterPTag = this.rawDocXml.indexOf('>', pStart) + 1;
      
      // Check if there's already a <w:pPr> inside this paragraph
      const pEndTag = this.rawDocXml.indexOf('</w:p>', pStart);
      const existingPPr = this.rawDocXml.indexOf('<w:pPr', pStart);
      
      if (existingPPr !== -1 && existingPPr < pEndTag) {
        // There's an existing <w:pPr>. Find its closing tag and inject before it.
        const pPrClose = this.rawDocXml.indexOf('</w:pPr>', existingPPr);
        if (pPrClose !== -1 && pPrClose < pEndTag) {
          const injection = `<w:shd w:val="clear" w:color="auto" w:fill="${bgColor}"/>` +
            `<w:pBdr><w:left w:val="single" w:sz="12" w:space="4" w:color="${color}"/></w:pBdr>`;
          this.rawDocXml = this.rawDocXml.slice(0, pPrClose) + injection + this.rawDocXml.slice(pPrClose);
        }
      } else {
        // No <w:pPr> exists. Create one right after <w:p...>
        const injection = `<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="${bgColor}"/>` +
          `<w:pBdr><w:left w:val="single" w:sz="12" w:space="4" w:color="${color}"/></w:pBdr></w:pPr>`;
        this.rawDocXml = this.rawDocXml.slice(0, afterPTag) + injection + this.rawDocXml.slice(afterPTag);
      }
    }
  }

  /**
   * Insert a summary report page at the very beginning of the document.
   */
  _insertSummaryBlockToRawXml(stats, results) {
    const scoreColor = stats.score > 80 ? '27AE60' : (stats.score > 50 ? 'D68910' : 'C0392B');
    const criticals = results.filter(r => r.status === 'error').slice(0, 10);

    let summaryXml = '';
    
    // Helper to create a simple paragraph
    const mkP = (text, color, bold, size) => {
      const bTag = bold ? '<w:b/>' : '';
      return `<w:p><w:pPr><w:jc w:val="left"/></w:pPr>` +
        `<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>` +
        `<w:sz w:val="${size}"/><w:color w:val="${color}"/>${bTag}</w:rPr>` +
        `<w:t xml:space="preserve">${this._escapeXml(text)}</w:t></w:r></w:p>`;
    };

    summaryXml += mkP('🏛️ REPORTE INSTITUCIONAL VRI-SCANNER 2.0', '0E6655', true, 32);
    summaryXml += mkP('SISTEMA DE VALIDACIÓN DE TESIS - UNAP 2025', '1B4F72', true, 24);
    summaryXml += mkP('──────────────────────────────────────────────', 'ABB2B9', false, 20);
    summaryXml += mkP(`📊 PUNTAJE DE CUMPLIMIENTO: ${stats.score}/100`, scoreColor, true, 28);
    summaryXml += mkP(`✅ Aprobados: ${stats.passed} | ❌ Errores: ${stats.errors} | ⚠️ Advertencias: ${stats.warnings}`, '34495E', false, 22);
    summaryXml += mkP('──────────────────────────────────────────────', 'ABB2B9', false, 20);

    if (criticals.length > 0) {
      summaryXml += mkP('⚠️ PRINCIPALES OBSERVACIONES CRÍTICAS:', 'C0392B', true, 22);
      criticals.forEach((c, i) => {
        summaryXml += mkP(`   ${i + 1}. [${c.category}] ${c.rule}: ${c.message}`, '922B21', false, 18);
      });
    }

    // Page break
    summaryXml += '<w:p><w:r><w:br w:type="page"/></w:r></w:p>';

    // Insert after <w:body> opening tag
    const bodyStart = this.rawDocXml.indexOf('<w:body');
    const bodyTagEnd = this.rawDocXml.indexOf('>', bodyStart) + 1;
    this.rawDocXml = this.rawDocXml.slice(0, bodyTagEnd) + summaryXml + this.rawDocXml.slice(bodyTagEnd);
  }

  _escapeXml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  _createCommentsXml(issues) {
    const builder = new xml2js.Builder({ renderOpts: { pretty: false }, headless: false });
    const comments = issues.map((issue, idx) => ({
      $: {
        'w:id': idx.toString(),
        'w:author': 'VRI-SCANNER',
        'w:date': new Date().toISOString(),
        'w:initials': 'VRI'
      },
      'w:p': [
        {
          'w:pPr': { 'w:pStyle': { $: { 'w:val': 'CommentText' } } },
          'w:r': [
            { 'w:rPr': { 'w:b': {}, 'w:color': { $: { 'w:val': issue.status === 'error' ? 'FF0000' : 'FF8800' } } }, 'w:t': `${issue.status.toUpperCase()}: ` },
            { 'w:t': issue.rule }
          ]
        },
        {
          'w:pPr': { 'w:pStyle': { $: { 'w:val': 'CommentText' } } },
          'w:r': { 'w:t': issue.message }
        },
        ...(issue.expected ? [{
          'w:pPr': { 'w:pStyle': { $: { 'w:val': 'CommentText' } } },
          'w:r': { 'w:rPr': { 'w:i': {} }, 'w:t': `Esperado: ${issue.expected} | Encontrado: ${issue.actual || 'No detectado'}` }
        }] : [])
      ]
    }));

    return builder.buildObject({
      'w:comments': {
        $: {
          'xmlns:w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'xmlns:r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        },
        'w:comment': comments
      }
    });
  }

  async _updateContentTypes() {
    const ctFile = this.zip.file('[Content_Types].xml');
    if (!ctFile) return;
    let ct = await ctFile.async('string');
    if (!ct.includes('comments.xml')) {
      ct = ct.replace('</Types>', '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>');
      this.zip.file('[Content_Types].xml', ct);
    }
  }

  async _updateRelationships() {
    const relsFile = this.zip.file('word/_rels/document.xml.rels');
    if (!relsFile) return;
    let rels = await relsFile.async('string');
    if (!rels.includes('comments.xml')) {
      rels = rels.replace('</Relationships>', '<Relationship Id="rIdComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>');
      this.zip.file('word/_rels/document.xml.rels', rels);
    }
  }
}

export default DocxAnnotator;
