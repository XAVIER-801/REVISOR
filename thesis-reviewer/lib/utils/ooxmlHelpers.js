/**
 * OOXML Helper utilities for reading and manipulating Word document XML
 * A .docx file is a ZIP containing XML files. The main content is in word/document.xml
 */

// Conversion constants
const TWIPS_PER_CM = 567;
const HALF_POINTS_PER_POINT = 2;
const EMU_PER_CM = 360000;

/**
 * Convert twips to centimeters
 */
function twipsToCm(twips) {
  return Math.round((twips / TWIPS_PER_CM) * 100) / 100;
}

/**
 * Convert centimeters to twips
 */
function cmToTwips(cm) {
  return Math.round(cm * TWIPS_PER_CM);
}

/**
 * Convert half-points to points (font sizes in OOXML are stored as half-points)
 */
function halfPointsToPoints(hp) {
  return hp / HALF_POINTS_PER_POINT;
}

/**
 * Convert line spacing value to display string
 * In OOXML, line spacing 240 = single (1.0), 360 = 1.5, 480 = double (2.0)
 */
function lineSpacingToDisplay(value) {
  if (!value) return 'unknown';
  const num = parseInt(value);
  if (num === 240) return '1.0';
  if (num === 360) return '1.5';
  if (num === 480) return '2.0';
  return (num / 240).toFixed(1);
}

/**
 * Safely extract text from a w:t node, handling all OOXML variations:
 * - string: "hello"
 * - object with _: { _: "hello", $: { "xml:space": "preserve" } }
 * - array of mixed: ["hello", { _: " world" }]
 * - empty object: {} (no text)
 */
function extractTextFromNode(t) {
  if (!t) return '';
  if (typeof t === 'string') return t;
  if (typeof t === 'number') return t.toString();
  if (Array.isArray(t)) return t.map(item => extractTextFromNode(item)).join('');
  // Object — check for _ (text content), otherwise it's an empty element
  if (typeof t === 'object') {
    if (t._ !== undefined) return String(t._);
    // If it only has $ (attributes) and no text, return empty
    if (t.$ && Object.keys(t).length === 1) return '';
    return '';
  }
  return '';
}

/**
 * Get text content from a paragraph element
 */
function getParagraphText(paragraph) {
  if (!paragraph || !paragraph['w:r']) return '';
  const runs = Array.isArray(paragraph['w:r']) ? paragraph['w:r'] : [paragraph['w:r']];
  return runs.map(run => {
    if (!run['w:t']) return '';
    return extractTextFromNode(run['w:t']);
  }).join('');
}

/**
 * Get paragraph properties
 * CRITICAL: Property names are mapped to match exactly what ruleEngine.js expects:
 *   alignment, indent, hangingIndent, firstLineIndent, lineSpacing, etc.
 */
