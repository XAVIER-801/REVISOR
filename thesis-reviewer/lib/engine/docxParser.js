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
import JSZip from 'jszip';
import xml2js from 'xml2js';
import {
  getParagraphText,
  getParagraphProperties,
  getRunProperties,
  getSectionProperties,
  getDefaultRunProps,
  extractTextFromNode
} from '../utils/ooxmlHelpers';
import ocrEngine from '../utils/ocrEngine';

// Unificamos la extracción de texto usando los helpers robustos


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
    const parser = new xml2js.Parser({ explicitArray: false, preserveChildrenOrder: false });
    this.documentXml = await parser.parseStringPromise(documentXmlStr);

    // 2b. Parse document.xml.rels to resolve image paths
    const relsFile = this.zip.file('word/_rels/document.xml.rels');
    this.relsMap = {};
    if (relsFile) {
      const relsXmlStr = await relsFile.async('string');
      const relsXml = await parser.parseStringPromise(relsXmlStr);
      let relList = relsXml.Relationships.Relationship;
      if (!Array.isArray(relList)) relList = [relList];
      relList.forEach(rel => {
        this.relsMap[rel.$.Id] = rel.$.Target;
      });
    }

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

    // ESTRATEGIA "HUNTER": Activamos OCR inteligente para encontrar actas escaneadas
    // Blindamos este proceso para que un fallo en OCR no detenga el análisis principal
    // OCR desactivado temporalmente para estabilizar el análisis rápido
    // await this._processImagesWithOCR();



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
    const allParagraphs = [];
    
    const walk = (node) => {
      if (!node || typeof node !== 'object') return;
      
      // If this object IS a paragraph or has w:p children
      if (node['w:p']) {
        const pList = Array.isArray(node['w:p']) ? node['w:p'] : [node['w:p']];
        pList.forEach(p => {
          const text = getParagraphText(p);
          const props = getParagraphProperties(p);
          const runs = this._extractRuns(p, props.style);
          const images = this._findImageIds(p);

          allParagraphs.push({
            index: allParagraphs.length,
            text: text.trim(),
            rawText: text,
            properties: props,
            runs,
            images,
            raw: p
          });
        });
      }
      
      // ALWAYS walk other keys, even if we found w:p
      // (Because an object might have w:p AND w:tbl as siblings)
      for (const key in node) {
        if (key === '$' || key === 'w:p') continue; // Already processed w:p
        const child = node[key];
        if (Array.isArray(child)) {
          child.forEach(c => walk(c));
        } else {
          walk(child);
        }
      }
    };

    walk(body);
    return allParagraphs;
  }

  _findImageIds(p) {
    const imageIds = [];
    
    // Look for w:drawing
    const walk = (node) => {
      if (!node) return;
      if (node['w:drawing']) {
        const drawings = Array.isArray(node['w:drawing']) ? node['w:drawing'] : [node['w:drawing']];
        drawings.forEach(d => {
          // Look for blip
          const blip = this._findInObject(d, 'a:blip');
          if (blip && blip.$ && blip.$['r:embed']) {
            imageIds.push(blip.$['r:embed']);
          }
        });
      }
      if (node['w:pict']) {
        const picts = Array.isArray(node['w:pict']) ? node['w:pict'] : [node['w:pict']];
        picts.forEach(pict => {
          const imdata = this._findInObject(pict, 'v:imagedata');
          if (imdata && imdata.$ && imdata.$['r:id']) {
            imageIds.push(imdata.$['r:id']);
          }
        });
      }
      
      for (const key in node) {
        if (typeof node[key] === 'object' && key !== '$') {
          walk(node[key]);
        }
      }
    };

    walk(p);
    return imageIds;
  }

  _findInObject(obj, keyToFind) {
    if (!obj || typeof obj !== 'object') return null;
    if (obj[keyToFind]) return obj[keyToFind];
    for (const key in obj) {
      if (typeof obj[key] === 'object' && key !== '$') {
        const found = this._findInObject(obj[key], keyToFind);
        if (found) return found;
      }
    }
    return null;
  }

  async _processImagesWithOCR() {
    const totalP = this.paragraphs.length;
    
    // ESTRATEGIA "FRANCOTIRADOR": Solo buscamos en el inicio y en el final (Anexos)
    // donde el usuario nos indica que están las 4 actas críticas.
    const paragraphsToScan = this.paragraphs.filter(p => {
      const hasImages = p.images && p.images.length > 0;
      const isAtStart = p.index < 150; // Primeras ~20-30 páginas
      const isAtEnd = p.index > (totalP - 200); // Anexos finales
      return hasImages && (isAtStart || isAtEnd);
    });

    const maxOCRBlocks = 8; // Suficiente para las 4 actas clave
    let blocksDone = 0;

    console.log(`DocxParser: Iniciando Sniper-OCR en extremos (Páginas iniciales y Anexos). Bloques detectados: ${paragraphsToScan.length}`);

    for (const p of paragraphsToScan) {
      if (blocksDone >= maxOCRBlocks) break;

      for (const relId of p.images) {
        if (blocksDone >= maxOCRBlocks) break;

        const target = this.relsMap[relId];
        if (!target) continue;
        
        const zipPath = target.startsWith('media/') ? `word/${target}` : target;
        const imgFile = this.zip.file(zipPath);
        
        if (imgFile) {
          const imgBuffer = await imgFile.async('nodebuffer');
          
          // Filtro por peso (Imágenes de actas suelen pesar entre 100KB y 4MB)
          if (imgBuffer.length < 80000 || imgBuffer.length > 6000000) continue; 

          console.log(`OCR Sniper: Escaneando acta potencial ${blocksDone + 1}/${maxOCRBlocks} (Pos: ${p.index < 150 ? 'Inicio' : 'Anexos'})...`);
          
          if (ocrEngine && typeof ocrEngine.recognize === 'function') {
            const ocrText = await ocrEngine.recognize(imgBuffer);
            if (ocrText && ocrText.trim()) {
              p.text += "\n[OCR DETECTED TEXT]: " + ocrText;
              if (p.normText !== undefined) {
                p.normText += ocrText.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[^A-Z0-9]/g, '');
              }
              p.ocrText = ocrText;
              blocksDone++;
            }
          }
        }
      }
    }
    console.log(`DocxParser: Sniper-OCR Finalizado. Actas procesadas: ${blocksDone}.`);
  }

  _extractRuns(paragraph, paragraphStyleId) {
    const runs = [];
    
    // Función recursiva para extraer texto de runs, capturando w:t, w:tab, w:br y w:sym
    const walkRun = (node) => {
      if (!node || typeof node !== 'object') return;
      
      if (node['w:r']) {
        const runElements = Array.isArray(node['w:r']) ? node['w:r'] : [node['w:r']];
        runElements.forEach(run => {
          // Extraemos el texto del run de forma robusta
          let textContent = '';
          const walkText = (tNode, key) => {
            if (key === 'w:t') textContent += extractTextFromNode(tNode);
            else if (key === 'w:tab' || key === 'w:br' || key === 'w:sym') textContent += ' ';
            else if (typeof tNode === 'object') {
              for (const k in tNode) {
                if (k === '$') continue;
                const child = tNode[k];
                if (Array.isArray(child)) child.forEach(c => walkText(c, k));
                else walkText(child, k);
              }
            }
          };
          walkText(run, 'w:r');

          const explicitProps = getRunProperties(run);
          const resolvedProps = this._resolveRunProperties(explicitProps, paragraphStyleId);

          runs.push({
            text: textContent,
            properties: resolvedProps,
            raw: run
          });
        });
      }
      
      // Seguimos buscando runs en elementos anidados (como w:hyperlink o w:sdt)
      for (const key in node) {
        if (key === '$' || key === 'w:r' || key === 'w:pPr' || key === 'w:rPr') continue;
        const child = node[key];
        if (Array.isArray(child)) child.forEach(c => walkRun(c));
        else walkRun(child);
      }
    };

    walkRun(paragraph);
    return runs;
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
