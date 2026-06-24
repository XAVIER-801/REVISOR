import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { createServerSupabase } from '../../../lib/supabase-server';

// JS Engine modules (Fallback)
import DocxParser from '../../../lib/engine/docxParser';
import RuleEngine from '../../../lib/engine/ruleEngine';
import DocxAnnotator from '../../../lib/engine/docxAnnotator';
import PdfParser from '../../../lib/engine/pdfParser';
import PdfAnnotator from '../../../lib/engine/pdfAnnotator';

// Python Backend URL (High-Fidelity Engine)
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

/**
 * Guarda los resultados de auditoría en Supabase (tesis + observaciones individuales).
 * Si Supabase no está configurado, se omite silenciosamente.
 */
async function saveAuditToSupabase(fileName, results, annotatedBase64, pyResult) {
  const supabase = createServerSupabase();
  if (!supabase) {
    console.log('[SUPABASE] No configurado — saltando guardado.');
    return null;
  }

  try {
    const allResults = results.results || [];
    const originalSnapshot = allResults.map(r => ({
      rule: r.rule,
      category: r.category,
      status: r.status,
      severity: r.severity,
      actual: r.actual,
      expected: r.expected,
    }));

    // 1. Insertar registro principal de la tesis
    const { data: thesis, error: thesisError } = await supabase
      .from('thesis_audits')
      .insert({
        filename: fileName,
        score: results.score,
        errors_count: results.errorCount,
        warnings_count: results.warningCount,
        passed_count: results.passedCount,
        status: 'pending_review',
        annotated_docx_base64: annotatedBase64 || null,
        original_results_snapshot: originalSnapshot,
      })
      .select('id')
      .single();

    if (thesisError) {
      console.error('[SUPABASE] Error al guardar tesis:', thesisError.message);
      return null;
    }

    const thesisId = thesis.id;

    // 2. Insertar observaciones individuales (solo errores y warnings)
    const observations = allResults
      .filter(r => r.status === 'error' || r.status === 'warning')
      .map(r => ({
        thesis_id: thesisId,
        rule: r.rule || '',
        category: r.category || '',
        severity: r.severity || r.status,
        message: r.message || '',
        expected: r.expected ? String(r.expected).substring(0, 500) : null,
        actual: r.actual ? String(r.actual).substring(0, 500) : null,
        paragraph_index: r.paragraphIndex ?? null,
        paragraph_text: r.paragraphText ? String(r.paragraphText).substring(0, 1000) : null,
        status: 'pending',
      }));

    if (observations.length > 0) {
      const { error: obsError } = await supabase
        .from('thesis_observations')
        .insert(observations);

      if (obsError) {
        console.error('[SUPABASE] Error al guardar observaciones:', obsError.message);
      }
    }

    console.log(`[SUPABASE] Tesis guardada: ${thesisId} — ${observations.length} observaciones.`);
    return thesisId;

  } catch (err) {
    console.error('[SUPABASE] Error inesperado:', err.message);
    return null;
  }
}

/**
 * Intenta enviar el archivo al Motor Python de Alta Fidelidad.
 * Si Python no está disponible, retorna null para usar el fallback JS.
 */
