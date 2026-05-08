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
 * Get text content from a paragraph element
 */
function getParagraphText(paragraph) {
  if (!paragraph || !paragraph['w:r']) return '';
  const runs = Array.isArray(paragraph['w:r']) ? paragraph['w:r'] : [paragraph['w:r']];
  return runs.map(run => {
    if (!run['w:t']) return '';
    const t = run['w:t'];
    if (typeof t === 'string') return t;
    if (Array.isArray(t)) return t.map(item => typeof item === 'string' ? item : (item._ || '')).join('');
    return t._ || t.toString() || '';
  }).join('');
}

/**
 * Get paragraph properties
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

  // Indentation
  if (pPr['w:ind']) {
    const ind = Array.isArray(pPr['w:ind']) ? pPr['w:ind'][0] : pPr['w:ind'];
    if (ind.$) {
      props.indentLeft = ind.$['w:left'] ? parseInt(ind.$['w:left']) : 0;
      props.indentRight = ind.$['w:right'] ? parseInt(ind.$['w:right']) : 0;
      props.indentFirstLine = ind.$['w:firstLine'] ? parseInt(ind.$['w:firstLine']) : undefined;
      props.indentHanging = ind.$['w:hanging'] ? parseInt(ind.$['w:hanging']) : undefined;
    }
  }

  // Style
  if (pPr['w:pStyle']) {
    const pStyle = Array.isArray(pPr['w:pStyle']) ? pPr['w:pStyle'][0] : pPr['w:pStyle'];
    props.style = pStyle.$ ? pStyle.$['w:val'] : undefined;
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

  // Bold
  if (rPr['w:b']) {
    const b = Array.isArray(rPr['w:b']) ? rPr['w:b'][0] : rPr['w:b'];
    props.bold = b.$ ? b.$['w:val'] !== '0' && b.$['w:val'] !== 'false' : true;
  }

  // Italic
  if (rPr['w:i']) {
    const i = Array.isArray(rPr['w:i']) ? rPr['w:i'][0] : rPr['w:i'];
    props.italic = i.$ ? i.$['w:val'] !== '0' && i.$['w:val'] !== 'false' : true;
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

  return props;
}

/**
 * Get section properties (margins, page size) from the document
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

  // Margins
  if (sectPr['w:pgMar']) {
    const pgMar = Array.isArray(sectPr['w:pgMar']) ? sectPr['w:pgMar'][0] : sectPr['w:pgMar'];
    if (pgMar.$) {
      props.marginTop = pgMar.$['w:top'] ? parseInt(pgMar.$['w:top']) : undefined;
      props.marginBottom = pgMar.$['w:bottom'] ? parseInt(pgMar.$['w:bottom']) : undefined;
      props.marginLeft = pgMar.$['w:left'] ? parseInt(pgMar.$['w:left']) : undefined;
      props.marginRight = pgMar.$['w:right'] ? parseInt(pgMar.$['w:right']) : undefined;
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