function getParagraphProperties(paragraph) {
  const pPr = paragraph['w:pPr'] ? (Array.isArray(paragraph['w:pPr']) ? paragraph['w:pPr'][0] : paragraph['w:pPr']) : null;
  if (!pPr) return {};

  const props = {};

  // Alignment
  if (pPr['w:jc']) {
    const jc = Array.isArray(pPr['w:jc']) ? pPr['w:jc'][0] : pPr['w:jc'];
    props.alignment = jc.$ ? jc.$['w:val'] : undefined;
  }

  // Spacing
  if (pPr['w:spacing']) {
    const spacing = Array.isArray(pPr['w:spacing']) ? pPr['w:spacing'][0] : pPr['w:spacing'];
    if (spacing.$) {
      props.spacingBefore = spacing.$['w:before'] ? parseInt(spacing.$['w:before']) : 0;
      props.spacingAfter = spacing.$['w:after'] ? parseInt(spacing.$['w:after']) : 0;
      props.lineSpacing = spacing.$['w:line'] ? parseInt(spacing.$['w:line']) : undefined;
      props.lineRule = spacing.$['w:lineRule'] || 'auto';
    }
  }

  // Indentation — mapped to the names ruleEngine.js uses
  if (pPr['w:ind']) {
    const ind = Array.isArray(pPr['w:ind']) ? pPr['w:ind'][0] : pPr['w:ind'];
    if (ind.$) {
      props.indent = ind.$['w:left'] ? parseInt(ind.$['w:left']) : 0;
      props.hangingIndent = ind.$['w:hanging'] ? parseInt(ind.$['w:hanging']) : 0;
      props.firstLineIndent = ind.$['w:firstLine'] ? parseInt(ind.$['w:firstLine']) : 0;
      // Keep the verbose names too for any code that might reference them
      props.indentLeft = props.indent;
      props.indentRight = ind.$['w:right'] ? parseInt(ind.$['w:right']) : 0;
      props.indentHanging = props.hangingIndent;
      props.indentFirstLine = props.firstLineIndent;
    }
  }

  // Style
  if (pPr['w:pStyle']) {
    const pStyle = Array.isArray(pPr['w:pStyle']) ? pPr['w:pStyle'][0] : pPr['w:pStyle'];
    props.style = pStyle.$ ? pStyle.$['w:val'] : undefined;
  }

  // Numbering (for bulleted/numbered lists)
  if (pPr['w:numPr']) {
    const numPr = Array.isArray(pPr['w:numPr']) ? pPr['w:numPr'][0] : pPr['w:numPr'];
    if (numPr['w:numId']) {
      const numId = Array.isArray(numPr['w:numId']) ? numPr['w:numId'][0] : numPr['w:numId'];
      props.numId = numId.$ ? parseInt(numId.$['w:val']) : undefined;
    }
  }

  return props;
}

/**
 * Get run (text) properties
 */
function getRunProperties(run) {
  const rPr = run['w:rPr'] ? (Array.isArray(run['w:rPr']) ? run['w:rPr'][0] : run['w:rPr']) : null;
  if (!rPr) return {};

  const props = {};

  // Font name
  if (rPr['w:rFonts']) {
    const fonts = Array.isArray(rPr['w:rFonts']) ? rPr['w:rFonts'][0] : rPr['w:rFonts'];
    if (fonts.$) {
      props.fontName = fonts.$['w:ascii'] || fonts.$['w:hAnsi'] || fonts.$['w:cs'] || undefined;
    }
  }

  // Font size (stored as half-points)
  if (rPr['w:sz']) {
    const sz = Array.isArray(rPr['w:sz']) ? rPr['w:sz'][0] : rPr['w:sz'];
    props.fontSize = sz.$ ? parseInt(sz.$['w:val']) : undefined;
  }
  // Also check w:szCs (complex script font size) as fallback
  if (!props.fontSize && rPr['w:szCs']) {
    const szCs = Array.isArray(rPr['w:szCs']) ? rPr['w:szCs'][0] : rPr['w:szCs'];
    props.fontSize = szCs.$ ? parseInt(szCs.$['w:val']) : undefined;
  }

  // Bold — check both w:b and w:bCs
  if (rPr['w:b']) {
    const b = Array.isArray(rPr['w:b']) ? rPr['w:b'][0] : rPr['w:b'];
    props.bold = b.$ ? b.$['w:val'] !== '0' && b.$['w:val'] !== 'false' : true;
  } else if (rPr['w:bCs']) {
    const bCs = Array.isArray(rPr['w:bCs']) ? rPr['w:bCs'][0] : rPr['w:bCs'];
    props.bold = bCs.$ ? bCs.$['w:val'] !== '0' && bCs.$['w:val'] !== 'false' : true;
  }

  // Italic — check both w:i and w:iCs
  if (rPr['w:i']) {
    const i = Array.isArray(rPr['w:i']) ? rPr['w:i'][0] : rPr['w:i'];
    props.italic = i.$ ? i.$['w:val'] !== '0' && i.$['w:val'] !== 'false' : true;
  } else if (rPr['w:iCs']) {
    const iCs = Array.isArray(rPr['w:iCs']) ? rPr['w:iCs'][0] : rPr['w:iCs'];
    props.italic = iCs.$ ? iCs.$['w:val'] !== '0' && iCs.$['w:val'] !== 'false' : true;
  }

  // Color
  if (rPr['w:color']) {
    const color = Array.isArray(rPr['w:color']) ? rPr['w:color'][0] : rPr['w:color'];
    props.color = color.$ ? color.$['w:val'] : undefined;
  }

  // Underline
  if (rPr['w:u']) {
    const u = Array.isArray(rPr['w:u']) ? rPr['w:u'][0] : rPr['w:u'];
    props.underline = u.$ ? u.$['w:val'] : 'single';
  }

  // Highlight
  if (rPr['w:highlight']) {
    const hl = Array.isArray(rPr['w:highlight']) ? rPr['w:highlight'][0] : rPr['w:highlight'];
    props.highlight = hl.$ ? hl.$['w:val'] : undefined;
  }

  // All caps
  if (rPr['w:caps']) {
    const caps = Array.isArray(rPr['w:caps']) ? rPr['w:caps'][0] : rPr['w:caps'];
    props.caps = caps.$ ? caps.$['w:val'] !== '0' && caps.$['w:val'] !== 'false' : true;
  }

  return props;
}

