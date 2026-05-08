/**
 * Rule Engine - Executes all format verification rules against a parsed DOCX document
 */
const formatRules = require('../config/formatRules.json');
const { twipsToCm, halfPointsToPoints, lineSpacingToDisplay } = require('../utils/ooxmlHelpers');

class RuleEngine {
  constructor(parsedDoc) {
    this.paragraphs = parsedDoc.paragraphs;
    this.sectionProps = parsedDoc.sectionProps;
    this.defaultRunProps = parsedDoc.defaultRunProps;
    this.results = [];
    this.errors = [];
    this.warnings = [];
    this.passed = [];
    this.score = 0;
  }

  analyze() {
    this.checkMargins();
    this.checkDefaultFont();
    this.checkStructure();
    this.checkResumen();
    this.checkAbstract();
    this.checkLineSpacing();
    this.checkParagraphFormatting();
    this.calculateScore();

    return {
      results: this.results,
      errors: this.errors,
      warnings: this.warnings,
      passed: this.passed,
      score: this.score,
      totalRules: this.results.length,
      errorCount: this.errors.length,
      warningCount: this.warnings.length,
      passedCount: this.passed.length
    };
  }

  addResult(rule) {
    this.results.push(rule);
    if (rule.status === 'error') this.errors.push(rule);
    else if (rule.status === 'warning') this.warnings.push(rule);
    else this.passed.push(rule);
  }

  // ============ MARGIN CHECK ============
  checkMargins() {
    const expected = formatRules.global.margins;
    const sp = this.sectionProps;

    const checks = [
      {
        name: 'Margen Superior',
        expected: expected.top,
        actual: sp.marginTop,
        display: expected.display.top
      },
      {
        name: 'Margen Inferior',
        expected: expected.bottom,
        actual: sp.marginBottom,
        display: expected.display.bottom
      },
      {
        name: 'Margen Izquierdo',
        expected: expected.left,
        actual: sp.marginLeft,
        display: expected.display.left
      },
      {
        name: 'Margen Derecho',
        expected: expected.right,
        actual: sp.marginRight,
        display: expected.display.right
      }
    ];

    checks.forEach(check => {
      const tolerance = 30; // ~0.05cm tolerance
      if (!check.actual) {
        this.addResult({
          id: `margin-${check.name}`,
          category: 'Márgenes',
          rule: check.name,
          status: 'warning',
          message: `No se pudo leer el ${check.name.toLowerCase()}.`,
          expected: check.display,
          actual: 'No detectado',
          paragraphIndex: -1
        });
      } else if (Math.abs(check.actual - check.expected) > tolerance) {
        this.addResult({
          id: `margin-${check.name}`,
          category: 'Márgenes',
          rule: check.name,
          status: 'error',
          message: `El ${check.name.toLowerCase()} es ${twipsToCm(check.actual)} cm, debe ser ${check.display}.`,
          expected: check.display,
          actual: `${twipsToCm(check.actual)} cm`,
          paragraphIndex: -1
        });
      } else {
        this.addResult({
          id: `margin-${check.name}`,
          category: 'Márgenes',
          rule: check.name,
          status: 'passed',
          message: `${check.name} correcto: ${check.display}`,
          expected: check.display,
          actual: `${twipsToCm(check.actual)} cm`,
          paragraphIndex: -1
        });
      }
    });
  }

