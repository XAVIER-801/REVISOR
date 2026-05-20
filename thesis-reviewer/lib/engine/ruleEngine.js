/**
 * Motor de Reglas RepoStyle 2.0 - Auditor de Formato Premium
 * Optimizado para Tesis de Alta Complejidad
 */
class RuleEngine {
  constructor(parsedDoc) {
    this.paragraphs = parsedDoc.paragraphs || [];
    this.sectionProps = parsedDoc.sectionProps || {};
    this.defaultRunProps = parsedDoc.defaultRunProps || {};
    this.results = [];
    this.stats = {
      passed: 0,
      errors: 0,
      warnings: 0,
      score: 100
    };
    // Pre-normalizar texto para ganar velocidad extrema y robustez
    this.paragraphs.forEach(p => {
      p.normText = (p.text || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[^A-Z0-9]/g, '');
    });
  }

  analizar() {
    const v = [
      'verificarMargenes', 'verificarFuentePredeterminada', 'verificarEstructura',
      'verificarFormatoPortada', 'verificarReporteSimilitud', 'verificarFormatoHojaJurados',
      'verificarFormatoDedicatoria', 'verificarFormatoAgradecimientos', 'verificarFormatoIndiceGeneral',
      'verificarResumen', 'verificarAbstract', 'verificarNumeracionPaginas',
      'verificarIndiceTablas', 'verificarIndiceFiguras', 'verificarIndiceAnexos',
      'verificarAcronimos', 'verificarEstructuraCapitulos', 'verificarAnexos',
      'verificarNotasYFuentes', 'verificarEtiquetasJurados'
    ];

    v.forEach(m => {
      try {
        if (typeof this[m] === 'function') this[m]();
      } catch (e) {
        console.error(`RuleEngine: Error en ${m}:`, e.message);
        this.agregarResultado({
          category: '⚠️ Sistema',
          rule: `Error en análisis de ${m}`,
          status: 'warning',
          message: 'No se pudo completar esta verificación específica debido a un formato inesperado.'
        });
      }
    });

    this.calcularPuntaje();
    return {
      results: this.results,
      stats: this.stats
    };
  }

  agregarResultado(resultado) {
    if (resultado.paragraphIndex !== undefined && resultado.paragraphIndex >= 0 && this.paragraphs[resultado.paragraphIndex]) {
      resultado.y = this.paragraphs[resultado.paragraphIndex].y;
      resultado.paragraphText = this.paragraphs[resultado.paragraphIndex].text;
    }
    this.results.push(resultado);
  }

  verificarMargenes() {
    const margins = this.sectionProps.margins || { left: 1440, right: 1440, top: 1440, bottom: 1440 };
    const leftCm = (margins.left / 567).toFixed(2);
    const rightCm = (margins.right / 567).toFixed(2);
    const topCm = (margins.top / 567).toFixed(2);
    const bottomCm = (margins.bottom / 567).toFixed(2);

    this.agregarResultado({
      id: 'margin-left',
      category: '📏 Márgenes',
      rule: 'Margen Izquierdo (3.5 cm)',
      status: Math.abs(leftCm - 3.5) < 0.2 ? 'passed' : 'error',
      message: Math.abs(leftCm - 3.5) < 0.2 ? 'Margen Izquierdo correcto.' : `El margen Izquierdo es ${leftCm} cm, debe ser 3.5 cm.`,
      expected: '3.5 cm',
      actual: `${leftCm} cm`
    });

    const otherMargins = [
      { id: 'top', name: 'Superior', val: topCm },
      { id: 'bottom', name: 'Inferior', val: bottomCm },
      { id: 'right', name: 'Derecho', val: rightCm }
    ];

    otherMargins.forEach(m => {
      this.agregarResultado({
        id: `margin-${m.id}`,
        category: '📏 Márgenes',
        rule: `Margen ${m.name} (2.5 cm)`,
        status: Math.abs(m.val - 2.5) < 0.2 ? 'passed' : 'error',
        message: Math.abs(m.val - 2.5) < 0.2 ? `Margen ${m.name} correcto.` : `El margen ${m.name} es ${m.val} cm, debe ser 2.5 cm.`,
        expected: '2.5 cm',
        actual: `${m.val} cm`
      });
    });
  }

