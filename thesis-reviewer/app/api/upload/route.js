import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

// We need to import our engine modules
import DocxParser from '../../../lib/engine/docxParser';
import RuleEngine from '../../../lib/engine/ruleEngine';
import DocxAnnotator from '../../../lib/engine/docxAnnotator';
import PdfParser from '../../../lib/engine/pdfParser';
import PdfAnnotator from '../../../lib/engine/pdfAnnotator';

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
    const isDocx = fileName.toLowerCase().endsWith('.docx');
    const isPdf = fileName.toLowerCase().endsWith('.pdf');

    if (!isDocx && !isPdf) {
      return NextResponse.json(
        { error: 'Solo se aceptan archivos .docx (Word) o .pdf. Por favor, suba un formato válido.' },
        { status: 400 }
      );
    }

    // Read file buffer
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // 1. Parse the document
    let parsedDoc;
    if (isDocx) {
      const parser = new DocxParser(buffer);
      parsedDoc = await parser.parse();
    } else {
      const parser = new PdfParser(buffer);
      parsedDoc = await parser.parse();
    }

    // 2. Run the rule engine
    const engine = new RuleEngine(parsedDoc);
    const analysis = engine.analizar();

    // 3. Generate annotated document
    let annotatedBuffer;
    if (isDocx) {
      const annotator = new DocxAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis); // Passing full analysis
    } else {
      const annotator = new PdfAnnotator(buffer);
      annotatedBuffer = await annotator.annotate(analysis); // Passing full analysis
    }

    // 4. Save annotated file temporarily
    const tmpDir = path.join(process.cwd(), 'tmp');
    await mkdir(tmpDir, { recursive: true });
    
    const safeName = fileName.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9.-]/g, '_');
    const annotatedFileName = `revisado_${safeName}`;
    const annotatedPath = path.join(tmpDir, annotatedFileName);
    await writeFile(annotatedPath, annotatedBuffer);

    const annotatedBase64 = annotatedBuffer.toString('base64');

    // 7. Return results
    return NextResponse.json({
      success: true,
      fileName: fileName,
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