  // ============ FONT CHECK ============
  checkDefaultFont() {
    const expectedFont = formatRules.global.font.name;
    const expectedSize = formatRules.global.font.size; // half-points (24 = 12pt)
    let wrongFontParagraphs = [];
    let wrongSizeParagraphs = [];
    let totalChecked = 0;

    this.paragraphs.forEach((para, idx) => {
      if (!para.text.trim()) return;
      totalChecked++;

      para.runs.forEach(run => {
        if (!run.text.trim()) return;

        // Check font name
        const fontName = run.properties.fontName || this.defaultRunProps.fontName;
        if (fontName && fontName !== expectedFont && fontName !== 'Times New Roman') {
          wrongFontParagraphs.push({
            index: idx,
            text: para.text.substring(0, 80),
            found: fontName
          });
        }

        // Check font size
        const fontSize = run.properties.fontSize || this.defaultRunProps.fontSize;
        if (fontSize && fontSize !== expectedSize) {
          // Allow different sizes for titles (16pts=32hp, 14pts=28hp, 18pts=36hp, 11pts=22hp, 10pts=20hp)
          const allowedSizes = [20, 22, 24, 28, 32, 36];
          if (!allowedSizes.includes(fontSize)) {
            wrongSizeParagraphs.push({
              index: idx,
              text: para.text.substring(0, 80),
              found: halfPointsToPoints(fontSize)
            });
          }
        }
      });
    });

    // Font name result
    if (wrongFontParagraphs.length === 0) {
      this.addResult({
        id: 'font-name',
        category: 'Tipografía',
        rule: 'Tipo de Fuente',
        status: 'passed',
        message: `Fuente correcta: ${expectedFont}`,
        expected: expectedFont,
        actual: expectedFont,
        paragraphIndex: -1
      });
    } else {
      this.addResult({
        id: 'font-name',
        category: 'Tipografía',
        rule: 'Tipo de Fuente',
        status: 'error',
        message: `Se encontraron ${wrongFontParagraphs.length} párrafo(s) con fuente incorrecta. Se espera "${expectedFont}".`,
        expected: expectedFont,
        actual: `${wrongFontParagraphs.length} párrafos con fuente incorrecta`,
        details: wrongFontParagraphs.slice(0, 10),
        paragraphIndex: wrongFontParagraphs[0]?.index ?? -1
      });
    }

    // Font size result
    if (wrongSizeParagraphs.length === 0) {
      this.addResult({
        id: 'font-size',
        category: 'Tipografía',
        rule: 'Tamaño de Fuente',
        status: 'passed',
        message: `Tamaño de fuente correcto: ${halfPointsToPoints(expectedSize)} ptos`,
        expected: `${halfPointsToPoints(expectedSize)} ptos`,
        actual: `${halfPointsToPoints(expectedSize)} ptos`,
        paragraphIndex: -1
      });
    } else {
      this.addResult({
        id: 'font-size',
        category: 'Tipografía',
        rule: 'Tamaño de Fuente',
        status: 'error',
        message: `Se encontraron ${wrongSizeParagraphs.length} párrafo(s) con tamaño de fuente no permitido.`,
        expected: `${halfPointsToPoints(expectedSize)} ptos (general)`,
        actual: `${wrongSizeParagraphs.length} párrafos con tamaño incorrecto`,
        details: wrongSizeParagraphs.slice(0, 10),
        paragraphIndex: wrongSizeParagraphs[0]?.index ?? -1
      });
    }
  }

  // ============ STRUCTURE CHECK ============
  checkStructure() {
    const requiredSections = formatRules.structure.requiredSections;
    const fullText = this.paragraphs.map(p => p.text.toUpperCase());

    requiredSections.forEach(section => {
      if (!section.required) return;

      const found = section.keywords.some(keyword =>
        fullText.some(text => text.includes(keyword.toUpperCase()))
      );

      if (found) {
        this.addResult({
          id: `structure-${section.id}`,
          category: 'Estructura',
          rule: section.name,
          status: 'passed',
          message: `Sección "${section.name}" encontrada.`,
          expected: 'Presente',
          actual: 'Presente',
          paragraphIndex: -1
        });
      } else {
        this.addResult({
          id: `structure-${section.id}`,
          category: 'Estructura',
          rule: section.name,
          status: 'error',
          message: `Sección obligatoria "${section.name}" NO encontrada en el documento.`,
          expected: 'Presente',
          actual: 'No encontrada',
          paragraphIndex: -1
        });
      }
    });
  }