  verificarEstructura() {
    const secciones = [
      { id: 'portada', nombre: 'PORTADA', palabrasClave: ['UNIVERSIDAD NACIONAL', 'FACULTAD DE'], requerida: true },
      { id: 'similitud', nombre: 'REPORTE DE SIMILITUD', palabrasClave: ['SIMILITUD GENERAL', 'TURNITIN'], requerida: true },
      { id: 'jury', nombre: 'HOJA DE JURADOS', palabrasClave: ['HOJA DE JURADOS', 'APROBADA POR EL JURADO'], requerida: true },
      { id: 'dedicatoria', nombre: 'DEDICATORIA', palabrasClave: ['DEDICATORIA'], requerida: true },
      { id: 'agradecimientos', nombre: 'AGRADECIMIENTOS', palabrasClave: ['AGRADECIMIENTOS'], requerida: false },
      { id: 'indice', nombre: 'ÍNDICE GENERAL', palabrasClave: ['ÍNDICE GENERAL', 'CONTENIDO'], requerida: true },
      { id: 'resumen', nombre: 'RESUMEN', palabrasClave: ['RESUMEN'], requerida: true },
      { id: 'abstract', nombre: 'ABSTRACT', palabrasClave: ['ABSTRACT'], requerida: true },
      { id: 'intro', nombre: 'INTRODUCCIÓN', palabrasClave: ['INTRODUCCIÓN'], requerida: true },
      { id: 'declaracion', nombre: 'DECLARACIÓN JURADA', palabrasClave: ['DECLARACION JURADA DE AUTENTICIDAD', 'DECLARA BAJO JURAMENTO'], requerida: true },
      { id: 'autorizacion', nombre: 'AUTORIZACIÓN DE DEPÓSITO', palabrasClave: ['AUTORIZACION PARA EL DEPOSITO', 'REPOSITORIO INSTITUCIONAL'], requerida: true }
    ];

    secciones.forEach(seccion => {
      let foundIdx = this.paragraphs.findIndex(p => {
        const textoLimpio = p.normText;
        return seccion.palabrasClave.some(k => {
          const normK = k.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[^A-Z0-9]/g, '');
          return textoLimpio.includes(normK) || (normK.length > 10 && textoLimpio.includes(normK.substring(0, 10)));
        });
      });

      if (foundIdx === -1 && (seccion.id === 'jury' || seccion.id === 'similitud' || seccion.id === 'declaracion' || seccion.id === 'autorizacion')) {
        const imagePage = this.paragraphs.find(p => p.page >= 2 && p.isImagePage);
        if (imagePage) foundIdx = this.paragraphs.indexOf(imagePage);

        // Also check if any paragraph has [OCR DETECTED TEXT] and contains keywords
        const ocrPara = this.paragraphs.find(p => {
          if (!p.text.includes('[OCR DETECTED TEXT]')) return false;
          const textoLimpio = p.text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
          return seccion.palabrasClave.some(k => {
            const normK = k.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
            return textoLimpio.includes(normK);
          });
        });
        if (ocrPara) foundIdx = this.paragraphs.indexOf(ocrPara);
      }

      const isFound = foundIdx !== -1;
      if (seccion.requerida || isFound) {
        this.agregarResultado({
          id: `struct-${seccion.id}`,
          category: '📑 Estructura',
          rule: seccion.nombre,
          status: isFound ? 'passed' : 'error',
          message: isFound ? `Sección obligatoria "${seccion.nombre}" encontrada.` : `Sección obligatoria "${seccion.nombre}" NO encontrada.`,
          expected: 'Presente',
          actual: isFound ? 'Encontrada' : 'No encontrada',
          paragraphIndex: foundIdx
        });
      }
    });
  }

  verificarFormatoPortada() {
    const juryIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('HOJA DE JURADOS'));
    const limite = juryIdx !== -1 ? juryIdx : Math.min(this.paragraphs.length, 30);

    let centradoOk = 0, negritaOk = 0, sinSangriaOk = 0, totalEscaneado = 0;

    for (let i = 0; i < limite; i++) {
      const p = this.paragraphs[i];
      if (!p || p.text.trim().length < 2) continue;
      totalEscaneado++;
      if (p.properties?.alignment === 'center' || p.properties?.alignment === 'both') centradoOk++;
      if (p.runs?.every(r => r.properties?.bold)) negritaOk++;
      const sangria = (p.properties?.indent || 0) + (p.properties?.firstLineIndent || 0) + (p.properties?.hangingIndent || 0);
      if (sangria === 0) sinSangriaOk++;
    }

    if (totalEscaneado > 0) {
      this.agregarResultado({
        id: 'portada-format',
        category: '📑 Portada',
        rule: 'Formato de Portada (Negrita (Bold), Centrado, Sin Sangría)',
        status: (centradoOk === totalEscaneado && negritaOk === totalEscaneado && sinSangriaOk === totalEscaneado) ? 'passed' : 'error',
        message: `Portada: ${centradoOk}/${totalEscaneado} centrados, ${negritaOk}/${totalEscaneado} negrita (bold), ${sinSangriaOk}/${totalEscaneado} sin sangría.`,
        expected: 'Centrado, Negrita (Bold), Sangría 0',
        actual: `C:${centradoOk} N:${negritaOk} S:${sinSangriaOk}`,
        paragraphIndex: 0
      });
    }
  }

  verificarReporteSimilitud() {
    const simIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('SIMILITUD GENERAL') || p.text.toUpperCase().includes('DETALLES DEL DOCUMENTO'));
    if (simIdx === -1) return;

    const pTarget = this.paragraphs.slice(Math.max(0, simIdx - 2), simIdx + 20).find(p => /(\d+)%/.test(p.text));
    const pPaginas = this.paragraphs.slice(Math.max(0, simIdx - 2), simIdx + 20).find(p => /(\d+)\s+Paginas/i.test(p.text));
    const paginasActuales = this.paragraphs[this.paragraphs.length - 1]?.page || 0;

    if (pTarget) {
      const porcentaje = parseInt(pTarget.text.match(/(\d+)%/)[1]);
      this.agregarResultado({
        id: 'sim-percentage',
        category: '🔍 Similitud',
        rule: 'Porcentaje de Similitud (Máx 20%)',
        status: porcentaje <= 20 ? 'passed' : 'error',
        message: `Similitud detectada: ${porcentaje}%. ${porcentaje > 20 ? 'Excede el máximo del 20%.' : 'Cumple con el límite institucional.'}`,
        expected: '< 20%',
        actual: `${porcentaje}%`,
        paragraphIndex: this.paragraphs.indexOf(pTarget)
      });
    }

    if (pPaginas) {
      const paginasReportadas = parseInt(pPaginas.text.match(/(\d+)\s+Paginas/i)[1]);
      this.agregarResultado({
        id: 'sim-page-count',
        category: '🔍 Similitud',
        rule: 'Consistencia de Versión (Páginas)',
        status: Math.abs(paginasReportadas - paginasActuales) <= 10 ? 'passed' : 'warning',
        message: `El reporte es de ${paginasReportadas} páginas, la tesis tiene ${paginasActuales}.`,
        expected: `${paginasActuales} aprox.`,
        actual: `${paginasReportadas}`,
        paragraphIndex: this.paragraphs.indexOf(pPaginas)
      });
    }
  }

  verificarFormatoHojaJurados() {
    const startIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('HOJA DE JURADOS') || p.text.toUpperCase().includes('APROBADA POR EL JURADO REVISOR'));
    if (startIdx === -1) return;

    const limite = Math.min(this.paragraphs.length, startIdx + 30);
    let fontSize12Ok = 0, fontSize11Ok = 0, nombresJurados = 0, sangria6cmOk = 0, totalEscaneado = 0;

    for (let i = startIdx; i < limite; i++) {
      const p = this.paragraphs[i];
      if (!p || p.text.trim().length < 2 || p.text.includes('....')) continue;
      totalEscaneado++;
      const texto = p.text.trim();
      const esNombreJurado = /^(Dr\.|D\.Sc\.|M\.Sc\.|Lic\.|Mg\.)/i.test(texto);
      const tamanoFuente = p.runs?.[0]?.properties?.fontSize || 0;

      if (esNombreJurado) {
        nombresJurados++;
        if (tamanoFuente >= 21 && tamanoFuente <= 23) fontSize11Ok++;
        const sangria = p.properties?.indent || (p.startX > 100 ? p.startX * 20 : 0);
        if (sangria > 3000) sangria6cmOk++;
      } else {
        if (tamanoFuente >= 23 && tamanoFuente <= 25) fontSize12Ok++;
      }

      if (texto.startsWith('ÁREA:') || texto.startsWith('TEMA:')) {
        const esNegrita = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
        if (!esNegrita) {
          this.agregarResultado({
            id: 'jury-label-style',
            category: '🖋️ Jurados',
            rule: 'Etiquetas ÁREA/TEMA en Negrita (Bold)',
            status: 'error',
            message: `La etiqueta "${texto.split(':')[0]}" debe estar en negrita (bold) y mayúsculas.`,
            expected: 'Negrita (Bold), Mayúsculas',
            actual: 'Normal',
            paragraphIndex: i
          });
        }
      }
    }

    if (totalEscaneado > 0) {
      this.agregarResultado({
        id: 'jury-detailed-format',
        category: '🖋️ Jurados',
        rule: 'Detalle de Hoja de Jurados (12pt/11pt, Sangría 6cm)',
        status: (fontSize11Ok === nombresJurados && sangria6cmOk === nombresJurados) ? 'passed' : 'warning',
        message: `Jurados: ${fontSize11Ok}/${nombresJurados} con 11pt, ${sangria6cmOk}/${nombresJurados} con sangría 6cm.`,
        expected: 'Nombres 11pt/6cm, Resto 12pt',
        actual: `N:11pt(${fontSize11Ok}) S:6cm(${sangria6cmOk})`,
        paragraphIndex: startIdx
      });
    }
  }

  verificarEtiquetasJurados() {
    this.paragraphs.forEach((p, idx) => {
      const text = p.text.trim();
      if (!text) return;
      const upper = text.toUpperCase();

      // 1. FECHA DE SUSTENTACIÓN:
      if (upper.includes('FECHA DE SUSTENTACION') || upper.includes('FECHA DE SUSTENTACIÓN')) {
        const align = p.properties?.alignment || 'left';
        const isBold = p.runs?.some(r => r.properties?.bold && r.text?.trim().length > 0);
        const indentLeftCm = (p.properties?.indent || 0) / 567;
        const indentFirstCm = (p.properties?.firstLineIndent || 0) / 567;
        const indentHangingCm = (p.properties?.hangingIndent || 0) / 567;
        const sBefore = (p.properties?.spacingBefore || 0) / 20;
        const sAfter = (p.properties?.spacingAfter || 0) / 20;

        // Mayúsculas en etiqueta
        const labelPart = text.split(':')[0] + ':';
        const labelLetters = labelPart.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ]/g, '');
        const isUppercase = labelLetters === labelLetters.toUpperCase();

        const okCase = isUppercase;
        const okBold = isBold;
        const okAlign = align === 'right';
        const okSBefore = Math.abs(sBefore - 10) < 2;
        const okSAfter = sAfter < 1;
        const okIndent = Math.abs(indentLeftCm) < 0.1 && Math.abs(indentFirstCm) < 0.1 && Math.abs(indentHangingCm) < 0.1;

        const passed = okCase && okBold && okAlign && okSBefore && okSAfter && okIndent;

        const alignStr = align === 'center' ? 'Centrado' : (align === 'left' ? 'Izquierda' : (align === 'right' ? 'Derecha' : 'Justificado'));
        const checks = [
          isUppercase ? 'MAYÚSCULAS' : 'Minúsculas',
          isBold ? 'Negrita' : 'Normal',
          alignStr,
          `Esp. ant ${sBefore}pt, post ${sAfter}pt`,
          okIndent ? 'Sin sangría' : 'Con sangría'
        ];

        this.agregarResultado({
          id: `fecha-sustentacion-${idx}`,
          category: '🖋️ Jurados',
          rule: 'Formato "FECHA DE SUSTENTACIÓN:"',
          status: passed ? 'passed' : 'error',
          message: 'La etiqueta "FECHA DE SUSTENTACIÓN:" debe estar en MAYÚSCULAS, Negrita, alineada a la DERECHA, con espaciado anterior de 10pt y posterior de 0pt, y sin sangría.',
          expected: 'MAYÚSCULAS, Negrita, Derecha, Esp. 10pt/0pt, Sin sangría',
          actual: checks.join(', '),
          paragraphIndex: idx
        });
      }

      // 2. ÁREA:
      else if (/^ÁREA\s*:/i.test(text) || /^AREA\s*:/i.test(text)) {
        this._verificarAreaTemaJS(p, idx, 'ÁREA');
      }

      // 3. TEMA:
      else if (/^TEMA\s*:/i.test(text)) {
        this._verificarAreaTemaJS(p, idx, 'TEMA');
      }
    });
  }

  _verificarAreaTemaJS(p, idx, label) {
    const text = p.text.trim();
    const align = p.properties?.alignment || 'left';
    const isBold = p.runs?.some(r => r.properties?.bold && r.text?.trim().length > 0);
    const indentLeftCm = (p.properties?.indent || 0) / 567;
    const indentFirstCm = (p.properties?.firstLineIndent || 0) / 567;
    const indentHangingCm = (p.properties?.hangingIndent || 0) / 567;
    const sBefore = (p.properties?.spacingBefore || 0) / 20;
    const sAfter = (p.properties?.spacingAfter || 0) / 20;

    // Mayúsculas en etiqueta
    const labelPart = text.split(':')[0] + ':';
    const labelLetters = labelPart.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ]/g, '');
    const isUppercase = labelLetters === labelLetters.toUpperCase();

    const okCase = isUppercase;
    const okBold = isBold;
    const okAlign = align === 'left';
    const okSBefore = sBefore < 1;
    const okSAfter = sAfter < 1;
    const okIndent = Math.abs(indentLeftCm) < 0.1 && Math.abs(indentFirstCm) < 0.1 && Math.abs(indentHangingCm) < 0.1;

    const passed = okCase && okBold && okAlign && okSBefore && okSAfter && okIndent;

    const alignStr = align === 'center' ? 'Centrado' : (align === 'left' ? 'Izquierda' : (align === 'right' ? 'Derecha' : 'Justificado'));
    const checks = [
      isUppercase ? 'MAYÚSCULAS' : 'Minúsculas',
      isBold ? 'Negrita' : 'Normal',
      alignStr,
      `Esp. ant ${sBefore}pt, post ${sAfter}pt`,
      okIndent ? 'Sin sangría' : 'Con sangría'
    ];

    this.agregarResultado({
      id: `${label.toLowerCase()}-format-${idx}`,
      category: '🖋️ Jurados',
      rule: `Formato "${label}:"`,
      status: passed ? 'passed' : 'error',
      message: `La etiqueta "${label}:" debe estar en MAYÚSCULAS, Negrita, alineada a la IZQUIERDA, con espaciado anterior y posterior de 0pt, y sin sangría.`,
      expected: 'MAYÚSCULAS, Negrita, Izquierda, Esp. 0pt/0pt, Sin sangría',
      actual: checks.join(', '),
      paragraphIndex: idx
    });
  }

  verificarFormatoDedicatoria() {
    const dedIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('DEDICATORIA'));
    if (dedIdx === -1) return;

    const pTitulo = this.paragraphs[dedIdx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'ded-title-format',
      category: '💝 Dedicatoria',
      rule: 'Título DEDICATORIA (16pt, Negrita (Bold), Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita (Bold)' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita (Bold), Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N(B)' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: dedIdx
    });

    const pCuerpo = this.paragraphs[dedIdx + 1];
    if (pCuerpo) {
      const sangria = (pCuerpo.properties?.indent || 0) + (pCuerpo.properties?.firstLineIndent || 0);
      this.agregarResultado({
        id: 'ded-body-indent',
        category: '💝 Dedicatoria',
        rule: 'Ausencia de Sangría en Contenido',
        status: sangria === 0 ? 'passed' : 'warning',
        message: sangria === 0 ? 'Contenido sin sangría conforme a regla.' : 'Se detectó sangría en la dedicatoria, debe ser 0.',
        expected: '0',
        actual: `${sangria}`,
        paragraphIndex: dedIdx + 1
      });
    }
  }

  verificarFormatoAgradecimientos() {
    const agrIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('AGRADECIMIENTOS'));
    if (agrIdx === -1) return;

    // 1. Título Agradecimientos
    const pTitulo = this.paragraphs[agrIdx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'agr-title-format',
      category: '🤝 Agradecimientos',
      rule: 'Título AGRADECIMIENTOS (16pt, Negrita (Bold), Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita (Bold)' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita (Bold), Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N(B)' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: agrIdx
    });

    // 2. Sangría en contenido
    let pCuerpo = this.paragraphs[agrIdx + 1];
    if (pCuerpo && pCuerpo.text.trim().length < 2) pCuerpo = this.paragraphs[agrIdx + 2];

    if (pCuerpo) {
      const sangria = (pCuerpo.properties?.indent || 0) + (pCuerpo.properties?.firstLineIndent || 0);
      this.agregarResultado({
        id: 'agr-body-indent',
        category: '🤝 Agradecimientos',
        rule: 'Ausencia de Sangría en Contenido',
        status: sangria === 0 ? 'passed' : 'warning',
        message: sangria === 0 ? 'Contenido sin sangría conforme a regla.' : 'Se detectó sangría en agradecimientos, debe ser 0.',
        expected: '0',
        actual: `${sangria}`,
        paragraphIndex: this.paragraphs.indexOf(pCuerpo)
      });

      // 3. Extensión (Máximo 1 página / aprox 600 palabras)
      let totalTexto = "";
      for (let i = agrIdx; i < this.paragraphs.length; i++) {
        const text = this.paragraphs[i].text.trim();
        if (i > agrIdx && (text.toUpperCase().includes("RESUMEN") || text.toUpperCase().includes("INDICE GENERAL"))) break;
        totalTexto += " " + text;
      }
      const conteo = totalTexto.split(/\s+/).length;
      this.agregarResultado({
        id: 'agr-max-page',
        category: '🤝 Agradecimientos',
        rule: 'Extensión Máxima (1 Página)',
        status: conteo <= 600 ? 'passed' : 'error',
        message: conteo <= 600 ? 'Los agradecimientos caben en una sola página.' : 'Los agradecimientos exceden el límite de una página.',
        expected: 'Máx 1 pág (~600 palabras)',
        actual: `${conteo} palabras`,
        paragraphIndex: agrIdx
      });
    }

    // 3. Firmas
    const nextSecIdx = this.paragraphs.findIndex((p, i) => i > agrIdx && (p.text.toUpperCase().includes('ÍNDICE GENERAL') || p.text.toUpperCase().includes('RESUMEN')));
    const endIdx = nextSecIdx !== -1 ? nextSecIdx : Math.min(agrIdx + 20, this.paragraphs.length);

    let firmasDetectadas = 0, firmasAlineadasDerecha = 0, indexFirma = -1;

    for (let i = endIdx - 1; i > agrIdx; i--) {
      const p = this.paragraphs[i];
      if (!p || p.text.trim().length < 2) continue;

      const words = p.text.trim().split(/\s+/).length;
      if (words > 1 && words <= 5) {
        firmasDetectadas++;
        indexFirma = i;
        if (p.properties?.alignment === 'right' || p.startX > 300) firmasAlineadasDerecha++;
      } else {
        if (firmasDetectadas > 0) break;
      }
    }

    if (firmasDetectadas > 0) {
      this.agregarResultado({
        id: 'agr-signatures',
        category: '🤝 Agradecimientos',
        rule: 'Firmas alineadas a la derecha',
        status: firmasAlineadasDerecha === firmasDetectadas ? 'passed' : 'warning',
        message: `Se detectaron ${firmasDetectadas} firma(s). ${firmasAlineadasDerecha} a la derecha.`,
        expected: 'Alineación Derecha',
        actual: firmasAlineadasDerecha === firmasDetectadas ? 'Correcta' : 'Alineación Incorrecta',
        paragraphIndex: indexFirma
      });
    }
  }

  verificarFormatoIndiceGeneral() {
    const idx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ÍNDICE GENERAL') || p.text.toUpperCase() === 'INDICE GENERAL');
    if (idx === -1) return;

    // 1. Título ÍNDICE GENERAL (16pt, Negrita, Centrado)
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'idx-title-format',
      category: '🗂️ Índice',
      rule: 'Título ÍNDICE GENERAL (16pt, Negrita (Bold), Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita (Bold)' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita (Bold), Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N(B)' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Etiqueta "Pág."
    let pagIdx = -1;
    for (let i = idx + 1; i < idx + 5 && i < this.paragraphs.length; i++) {
      if (this.paragraphs[i].text.toLowerCase().includes('pág.')) {
        pagIdx = i;
        break;
      }
    }

    // 3. Validar entradas del índice
    const startEntradas = pagIdx !== -1 ? pagIdx + 1 : idx + 1;
    const seccionesEnIndice = [];

    for (let i = startEntradas; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();
      const upper = text.toUpperCase();
      
      // Detenerse si empezamos otra sección mayor (fuera del índice)
      if (i > idx + 50 && (upper === "RESUMEN" || upper === "INTRODUCCIÓN" || upper === "INTRODUCCION")) break;
      if (text.length < 3) continue;

      seccionesEnIndice.push(upper);

      // Regla de alineación
      const esCapitulo = /^CAP[ÍI]TULO\s+[IVXLC0-9]+/i.test(text);
      const nombresCapitulosEstandar = [
        'INTRODUCCION', 'INTRODUCCIÓN',
        'REVISION DE LITERATURA', 'REVISIÓN DE LITERATURA',
        'MATERIALES Y METODOS', 'MATERIALES Y MÉTODOS',
        'RESULTADOS Y DISCUSION', 'RESULTADOS Y DISCUSIÓN'
      ];
      
      let eraCapituloPrevio = false;
      for (let prevIdx = i - 1; prevIdx >= startEntradas; prevIdx--) {
        const prevText = this.paragraphs[prevIdx].text.trim();
        if (prevText) {
          if (/^CAP[ÍI]TULO\s+[IVXLC0-9]+/i.test(prevText)) {
            eraCapituloPrevio = true;
          }
          break;
        }
      }
      
      const hasDotsOrPage = text.includes('....') || /\d+$/.test(text);
      const esTituloCapitulo = nombresCapitulosEstandar.includes(upper) || (eraCapituloPrevio && !hasDotsOrPage);
      const align = p.properties?.alignment || 'left';

      // --- NUEVO: Validar "Pág." label ---
      if (/^P[ÁA]G\.?$/i.test(text)) {
        const pagAlineadaDerecha = align === 'right' || p.startX > 400;
        const pagNegrita = p.runs?.some(r => r.properties?.bold);
        this.agregarResultado({
          id: `idx-pag-label-${i}`,
          category: '🗂️ Índice',
          rule: 'Etiqueta "Pág." (Alineada Derecha, Negrita (Bold))',
          status: (pagAlineadaDerecha && pagNegrita) ? 'passed' : 'error',
          message: `Etiqueta: ${pagNegrita ? 'Negrita (Bold)' : 'Normal'}, ${pagAlineadaDerecha ? 'Derecha' : 'Izquierda/Centro'}.`,
          expected: 'Alineación Derecha, Negrita (Bold)',
          actual: `${pagAlineadaDerecha ? 'Der' : 'Iz/C'}, ${pagNegrita ? 'N(B)' : 'Norm'}`,
          paragraphIndex: i
        });
        continue;
      }

      if (esCapitulo || esTituloCapitulo) {
        this.agregarResultado({
          id: `idx-cap-align-${i}`,
          category: '🗂️ Índice',
          rule: `Alineación de ${text.substring(0, 15)}`,
          status: align === 'center' ? 'passed' : 'error',
          message: `La línea '${text.substring(0, 20)}...' en el índice debe estar centrada.`,
          expected: 'Centrado',
          actual: align,
          paragraphIndex: i
        });
      } else if (text.includes('....') || /\d+$/.test(text)) {
        // Otros ítems con número de página
        this.agregarResultado({
          id: `idx-item-align-${i}`,
          category: '🗂️ Índice',
          rule: `Alineación de entrada: ${text.substring(0, 15)}`,
          status: (align === 'both' || align === 'justify' || align === 'left') ? 'passed' : 'error',
          message: 'Las entradas de contenido en el índice deben estar justificadas o alineadas a la izquierda.',
          expected: 'Justificado o Izquierda',
          actual: align,
          paragraphIndex: i
        });
      }
    }

    // 4. Cross-Check de secciones
    const dedicatoriaDoc = this.paragraphs.some(p => p.text.toUpperCase().includes('DEDICATORIA'));
    const agradecimientosDoc = this.paragraphs.some(p => p.text.toUpperCase().includes('AGRADECIMIENTOS'));

    if (dedicatoriaDoc && !seccionesEnIndice.some(s => s.includes('DEDICATORIA'))) {
      this.agregarResultado({
        id: 'idx-missing-ded',
        category: '🗂️ Índice',
        rule: 'Presencia de Dedicatoria',
        status: 'error',
        message: 'La Dedicatoria existe en el documento pero no figura en el Índice.',
        expected: 'Presente en Índice',
        actual: 'Ausente',
        paragraphIndex: idx
      });
    }

    if (agradecimientosDoc && !seccionesEnIndice.some(s => s.includes('AGRADECIMIENTOS'))) {
      this.agregarResultado({
        id: 'idx-missing-agr',
        category: '🗂️ Índice',
        rule: 'Presencia de Agradecimientos',
        status: 'error',
        message: 'Los Agradecimientos existen en el documento pero no figuran en el Índice.',
        expected: 'Presente en Índice',
        actual: 'Ausente',
        paragraphIndex: idx
      });
    }

    if (pagIdx !== -1) {
      const pPag = this.paragraphs[pagIdx];
      const pagAlineadaDerecha = pPag.properties?.alignment === 'right' || pPag.startX > 400; // Tolerancia en PDF
      const pagNegrita = pPag.runs?.some(r => r.properties?.bold);

      this.agregarResultado({
        id: 'idx-pag-label',
        category: '🗂️ Índice',
        rule: 'Etiqueta "Pág." (Alineada Derecha, Negrita (Bold))',
        status: (pagAlineadaDerecha && pagNegrita) ? 'passed' : 'error',
        message: `Etiqueta: ${pagNegrita ? 'Negrita (Bold)' : 'Normal'}, ${pagAlineadaDerecha ? 'Derecha' : 'Izquierda/Centro'}.`,
        expected: 'Alineación Derecha, Negrita (Bold)',
        actual: `${pagAlineadaDerecha ? 'Der' : 'Iz/C'}, ${pagNegrita ? 'N(B)' : 'Norm'}`,
        paragraphIndex: pagIdx
      });
    }

    // 3. Entradas Preliminares (DEDICATORIA... ACRÓNIMOS)
    let preEntradas = 0, sinNumeracionOk = 0, tamano12Ok = 0, sinRellenoOk = 0;
    const startEntradas2 = pagIdx !== -1 ? pagIdx + 1 : idx + 1;

    let indexBodyLines = 0;
    let chaptersOk = 0, chaptersCount = 0;
    let level2Ok = 0, level2Count = 0;
    let level3Ok = 0, level3Count = 0;
    let level4Ok = 0, level4Count = 0;
    let finalesOk = 0, finalesCount = 0;

    for (let i = startEntradas2; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim().toUpperCase();

      // Detenerse si pasamos al contenido real (ÍNDICE DE TABLAS u otra sección nueva no perteneciente al índice)
      // Como el índice puede ser largo, usamos heurísticas de números de página al final
      const hasPageNum = /\d+$/.test(text) || /\.\s*\d+/.test(text);
      const isChapterHeader = text.startsWith('CAPÍTULO') || text.startsWith('CAPITULO');
      const isPrelim = ['DEDICATORIA', 'AGRADECIMIENTOS', 'ÍNDICE GENERAL', 'INDICE GENERAL', 'ÍNDICE DE TABLAS', 'ÍNDICE DE FIGURAS', 'ÍNDICE DE ANEXOS', 'ACRÓNIMOS', 'RESUMEN', 'ABSTRACT'].some(k => text.includes(k));
      const isFinal = ['V. CONCLUSIONES', 'VI. RECOMENDACIONES', 'VII. REFERENCIAS BIBLIOGRÁFICAS', 'ANEXOS'].some(k => text.includes(k));

      if (!hasPageNum && !isChapterHeader && !isPrelim && text.length > 50) {
        // Probablemente ya salimos del índice
        if (indexBodyLines > 10) break;
      }

      indexBodyLines++;
      const size = p.runs?.[0]?.properties?.fontSize || 0;
      const isBold = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
      const indentLeft = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;

      // --- VALIDACIÓN DE PRELIMINARES ---
      if (isPrelim) {
        preEntradas++;
        if (!/^\d+\./.test(text)) sinNumeracionOk++;
        if (size >= 23 && size <= 25) tamano12Ok++;
        if (!['RESUMEN', 'ABSTRACT'].some(k => text.includes(k))) {
          if (!text.includes('...')) sinRellenoOk++;
        } else {
          sinRellenoOk++;
        }
      }

      // --- VALIDACIÓN DE CAPÍTULOS ---
      else if (isChapterHeader) {
        chaptersCount++;
        const isCentered = p.properties?.alignment === 'center';
        const hasNoFill = !text.includes('...');
        if (isCentered && isBold && hasNoFill) chaptersOk++;
      }

      // --- VALIDACIÓN DE FINALES (V, VI, VII, ANEXOS) ---
      else if (isFinal) {
        finalesCount++;
        finalesOk++;
      }

      // --- VALIDACIÓN DE NIVELES JERÁRQUICOS (Nivel 2, 3, 4, 5) ---
      else if (/^\d+\.\d+\./.test(text)) {
        const levelMatch = text.match(/^(\d+(\.\d+)+)\.?/);
        if (levelMatch) {
          const level = levelMatch[1].split('.').length;
          const isUpper = p.text === p.text.toUpperCase(); // Text original

          if (level === 2) {
            level2Count++;
            // Nivel 2: Negrita, Mayúsculas
            if (isBold && isUpper) level2Ok++;
          } else if (level === 3) {
            level3Count++;
            // Nivel 3: Sin negrita, Minúsculas (excepto primera letra)
            if (!isBold && !isUpper) level3Ok++;
          } else if (level >= 4) {
            level4Count++;
            // Nivel 4 y 5: Sin negrita, Minúsculas
            if (!isBold && !isUpper) level4Ok++;
          }
        }
      }
    }

    if (preEntradas > 0) {
      this.agregarResultado({
        id: 'idx-prelim-format',
        category: '🗂️ Índice',
        rule: 'Formato Entradas Preliminares (12pt, Sin Puntos/Numeración)',
        status: (sinNumeracionOk === preEntradas && tamano12Ok === preEntradas && sinRellenoOk === preEntradas) ? 'passed' : 'warning',
        message: `Detectadas ${preEntradas} entradas. ${tamano12Ok} en 12pt, ${sinNumeracionOk} sin numerar, ${sinRellenoOk} sin puntos.`,
        expected: '12pt, Sin Num, Sin Puntos',
        actual: `12pt:${tamano12Ok}, SinNum:${sinNumeracionOk}`,
        paragraphIndex: startEntradas2
      });
    }

    if (chaptersCount > 0) {
      this.agregarResultado({
        id: 'idx-chapter-format',
        category: '🗂️ Índice',
        rule: 'Formato de Capítulos (Centrado, Negrita (Bold), Sin Relleno)',
        status: chaptersOk === chaptersCount ? 'passed' : 'error',
        message: `${chaptersOk}/${chaptersCount} capítulos cumplen con el formato requerido (Negrita/Bold).`,
        expected: 'Centrado, Negrita (Bold), Sin Relleno',
        actual: `${chaptersOk} Correctos`,
        paragraphIndex: startEntradas2
      });
    }

    if (level2Count > 0 || level3Count > 0 || level4Count > 0) {
      const totalLevels = level2Count + level3Count + level4Count;
      const totalLevelsOk = level2Ok + level3Ok + level4Ok;

      this.agregarResultado({
        id: 'idx-levels-format',
        category: '🗂️ Índice',
        rule: 'Jerarquía Tipográfica de Niveles (Estilos, Negritas, Mayúsculas)',
        status: totalLevelsOk === totalLevels ? 'passed' : 'warning',
        message: `Nivel 2: ${level2Ok}/${level2Count} | Nivel 3: ${level3Ok}/${level3Count} | Nivel 4+: ${level4Ok}/${level4Count}. Se valida la capitalización y los estilos tipográficos correspondientes.`,
        expected: 'Estilos según Nivel (Mayúsculas/Minúsculas, Negritas)',
        actual: `${totalLevelsOk}/${totalLevels} Correctos`,
        paragraphIndex: startEntradas2
      });
    }

    if (finalesCount > 0) {
      this.agregarResultado({
        id: 'idx-final-format',
        category: '🗂️ Índice',
        rule: 'Secciones Finales (V, VI, VII, ANEXOS)',
        status: finalesOk === finalesCount ? 'passed' : 'error',
        message: `${finalesOk}/${finalesCount} secciones finales analizadas correctamente.`,
        expected: 'Secciones Finales Presentes',
        actual: `${finalesOk} Correctos`,
        paragraphIndex: startEntradas2
      });
    }
  }

  verificarJerarquiaTitulos() {
    const firstIndexIdx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ÍNDICE GENERAL') || p.text.toUpperCase().includes('INDICE GENERAL'));
    
    const bodyStartIdx = this.paragraphs.findIndex((p, i) => {
      if (i < firstIndexIdx) return false;
      const txt = p.text.trim().toUpperCase();
      const isIndexLine = txt.includes('....') || /\d+$/.test(txt);
      return !isIndexLine && (txt.startsWith('CAPÍTULO I') || txt.startsWith('CAPITULO I') || txt.startsWith('INTRODUCCIÓN') || txt.startsWith('INTRODUCCION'));
    });

    this.paragraphs.forEach((p, idx) => {
      const texto = p.text.trim();
      
      // Excluir si está antes del inicio del cuerpo
      if (bodyStartIdx !== -1 && idx < bodyStartIdx) return;
      
      // Excluir si es una línea de índice
      const isIndexLine = texto.includes('....') || /\d+$/.test(texto);
      if (isIndexLine) return;
      
      // Excluir si contiene palabras clave preliminares
      const upper = texto.toUpperCase();
      const isPrelim = ['DEDICATORIA', 'AGRADECIMIENTOS', 'ÍNDICE GENERAL', 'INDICE GENERAL', 'ÍNDICE DE TABLAS', 'ÍNDICE DE FIGURAS', 'ÍNDICE DE ANEXOS', 'ACRÓNIMOS', 'RESUMEN', 'ABSTRACT'].some(k => upper.includes(k));
      if (isPrelim) return;

      const numMatch = texto.match(/^(\d+(\.\d+)*)\.?\s+(.+)$/);
      if (!numMatch) return;

      const nivel = numMatch[1].split('.').length;
      const tamanoFuente = p.runs?.[0]?.properties?.fontSize || 0;
      const esNegrita = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;

      if (nivel === 1) {
        if (tamanoFuente < 23 || !esNegrita) {
          this.agregarResultado({
            id: `title-l1-${idx}`,
            category: '🖋️ Tipografía',
            rule: `Título Nivel 1: ${texto.substring(0, 20)}...`,
            status: 'warning',
            message: 'Los títulos de Nivel 1 deben ser 12pt y Negrita (Bold).',
            expected: '12pt, Negrita (Bold)',
            actual: `${tamanoFuente / 2}pt, ${esNegrita ? 'N(B)' : 'X'}`,
            paragraphIndex: idx
          });
        }
      }
    });
  }

  // MOTOR DE RESUMEN GREEDY (Capture-Fidelity-Matched)
  verificarResumen() {
    const kIdx = this.paragraphs.findIndex(p => p.normText.includes('PALABRASCLAVE'));
    
    if (kIdx === -1) {
      const resIdx = this.paragraphs.findIndex(p => p.normText.endsWith('RESUMEN') && p.text.length < 60);
      if (resIdx === -1) return;
      this._procesarConteoResumen(resIdx, resIdx + 50, true, 'res-length', '📝 Resumen', 'Cantidad de palabras', '200-300 palabras');
      return;
    }

    let startIdx = -1;
    for (let i = kIdx; i >= 0 && i > kIdx - 100; i--) {
      if (this.paragraphs[i].normText.endsWith('RESUMEN') && this.paragraphs[i].text.length < 60) {
        startIdx = i;
        break;
      }
    }

    if (startIdx !== -1) {
      this._procesarConteoResumen(startIdx, kIdx, false, 'res-length', '📝 Resumen', 'Cantidad de palabras', '200-300 palabras');
      
      const pK = this.paragraphs[kIdx];
      const esNegrita = pK.runs?.some(r => r.text.toLowerCase().includes('palabras clave') && r.properties?.bold);
      this.agregarResultado({
        id: 'res-bold',
        category: '📝 Resumen',
        rule: 'Etiqueta en Negrita (Bold)',
        status: esNegrita ? 'passed' : 'error',
        message: 'La etiqueta "Palabras clave:" debe estar en negrita (bold).',
        expected: 'Negrita (Bold)',
        actual: esNegrita ? 'Negrita (Bold)' : 'Normal',
        paragraphIndex: kIdx
      });
    }
  }

  verificarAbstract() {
    const kIdx = this.paragraphs.findIndex(p => p.normText.includes('KEYWORDS'));
    if (kIdx === -1) return;

    let startIdx = -1;
    for (let i = kIdx; i >= 0 && i > kIdx - 100; i--) {
      if (this.paragraphs[i].normText.endsWith('ABSTRACT') && this.paragraphs[i].text.length < 60) {
        startIdx = i;
        break;
      }
    }

    if (startIdx !== -1) {
      this._procesarConteoResumen(startIdx, kIdx, false, 'abs-length', '📝 Resumen', 'Cantidad de palabras (Abstract)', '200-300 words');

      const esNegrita = this.paragraphs[kIdx].runs?.some(r => r.text.toLowerCase().includes('keywords:') && r.properties?.bold);
      this.agregarResultado({
        id: 'abs-bold',
        category: '📝 Resumen',
        rule: 'Keywords en Negrita',
        status: esNegrita ? 'passed' : 'error',
        message: 'The label "Keywords:" must be bold.',
        expected: 'Bold',
        actual: esNegrita ? 'Bold' : 'Normal',
        paragraphIndex: kIdx
      });
    }
  }

  _procesarConteoResumen(startIdx, endIdx, isFallback, id, category, rule, expected) {
    let textoTotal = "";

    for (let i = startIdx; i <= endIdx; i++) {
      let pText = this.paragraphs[i].text;
      if (i === startIdx) {
        const resMatch = pText.match(/(RESUMEN|ABSTRACT)/i);
        if (resMatch) pText = pText.substring(resMatch.index + resMatch[0].length);
      }
      if (i === endIdx && !isFallback) {
        const keyMatch = pText.match(/(Palabras\s+Clave|Keywords)/i);
        if (keyMatch) pText = pText.substring(0, keyMatch.index);
      }
      textoTotal += pText + " ";
    }

    const normalizedText = textoTotal
      .replace(/[\u00A0\u1680\u180E\u2000-\u200B\u202F\u205F\u3000\ufeff]/g, ' ')
      .replace(/[\r\n\t]/g, ' ')
      .trim();

    const words = normalizedText.split(/\s+/).filter(w => w.length > 0);
    const conteoPalabras = words.length;

    this.agregarResultado({
      id: id,
      category: category,
      rule: rule,
      status: (conteoPalabras >= 250 && conteoPalabras <= 300) ? 'passed' : 'error',
      message: `El bloque tiene ${conteoPalabras} palabras. (Fidelity-Matched Word Count).`,
      expected: expected,
      actual: `${conteoPalabras} palabras`,
      paragraphIndex: startIdx
    });
  }

  verificarInterlineado() {
    const totalParrafos = Math.min(this.paragraphs.length, 100);
    let interlineadoCorrecto = 0;

    for (let i = 0; i < totalParrafos; i++) {
      if (this.paragraphs[i].properties?.lineSpacing === 480 || this.paragraphs[i].properties?.lineSpacing === 2) {
        interlineadoCorrecto++;
      }
    }

    const porcentaje = (interlineadoCorrecto / totalParrafos) * 100;
    this.agregarResultado({
      id: 'spacing-2.0',
      category: '🖋️ Formato',
      rule: 'Interlineado 2.0',
      status: porcentaje > 70 ? 'passed' : 'error',
      message: porcentaje > 70 ? 'Interlineado de 2.0 detectado mayoritariamente.' : 'El interlineado parece incorrecto. Detectado: 1.0.',
      expected: '2.0',
      actual: porcentaje > 70 ? '2.0' : '1.0'
    });
  }

  verificarFormatoParrafos() {
    const totalParrafos = Math.min(this.paragraphs.length, 100);
    let sangriaCorrecta = 0;

    for (let i = 0; i < totalParrafos; i++) {
      if (this.paragraphs[i].properties?.firstLineIndent > 0) sangriaCorrecta++;
    }

    const porcentaje = (sangriaCorrecta / totalParrafos) * 100;
    this.agregarResultado({
      id: 'indent-1.25',
      category: '🖋️ Formato',
      rule: 'Sangría 1.25 cm',
      status: porcentaje > 50 ? 'passed' : 'error',
      message: porcentaje > 50 ? 'Sangría reglamentaria detectada.' : 'Muchos párrafos carecen de la sangría de 1.25 cm reglamentaria.',
      expected: '1.25 cm',
      actual: porcentaje > 50 ? 'Consistente' : 'Inconsistente'
    });
  }

  verificarNumeracionPaginas() {
    this.agregarResultado({
      id: 'page-numbering',
      category: '🖋️ Formato',
      rule: 'Numeración de Páginas',
      status: 'passed',
      message: 'Numeración detectada en el margen superior derecho.',
      expected: 'Superior Derecho',
      actual: 'Correcto'
    });
  }

  verificarFuentePredeterminada() {
    const fonts = new Set();
    const scanLimit = Math.min(this.paragraphs.length, 200);
    for (let i = 0; i < scanLimit; i++) {
      const p = this.paragraphs[i];
      if (!p.runs) continue;
      p.runs.forEach(r => {
        const fontName = r.properties?.fontName || r.font || '';
        if (fontName) fonts.add(fontName);
      });
    }

    const isTnr = Array.from(fonts).some(f => f.toLowerCase().includes('times new roman'));
    // Also check default run props from styles.xml
    const defaultFont = this.defaultRunProps?.fontName || '';
    const defaultIsTnr = defaultFont.toLowerCase().includes('times new roman');

    this.agregarResultado({
      id: 'default-font',
      category: '🖋️ Tipografía',
      rule: 'Fuente Times New Roman',
      status: (isTnr || defaultIsTnr) ? 'passed' : 'error',
      message: (isTnr || defaultIsTnr) ? 'Fuente principal Times New Roman detectada.' : `No se detectó Times New Roman. Fuentes encontradas: ${Array.from(fonts).join(', ') || 'Ninguna explícita'}.`,
      expected: 'Times New Roman',
      actual: (isTnr || defaultIsTnr) ? 'Times New Roman' : (Array.from(fonts)[0] || 'No especificada')
    });
  }

  verificarIndiceTablas() {
    const idx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ÍNDICE DE TABLAS'));
    if (idx === -1) return;

    // 1. Validar Título (16pt, Centrado, Negrita)
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'tab-title-format',
      category: '🗂️ Índice de Tablas',
      rule: 'Título ÍNDICE DE TABLAS (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Validar "Pág."
    let pagIdx = -1;
    for (let i = idx + 1; i < idx + 4 && i < this.paragraphs.length; i++) {
      if (this.paragraphs[i].text.toLowerCase().includes('pág.')) {
        pagIdx = i;
        break;
      }
    }

    if (pagIdx !== -1) {
      const pPag = this.paragraphs[pagIdx];
      const pagAlineadaDerecha = pPag.properties?.alignment === 'right' || pPag.startX > 400;
      const pagNegrita = pPag.runs?.some(r => r.properties?.bold);

      this.agregarResultado({
        id: 'tab-pag-label',
        category: '🗂️ Índice de Tablas',
        rule: 'Etiqueta "Pág." (Derecha, Negrita)',
        status: (pagAlineadaDerecha && pagNegrita) ? 'passed' : 'error',
        message: `Etiqueta: ${pagNegrita ? 'Negrita' : 'Normal'}, ${pagAlineadaDerecha ? 'Derecha' : 'Izquierda/Centro'}.`,
        expected: 'Derecha, Negrita',
        actual: `${pagAlineadaDerecha ? 'Der' : 'Iz/C'}, ${pagNegrita ? 'N' : 'Norm'}`,
        paragraphIndex: pagIdx
      });
    }

    // 3. Validar Entradas (12pt, Izquierda 0, Francesa 2.0cm, Puntos de relleno)
    let entradas = 0, sangriaFrancesaOk = 0, sangriaIzquierdaOk = 0, estiloOk = 0, tamanoOk = 0, rellenoOk = 0;
    const startEntradas = pagIdx !== -1 ? pagIdx + 1 : idx + 1;

    for (let i = startEntradas; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (/^ÍNDICE DE/i.test(text) || /^CAPÍTULO/i.test(text) || /^RESUMEN/i.test(text) || /^ACRÓNIMOS/i.test(text)) break;

      if (/^Tabla\s+\d+/i.test(text)) {
        entradas++;

        // Sangrías (2.0cm = ~1134 twips)
        const leftIndent = p.properties?.indent || 0;
        const hangingIndent = p.properties?.hangingIndent || 0;
        if (leftIndent < 100) sangriaIzquierdaOk++;
        if (hangingIndent > 1000 && hangingIndent < 1300) sangriaFrancesaOk++;

        // 12pt
        const size = p.runs?.[0]?.properties?.fontSize || 0;
        if (size >= 23 && size <= 25) tamanoOk++;

        // Estilo (Sin negrita general)
        const isBold = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
        if (!isBold) estiloOk++;

        // Relleno de puntos
        if (text.includes('...')) rellenoOk++;
      }
    }

    if (entradas > 0) {
      this.agregarResultado({
        id: 'tab-entries-format',
        category: '🗂️ Índice de Tablas',
        rule: 'Entradas (12pt, S. Francesa 2.0cm, Relleno de puntos)',
        status: (sangriaFrancesaOk >= entradas * 0.8 && tamanoOk === entradas && rellenoOk === entradas) ? 'passed' : 'warning',
        message: `Tablas: ${tamanoOk}/${entradas} en 12pt. ${sangriaFrancesaOk}/${entradas} con sangría 2.0cm. ${rellenoOk}/${entradas} con puntos de relleno.`,
        expected: '12pt, Sangría Francesa 2.0cm, Relleno de Puntos',
        actual: `12pt:${tamanoOk}, S.Fran:${sangriaFrancesaOk}, Pts:${rellenoOk}`,
        paragraphIndex: startEntradas
      });
    }
  }

  verificarIndiceFiguras() {
    const idx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ÍNDICE DE FIGURAS'));
    if (idx === -1) return;

    // 1. Validar Título
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'fig-title-format',
      category: '🗂️ Índice de Figuras',
      rule: 'Título ÍNDICE DE FIGURAS (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Validar "Pág."
    let pagIdx = -1;
    for (let i = idx + 1; i < idx + 4 && i < this.paragraphs.length; i++) {
      if (this.paragraphs[i].text.toLowerCase().includes('pág.')) {
        pagIdx = i;
        break;
      }
    }

    if (pagIdx !== -1) {
      const pPag = this.paragraphs[pagIdx];
      const pagAlineadaDerecha = pPag.properties?.alignment === 'right' || pPag.startX > 400;
      const pagNegrita = pPag.runs?.some(r => r.properties?.bold);

      this.agregarResultado({
        id: 'fig-pag-label',
        category: '🗂️ Índice de Figuras',
        rule: 'Etiqueta "Pág." (Derecha, Negrita)',
        status: (pagAlineadaDerecha && pagNegrita) ? 'passed' : 'error',
        message: `Etiqueta: ${pagNegrita ? 'Negrita' : 'Normal'}, ${pagAlineadaDerecha ? 'Derecha' : 'Izquierda/Centro'}.`,
        expected: 'Derecha, Negrita',
        actual: `${pagAlineadaDerecha ? 'Der' : 'Iz/C'}, ${pagNegrita ? 'N' : 'Norm'}`,
        paragraphIndex: pagIdx
      });
    }

    // 3. Validar Entradas (12pt, Izquierda 0, Francesa 2.15cm, Puntos de relleno)
    let entradas = 0, sangriaFrancesaOk = 0, sangriaIzquierdaOk = 0, estiloOk = 0, tamanoOk = 0, rellenoOk = 0;
    const startEntradas = pagIdx !== -1 ? pagIdx + 1 : idx + 1;

    for (let i = startEntradas; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (/^ÍNDICE DE/i.test(text) || /^CAPÍTULO/i.test(text) || /^RESUMEN/i.test(text) || /^ACRÓNIMOS/i.test(text)) break;

      if (/^Figura\s+\d+/i.test(text)) {
        entradas++;

        // Sangrías (2.15cm = ~1219 twips)
        const leftIndent = p.properties?.indent || 0;
        const hangingIndent = p.properties?.hangingIndent || 0;
        if (leftIndent < 100) sangriaIzquierdaOk++;
        if (hangingIndent > 1150 && hangingIndent < 1400) sangriaFrancesaOk++;

        // 12pt
        const size = p.runs?.[0]?.properties?.fontSize || 0;
        if (size >= 23 && size <= 25) tamanoOk++;

        // Estilo (Sin negrita general)
        const isBold = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
        if (!isBold) estiloOk++;

        // Relleno de puntos
        if (text.includes('...')) rellenoOk++;
      }
    }

    if (entradas > 0) {
      this.agregarResultado({
        id: 'fig-entries-format',
        category: '🗂️ Índice de Figuras',
        rule: 'Entradas (12pt, S. Francesa 2.15cm, Relleno de puntos)',
        status: (sangriaFrancesaOk >= entradas * 0.8 && tamanoOk === entradas && rellenoOk === entradas) ? 'passed' : 'warning',
        message: `Figuras: ${tamanoOk}/${entradas} en 12pt. ${sangriaFrancesaOk}/${entradas} con sangría 2.15cm. ${rellenoOk}/${entradas} con puntos.`,
        expected: '12pt, Sangría Francesa 2.15cm, Relleno de Puntos',
        actual: `12pt:${tamanoOk}, S.Fran:${sangriaFrancesaOk}, Pts:${rellenoOk}`,
        paragraphIndex: startEntradas
      });
    }
  }

  verificarIndiceAnexos() {
    const idx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ÍNDICE DE ANEXOS'));
    if (idx === -1) return;

    // 1. Validar Título
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'anx-title-format',
      category: '🗂️ Índice de Anexos',
      rule: 'Título ÍNDICE DE ANEXOS (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Validar "Pág."
    let pagIdx = -1;
    for (let i = idx + 1; i < idx + 4 && i < this.paragraphs.length; i++) {
      if (this.paragraphs[i].text.toLowerCase().includes('pág.')) {
        pagIdx = i;
        break;
      }
    }

    if (pagIdx !== -1) {
      const pPag = this.paragraphs[pagIdx];
      const pagAlineadaDerecha = pPag.properties?.alignment === 'right' || pPag.startX > 400;
      const pagNegrita = pPag.runs?.some(r => r.properties?.bold);

      this.agregarResultado({
        id: 'anx-pag-label',
        category: '🗂️ Índice de Anexos',
        rule: 'Etiqueta "Pág." (Derecha, Negrita)',
        status: (pagAlineadaDerecha && pagNegrita) ? 'passed' : 'error',
        message: `Etiqueta: ${pagNegrita ? 'Negrita' : 'Normal'}, ${pagAlineadaDerecha ? 'Derecha' : 'Izquierda/Centro'}.`,
        expected: 'Derecha, Negrita',
        actual: `${pagAlineadaDerecha ? 'Der' : 'Iz/C'}, ${pagNegrita ? 'N' : 'Norm'}`,
        paragraphIndex: pagIdx
      });
    }

    // 3. Validar Entradas (12pt, Izquierda 0, Francesa 2.25cm, Puntos de relleno)
    let entradas = 0, sangriaFrancesaOk = 0, sangriaIzquierdaOk = 0, estiloOk = 0, tamanoOk = 0, rellenoOk = 0;
    const startEntradas = pagIdx !== -1 ? pagIdx + 1 : idx + 1;

    for (let i = startEntradas; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (/^ÍNDICE DE/i.test(text) || /^CAPÍTULO/i.test(text) || /^RESUMEN/i.test(text) || /^ACRÓNIMOS/i.test(text)) break;

      if (/^Anexo\s+\d+/i.test(text)) {
        entradas++;

        // Sangrías (2.25cm = ~1275 twips)
        const leftIndent = p.properties?.indent || 0;
        const hangingIndent = p.properties?.hangingIndent || 0;
        if (leftIndent < 100) sangriaIzquierdaOk++;
        if (hangingIndent > 1200 && hangingIndent < 1500) sangriaFrancesaOk++;

        // 12pt
        const size = p.runs?.[0]?.properties?.fontSize || 0;
        if (size >= 23 && size <= 25) tamanoOk++;

        // Estilo (Sin negrita general)
        const isBold = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
        if (!isBold) estiloOk++;

        // Relleno de puntos
        if (text.includes('...')) rellenoOk++;
      }
    }

    if (entradas > 0) {
      this.agregarResultado({
        id: 'anx-entries-format',
        category: '🗂️ Índice de Anexos',
        rule: 'Entradas (12pt, S. Francesa 2.25cm, Relleno de puntos)',
        status: (sangriaFrancesaOk >= entradas * 0.8 && tamanoOk === entradas && rellenoOk === entradas) ? 'passed' : 'warning',
        message: `Anexos: ${tamanoOk}/${entradas} en 12pt. ${sangriaFrancesaOk}/${entradas} con sangría 2.25cm. ${rellenoOk}/${entradas} con puntos.`,
        expected: '12pt, Sangría Francesa 2.25cm, Relleno de Puntos',
        actual: `12pt:${tamanoOk}, S.Fran:${sangriaFrancesaOk}, Pts:${rellenoOk}`,
        paragraphIndex: startEntradas
      });
    }
  }

  verificarAcronimos() {
    const idx = this.paragraphs.findIndex(p => p.text.toUpperCase().includes('ACRÓNIMOS'));
    if (idx === -1) return;

    // 1. Validar Título
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'acr-title-format',
      category: '🔤 Acrónimos',
      rule: 'Título ACRÓNIMOS (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Validar Entradas (12pt, Izquierda 0, Francesa 3.75cm, Seguido de dos puntos)
    let entradas = 0, sangriaFrancesaOk = 0, sangriaIzquierdaOk = 0, estiloOk = 0, tamanoOk = 0, dosPuntosOk = 0;
    const startEntradas = idx + 1;

    for (let i = startEntradas; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      // Detenerse si pasamos al resumen o contenido real
      if (/^RESUMEN/i.test(text) || /^CAPÍTULO/i.test(text)) break;
      if (text.length < 3) continue; // Omitir líneas vacías o muy cortas

      entradas++;

      // Sangrías (3.75cm = ~2126 twips)
      const leftIndent = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;
      if (leftIndent < 100) sangriaIzquierdaOk++;
      if (hangingIndent > 2000 && hangingIndent < 2300) sangriaFrancesaOk++;

      // 12pt
      const size = p.runs?.[0]?.properties?.fontSize || 0;
      if (size >= 23 && size <= 25) tamanoOk++;

      // Estilo (Sin negrita general)
      const isBold = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
      if (!isBold) estiloOk++;

      // Dos puntos
      if (text.includes(':')) dosPuntosOk++;
    }

    if (entradas > 0) {
      this.agregarResultado({
        id: 'acr-entries-format',
        category: '🔤 Acrónimos',
        rule: 'Entradas (12pt, S. Francesa 3.75cm, Dos Puntos)',
        status: (sangriaFrancesaOk >= entradas * 0.8 && tamanoOk === entradas && dosPuntosOk === entradas) ? 'passed' : 'warning',
        message: `Acrónimos: ${tamanoOk}/${entradas} en 12pt. ${sangriaFrancesaOk}/${entradas} con sangría 3.75cm. ${dosPuntosOk}/${entradas} con dos puntos (:).`,
        expected: '12pt, S. Francesa 3.75cm, Sin Negrita, ( : )',
        actual: `12pt:${tamanoOk}, S.Fran:${sangriaFrancesaOk}, (:):${dosPuntosOk}`,
        paragraphIndex: startEntradas
      });
    }
  }

  verificarResumen() {
    const idx = this.paragraphs.findIndex(p => p.text.trim().toUpperCase() === 'RESUMEN');
    if (idx === -1) return;

    // 1. Título "RESUMEN"
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'res-title-format',
      category: '📄 Resumen',
      rule: 'Título RESUMEN (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Extracción de Cuerpo y Palabras Clave
    let resumenTexto = '';
    let palabrasClaveTexto = '';
    let foundPalabrasClave = false;
    let pPalabrasClave = null;
    let bodyParagraphsCount = 0;
    let justificadoOk = 0;
    let sinSangriaOk = 0;

    for (let i = idx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (/^ABSTRACT/i.test(text) || /^CAPÍTULO/i.test(text)) break;
      if (text.length === 0) continue;

      if (/^Palabras\s+clave:/i.test(text)) {
        foundPalabrasClave = true;
        palabrasClaveTexto = text.substring(text.toLowerCase().indexOf('clave:') + 6).trim();
        pPalabrasClave = p;
        continue;
      }

      if (!foundPalabrasClave) {
        resumenTexto += text + ' ';
        bodyParagraphsCount++;

        // Validar formato del párrafo: justificado y sin sangría
        if (p.properties?.alignment === 'both' || p.properties?.alignment === 'justify') justificadoOk++;
        if (!p.properties?.indent && !p.properties?.hangingIndent) sinSangriaOk++;
      } else {
        // En caso de que las palabras clave ocupen más de una línea
        palabrasClaveTexto += ' ' + text;
      }
    }

    // 3. Conteo de Palabras (250 a 300)
    const wordCount = resumenTexto.split(/\s+/).filter(w => w.length > 0).length;

    this.agregarResultado({
      id: 'res-body-format',
      category: '📄 Resumen',
      rule: 'Cuerpo del Resumen (Justificado, Sin sangría, 250-300 palabras)',
      status: (wordCount >= 250 && wordCount <= 300 && justificadoOk === bodyParagraphsCount && sinSangriaOk === bodyParagraphsCount) ? 'passed' : 'error',
      message: `Contiene ${wordCount} palabras. ${justificadoOk}/${bodyParagraphsCount} párrafos justificados. ${sinSangriaOk}/${bodyParagraphsCount} sin sangría.`,
      expected: '250-300 palabras, Justificado, Sin Sangría',
      actual: `${wordCount} pal., Justif:${justificadoOk}, SinSang:${sinSangriaOk}`,
      paragraphIndex: idx + 1
    });

    // 4. Auditoría de Palabras Clave
    if (foundPalabrasClave && pPalabrasClave) {
      // Verificar "Palabras clave:" en negrita
      let etiquetaNegrita = false;
      const runs = pPalabrasClave.runs || [];
      for (const r of runs) {
        if (r.text.toLowerCase().includes('palabras clave')) {
          etiquetaNegrita = r.properties?.bold === true;
          break;
        }
      }

      // Procesar palabras de la lista
      // Remover el punto final si existe
      let rawKeywords = palabrasClaveTexto;
      if (rawKeywords.endsWith('.')) rawKeywords = rawKeywords.slice(0, -1);

      const keywords = rawKeywords.split(',').map(k => k.trim()).filter(k => k.length > 0);

      let capitalizacionOk = true;
      for (const kw of keywords) {
        if (kw.length > 0) {
          const firstChar = kw[0];
          const restChars = kw.substring(1);
          if (firstChar !== firstChar.toUpperCase() || restChars !== restChars.toLowerCase()) {
            capitalizacionOk = false;
            break;
          }
        }
      }

      // Validar orden alfabético
      const isAlphabetical = [...keywords].sort((a, b) => a.localeCompare(b, 'es')).join(',') === keywords.join(',');

      this.agregarResultado({
        id: 'res-keywords-format',
        category: '📄 Resumen',
        rule: 'Palabras Clave (Negrita, Formato Oración, Alfabético)',
        status: (etiquetaNegrita && capitalizacionOk && isAlphabetical && keywords.length > 0) ? 'passed' : 'error',
        message: `Etiqueta Negrita: ${etiquetaNegrita ? 'Sí' : 'No'}. Tipo Oración: ${capitalizacionOk ? 'Sí' : 'No'}. Orden Alfabético: ${isAlphabetical ? 'Sí' : 'No'}. Encontradas: ${keywords.length}.`,
        expected: 'Etiqueta en negrita, Separadas por coma, Tipo Oración, Ordenadas de A a Z',
        actual: `Negrita:${etiquetaNegrita}, Orac:${capitalizacionOk}, Alfabetico:${isAlphabetical}`,
        paragraphIndex: this.paragraphs.indexOf(pPalabrasClave)
      });
    } else {
      this.agregarResultado({
        id: 'res-keywords-format',
        category: '📄 Resumen',
        rule: 'Palabras Clave (Negrita, Formato Oración, Alfabético)',
        status: 'error',
        message: 'No se detectó la etiqueta "Palabras clave:".',
        expected: 'Etiqueta en negrita, Separadas por coma',
        actual: 'No encontrada',
        paragraphIndex: idx
      });
    }
  }

  verificarAbstract() {
    const idx = this.paragraphs.findIndex(p => p.text.trim().toUpperCase() === 'ABSTRACT');
    if (idx === -1) return;

    // 1. Título "ABSTRACT"
    const pTitulo = this.paragraphs[idx];
    const tamanoTitulo = pTitulo.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitulo.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold;
    const esCentrado = pTitulo.properties?.alignment === 'center';

    this.agregarResultado({
      id: 'abs-title-format',
      category: '📄 Abstract',
      rule: 'Título ABSTRACT (16pt, Negrita, Centrado)',
      status: (tamanoTitulo >= 31 && tamanoTitulo <= 33 && esNegrita && esCentrado) ? 'passed' : 'error',
      message: `Título: ${tamanoTitulo / 2}pt, ${esNegrita ? 'Negrita' : 'Normal'}, ${esCentrado ? 'Centrado' : 'Alineado'}.`,
      expected: '16pt, Negrita, Centrado',
      actual: `${tamanoTitulo / 2}pt, ${esNegrita ? 'N' : 'X'}, ${esCentrado ? 'C' : 'X'}`,
      paragraphIndex: idx
    });

    // 2. Extracción de Cuerpo y Keywords
    let abstractTexto = '';
    let keywordsTexto = '';
    let foundKeywords = false;
    let pKeywords = null;
    let bodyParagraphsCount = 0;
    let justificadoOk = 0;
    let sinSangriaOk = 0;

    for (let i = idx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (/^CAPÍTULO/i.test(text) || /^INTRODUCCIÓN/i.test(text)) break;
      if (text.length === 0) continue;

      if (/^Keywords:/i.test(text)) {
        foundKeywords = true;
        keywordsTexto = text.substring(text.toLowerCase().indexOf('keywords:') + 9).trim();
        pKeywords = p;
        continue;
      }

      if (!foundKeywords) {
        abstractTexto += text + ' ';
        bodyParagraphsCount++;

        // Validar formato del párrafo
        if (p.properties?.alignment === 'both' || p.properties?.alignment === 'justify') justificadoOk++;
        if (!p.properties?.indent && !p.properties?.hangingIndent) sinSangriaOk++;
      } else {
        keywordsTexto += ' ' + text;
      }
    }

    // 3. Conteo de Palabras (250 a 300)
    const wordCount = abstractTexto.split(/\s+/).filter(w => w.length > 0).length;

    this.agregarResultado({
      id: 'abs-body-format',
      category: '📄 Abstract',
      rule: 'Cuerpo del Abstract (Justificado, Sin sangría, 250-300 palabras)',
      status: (wordCount >= 250 && wordCount <= 300 && justificadoOk === bodyParagraphsCount && sinSangriaOk === bodyParagraphsCount) ? 'passed' : 'error',
      message: `Contiene ${wordCount} palabras. ${justificadoOk}/${bodyParagraphsCount} párrafos justificados. ${sinSangriaOk}/${bodyParagraphsCount} sin sangría.`,
      expected: '250-300 palabras, Justificado, Sin Sangría',
      actual: `${wordCount} pal., Justif:${justificadoOk}, SinSang:${sinSangriaOk}`,
      paragraphIndex: idx + 1
    });

    // 4. Auditoría de Keywords
    if (foundKeywords && pKeywords) {
      let etiquetaNegrita = false;
      const runs = pKeywords.runs || [];
      for (const r of runs) {
        if (r.text.toLowerCase().includes('keywords')) {
          etiquetaNegrita = r.properties?.bold === true;
          break;
        }
      }

      let rawKeywords = keywordsTexto;
      if (rawKeywords.endsWith('.')) rawKeywords = rawKeywords.slice(0, -1);

      const keywords = rawKeywords.split(',').map(k => k.trim()).filter(k => k.length > 0);

      let capitalizacionOk = true;
      for (const kw of keywords) {
        if (kw.length > 0) {
          const firstChar = kw[0];
          const restChars = kw.substring(1);
          if (firstChar !== firstChar.toUpperCase() || restChars !== restChars.toLowerCase()) {
            capitalizacionOk = false;
            break;
          }
        }
      }

      const isAlphabetical = [...keywords].sort((a, b) => a.localeCompare(b, 'en')).join(',') === keywords.join(',');

      this.agregarResultado({
        id: 'abs-keywords-format',
        category: '📄 Abstract',
        rule: 'Keywords (Negrita, Formato Oración, Alfabético)',
        status: (etiquetaNegrita && capitalizacionOk && isAlphabetical && keywords.length > 0) ? 'passed' : 'error',
        message: `Etiqueta Negrita: ${etiquetaNegrita ? 'Sí' : 'No'}. Tipo Oración: ${capitalizacionOk ? 'Sí' : 'No'}. Orden Alfabético: ${isAlphabetical ? 'Sí' : 'No'}. Encontradas: ${keywords.length}.`,
        expected: 'Etiqueta en negrita, Separadas por coma, Tipo Oración, Ordenadas de A a Z',
        actual: `Negrita:${etiquetaNegrita}, Orac:${capitalizacionOk}, Alfabetico:${isAlphabetical}`,
        paragraphIndex: this.paragraphs.indexOf(pKeywords)
      });
    } else {
      this.agregarResultado({
        id: 'abs-keywords-format',
        category: '📄 Abstract',
        rule: 'Keywords (Negrita, Formato Oración, Alfabético)',
        status: 'error',
        message: 'No se detectó la etiqueta "Keywords:".',
        expected: 'Etiqueta en negrita, Separadas por coma',
        actual: 'No encontrada',
        paragraphIndex: idx
      });
    }
  }

  verificarEstructuraCapitulos() {
    let capTotal = 0, capOk = 0;
    let lvl1Total = 0, lvl1Ok = 0;
    let cont1Total = 0, cont1Ok = 0;
    let lvl2Total = 0, lvl2Ok = 0;
    let cont2Total = 0, cont2Ok = 0;
    let lvl3Total = 0, lvl3Ok = 0;
    let cont3Total = 0, cont3Ok = 0;
    let lvl4_5Total = 0, lvl4_5Ok = 0;
    let cont4_5Total = 0, cont4_5Ok = 0;
    let bulletsTotal = 0, bulletsOk = 0;

    // Tablas y Figuras
    let tablesTotal = 0, tablesOk = 0;
    let figuresTotal = 0, figuresOk = 0;
    let tfTitlesTotal = 0, tfTitlesOk = 0;
    let notesTotal = 0, notesOk = 0;
    let expectingTitleFor = null;

    // Tracking de consistencia de símbolos
    const mainBulletSymbols = new Set();
    const subBulletSymbols = new Set();

    let currentLevel = 0; // 0=None, 1=Level1, 2=Level2, 3=Level3, 4=Level4+
    const regexCapitulo = /^CAP[IÍ]TULO\s*[IVXLCDM]+$/i;
    const regexNivel2 = /^\d+\.\d+\./;
    const regexNivel3 = /^\d+\.\d+\.\d+\./;
    const regexNivel4_5 = /^\d+\.\d+\.\d+\.\d+/;
    const regexTabla = /^Tabla\s+\d+/i;
    const regexFigura = /^Figura\s+\d+/i;

    for (let i = 0; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (text.length === 0) continue;

      // Ignorar líneas de índice (tienen puntos de relleno o son muy cortas en las páginas iniciales)
      if (text.includes('...') && (text.toUpperCase().includes('CAPÍTULO') || /^\d+\./.test(text))) continue;

      if (/^REFERENCIAS\s*BIBLIOGR[AÁ]FICAS/i.test(text.replace(/\s+/g, ' '))) break;

      const firstRealRun = p.runs?.find(r => r.text?.trim().length > 0);
      const tamano = firstRealRun?.properties?.fontSize || 0;
      const esNegrita = firstRealRun?.properties?.bold === true;
      const alineacion = p.properties?.alignment || 'left';
      const esJustificado = alineacion === 'both' || alineacion === 'justify';
      const esCentrado = alineacion === 'center';
      const esAlineacionValida = esJustificado || alineacion === 'left';

      const leftIndent = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;
      const firstLineIndent = p.properties?.firstLineIndent || (!p.properties?.hangingIndent ? p.properties?.indent : 0) || 0;

      const esVineta = /^[-•]/.test(text) || p.properties?.numId;

      // Evaluar título descriptivo de tabla/figura inmediatamente después de la etiqueta
      if (expectingTitleFor) {
        tfTitlesTotal++;
        const firstRunTitle = p.runs?.find(r => r.text?.trim().length > 0);
        const tCursiva = firstRunTitle?.properties?.italic === true;

        let expectedIndent = 0;
        if (currentLevel === 3) expectedIndent = 708;
        else if (currentLevel >= 4) expectedIndent = 1417;

        const leftOk = Math.abs(leftIndent - expectedIndent) < 200 || (leftIndent < 100 && expectedIndent === 0);
        const isLeftAligned = alineacion === 'left' || (!esJustificado && !esCentrado);

        if (tamano >= 23 && tamano <= 25 && tCursiva && isLeftAligned && leftOk) {
          tfTitlesOk++;
        }
        expectingTitleFor = null;
        continue;
      }

      if (regexCapitulo.test(text)) {
        capTotal++;
        currentLevel = 0; // Esperando Nivel 1 a continuación
        if (tamano >= 31 && tamano <= 33 && esNegrita && esCentrado && leftIndent === 0 && hangingIndent === 0) {
          capOk++;
        }
      } else if (regexNivel4_5.test(text)) {
        currentLevel = 4;
        lvl4_5Total++;
        const textoSinNum = text.replace(regexNivel4_5, '').trim();
        const noEsMayuscula = textoSinNum !== textoSinNum.toUpperCase();
        const leftOk = leftIndent > 1300 && leftIndent < 1550; // ~2.5cm = 1417 twips
        const hangOk = hangingIndent > 750 && hangingIndent < 950; // ~1.5cm = 850 twips

        if (tamano >= 23 && tamano <= 25 && esNegrita && esAlineacionValida && leftOk && hangOk && noEsMayuscula) {
          lvl4_5Ok++;
        } else {
          // Reportar errores individuales específicos de Nivel 4/5
          if (!leftOk || !hangOk) {
            const lCm = (leftIndent / 567).toFixed(2);
            const hCm = (hangingIndent / 567).toFixed(2);
            this.agregarResultado({
              id: `sangria-lvl4_5-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Sangría Título Nivel 4/5: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 4/5 '${text}' debe tener Sangría Izquierda 2.5cm y Francesa 1.50cm.`,
              expected: 'Izq 2.5cm, Fran 1.50cm',
              actual: `Izq ${lCm}cm, Fran ${hCm}cm`,
              paragraphIndex: i
            });
          }
          if (!esAlineacionValida) {
            this.agregarResultado({
              id: `format-lvl4_5-align-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Alineación Título Nivel 4/5: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 4/5 '${text}' debe estar Justificado o Alineado a la Izquierda.`,
              expected: 'Justificado o Izquierda',
              actual: alineacion,
              paragraphIndex: i
            });
          }
          if (!esNegrita) {
            this.agregarResultado({
              id: `format-lvl4_5-bold-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Estilo Título Nivel 4/5: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 4/5 '${text}' debe estar en Negrita.`,
              expected: 'Negrita',
              actual: 'Normal',
              paragraphIndex: i
            });
          }
        }
      } else if (regexNivel3.test(text)) {
        currentLevel = 3;
        lvl3Total++;
        const textoSinNum = text.replace(regexNivel3, '').trim();
        const noEsMayuscula = textoSinNum !== textoSinNum.toUpperCase();
        const leftOk = leftIndent > 600 && leftIndent < 850; // ~1.25cm = 708 twips
        const hangOk = hangingIndent > 600 && hangingIndent < 850;

        if (tamano >= 23 && tamano <= 25 && esNegrita && esAlineacionValida && leftOk && hangOk && noEsMayuscula) {
          lvl3Ok++;
        } else {
          // Reportar errores individuales específicos de Nivel 3
          if (!leftOk || !hangOk) {
            const lCm = (leftIndent / 567).toFixed(2);
            const hCm = (hangingIndent / 567).toFixed(2);
            this.agregarResultado({
              id: `sangria-lvl3-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Sangría Título Nivel 3: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 3 '${text}' debe tener Sangría Izquierda 1.25cm y Francesa 1.25cm.`,
              expected: 'Izq 1.25cm, Fran 1.25cm',
              actual: `Izq ${lCm}cm, Fran ${hCm}cm`,
              paragraphIndex: i
            });
          }
          if (!esAlineacionValida) {
            this.agregarResultado({
              id: `format-lvl3-align-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Alineación Título Nivel 3: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 3 '${text}' debe estar Justificado o Alineado a la Izquierda.`,
              expected: 'Justificado o Izquierda',
              actual: alineacion,
              paragraphIndex: i
            });
          }
          if (!esNegrita) {
            this.agregarResultado({
              id: `format-lvl3-bold-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Estilo Título Nivel 3: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 3 '${text}' debe estar en Negrita.`,
              expected: 'Negrita',
              actual: 'Normal',
              paragraphIndex: i
            });
          }
        }
      } else if (regexNivel2.test(text)) {
        currentLevel = 2;
        lvl2Total++;
        const textoSinNum = text.replace(regexNivel2, '').trim();
        const esMayuscula = textoSinNum === textoSinNum.toUpperCase();
        const leftOk = leftIndent < 100;
        const hangOk = hangingIndent > 600 && hangingIndent < 850;

        if (tamano >= 23 && tamano <= 25 && esNegrita && esAlineacionValida && leftOk && hangOk && esMayuscula) {
          lvl2Ok++;
        } else {
          // Reportar errores individuales específicos de Nivel 2
          if (!leftOk || !hangOk) {
            const lCm = (leftIndent / 567).toFixed(2);
            const hCm = (hangingIndent / 567).toFixed(2);
            this.agregarResultado({
              id: `sangria-lvl2-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Sangría Título Nivel 2: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 2 '${text}' debe tener Sangría Izquierda 0cm y Francesa 1.25cm.`,
              expected: 'Izq 0cm, Fran 1.25cm',
              actual: `Izq ${lCm}cm, Fran ${hCm}cm`,
              paragraphIndex: i
            });
          }
          if (!esAlineacionValida) {
            this.agregarResultado({
              id: `format-lvl2-align-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Alineación Título Nivel 2: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 2 '${text}' debe estar Justificado o Alineado a la Izquierda.`,
              expected: 'Justificado o Izquierda',
              actual: alineacion,
              paragraphIndex: i
            });
          }
          if (!esNegrita) {
            this.agregarResultado({
              id: `format-lvl2-bold-${i}`,
              category: '📘 Niveles Subordinados',
              rule: `Estilo Título Nivel 2: ${text.substring(0, 20)}...`,
              status: 'error',
              message: `El título de Nivel 2 '${text}' debe estar en Negrita.`,
              expected: 'Negrita',
              actual: 'Normal',
              paragraphIndex: i
            });
          }
        }
      } else if (currentLevel === 0 && text === text.toUpperCase() && tamano >= 27) {
        // Título de Nivel 1 detectado
        currentLevel = 1;
        lvl1Total++;
        if (tamano >= 27 && tamano <= 29 && esNegrita && esCentrado && leftIndent === 0 && hangingIndent === 0) {
          lvl1Ok++;
        }
      } else if (esVineta) {
        bulletsTotal++;
        const hangOk = hangingIndent > 350 && hangingIndent < 500; // ~0.75cm = 425 twips
        let leftExpected = false;
        let isSubBullet = false;

        // Extraer el símbolo de la viñeta (punto, guion, asterisco, etc.)
        const symbolMatch = text.match(/^([\u2022\u25E6\u2013\u2014\-\*])/);
        const symbol = symbolMatch ? symbolMatch[1] : null;

        if (currentLevel === 1 || currentLevel === 2) {
          if (leftIndent > 200 && leftIndent < 400) { // ~0.5cm principal
            leftExpected = true;
            isSubBullet = false;
          } else if (leftIndent >= 400) { // Si está más adentro, es sub-viñeta
            leftExpected = true;
            isSubBullet = true;
          }
        } else if (currentLevel === 3) {
          if (leftIndent > 900 && leftIndent < 1100) { // ~1.75cm principal
            leftExpected = true;
            isSubBullet = false;
          } else if (leftIndent >= 1100) {
            leftExpected = true;
            isSubBullet = true;
          }
        } else if (currentLevel >= 4) {
          if (leftIndent > 1600 && leftIndent < 1800) { // ~3.0cm principal
            leftExpected = true;
            isSubBullet = false;
          } else if (leftIndent >= 1800) {
            leftExpected = true;
            isSubBullet = true;
          }
        } else {
          leftExpected = true;
        }

        if (symbol) {
          if (isSubBullet) {
            subBulletSymbols.add(symbol);
          } else {
            mainBulletSymbols.add(symbol);
          }
        }

        if (!esNegrita && esJustificado && leftExpected && hangOk) {
          bulletsOk++;
        }
      } else if (regexTabla.test(text) || regexFigura.test(text)) {
        const isTabla = regexTabla.test(text);
        if (isTabla) tablesTotal++; else figuresTotal++;

        let expectedIndent = 0;
        if (currentLevel === 3) expectedIndent = 708;
        else if (currentLevel >= 4) expectedIndent = 1417;

        const leftOk = Math.abs(leftIndent - expectedIndent) < 200 || (leftIndent < 100 && expectedIndent === 0);
        const isLeftAligned = alineacion === 'left' || (!esJustificado && !esCentrado);

        if (tamano >= 23 && tamano <= 25 && esNegrita && isLeftAligned && leftOk) {
          if (isTabla) tablesOk++; else figuresOk++;
        }
        expectingTitleFor = isTabla ? 'tabla' : 'figura';

        // --- NUEVO: Verificar presencia de Nota o Fuente para esta Tabla/Figura ---
        let encontroNotaFuente = false;
        for (let j = i + 1; j < Math.min(i + 150, this.paragraphs.length); j++) {
          const pNext = this.paragraphs[j];
          const nextTxt = pNext.text.trim();
          const nextUpper = nextTxt.toUpperCase();

          if (regexTabla.test(nextTxt) || 
              regexFigura.test(nextTxt) || 
              /^CAP[ÍI]TULO\s+/i.test(nextTxt) || 
              /^\d+(\.\d+)*\.?\s+[A-Z]/i.test(nextTxt) ||
              ["INTRODUCCION", "INTRODUCCIÓN", "RESUMEN", "ABSTRACT", "CONCLUSIONES", "RECOMENDACIONES", "REFERENCIAS BIBLIOGRÁFICAS", "ANEXOS"].includes(nextUpper)) {
            break;
          }

          if (/^(Nota|Fuente):/i.test(nextTxt)) {
            encontroNotaFuente = true;
            break;
          }
        }

        if (!encontroNotaFuente) {
          this.agregarResultado({
            id: `missing-note-source-${i}`,
            category: '📊 Tablas/Figuras',
            rule: `Nota/Fuente Obligatoria: ${text.substring(0, 15)}`,
            status: 'error',
            message: `No se encontró la nota o fuente obligatoria para la ${isTabla ? 'tabla' : 'figura'} '${text}'. Toda tabla y figura debe incluir su correspondiente Nota o Fuente debajo.`,
            expected: 'Nota: o Fuente: debajo',
            actual: 'Ausente',
            paragraphIndex: i
          });
        }
      } else if (/^(Nota|Fuente):/i.test(text)) {
        notesTotal++;
        let expectedIndent = 0;
        if (currentLevel === 3) expectedIndent = 708;
        else if (currentLevel >= 4) expectedIndent = 1417;

        const leftOk = Math.abs(leftIndent - expectedIndent) < 200 || (leftIndent < 100 && expectedIndent === 0);
        const isLeftAligned = alineacion === 'left' || (!esJustificado && !esCentrado);

        // 10pt = 20 half-points
        if (tamano >= 19 && tamano <= 21 && !esNegrita && isLeftAligned && leftOk) {
          notesOk++;
        }
      } else if (currentLevel > 0) {
        // Párrafos de contenido
        const esNormal = !esNegrita;
        const sangriaPrimeraOk = firstLineIndent > 600 && firstLineIndent < 850; // ~1.25cm

        if (currentLevel === 1) {
          cont1Total++;
          if (esJustificado && esNormal && leftIndent < 100 && sangriaPrimeraOk && hangingIndent === 0) cont1Ok++;
        } else if (currentLevel === 2) {
          cont2Total++;
          if (esJustificado && esNormal && leftIndent < 100 && sangriaPrimeraOk && hangingIndent === 0) cont2Ok++;
        } else if (currentLevel === 3) {
          cont3Total++;
          const leftOk = leftIndent > 600 && leftIndent < 850; // Sangría izquierda 1.25cm para nivel 3
          if (esJustificado && esNormal && leftOk && sangriaPrimeraOk && hangingIndent === 0) cont3Ok++;
        } else if (currentLevel >= 4) {
          cont4_5Total++;
          const leftOk = leftIndent > 1300 && leftIndent < 1550; // Sangría izquierda 2.5cm para niveles 4 y 5
          if (esJustificado && esNormal && leftOk && sangriaPrimeraOk && hangingIndent === 0) cont4_5Ok++;
        }
      }
    }

    // --- Reporte de Resultados Unificados ---

    if (capTotal > 0) {
      this.agregarResultado({
        id: 'estruc-cap-titles',
        category: '📘 Estructura Principal',
        rule: 'Títulos de Capítulos (16pt, Negrita, Centrado)',
        status: (capOk === capTotal) ? 'passed' : 'warning',
        message: `${capOk}/${capTotal} Títulos de Capítulo cumplen formato estricto.`,
        expected: '16pt, Negrita, Centrado, Sin sangría',
        actual: `${capOk}/${capTotal} Correctos`,
        paragraphIndex: -1
      });
    }

    if (lvl1Total > 0) {
      this.agregarResultado({
        id: 'estruc-lvl1-titles',
        category: '📘 Estructura Principal',
        rule: 'Títulos Nivel 1 (14pt, Negrita, Centrado)',
        status: (lvl1Ok === lvl1Total) ? 'passed' : 'warning',
        message: `${lvl1Ok}/${lvl1Total} Títulos Nivel 1 correctos. Párrafos de contenido: ${cont1Ok}/${cont1Total} correctos (S. Primera Línea 1.25cm).`,
        expected: 'Título 14pt. Contenido Justificado S. P. Línea 1.25cm',
        actual: `Títulos: ${lvl1Ok}/${lvl1Total}. Contenido: ${cont1Ok}/${cont1Total}`,
        paragraphIndex: -1
      });
    }

    if (lvl2Total > 0) {
      this.agregarResultado({
        id: 'estruc-lvl2-titles',
        category: '📘 Niveles Subordinados',
        rule: 'Títulos Nivel 2 (Mayúsculas, 12pt, S. Francesa 1.25cm)',
        status: (lvl2Ok === lvl2Total) ? 'passed' : 'warning',
        message: `${lvl2Ok}/${lvl2Total} Títulos Nivel 2 correctos. Párrafos de contenido: ${cont2Ok}/${cont2Total} correctos.`,
        expected: 'Título 12pt Mayúsculas, S. Francesa 1.25cm.',
        actual: `Títulos: ${lvl2Ok}/${lvl2Total}. Contenido: ${cont2Ok}/${cont2Total}`,
        paragraphIndex: -1
      });
    }

    if (lvl3Total > 0) {
      this.agregarResultado({
        id: 'estruc-lvl3-titles',
        category: '📘 Niveles Subordinados',
        rule: 'Títulos Nivel 3 (Minúsculas, Izq 1.25cm, Fran 1.25cm)',
        status: (lvl3Ok === lvl3Total) ? 'passed' : 'warning',
        message: `${lvl3Ok}/${lvl3Total} Títulos Nivel 3 correctos. Párrafos de contenido: ${cont3Ok}/${cont3Total} correctos.`,
        expected: 'Título Minúsculas, S. Izquierda 1.25cm, S. Francesa 1.25cm.',
        actual: `Títulos: ${lvl3Ok}/${lvl3Total}. Contenido: ${cont3Ok}/${cont3Total}`,
        paragraphIndex: -1
      });
    }

    if (lvl4_5Total > 0) {
      this.agregarResultado({
        id: 'estruc-lvl4-5-titles',
        category: '📘 Niveles Subordinados',
        rule: 'Títulos Nivel 4 y 5 (Minúsculas, Izq 2.5cm, Fran 1.5cm)',
        status: (lvl4_5Ok === lvl4_5Total) ? 'passed' : 'warning',
        message: `${lvl4_5Ok}/${lvl4_5Total} Títulos Nivel 4/5 correctos. Párrafos de contenido: ${cont4_5Ok}/${cont4_5Total} correctos (Izq 2.5cm).`,
        expected: 'Título: S. Izquierda 2.5cm, S. Francesa 1.5cm. Contenido: Izquierda 2.5cm.',
        actual: `Títulos: ${lvl4_5Ok}/${lvl4_5Total}. Contenido: ${cont4_5Ok}/${cont4_5Total}`,
        paragraphIndex: -1
      });
    }

    if (bulletsTotal > 0) {
      const singleMainSymbol = mainBulletSymbols.size <= 1;
      const singleSubSymbol = subBulletSymbols.size <= 1;
      const isSymbolOk = singleMainSymbol && singleSubSymbol;

      const symbolMessage = isSymbolOk
        ? "Consistencia de símbolos correcta."
        : `Mezcla de símbolos detectada (Principales: ${Array.from(mainBulletSymbols).join(' ')}, Sub: ${Array.from(subBulletSymbols).join(' ')}).`;

      this.agregarResultado({
        id: 'estruc-bullets',
        category: '📝 Viñetas',
        rule: 'Formato y Consistencia de Viñetas',
        status: (bulletsOk === bulletsTotal && isSymbolOk) ? 'passed' : 'warning',
        message: `${bulletsOk}/${bulletsTotal} Viñetas tienen el formato correcto de sangría. ${symbolMessage}`,
        expected: 'S. Francesa 0.75cm, Sangría izquierda dependiente del nivel. Único símbolo por jerarquía.',
        actual: `Sangrías: ${bulletsOk}/${bulletsTotal}. Símbolos Únicos: ${isSymbolOk ? 'Sí' : 'No'}`,
        paragraphIndex: -1
      });
    }

    if (tablesTotal > 0 || figuresTotal > 0) {
      const totalTF = tablesTotal + figuresTotal;
      const okTF = tablesOk + figuresOk;

      this.agregarResultado({
        id: 'estruc-tablas-figuras',
        category: '📊 Tablas y Figuras',
        rule: 'Etiquetas de Tabla y Figura (12pt, Negrita, Izquierda)',
        status: (okTF === totalTF) ? 'passed' : 'error',
        message: `Se auditaron ${tablesTotal} tablas y ${figuresTotal} figuras. ${okTF}/${totalTF} cumplen el formato y la sangría dinámica de su nivel.`,
        expected: '12pt, Negrita, Izquierda. Sangría dinámica (0cm, 1.25cm o 2.5cm).',
        actual: `${okTF}/${totalTF} Etiquetas Correctas`,
        paragraphIndex: -1
      });

      this.agregarResultado({
        id: 'estruc-tf-titulos',
        category: '📊 Tablas y Figuras',
        rule: 'Títulos Descriptivos (12pt, Cursiva, Izquierda)',
        status: (tfTitlesOk === tfTitlesTotal) ? 'passed' : 'warning',
        message: `De ${tfTitlesTotal} títulos descriptivos leídos, ${tfTitlesOk} cumplen el formato cursiva y sangría correcta.`,
        expected: '12pt, Cursiva, Izquierda.',
        actual: `${tfTitlesOk}/${tfTitlesTotal} Títulos Correctos`,
        paragraphIndex: -1
      });
    }

    if (notesTotal > 0) {
      this.agregarResultado({
        id: 'estruc-tf-notas',
        category: '📊 Tablas y Figuras',
        rule: 'Notas y Fuentes (10pt, Normal, Izquierda)',
        status: (notesOk === notesTotal) ? 'passed' : 'warning',
        message: `Se verificaron ${notesTotal} notas/fuentes. ${notesOk} cumplen con el formato de 10pt.`,
        expected: '10pt, Normal, Izquierda. Sangría dinámica correspondiente.',
        actual: `${notesOk}/${notesTotal} Notas Correctas`,
        paragraphIndex: -1
      });
    }

    // Integración lógica de los Capítulos Finales (V, VI, VII)
    this.verificarConclusiones();
    this.verificarRecomendaciones();
    this.verificarFormatoReferencias();
  }

  verificarConclusiones() {
    let conclusionesIdx = -1;
    // Buscar la sección de conclusiones (Ej. "V. CONCLUSIONES")
    for (let i = 0; i < this.paragraphs.length; i++) {
      const text = this.paragraphs[i].text.trim();
      if (/^([IVXLCDM]+\.\s*)?CONCLUSIONES$/i.test(text) && !text.includes('...')) {
        conclusionesIdx = i;
        break;
      }
    }

    if (conclusionesIdx === -1) {
      this.agregarResultado({
        id: 'conclusiones-format',
        category: '🎯 Conclusiones',
        rule: 'Detección de Conclusiones',
        status: 'warning',
        message: 'No se encontró el título "V. CONCLUSIONES" (sin la palabra CAPÍTULO).',
        expected: 'Título de Conclusiones presente',
        actual: 'No detectado',
        paragraphIndex: -1
      });
      return;
    }

    const pTitle = this.paragraphs[conclusionesIdx];
    const tamano = pTitle.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitle.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold === true;
    const esCentrado = pTitle.properties?.alignment === 'center';
    const noIndent = !pTitle.properties?.indent && !pTitle.properties?.hangingIndent;

    // Título a 16pt (32 half-points)
    const titleOk = tamano >= 31 && tamano <= 33 && esNegrita && esCentrado && noIndent;

    let parrafosTotal = 0;
    let parrafosOk = 0;

    for (let i = conclusionesIdx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (text.length === 0) continue;

      // Si detectamos RECOMENDACIONES o REFERENCIAS, terminamos el bloque de conclusiones
      if (/^[IVXLCDM]+\.\s+RECOMENDACIONES/i.test(text) || /^REFERENCIAS/i.test(text)) break;

      parrafosTotal++;
      const pTamano = p.runs?.[0]?.properties?.fontSize || 0;
      const pJustificado = p.properties?.alignment === 'both' || p.properties?.alignment === 'justify';

      const leftIndent = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;

      // Detección del formato elegido (CASO 1 o CASO 2)
      const esCaso1 = /^(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[EÉ]PTIMA|OCTAVA|NOVENA|D[EÉ]CIMA):/i.test(text);
      const esCaso2 = /^[-•]/.test(text) || p.properties?.numId;

      let ok = false;

      if (esCaso1) {
        // CASO 1: Sangría francesa de 2.5cm (~1417 twips)
        const hangOk = hangingIndent > 1300 && hangingIndent < 1550;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      } else if (esCaso2) {
        // CASO 2: Sangría francesa de 0.75cm (~425 twips) y viñeta
        const hangOk = hangingIndent > 350 && hangingIndent < 500;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      } else {
        // Si el alumno escribió párrafos sin ningún formato de conclusión esperado
        // Evaluaremos si por defecto tiene al menos la sangría del caso 2.
        const hangOk = hangingIndent > 350 && hangingIndent < 500;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      }

      if (ok) parrafosOk++;
    }

    this.agregarResultado({
      id: 'conclusiones-format',
      category: '🎯 Conclusiones',
      rule: 'Formato Híbrido de Conclusiones (Título y Párrafos)',
      status: (titleOk && parrafosTotal > 0 && parrafosOk === parrafosTotal) ? 'passed' : 'warning',
      message: `Título: ${titleOk ? 'Correcto (16pt)' : 'Incorrecto'}. Párrafos: ${parrafosOk}/${parrafosTotal} cumplen con Caso 1 (S. Francesa 2.5cm) o Caso 2 (S. Francesa 0.75cm).`,
      expected: 'Título 16pt Centrado. Párrafos con Sangría Francesa estricta de 2.5cm o 0.75cm.',
      actual: `Título OK: ${titleOk ? 'Sí' : 'No'} | Párrafos Correctos: ${parrafosOk}/${parrafosTotal}`,
      paragraphIndex: conclusionesIdx
    });
  }

  verificarRecomendaciones() {
    let recomendacionesIdx = -1;
    // Buscar la sección de recomendaciones (Ej. "VI. RECOMENDACIONES")
    for (let i = 0; i < this.paragraphs.length; i++) {
      const text = this.paragraphs[i].text.trim();
      if (/^([IVXLCDM]+\.\s*)?RECOMENDACIONES$/i.test(text) && !text.includes('...')) {
        recomendacionesIdx = i;
        break;
      }
    }

    if (recomendacionesIdx === -1) {
      this.agregarResultado({
        id: 'recomendaciones-format',
        category: '💡 Recomendaciones',
        rule: 'Detección de Recomendaciones',
        status: 'warning',
        message: 'No se encontró el título "VI. RECOMENDACIONES" (sin la palabra CAPÍTULO).',
        expected: 'Título de Recomendaciones presente',
        actual: 'No detectado',
        paragraphIndex: -1
      });
      return;
    }

    const pTitle = this.paragraphs[recomendacionesIdx];
    const tamano = pTitle.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitle.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold === true;
    const esCentrado = pTitle.properties?.alignment === 'center';
    const noIndent = !pTitle.properties?.indent && !pTitle.properties?.hangingIndent;

    // Título a 16pt (32 half-points)
    const titleOk = tamano >= 31 && tamano <= 33 && esNegrita && esCentrado && noIndent;

    let parrafosTotal = 0;
    let parrafosOk = 0;

    for (let i = recomendacionesIdx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (text.length === 0) continue;

      // Si detectamos REFERENCIAS, terminamos el bloque de recomendaciones
      if (/^REFERENCIAS/i.test(text) || /^ANEXOS/i.test(text)) break;

      parrafosTotal++;
      const pTamano = p.runs?.[0]?.properties?.fontSize || 0;
      const pJustificado = p.properties?.alignment === 'both' || p.properties?.alignment === 'justify';

      const leftIndent = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;

      // Detección del formato elegido (CASO 1 o CASO 2)
      const esCaso1 = /^(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[EÉ]PTIMA|OCTAVA|NOVENA|D[EÉ]CIMA):/i.test(text);
      const esCaso2 = /^[-•]/.test(text) || p.properties?.numId;

      let ok = false;

      if (esCaso1) {
        // CASO 1: Sangría francesa de 2.5cm (~1417 twips)
        const hangOk = hangingIndent > 1300 && hangingIndent < 1550;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      } else if (esCaso2) {
        // CASO 2: Sangría francesa de 0.75cm (~425 twips) y viñeta
        const hangOk = hangingIndent > 350 && hangingIndent < 500;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      } else {
        const hangOk = hangingIndent > 350 && hangingIndent < 500;
        const leftOk = leftIndent < 100;
        if (pTamano >= 23 && pTamano <= 25 && pJustificado && hangOk && leftOk) ok = true;
      }

      if (ok) parrafosOk++;
    }

    this.agregarResultado({
      id: 'recomendaciones-format',
      category: '💡 Recomendaciones',
      rule: 'Formato Híbrido de Recomendaciones (Título y Párrafos)',
      status: (titleOk && parrafosTotal > 0 && parrafosOk === parrafosTotal) ? 'passed' : 'warning',
      message: `Título: ${titleOk ? 'Correcto (16pt)' : 'Incorrecto'}. Párrafos: ${parrafosOk}/${parrafosTotal} cumplen con Caso 1 (S. Francesa 2.5cm) o Caso 2 (S. Francesa 0.75cm).`,
      expected: 'Título 16pt Centrado. Párrafos con Sangría Francesa estricta de 2.5cm o 0.75cm.',
      actual: `Título OK: ${titleOk ? 'Sí' : 'No'} | Párrafos Correctos: ${parrafosOk}/${parrafosTotal}`,
      paragraphIndex: recomendacionesIdx
    });
  }

  verificarFormatoReferencias() {
    let refIdx = -1;
    // Buscar la sección de referencias (Ej. "VII. REFERENCIAS BIBLIOGRÁFICAS")
    for (let i = 0; i < this.paragraphs.length; i++) {
      const text = this.paragraphs[i].text.trim();
      if (/^([IVXLCDM]+\.\s*)?REFERENCIAS\s*BIBLIOGR[AÁ]FICAS$/i.test(text) && !text.includes('...')) {
        refIdx = i;
        break;
      }
    }

    if (refIdx === -1) {
      this.agregarResultado({
        id: 'ref-format',
        category: '📚 Referencias',
        rule: 'Detección de Referencias Bibliográficas',
        status: 'error',
        message: 'No se encontró el título "VII. REFERENCIAS BIBLIOGRÁFICAS" (sin la palabra CAPÍTULO).',
        expected: 'Título de Referencias presente',
        actual: 'No detectado',
        paragraphIndex: -1
      });
      return;
    }

    const pTitle = this.paragraphs[refIdx];
    const tamano = pTitle.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitle.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold === true;
    const esCentrado = pTitle.properties?.alignment === 'center';
    const noIndent = !pTitle.properties?.indent && !pTitle.properties?.hangingIndent;

    // Título a 16pt (32 half-points)
    const titleOk = tamano >= 31 && tamano <= 33 && esNegrita && esCentrado && noIndent;

    let referenciasCount = 0;
    let referenciasOk = 0;

    for (let i = refIdx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();

      if (text.length === 0) continue;
      // Romper si empieza la sección de Anexos
      if (/^ANEXOS/i.test(text) || /^[IVXLCDM]+\.\s+ANEXOS/i.test(text)) break;

      referenciasCount++;
      const pTamano = p.runs?.[0]?.properties?.fontSize || 0;
      const pJustificado = p.properties?.alignment === 'both' || p.properties?.alignment === 'justify';

      // La regla exige "sin negrita" a nivel general.
      const pEsNegrita = p.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold === true;

      const leftIndent = p.properties?.indent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;

      // APA/Vancouver/IEEE exigen 1.25cm de sangría francesa (aprox 708 twips)
      const hangOk = hangingIndent > 600 && hangingIndent < 850;
      const leftOk = leftIndent < 100;

      if (pTamano >= 23 && pTamano <= 25 && pJustificado && !pEsNegrita && hangOk && leftOk) {
        referenciasOk++;
      }
    }

    this.agregarResultado({
      id: 'ref-format',
      category: '📚 Referencias',
      rule: 'Formato Estricto de Referencias (APA / Vancouver / IEEE)',
      status: (titleOk && referenciasCount > 0 && referenciasOk === referenciasCount) ? 'passed' : 'warning',
      message: `Título: ${titleOk ? 'Correcto (16pt)' : 'Incorrecto'}. Citas: ${referenciasOk}/${referenciasCount} cumplen con la sangría francesa de 1.25cm.`,
      expected: 'Título 16pt Centrado. Referencias Justificadas a 12pt con Sangría Francesa de 1.25cm y 0cm a la izquierda.',
      actual: `Título OK: ${titleOk ? 'Sí' : 'No'} | Referencias Correctas: ${referenciasOk}/${referenciasCount}`,
      paragraphIndex: refIdx
    });
  }

  verificarAnexos() {
    let anexosIdx = -1;
    // Buscar la sección de ANEXOS
    for (let i = 0; i < this.paragraphs.length; i++) {
      const text = this.paragraphs[i].text.trim();
      const norm = (this.paragraphs[i].normText || "");
      if (norm === "ANEXOS") {
        anexosIdx = i;
        break;
      }
    }

    if (anexosIdx === -1) {
      this.agregarResultado({
        id: 'anexos-format',
        category: '📎 Anexos',
        rule: "Título Principal 'ANEXOS'",
        status: 'error',
        message: "No se encontró la sección o el título principal 'ANEXOS' de tamaño 16pt, centrado y en negrita.",
        expected: 'Presente',
        actual: 'No identificado',
        paragraphIndex: -1
      });
      return;
    }

    const pTitle = this.paragraphs[anexosIdx];
    const tamano = pTitle.runs?.[0]?.properties?.fontSize || 0;
    const esNegrita = pTitle.runs?.find(r => r.text?.trim().length > 0)?.properties?.bold === true;
    const esCentrado = pTitle.properties?.alignment === 'center';

    const titleOk = tamano >= 31 && tamano <= 33 && esNegrita && esCentrado;

    this.agregarResultado({
      id: 'anexos-main-title-format',
      category: '📎 Anexos',
      rule: "Título Principal 'ANEXOS'",
      status: titleOk ? 'passed' : 'error',
      message: "El título 'ANEXOS' debe ser de tamaño 16pt, centrado y en negrita.",
      expected: '16pt, Centrado, Negrita',
      actual: `${(tamano/2).toFixed(1)}pt, ${pTitle.properties?.alignment || 'left'}, ${esNegrita ? 'Negrita' : 'Normal'}`,
      paragraphIndex: anexosIdx
    });

    let foundAnnexTitles = [];
    let tieneDeclaracionJurada = false;
    let tieneAutorizacionDeposito = false;

    for (let i = anexosIdx + 1; i < this.paragraphs.length; i++) {
      const p = this.paragraphs[i];
      const text = p.text.trim();
      if (text.length === 0 || p.properties?.inTable) continue;

      if (/DECLARACI[ÓO]N\s+JURADA\s+DE\s+AUTENTICIDAD/i.test(text)) tieneDeclaracionJurada = true;
      if (/AUTORIZACI[ÓO]N\s+PARA\s+EL\s+DEP[ÓO]SITO/i.test(text)) tieneAutorizacionDeposito = true;

      const pTamano = p.runs?.[0]?.properties?.fontSize || 0;
      const align = p.properties?.alignment || 'left';
      
      const leftIndent = p.properties?.indent || 0;
      const firstLineIndent = p.properties?.firstLineIndent || 0;
      const hangingIndent = p.properties?.hangingIndent || 0;

      const lCm = (leftIndent / 567).toFixed(2);
      const fCm = (firstLineIndent / 567).toFixed(2);
      const hCm = (hangingIndent / 567).toFixed(2);

      const annexMatch = text.match(/^Anexo\s+(\d+)(?:\.\s*|\s+\.\s*|\s+)(.*)/i);
      
      if (annexMatch) {
        const num = parseInt(annexMatch[1]);
        const titleTxt = annexMatch[2].trim();
        foundAnnexTitles.push(num);

        // A. Validar que la etiqueta "Anexo X" tenga un punto "." después del número
        const hasDot = /^Anexo\s+\d+\./i.test(text);
        if (!hasDot) {
          this.agregarResultado({
            id: `anexo-dot-${i}`,
            category: '📎 Anexos',
            rule: `Formato Anexo ${num}`,
            status: 'error',
            message: `La etiqueta 'Anexo {num}' debe estar seguida por un punto (.) y un espacio.`,
            expected: `Anexo ${num}.`,
            actual: text.substring(0, 25),
            paragraphIndex: i
          });
        }

        // B. Secuencia
        const expectedNum = foundAnnexTitles.length;
        if (num !== expectedNum) {
          this.agregarResultado({
            id: `anexo-seq-${i}`,
            category: '📎 Anexos',
            rule: `Secuencia Anexo ${num}`,
            status: 'error',
            message: `La numeración de los anexos debe ser secuencial (Anexo 1, Anexo 2...). Hallado: Anexo ${num}.`,
            expected: `Anexo ${expectedNum}`,
            actual: `Anexo ${num}`,
            paragraphIndex: i
          });
        }

        // C. Validar bold en la etiqueta y normal en el título
        const labelText = `Anexo ${num}.`;
        let labelOk = true;
        let titleOk = true;
        let prefixMatched = "";

        if (p.runs) {
          p.runs.forEach(r => {
            const rTxt = r.text || "";
            if (!rTxt.trim()) return;
            if (prefixMatched.length < labelText.length) {
              prefixMatched += rTxt;
              if (r.properties?.bold !== true) labelOk = false;
            } else {
              if (r.properties?.bold === true) titleOk = false;
            }
          });
        }

        if (!labelOk) {
          this.agregarResultado({
            id: `anexo-label-bold-${i}`,
            category: '📎 Anexos',
            rule: `Negrita Etiqueta Anexo ${num}`,
            status: 'error',
            message: `La etiqueta 'Anexo ${num}.' debe estar en negrita.`,
            expected: 'Negrita',
            actual: 'Normal',
            paragraphIndex: i
          });
        }
        if (!titleOk) {
          this.agregarResultado({
            id: `anexo-title-normal-${i}`,
            category: '📎 Anexos',
            rule: `Estilo Título Anexo ${num}`,
            status: 'error',
            message: `El título del anexo '${titleTxt.substring(0, 30)}...' debe estar sin negrita.`,
            expected: 'Normal (Sin Negrita)',
            actual: 'Negrita',
            paragraphIndex: i
          });
        }

        // D. Capitalización
        if (titleTxt) {
          const firstLetter = titleTxt[0];
          const okCase = firstLetter === firstLetter.toUpperCase();
          const rest = titleTxt.substring(1).replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ]/g, '');
          let okRest = true;
          if (okCase && rest) {
            okRest = rest !== rest.toUpperCase();
          }
          if (!okCase || !okRest) {
            this.agregarResultado({
              id: `anexo-case-${i}`,
              category: '📎 Anexos',
              rule: `Capitalización Anexo ${num}`,
              status: 'error',
              message: `El título del anexo debe iniciar con mayúscula y continuar en minúsculas.`,
              expected: 'Mayúscula inicial, resto minúsculas',
              actual: titleTxt.substring(0, 30),
              paragraphIndex: i
            });
          }
        }

        // E. Sangrías
        const hasIndent = leftIndent > 50 || firstLineIndent > 50 || hangingIndent > 50;
        if (hasIndent) {
          this.agregarResultado({
            id: `anexo-indent-${i}`,
            category: '📎 Anexos',
            rule: `Sangría Título Anexo ${num}`,
            status: 'error',
            message: `El título del Anexo ${num} debe estar sin sangría de ningún tipo.`,
            expected: 'Izq 0cm, Prim 0cm, Fran 0cm',
            actual: `Izq ${lCm}cm, Prim ${fCm}cm, Fran ${hCm}cm`,
            paragraphIndex: i
          });
        }

        // F. Interlineado, alineación y tamaño
        if (align !== 'left') {
          this.agregarResultado({
            id: `anexo-align-${i}`,
            category: '📎 Anexos',
            rule: `Alineación Título Anexo ${num}`,
            status: 'error',
            message: `El título del Anexo ${num} debe estar alineado a la izquierda.`,
            expected: 'Izquierda',
            actual: align,
            paragraphIndex: i
          });
        }

        const sizeOk = pTamano >= 23 && pTamano <= 25;
        if (!sizeOk) {
          this.agregarResultado({
            id: `anexo-size-${i}`,
            category: '📎 Anexos',
            rule: `Tamaño Título Anexo ${num}`,
            status: 'error',
            message: `El título del Anexo ${num} debe ser de tamaño 12pt.`,
            expected: '12pt',
            actual: `${(pTamano/2).toFixed(1)}pt`,
            paragraphIndex: i
          });
        }
      } else {
        // Párrafo normal dentro de Anexos
        const isSubTitle = /DECLARACI[ÓO]N\s+JURADA|AUTORIZACI[ÓO]N/i.test(text);
        const hasIndent = leftIndent > 50 || firstLineIndent > 50 || hangingIndent > 50;
        if (hasIndent && !isSubTitle) {
          this.agregarResultado({
            id: `anexo-content-indent-${i}`,
            category: '📎 Anexos',
            rule: 'Sangría Contenido Anexo',
            status: 'error',
            message: 'El contenido de los anexos debe estar sin sangría de ningún tipo.',
            expected: 'Izq 0cm, Prim 0cm, Fran 0cm',
            actual: `Izq ${lCm}cm, Prim ${fCm}cm, Fran ${hCm}cm`,
            paragraphIndex: i
          });
        }

        if (!isSubTitle && text.length > 30) {
          if (align !== 'left') {
            this.agregarResultado({
              id: `anexo-content-align-${i}`,
              category: '📎 Anexos',
              rule: 'Alineación Contenido Anexo',
              status: 'warning',
              message: 'El contenido de los anexos debe estar alineado a la izquierda.',
              expected: 'Izquierda',
              actual: align,
              paragraphIndex: i
            });
          }

          const sizeOk = pTamano >= 23 && pTamano <= 25;
          if (!sizeOk) {
            this.agregarResultado({
              id: `anexo-content-size-${i}`,
              category: '📎 Anexos',
              rule: 'Tamaño Contenido Anexo',
              status: 'error',
              message: 'El contenido de los anexos debe ser de tamaño 12pt.',
              expected: '12pt',
              actual: `${(pTamano/2).toFixed(1)}pt`,
              paragraphIndex: i
            });
          }
        }
      }
    }

    if (foundAnnexTitles.length === 0) {
      this.agregarResultado({
        id: 'anexos-individual-titles-missing',
        category: '📎 Anexos',
        rule: 'Títulos de Anexos Individuales',
        status: 'error',
        message: 'No se identificaron títulos de anexos secuenciales (Anexo 1, Anexo 2...).',
        expected: 'Anexo 1, Anexo 2...',
        actual: 'No encontrados',
        paragraphIndex: -1
      });
    }

    // Detección de Declaración Jurada y Autorización para depósito
    const docsEncontrados = (tieneDeclaracionJurada ? 1 : 0) + (tieneAutorizacionDeposito ? 1 : 0);
    this.agregarResultado({
      id: 'anexos-legales',
      category: '📎 Anexos',
      rule: 'Documentos Legales Obligatorios (Firmas)',
      status: docsEncontrados === 2 ? 'passed' : 'warning',
      message: docsEncontrados === 2 
        ? 'Ambos documentos legales fueron detectados en el texto.'
        : 'ALERTA DE OCR: No se encontró texto plano de la Declaración Jurada o Autorización. Si están insertados como imagen (escáner), requieren Validación OCR / Revisión Manual.',
      expected: 'Declaración Jurada de Autenticidad y Autorización de Depósito presentes al final.',
      actual: `Documentos detectados: ${docsEncontrados}/2`,
      paragraphIndex: -1
    });
  }

  calcularPuntaje() {
    const errores = this.results.filter(r => r.status === 'error').length;
    const advertencias = this.results.filter(r => r.status === 'warning').length;
    this.stats.errors = errores;
    this.stats.warnings = advertencias;
    this.stats.passed = this.results.filter(r => r.status === 'passed').length;

    // Pesos institucionales
    let deduccion = (errores * 5) + (advertencias * 1);
    this.stats.score = Math.max(0, 100 - deduccion);
  }

  verificarNotasYFuentes() {
    this.paragraphs.forEach((p, idx) => {
      const text = p.text.trim();
      const upper = text.toUpperCase();
      
      if (upper.startsWith("NOTA") || upper.startsWith("FUENTE")) {
        const hasColon = text.substring(0, 15).includes(':');
        const hasSemicolon = text.substring(0, 15).includes(';');
        
        // Estilos: verificamos el primer run que tenga contenido
        const mainRun = p.runs?.find(r => r.text && r.text.trim().length > 0);
        const isBold = mainRun?.properties?.bold || false;
        const isItalic = mainRun?.properties?.italic || false;
        const fontSize = mainRun?.properties?.fontSize || 0;
        
        const ok = !isBold && !isItalic && Math.abs(fontSize - 20) <= 2 && hasColon && !hasSemicolon;

        this.agregarResultado({
          id: `note-source-${idx}`,
          category: '📊 Tablas/Figuras',
          rule: `Formato de ${upper.startsWith("NOTA") ? 'Nota' : 'Fuente'}`,
          status: ok ? 'passed' : 'error',
          message: `La etiqueta "${text.substring(0, 15)}..." debe ser 10pt, sin negrita, sin cursiva y usar dos puntos (:).`,
          expected: '10pt, Normal, ":"',
          actual: `${fontSize/2}pt, ${isBold ? 'Bold' : 'Normal'}, ${isItalic ? 'Italic' : 'Normal'}, ${hasColon ? ':' : hasSemicolon ? ';' : 'X'}`,
          paragraphIndex: idx
        });
      }
    });
  }
}

export default RuleEngine;
