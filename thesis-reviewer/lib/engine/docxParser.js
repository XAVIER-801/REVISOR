/**
 * DOCX Parser - Reads and parses .docx files by extracting their internal XML
 * A .docx file is a ZIP archive containing XML files:
 * - word/document.xml: main content
 * - word/styles.xml: styles definitions
 * - word/settings.xml: document settings
 * 
 * CRITICAL: This parser resolves style inheritance. When a paragraph references
 * a style (e.g. "Heading1"), the parser looks up that style's run properties
 * (bold, fontSize, fontName) and applies them to any runs that don't have
 * those properties set explicitly.
 */
const JSZip = require('jszip');
const xml2js = require('xml2js');
const {
  getParagraphText,
  getParagraphProperties,
  getRunProperties,
  getSectionProperties,
  getDefaultRunProps
} = require('../utils/ooxmlHelpers');

// We need the text extractor from the helpers
function extractTextFromNode(t) {
  if (!t) return '';
  if (typeof t === 'string') return t;
  if (typeof t === 'number') return t.toString();
  if (Array.isArray(t)) return t.map(item => extractTextFromNode(item)).join('');
  if (typeof t === 'object') {
    if (t._ !== undefined) return String(t._);
    if (t.$ && Object.keys(t).length === 1) return '';
    return '';
  }
  return '';
}

class DocxParser {
  constructor(buffer) {
    this.buffer = buffer;
    this.zip = null;
    this.documentXml = null;
    this.stylesXml = null;
    this.paragraphs = [];
    this.sectionProps = {};
    this.defaultRunProps = {};
    this.styleMap = {}; // Maps style IDs to their run properties
  }

  async parse() {
    // 1. Unzip the docx
    this.zip = await JSZip.loadAsync(this.buffer);

    // 2. Parse document.xml
    const documentXmlStr = await this.zip.file('word/document.xml').async('string');
    const parser = new xml2js.Parser({ explicitArray: false, preserveChildrenOrder: true });
    this.documentXml = await parser.parseStringPromise(documentXmlStr);

    // 3. Parse styles.xml if exists — build a style map for inheritance
    const stylesFile = this.zip.file('word/styles.xml');
    if (stylesFile) {
      const stylesXmlStr = await stylesFile.async('string');
      this.stylesXml = await parser.parseStringPromise(stylesXmlStr);
      this.defaultRunProps = getDefaultRunProps(this.stylesXml);
      this._buildStyleMap();
    }

    // 4. Extract body
    const body = this.documentXml['w:document']['w:body'];

    // 5. Get section properties (margins, page size)
    this.sectionProps = getSectionProperties(body);

    // 6. Extract all paragraphs with their properties
    this.paragraphs = this._extractParagraphs(body);

    return {
      paragraphs: this.paragraphs,
      sectionProps: this.sectionProps,
      defaultRunProps: this.defaultRunProps,
      zip: this.zip,
      documentXml: this.documentXml
    };
  }

  /**
   * Build a map of style IDs -> run properties from styles.xml
   * This is used for style inheritance resolution.
   */
  _buildStyleMap() {
    if (!this.stylesXml || !this.stylesXml['w:styles']) return;
    const styles = this.stylesXml['w:styles'];
    let styleList = styles['w:style'];
    if (!styleList) return;
    if (!Array.isArray(styleList)) styleList = [styleList];

    for (const style of styleList) {
      const id = style.$?.['w:styleId'];
      if (!id) continue;

      const runProps = {};

      // Get rPr from the style definition
      const rPr = style['w:rPr'];
      if (rPr) {
        const resolved = getRunProperties({ 'w:rPr': rPr });
        Object.assign(runProps, resolved);
      }

      // Get paragraph-level rPr too (w:pPr -> w:rPr)
      const pPr = style['w:pPr'];
      if (pPr) {
        const pPrObj = Array.isArray(pPr) ? pPr[0] : pPr;
        if (pPrObj['w:rPr']) {
          const resolved = getRunProperties({ 'w:rPr': pPrObj['w:rPr'] });
          // Only fill in what wasn't already set
          for (const key of Object.keys(resolved)) {
            if (runProps[key] === undefined) runProps[key] = resolved[key];
          }
        }
      }

      // Check for basedOn style (chain inheritance)
      const basedOn = style['w:basedOn'];
      if (basedOn) {
        const baseId = (Array.isArray(basedOn) ? basedOn[0] : basedOn).$?.['w:val'];
        if (baseId) runProps._basedOn = baseId;
      }

      this.styleMap[id] = runProps;
    }

    // Resolve basedOn chains (up to 5 levels deep)
    for (let pass = 0; pass < 5; pass++) {
      for (const id of Object.keys(this.styleMap)) {
        const props = this.styleMap[id];
        if (props._basedOn && this.styleMap[props._basedOn]) {
          const parent = this.styleMap[props._basedOn];
          for (const key of Object.keys(parent)) {
            if (key === '_basedOn') continue;
            if (props[key] === undefined) props[key] = parent[key];
          }
        }
      }
    }
  }

  /**
   * Resolve run properties by merging: explicit run props > paragraph style > default
   */
  _resolveRunProperties(runExplicitProps, paragraphStyleId) {
    const resolved = { ...runExplicitProps };
    
    // Fill from paragraph style
    if (paragraphStyleId && this.styleMap[paragraphStyleId]) {
      const styleProps = this.styleMap[paragraphStyleId];
      for (const key of Object.keys(styleProps)) {
        if (key === '_basedOn') continue;
        if (resolved[key] === undefined) resolved[key] = styleProps[key];
      }
    }

    // Fill from document defaults
    for (const key of Object.keys(this.defaultRunProps)) {
      if (resolved[key] === undefined) resolved[key] = this.defaultRunProps[key];
    }

    return resolved;
  }

  _extractParagraphs(body) {
    const paragraphElements = body['w:p'];
    if (!paragraphElements) return [];

    const pList = Array.isArray(paragraphElements) ? paragraphElements : [paragraphElements];
    
    return pList.map((p, index) => {
      const text = getParagraphText(p);
      const props = getParagraphProperties(p);
      const runs = this._extractRuns(p, props.style);

      return {
        index,
        text: text.trim(),
        rawText: text,
        properties: props,
        runs,
        raw: p
      };
    });
  }

  _extractRuns(paragraph, paragraphStyleId) {
    if (!paragraph['w:r']) return [];
    const runElements = Array.isArray(paragraph['w:r']) ? paragraph['w:r'] : [paragraph['w:r']];

    return runElements.map(run => {
      const textContent = extractTextFromNode(run['w:t']);
      const explicitProps = getRunProperties(run);
      
      // Resolve with style inheritance
      const resolvedProps = this._resolveRunProperties(explicitProps, paragraphStyleId);

      return {
        text: textContent,
        properties: resolvedProps,
        raw: run
      };
    });
  }

  /**
   * Get the raw XML string for document.xml
   */
  async getDocumentXmlString() {
    if (!this.zip) return null;
    return await this.zip.file('word/document.xml').async('string');
  }

  /**
   * Get full text content of the document
   */
  getFullText() {
    return this.paragraphs.map(p => p.text).filter(t => t.length > 0).join('\n');
  }

  /**
   * Find paragraphs containing specific text
   */
  findParagraphsByText(searchText, caseInsensitive = true) {
    return this.paragraphs.filter(p => {
      const text = caseInsensitive ? p.text.toUpperCase() : p.text;
      const search = caseInsensitive ? searchText.toUpperCase() : searchText;
      return text.includes(search);
    });
  }
}

export default DocxParser;