  // ============ RESUMEN CHECK ============
  checkResumen() {
    const config = formatRules.sections.resumen;
    const resumenParaIdx = this.paragraphs.findIndex(p =>
      p.text.toUpperCase().trim() === 'RESUMEN'
    );

    if (resumenParaIdx === -1) return;

    // Find the abstract/next section to delimit the resumen
    const abstractIdx = this.paragraphs.findIndex((p, i) =>
      i > resumenParaIdx && p.text.toUpperCase().trim() === 'ABSTRACT'
    );
    const endIdx = abstractIdx > 0 ? abstractIdx : this.paragraphs.length;

    // Collect resumen text
    const resumenParagraphs = this.paragraphs.slice(resumenParaIdx + 1, endIdx);
    const resumenText = resumenParagraphs.map(p => p.text).filter(t => t.trim()).join(' ');
    const wordCount = resumenText.split(/\s+/).filter(w => w.length > 0).length;

    // Check word count
    if (wordCount >= config.minWords && wordCount <= config.maxWords) {
      this.addResult({
        id: 'resumen-wordcount',
        category: 'Resumen',
        rule: 'Extensión del Resumen',
        status: 'passed',
        message: `El resumen tiene ${wordCount} palabras (rango permitido: ${config.minWords}-${config.maxWords}).`,
        expected: `${config.minWords}-${config.maxWords} palabras`,
        actual: `${wordCount} palabras`,
        paragraphIndex: resumenParaIdx
      });
    } else {
      this.addResult({
        id: 'resumen-wordcount',
        category: 'Resumen',
        rule: 'Extensión del Resumen',
        status: 'error',
        message: `El resumen tiene ${wordCount} palabras. Debe tener entre ${config.minWords} y ${config.maxWords} palabras.`,
        expected: `${config.minWords}-${config.maxWords} palabras`,
        actual: `${wordCount} palabras`,
        paragraphIndex: resumenParaIdx
      });
    }

    // Check for "Palabras clave:"
    const keywordsLine = resumenParagraphs.find(p =>
      p.text.toLowerCase().includes('palabras clave')
    );

    if (keywordsLine) {
      this.addResult({
        id: 'resumen-keywords',
        category: 'Resumen',
        rule: 'Palabras Clave',
        status: 'passed',
        message: 'Se encontró la sección de "Palabras clave" en el resumen.',
        expected: 'Presente',
        actual: 'Presente',
        paragraphIndex: resumenParaIdx
      });

      // Check if "Palabras clave:" is bold
      const kwRuns = keywordsLine.runs.filter(r =>
        r.text.toLowerCase().includes('palabras clave')
      );
      const isBold = kwRuns.some(r => r.properties.bold === true);

      if (isBold) {
        this.addResult({
          id: 'resumen-keywords-bold',
          category: 'Resumen',
          rule: 'Formato "Palabras clave:"',
          status: 'passed',
          message: '"Palabras clave:" está en negrita correctamente.',
          expected: 'Negrita',
          actual: 'Negrita',
          paragraphIndex: keywordsLine.index
        });
      } else {
        this.addResult({
          id: 'resumen-keywords-bold',
          category: 'Resumen',
          rule: 'Formato "Palabras clave:"',
          status: 'error',
          message: '"Palabras clave:" debe estar en negrita.',
          expected: 'Negrita',
          actual: 'Sin negrita',
          paragraphIndex: keywordsLine.index
        });
      }
    } else {
      this.addResult({
        id: 'resumen-keywords',
        category: 'Resumen',
        rule: 'Palabras Clave',
        status: 'error',
        message: 'No se encontró la sección "Palabras clave:" en el resumen.',
        expected: 'Presente',
        actual: 'No encontrada',
        paragraphIndex: resumenParaIdx
      });
    }
  }

  // ============ ABSTRACT CHECK ============
  checkAbstract() {
    const abstractParaIdx = this.paragraphs.findIndex(p =>
      p.text.toUpperCase().trim() === 'ABSTRACT'
    );

    if (abstractParaIdx === -1) return;

    // Find keywords
    const nextSectionIdx = this.paragraphs.findIndex((p, i) =>
      i > abstractParaIdx && (
        p.text.toUpperCase().includes('CAPÍTULO') ||
        p.text.toUpperCase().includes('CAPITULO')
      )
    );
    const endIdx = nextSectionIdx > 0 ? nextSectionIdx : this.paragraphs.length;
    const abstractParagraphs = this.paragraphs.slice(abstractParaIdx + 1, endIdx);

    const keywordsLine = abstractParagraphs.find(p =>
      p.text.toLowerCase().includes('keywords')
    );

    if (keywordsLine) {
      this.addResult({
        id: 'abstract-keywords',
        category: 'Abstract',
        rule: 'Keywords',
        status: 'passed',
        message: 'Se encontró la sección de "Keywords" en el abstract.',
        expected: 'Presente',
        actual: 'Presente',
        paragraphIndex: abstractParaIdx
      });
    } else {
      this.addResult({
        id: 'abstract-keywords',
        category: 'Abstract',
        rule: 'Keywords',
        status: 'error',
        message: 'No se encontró la sección "Keywords:" en el abstract.',
        expected: 'Presente',
        actual: 'No encontrada',
        paragraphIndex: abstractParaIdx
      });
    }
  }

