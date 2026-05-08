/**
 * DOCX Annotator - Inserts visual annotations (highlights, comments, red text, borders) 
 * into the Word document XML to mark format errors in-place.
 */
const JSZip = require('jszip');
const xml2js = require('xml2js');

class DocxAnnotator {
  constructor(originalBuffer) {
    this.originalBuffer = originalBuffer;
    this.zip = null;
    this.documentObj = null;
    // Use a builder that preserves the structure as much as possible
    this.builder = new xml2js.Builder({ 
      renderOpts: { pretty: false },
      headless: false
    });
  }

  async init() {
    this.zip = await JSZip.loadAsync(this.originalBuffer);
    const docXmlStr = await this.zip.file('word/document.xml').async('string');
    const parser = new xml2js.Parser({ 
      explicitArray: false, 
      preserveChildrenOrder: true,
      attrkey: '$',
      charkey: '_'
    });
    this.documentObj = await parser.parseStringPromise(docXmlStr);
  }

  /**
   * Add annotations based on analysis results
   */
  async annotate(analysisResults) {
    await this.init();

    const errors = analysisResults.errors || [];
    const warnings = analysisResults.warnings || [];
    const allIssues = [...errors, ...warnings];

    // 1. Modify paragraphs in-place with visual markers
    this._applyVisualMarkers(allIssues);

    // 2. Add summary block at the beginning
    this._insertSummaryBlock(analysisResults);

    // 3. Create/Update comments XML file and link them
    const commentsXml = this._createCommentsXml(allIssues);
    this.zip.file('word/comments.xml', commentsXml);

    // Update content types and relationships
    await this._updateContentTypes();
    await this._updateRelationships();

    // Save modified document.xml
    const modifiedXml = this.builder.buildObject(this.documentObj);
    this.zip.file('word/document.xml', modifiedXml);

    return await this.zip.generateAsync({ type: 'nodebuffer' });
  }

  _applyVisualMarkers(issues) {
    const body = this.documentObj['w:document']['w:body'];
    const paragraphs = body['w:p'];
    if (!paragraphs) return;

    // Convert to array if it's a single object
    let pList = Array.isArray(paragraphs) ? paragraphs : [paragraphs];
    
    // We need to be careful with the array reference if we want to update it in the object
    if (!Array.isArray(paragraphs)) {
      body['w:p'] = pList;
    }

    issues.forEach((issue, issueIdx) => {
      const pIdx = issue.paragraphIndex;
      if (pIdx === undefined || pIdx < 0 || pIdx >= pList.length) return;

      const p = pList[pIdx];
      
      // Ensure paragraph properties exist
      if (!p['w:pPr']) p['w:pPr'] = {};
      const pPr = p['w:pPr'];

      // Apply Paragraph Border (Simulates a "Box" around the error)
      const color = issue.status === 'error' ? 'FF0000' : 'FF8800';
      
      // Box effect: apply borders to all 4 sides
      pPr['w:pBdr'] = {
        'w:top': { $: { 'w:val': 'single', 'w:sz': '18', 'w:space': '4', 'w:color': color } },
        'w:bottom': { $: { 'w:val': 'single', 'w:sz': '18', 'w:space': '4', 'w:color': color } },
        'w:left': { $: { 'w:val': 'single', 'w:sz': '18', 'w:space': '4', 'w:color': color } },
        'w:right': { $: { 'w:val': 'single', 'w:sz': '18', 'w:space': '4', 'w:color': color } }
      };

      // Shading effect (light background)
      pPr['w:shd'] = { $: { 'w:val': 'clear', 'w:color': 'auto', 'w:fill': issue.status === 'error' ? 'FFE6E6' : 'FFF9E6' } };

      // Apply highlighting to all runs in the paragraph
      if (p['w:r']) {
        const runs = Array.isArray(p['w:r']) ? p['w:r'] : [p['w:r']];
        runs.forEach(r => {
          if (!r['w:rPr']) r['w:rPr'] = {};
          const rPr = r['w:rPr'];
          
          // Highlighting (Text background)
          rPr['w:highlight'] = { $: { 'w:val': issue.status === 'error' ? 'red' : 'yellow' } };
          
          // Underline
          rPr['w:u'] = { $: { 'w:val': 'double', 'w:color': color } };
          
          // Change text color to red if error
          if (issue.status === 'error') {
            rPr['w:color'] = { $: { 'w:val': 'FF0000' } };
          }
        });
      }

      // Add a comment reference at the start of the paragraph content
      const commentReference = { 
        'w:r': { 
          'w:rPr': { 
            'w:rStyle': { $: { 'w:val': 'CommentReference' } } 
          }, 
          'w:commentReference': { $: { 'w:id': issueIdx.toString() } } 
        } 
      };

      if (!p['w:commentRangeStart']) {
        p['w:commentRangeStart'] = { $: { 'w:id': issueIdx.toString() } };
        p['w:commentRangeEnd'] = { $: { 'w:id': issueIdx.toString() } };
      }
    });
  }

