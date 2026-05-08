const fs = require('fs');
const path = require('path');

async function extractPdf() {
  const { PDFParse } = require('pdf-parse');
  const pdfPath = path.join(__dirname, 'GUIA DE FORMATO DE TESIS 2.0.pdf');
  const dataBuffer = fs.readFileSync(pdfPath);
  const uint8 = new Uint8Array(dataBuffer);
  const parser = new PDFParse(uint8);
  const data = await parser.getText();
  
  const outputPath = path.join(__dirname, 'guia_formato_texto.txt');
  fs.writeFileSync(outputPath, typeof data === 'string' ? data : JSON.stringify(data, null, 2), 'utf-8');
  console.log('PDF extracted successfully');
  console.log('\n--- CONTENT ---\n');
  console.log(typeof data === 'string' ? data : JSON.stringify(data, null, 2));
}

extractPdf().catch(console.error);
