/**
 * DOCX Parser - Reads and parses .docx files by extracting their internal XML
 * A .docx file is a ZIP archive containing XML files:
 * - word/document.xml: main content
 * - word/styles.xml: styles definitions
 * - word/settings.xml: document settings
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

class DocxParser {
  constructor(buffer) {
    this.buffer = buffer;
    this.zip = null;
    this.documentXml = null;
    this.stylesXml = null;
    this.paragraphs = [];
    this.sectionProps = {};
    this.defaultRunProps = {};
  }

  async parse() {
    // 1. Unzip the docx
    this.zip = await JSZip.loadAsync(this.buffer);

    // 2. Parse document.xml
    const documentXmlStr = await this.zip.file('word/document.xml').async('string');
    const parser = new xml2js.Parser({ explicitArray: false, preserveChildrenOrder: true });
    this.documentXml = await parser.parseStringPromise(documentXmlStr);

    // 3. Parse styles.xml if exists
    const stylesFile = this.zip.file('word/styles.xml');
    if (stylesFile) {
      const stylesXmlStr = await stylesFile.async('string');
      this.stylesXml = await parser.parseStringPromise(stylesXmlStr);
      this.defaultRunProps = getDefaultRunProps(this.stylesXml);
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

  _extractParagraphs(body) {
    const paragraphElements = body['w:p'];
    if (!paragraphElements) return [];

    const pList = Array.isArray(paragraphElements) ? paragraphElements : [paragraphElements];
    
    return pList.map((p, index) => {
      const text = getParagraphText(p);
      const props = getParagraphProperties(p);
      const runs = this._extractRuns(p);

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

  _extractRuns(paragraph) {
    if (!paragraph['w:r']) return [];
    const runElements = Array.isArray(paragraph['w:r']) ? paragraph['w:r'] : [paragraph['w:r']];

    return runElements.map(run => {
      const text = run['w:t'];
      let textContent = '';
      if (text) {
        if (typeof text === 'string') textContent = text;
        else if (text._) textContent = text._;
        else if (Array.isArray(text)) textContent = text.map(t => typeof t === 'string' ? t : (t._ || '')).join('');
        else textContent = text.toString();
      }

      return {
        text: textContent,
        properties: getRunProperties(run),
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

module.exports = DocxParser;