  _insertSummaryBlock(results) {
    const body = this.documentObj['w:document']['w:body'];
    const { score, errorCount, warningCount, passedCount } = results;

    const summaryParagraphs = [];
    
    // Add title and stats
    summaryParagraphs.push(this._createSimpleParagraph('⚡ REPORTE DE REVISIÓN DE FORMATO - REPOSITORIO UNA PUNO', '1565C0', true, 28));
    summaryParagraphs.push(this._createSimpleParagraph(`📊 Puntuación: ${score}/100  |  ✅ ${passedCount} aprobados  |  ❌ ${errorCount} errores  |  ⚠️ ${warningCount} advertencias`, '333333', false, 22));
    summaryParagraphs.push(this._createSimpleParagraph('═══════════════════════════════════════════════════════', '2196F3', false, 20));

    // Errors summary
    if (results.errors.length > 0) {
      summaryParagraphs.push(this._createSimpleParagraph('❌ ERRORES ENCONTRADOS:', 'D32F2F', true, 24));
      results.errors.forEach((err, i) => {
        summaryParagraphs.push(this._createSimpleParagraph(`   ${i + 1}. [${err.category}] ${err.message}`, 'C62828', false, 20));
      });
    }

    // Warnings summary
    if (results.warnings.length > 0) {
      summaryParagraphs.push(this._createSimpleParagraph('⚠️ ADVERTENCIAS:', 'F57F17', true, 24));
      results.warnings.forEach((warn, i) => {
        summaryParagraphs.push(this._createSimpleParagraph(`   ${i + 1}. [${warn.category}] ${warn.message}`, 'E65100', false, 20));
      });
    }

    // Add page break
    summaryParagraphs.push({
      'w:pPr': {},
      'w:r': { 'w:br': { $: { 'w:type': 'page' } } }
    });

    // Prepend to body
    const existingPs = Array.isArray(body['w:p']) ? body['w:p'] : (body['w:p'] ? [body['w:p']] : []);
    body['w:p'] = [...summaryParagraphs, ...existingPs];
  }

  _createSimpleParagraph(text, color, bold, size) {
    return {
      'w:pPr': {
        'w:spacing': { $: { 'w:after': '0', 'w:line': '240', 'w:lineRule': 'auto' } },
        'w:jc': { $: { 'w:val': 'left' } }
      },
      'w:r': {
        'w:rPr': {
          'w:rFonts': { $: { 'w:ascii': 'Consolas', 'w:hAnsi': 'Consolas', 'w:cs': 'Consolas' } },
          'w:sz': { $: { 'w:val': size.toString() } },
          'w:szCs': { $: { 'w:val': size.toString() } },
          'w:color': { $: { 'w:val': color } },
          ...(bold ? { 'w:b': {}, 'w:bCs': {} } : {})
        },
        'w:t': { _: text }
      }
    };
  }

  _createCommentsXml(issues) {
    const comments = issues.map((issue, idx) => ({
      $: {
        'w:id': idx.toString(),
        'w:author': 'Revisor UNA Puno',
        'w:date': '2025-01-01T00:00:00Z',
        'w:initials': 'RUP'
      },
      'w:p': [
        {
          'w:pPr': { 'w:pStyle': { $: { 'w:val': 'CommentText' } } },
          'w:r': [
            { 'w:rPr': { 'w:b': {}, 'w:color': { $: { 'w:val': issue.status === 'error' ? 'FF0000' : 'FF8800' } } }, 'w:t': `${issue.status === 'error' ? '❌ ERROR' : '⚠️ ADVERTENCIA'}: ` },
            { 'w:t': issue.message }
          ]
        },
        {
          'w:pPr': { 'w:pStyle': { $: { 'w:val': 'CommentText' } } },
          'w:r': { 'w:rPr': { 'w:i': {} }, 'w:t': `Esperado: ${issue.expected} | Encontrado: ${issue.actual}` }
        }
      ]
    }));

    return this.builder.buildObject({
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

module.exports = DocxAnnotator;