  // ============ LINE SPACING CHECK ============
  checkLineSpacing() {
    const expectedSpacing = formatRules.global.lineSpacing.value;
    let wrongSpacingCount = 0;
    let totalChecked = 0;
    const wrongParagraphs = [];

    this.paragraphs.forEach((para, idx) => {
      if (!para.text.trim()) return;
      totalChecked++;

      const ls = para.properties.lineSpacing;
      if (ls && ls !== expectedSpacing) {
        // Allow 1.5 (360) for specific sections like jurados, referencias
        const allowedSpacings = [240, 360, 480];
        if (!allowedSpacings.includes(ls)) {
          wrongSpacingCount++;
          wrongParagraphs.push({
            index: idx,
            text: para.text.substring(0, 60),
            found: lineSpacingToDisplay(ls)
          });
        }
      }
    });

    if (wrongSpacingCount === 0) {
      this.addResult({
        id: 'line-spacing',
        category: 'Espaciado',
        rule: 'Interlineado',
        status: 'passed',
        message: 'Interlineado correcto en el documento.',
        expected: `${formatRules.global.lineSpacing.display}`,
        actual: 'Correcto',
        paragraphIndex: -1
      });
    } else {
      this.addResult({
        id: 'line-spacing',
        category: 'Espaciado',
        rule: 'Interlineado',
        status: 'warning',
        message: `Se encontraron ${wrongSpacingCount} párrafo(s) con interlineado no estándar.`,
        expected: formatRules.global.lineSpacing.display,
        actual: `${wrongSpacingCount} párrafos con interlineado distinto`,
        details: wrongParagraphs.slice(0, 5),
        paragraphIndex: wrongParagraphs[0]?.index ?? -1
      });
    }
  }

  // ============ PARAGRAPH FORMATTING CHECK ============
  checkParagraphFormatting() {
    let noIndentCount = 0;
    let totalContentParagraphs = 0;
    const noIndentParagraphs = [];

    // Check content paragraphs (not titles, not empty)
    this.paragraphs.forEach((para, idx) => {
      if (!para.text.trim()) return;

      // Skip title-like paragraphs (all caps, short text, centered)
      const isTitle = (
        para.text === para.text.toUpperCase() && para.text.length < 80 ||
        para.properties.alignment === 'center' ||
        para.text.startsWith('CAPÍTULO') ||
        para.text.startsWith('CAPITULO')
      );

      if (isTitle) return;

      // Skip very short paragraphs (likely labels or list items)
      if (para.text.length < 30) return;

      totalContentParagraphs++;

      // Check first line indent
      const indent = para.properties.indentFirstLine;
      if (!indent || indent === 0) {
        noIndentCount++;
        if (noIndentParagraphs.length < 5) {
          noIndentParagraphs.push({
            index: idx,
            text: para.text.substring(0, 60)
          });
        }
      }
    });

    if (totalContentParagraphs === 0) return;

    const percentWithIndent = ((totalContentParagraphs - noIndentCount) / totalContentParagraphs * 100).toFixed(0);

    if (noIndentCount === 0 || parseInt(percentWithIndent) > 70) {
      this.addResult({
        id: 'paragraph-indent',
        category: 'Formato de Párrafo',
        rule: 'Sangría de Primera Línea',
        status: noIndentCount === 0 ? 'passed' : 'warning',
        message: noIndentCount === 0
          ? 'Todos los párrafos de contenido tienen sangría de primera línea.'
          : `${noIndentCount} de ${totalContentParagraphs} párrafos sin sangría de primera línea (${percentWithIndent}% tienen sangría).`,
        expected: '1.25 cm de sangría de primera línea',
        actual: noIndentCount === 0 ? 'Correcto' : `${noIndentCount} párrafos sin sangría`,
        details: noIndentParagraphs,
        paragraphIndex: noIndentParagraphs[0]?.index ?? -1
      });
    } else {
      this.addResult({
        id: 'paragraph-indent',
        category: 'Formato de Párrafo',
        rule: 'Sangría de Primera Línea',
        status: 'error',
        message: `${noIndentCount} de ${totalContentParagraphs} párrafos no tienen sangría de primera línea de 1.25 cm.`,
        expected: '1.25 cm de sangría de primera línea',
        actual: `${noIndentCount} párrafos sin sangría (solo ${percentWithIndent}% tienen sangría)`,
        details: noIndentParagraphs,
        paragraphIndex: noIndentParagraphs[0]?.index ?? -1
      });
    }
  }

  calculateScore() {
    if (this.results.length === 0) {
      this.score = 0;
      return;
    }
    const passedWeight = this.passed.length * 1;
    const warningWeight = this.warnings.length * 0.5;
    const errorWeight = this.errors.length * 0;
    this.score = Math.round(((passedWeight + warningWeight) / this.results.length) * 100);
  }
}

module.exports = RuleEngine;
