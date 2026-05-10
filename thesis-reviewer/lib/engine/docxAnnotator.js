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
import JSZip from 'jszip';
import xml2js from 'xml2js';

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
   * Apply visual markers and native Word comment anchors.
   */
  _applyVisualMarkersToRawXml(issues) {
    const issuesByParagraph = {};
    issues.forEach((issue, idx) => {
      const pIdx = issue.paragraphIndex;
      if (pIdx === undefined || pIdx < 0) return;
      if (!issuesByParagraph[pIdx]) issuesByParagraph[pIdx] = [];
      issuesByParagraph[pIdx].push({ ...issue, commentId: idx });
    });

    const pPositions = [];
    const pRegex = /<w:p[\s>]/g;
    let match;
    while ((match = pRegex.exec(this.rawDocXml)) !== null) {
      pPositions.push(match.index);
    }

    const sortedIndices = Object.keys(issuesByParagraph).map(Number).sort((a, b) => b - a);

    for (const pIdx of sortedIndices) {
      if (pIdx >= pPositions.length) continue;
      
      const issuesForP = issuesByParagraph[pIdx];
      const worstStatus = issuesForP.some(i => i.status === 'error') ? 'error' : 'warning';
      const color = worstStatus === 'error' ? 'FFA07A' : 'FFDAB9';
      const bgColor = worstStatus === 'error' ? 'FFF5F0' : 'FFFAEF';

      const pStart = pPositions[pIdx];
      const afterPTag = this.rawDocXml.indexOf('>', pStart) + 1;
      const pEndTag = this.rawDocXml.indexOf('</w:p>', pStart);
      const existingPPr = this.rawDocXml.indexOf('<w:pPr', pStart);
      
      // 1. Inject shading and borders
      if (existingPPr !== -1 && existingPPr < pEndTag) {
        const pPrClose = this.rawDocXml.indexOf('</w:pPr>', existingPPr);
        if (pPrClose !== -1 && pPrClose < pEndTag) {
          const injection = `<w:shd w:val="clear" w:color="auto" w:fill="${bgColor}"/>` +
            `<w:pBdr><w:left w:val="single" w:sz="12" w:space="4" w:color="${color}"/></w:pBdr>`;
          this.rawDocXml = this.rawDocXml.slice(0, pPrClose) + injection + this.rawDocXml.slice(pPrClose);
        }
      } else {
        const injection = `<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="${bgColor}"/>` +
          `<w:pBdr><w:left w:val="single" w:sz="12" w:space="4" w:color="${color}"/></w:pBdr></w:pPr>`;
        this.rawDocXml = this.rawDocXml.slice(0, afterPTag) + injection + this.rawDocXml.slice(afterPTag);
      }

      // 2. Inject native Word comment anchors (MUST be inside <w:p>)
      // We place the anchor around the first run of the paragraph
      const firstRun = this.rawDocXml.indexOf('<w:r', pStart);
      if (firstRun !== -1 && firstRun < pEndTag) {
        const firstRunEnd = this.rawDocXml.indexOf('</w:r>', firstRun) + 6;
        if (firstRunEnd > 6 && firstRunEnd <= pEndTag) {
          let commentAnchors = '';
          issuesForP.forEach(iss => {
            commentAnchors += `<w:commentRangeStart w:id="${iss.commentId}"/><w:commentRangeEnd w:id="${iss.commentId}"/><w:r><w:commentReference w:id="${iss.commentId}"/></w:r>`;
          });
          this.rawDocXml = this.rawDocXml.slice(0, firstRun) + commentAnchors + this.rawDocXml.slice(firstRun);
        }
      }
    }
  }

  /**
   * Insert a summary report page with ALL observations.
   */
  _insertSummaryBlockToRawXml(stats, results) {
    const scoreColor = stats.score > 80 ? '27AE60' : (stats.score > 50 ? 'D68910' : 'C0392B');
    const allIssues = results.filter(r => r.status !== 'passed');

    let summaryXml = '';
    const mkP = (text, color, bold, size, italic = false) => {
      const bTag = bold ? '<w:b/>' : '';
      const iTag = italic ? '<w:i/>' : '';
      return `<w:p><w:pPr><w:jc w:val="left"/></w:pPr>` +
        `<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>` +
        `<w:sz w:val="${size}"/><w:color w:val="${color}"/>${bTag}${iTag}</w:rPr>` +
        `<w:t xml:space="preserve">${this._escapeXml(text)}</w:t></w:r></w:p>`;
    };

    summaryXml += mkP('🏛️ REPORTE INSTITUCIONAL REPOSTYLE 2.0', '0E6655', true, 32);
    summaryXml += mkP('AUDITOR DE FORMATO Y ESTILO DE TESIS - VRI UNAP', '1B4F72', true, 24);
    summaryXml += mkP('──────────────────────────────────────────────', 'ABB2B9', false, 20);
    summaryXml += mkP(`📊 PUNTAJE DE CUMPLIMIENTO: ${stats.score}/100`, scoreColor, true, 28);
    summaryXml += mkP(`✅ Aprobados: ${stats.passed} | ❌ Errores: ${stats.errors} | ⚠️ Advertencias: ${stats.warnings}`, '34495E', false, 22);
    summaryXml += mkP('──────────────────────────────────────────────', 'ABB2B9', false, 20);

    if (allIssues.length > 0) {
      summaryXml += mkP(`📋 LISTADO COMPLETO DE OBSERVACIONES (${allIssues.length}):`, '2E4053', true, 22);
      allIssues.forEach((c, i) => {
        const color = c.status === 'error' ? 'C0392B' : 'D68910';
        summaryXml += mkP(`   ${i + 1}. [${c.category}] ${c.rule}`, color, true, 18);
        summaryXml += mkP(`      Hallazgo: ${c.message}`, '566573', false, 16);
        if (c.expected) {
          summaryXml += mkP(`      💡 DEBE SER: ${c.expected}`, '1B4F72', true, 16, true);
        }
        summaryXml += mkP(' ', 'FFFFFF', false, 8); // Spacer
      });
    }

    summaryXml += '<w:p><w:r><w:br w:type="page"/></w:r></w:p>';
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
        'w:author': 'RepoStyle',
        'w:date': new Date().toISOString(),
        'w:initials': 'RS'
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