/**
 * Get section properties (margins, page size) from the document
 * CRITICAL: Returns a `margins` object with `left`, `right`, `top`, `bottom`
 * keys to match what ruleEngine.js expects.
 */
function getSectionProperties(body) {
  const sectPr = body['w:sectPr'] ? (Array.isArray(body['w:sectPr']) ? body['w:sectPr'][0] : body['w:sectPr']) : null;
  if (!sectPr) return {};

  const props = {};

  // Page size
  if (sectPr['w:pgSz']) {
    const pgSz = Array.isArray(sectPr['w:pgSz']) ? sectPr['w:pgSz'][0] : sectPr['w:pgSz'];
    if (pgSz.$) {
      props.pageWidth = pgSz.$['w:w'] ? parseInt(pgSz.$['w:w']) : undefined;
      props.pageHeight = pgSz.$['w:h'] ? parseInt(pgSz.$['w:h']) : undefined;
    }
  }

  // Margins — ruleEngine.js expects: this.sectionProps.margins.left, .right, .top, .bottom
  if (sectPr['w:pgMar']) {
    const pgMar = Array.isArray(sectPr['w:pgMar']) ? sectPr['w:pgMar'][0] : sectPr['w:pgMar'];
    if (pgMar.$) {
      props.margins = {
        left: pgMar.$['w:left'] ? parseInt(pgMar.$['w:left']) : 1440,
        right: pgMar.$['w:right'] ? parseInt(pgMar.$['w:right']) : 1440,
        top: pgMar.$['w:top'] ? parseInt(pgMar.$['w:top']) : 1440,
        bottom: pgMar.$['w:bottom'] ? parseInt(pgMar.$['w:bottom']) : 1440
      };
      // Keep flat keys too for backward compatibility
      props.marginTop = props.margins.top;
      props.marginBottom = props.margins.bottom;
      props.marginLeft = props.margins.left;
      props.marginRight = props.margins.right;
    }
  }

  return props;
}

/**
 * Get default run properties from styles.xml
 */
function getDefaultRunProps(stylesXml) {
  if (!stylesXml || !stylesXml['w:styles']) return {};
  const styles = stylesXml['w:styles'];
  const docDefaults = styles['w:docDefaults'];
  if (!docDefaults) return {};

  const dd = Array.isArray(docDefaults) ? docDefaults[0] : docDefaults;
  const rPrDefault = dd['w:rPrDefault'];
  if (!rPrDefault) return {};

  const rpd = Array.isArray(rPrDefault) ? rPrDefault[0] : rPrDefault;
  const rPr = rpd['w:rPr'];
  if (!rPr) return {};

  const rp = Array.isArray(rPr) ? rPr[0] : rPr;
  return getRunProperties({ 'w:rPr': rp });
}

module.exports = {
  twipsToCm,
  cmToTwips,
  halfPointsToPoints,
  lineSpacingToDisplay,
  getParagraphText,
  getParagraphProperties,
  getRunProperties,
  getSectionProperties,
  getDefaultRunProps,
  TWIPS_PER_CM,
  HALF_POINTS_PER_POINT,
  EMU_PER_CM
};
