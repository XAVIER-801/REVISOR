import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

// JS Engine modules (Fallback)
import DocxParser from '../../../lib/engine/docxParser';
import RuleEngine from '../../../lib/engine/ruleEngine';
import DocxAnnotator from '../../../lib/engine/docxAnnotator';
import PdfParser from '../../../lib/engine/pdfParser';
import PdfAnnotator from '../../../lib/engine/pdfAnnotator';

// Python Backend URL (High-Fidelity Engine)
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

/**
 * Intenta enviar el archivo al Motor Python de Alta Fidelidad.
 * Si Python no está disponible, retorna null para usar el fallback JS.
 */
async function tryPythonEngine(file, fileName) {
  try {
    const pythonForm = new FormData();
    pythonForm.append('file', file, fileName);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

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
    // 1. Intentar Motor Python (Alta Fidelidad) primero
    // 2. Si falla, usar Motor JS local (Fallback)

    // Para archivos .doc y .docx, USAR SIEMPRE el motor Python (Alta Fidelidad)
    if (isDoc || isDocx) {
      const pyResult = await tryPythonEngine(file, fileName);
      if (pyResult) {
        return NextResponse.json({
          success: true,
          fileName: fileName,
          engine: 'python-hifi',
          annotatedBase64: pyResult.annotatedBase64, // Usar la anotación de Python
          results: {
            score: pyResult.stats.score,
            totalRules: pyResult.results.length,
            errorCount: pyResult.stats.errors,
            warningCount: pyResult.stats.warnings,
            passedCount: pyResult.results.filter(r => r.status === 'passed').length,
            results: pyResult.results
          }
        });
      }
      
      return NextResponse.json(
        { error: 'El Motor de Alta Fidelidad (Python) no está respondiendo. Por favor, reinicie el contenedor con "docker-compose restart".' },
        { status: 503 }
      );
    }

    // ===== FALLBACK: Motor JS Local =====
    console.log('[JS-ENGINE] Usando motor JavaScript local.');

    // 1. Parse the document with timeout protection
    let parsedDoc;
    const parsePromise = isDocx 
      ? new DocxParser(buffer).parse() 
      : new PdfParser(buffer).parse();

    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Procesamiento demasiado largo (3 min).')), 180000)
    );

    parsedDoc = await Promise.race([parsePromise, timeoutPromise]);

    // 2. Run the rule engine
    const engine = new RuleEngine(parsedDoc);
    const analysis = engine.analizar();

    // 3. Generate annotated document
    let annotatedBuffer;
    if (isDocx) {
      const annotator = new DocxAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis);
    } else {
      const annotator = new PdfAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis);
    }

    // 4. Save annotated file temporarily
    const tmpDir = path.join(process.cwd(), 'tmp');
    await mkdir(tmpDir, { recursive: true });
    
    const safeName = fileName.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9.-]/g, '_');
    const annotatedFileName = `revisado_${safeName}`;
    const annotatedPath = path.join(tmpDir, annotatedFileName);
    await writeFile(annotatedPath, annotatedBuffer);

    const annotatedBase64 = annotatedBuffer.toString('base64');

    return NextResponse.json({
      success: true,
      fileName: fileName,
      engine: 'js-local',
      annotatedFileName: annotatedFileName,
      results: {
        score: analysis.stats.score,
        totalRules: analysis.results.length,
        errorCount: analysis.stats.errors,
        warningCount: analysis.stats.warnings,
        passedCount: analysis.stats.passed,
        results: analysis.results
      },
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
