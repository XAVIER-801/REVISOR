import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

// We need to import our engine modules
const DocxParser = require('../../../lib/engine/docxParser');
const RuleEngine = require('../../../lib/engine/ruleEngine');
const DocxAnnotator = require('../../../lib/engine/docxAnnotator');

export const config = {
  api: {
    bodyParser: false,
  },
};

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');

    if (!file) {
      return NextResponse.json({ error: 'No se subió ningún archivo' }, { status: 400 });
    }

    // Validate file type
    const fileName = file.name;
    if (!fileName.toLowerCase().endsWith('.docx')) {
      return NextResponse.json(
        { error: 'Solo se aceptan archivos .docx (Word). Por favor, convierta su documento.' },
        { status: 400 }
      );
    }

    // Read file buffer
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // 1. Parse the DOCX
    const parser = new DocxParser(buffer);
    const parsedDoc = await parser.parse();

    // 2. Run the rule engine
    const engine = new RuleEngine(parsedDoc);
    const results = engine.analyze();

    // 3. Generate annotated DOCX
    const annotator = new DocxAnnotator(buffer);
    const annotatedBuffer = await annotator.annotate(results);

    // 4. Save annotated file temporarily
    const tmpDir = path.join(process.cwd(), 'tmp');
    await mkdir(tmpDir, { recursive: true });
    
    const annotatedFileName = `revisado_${fileName}`;
    const annotatedPath = path.join(tmpDir, annotatedFileName);
    await writeFile(annotatedPath, annotatedBuffer);

    // 5. Also save original buffer for the preview
    const originalPath = path.join(tmpDir, `original_${fileName}`);
    await writeFile(originalPath, buffer);

    // 6. Convert annotated DOCX to base64 for preview
    const annotatedBase64 = annotatedBuffer.toString('base64');

    // 7. Return results
    return NextResponse.json({
      success: true,
      fileName: fileName,
      annotatedFileName: annotatedFileName,
      results: {
        score: results.score,
        totalRules: results.totalRules,
        errorCount: results.errorCount,
        warningCount: results.warningCount,
        passedCount: results.passedCount,
        errors: results.errors.map(e => ({
          id: e.id,
          category: e.category,
          rule: e.rule,
          status: e.status,
          message: e.message,
          expected: e.expected,
          actual: e.actual,
          details: e.details?.slice(0, 5)
        })),
        warnings: results.warnings.map(w => ({
          id: w.id,
          category: w.category,
          rule: w.rule,
          status: w.status,
          message: w.message,
          expected: w.expected,
          actual: w.actual,
          details: w.details?.slice(0, 5)
        })),
        passed: results.passed.map(p => ({
          id: p.id,
          category: p.category,
          rule: p.rule,
          status: p.status,
          message: p.message,
          expected: p.expected,
          actual: p.actual
        }))
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