async function tryPythonEngine(file, fileName) {
  try {
    const pythonForm = new FormData();
    pythonForm.append('file', file, fileName);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 900000); // 15 min timeout

    const response = await fetch(`${PYTHON_API_URL}/audit`, {
      method: 'POST',
      body: pythonForm,
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      console.warn(`[PYTHON-ENGINE] HTTP ${response.status}: ${await response.text()}`);
      return null;
    }

    const pyResult = await response.json();
    console.log(`[PYTHON-ENGINE] Auditoría completada. Score: ${pyResult.stats?.score}`);
    return pyResult;
  } catch (err) {
    console.warn(`[PYTHON-ENGINE] No disponible (${err.message}). Usando motor JS local.`);
    return null;
  }
}

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');

    if (!file) {
      return NextResponse.json({ error: 'No se subió ningún archivo' }, { status: 400 });
    }

    // Validate file type
    const fileName = file.name;
    const isDocx = fileName.toLowerCase().endsWith('.docx');
    const isPdf = fileName.toLowerCase().endsWith('.pdf');
    const isDoc = fileName.toLowerCase().endsWith('.doc');

    if (!isDocx && !isPdf && !isDoc) {
      return NextResponse.json(
        { error: 'Solo se aceptan archivos .docx, .doc (Word) o .pdf. Por favor, suba un formato válido.' },
        { status: 400 }
      );
    }

    // Read file buffer
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // ===== ESTRATEGIA HÍBRIDA =====
    if (isDoc || isDocx) {
      const pyResult = await tryPythonEngine(file, fileName);
      if (pyResult) {
        const resultsData = {
          score: pyResult.stats.score,
          totalRules: pyResult.results.length,
          errorCount: pyResult.stats.errors,
          warningCount: pyResult.stats.warnings,
          passedCount: pyResult.results.filter(r => r.status === 'passed').length,
          results: pyResult.results
        };

        // Guardar en Supabase de forma asíncrona (no bloquea la respuesta)
        const annotatedBase64 = pyResult.annotatedBase64 || null;
        saveAuditToSupabase(fileName, resultsData, annotatedBase64, pyResult)
          .catch(err => console.error('[SUPABASE] Error en guardado asíncrono:', err));

        return NextResponse.json({
          success: true,
          fileName: fileName,
          engine: 'python-hifi',
          annotatedBase64: pyResult.annotatedBase64,
          annotatedFileName: `auditada_${fileName}`,
          results: resultsData
        });
      }
      
      return NextResponse.json(
        { error: 'El Motor de Alta Fidelidad (Python) no está respondiendo. Por favor, reinicie el contenedor con "docker-compose restart".' },
        { status: 503 }
      );
    }

    // ===== FALLBACK: Motor JS Local =====
    console.log('[JS-ENGINE] Usando motor JavaScript local.');

    let parsedDoc;
    const parsePromise = isDocx 
      ? new DocxParser(buffer).parse() 
      : new PdfParser(buffer).parse();

    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Procesamiento demasiado largo (15 min).')), 900000)
    );

    parsedDoc = await Promise.race([parsePromise, timeoutPromise]);

    const engine = new RuleEngine(parsedDoc);
    const analysis = engine.analizar();

    let annotatedBuffer;
    if (isDocx) {
      const annotator = new DocxAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis);
    } else {
      const annotator = new PdfAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis);
    }

    const tmpDir = path.join(process.cwd(), 'tmp');
    await mkdir(tmpDir, { recursive: true });
    
    const safeName = fileName.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9.-]/g, '_');
    const annotatedFileName = `revisado_${safeName}`;
    const annotatedPath = path.join(tmpDir, annotatedFileName);
    await writeFile(annotatedPath, annotatedBuffer);

    const annotatedBase64 = annotatedBuffer.toString('base64');

    const resultsData = {
      score: analysis.stats.score,
      totalRules: analysis.results.length,
      errorCount: analysis.stats.errors,
      warningCount: analysis.stats.warnings,
      passedCount: analysis.stats.passed,
      results: analysis.results
    };

    // Guardar en Supabase
    saveAuditToSupabase(fileName, resultsData, annotatedBase64, null)
      .catch(err => console.error('[SUPABASE] Error en guardado asíncrono:', err));

    return NextResponse.json({
      success: true,
      fileName: fileName,
      engine: 'js-local',
      annotatedFileName: annotatedFileName,
      results: resultsData,
      annotatedBase64: annotatedBase64,
      paragraphCount: parsedDoc.paragraphs.length
    });

  } catch (error) {
    console.error('Error processing document:', error);
    return NextResponse.json(
      { error: `Error al procesar el documento: ${error.message}` },
      { status: 500 }
    );
  }
}
