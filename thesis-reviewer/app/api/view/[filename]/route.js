import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request, { params }) {
  try {
    const { filename } = params;
    const tmpDir = path.join(process.cwd(), 'tmp');
    const filePath = path.join(tmpDir, filename);

    if (!fs.existsSync(filePath)) {
      return new Response('Archivo no encontrado', { status: 404 });
    }

    const fileBuffer = fs.readFileSync(filePath);
    
    // Determine content type
    const contentType = filename.toLowerCase().endsWith('.pdf') 
      ? 'application/pdf' 
      : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

    return new Response(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `inline; filename="${filename}"`,
      },
    });
  } catch (error) {
    console.error('Error serving file:', error);
    return new Response('Error interno', { status: 500 });
  }
}
