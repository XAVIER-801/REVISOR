import pdf from 'pdf-parse/lib/pdf-parse.js';

class PdfParser {
  constructor(buffer) {
    this.buffer = buffer;
  }

  async parse() {
    const pageInfos = [];
    const paragraphs = [];
    const allLines = [];

    if (!this.buffer) {
      throw new Error("No PDF buffer provided to Parser");
    }

    // Ensure we are working with a proper Buffer
    const pdfBuffer = Buffer.isBuffer(this.buffer) ? this.buffer : Buffer.from(this.buffer);

    const options = {
      pagerender: async (pageData) => {
        const textContent = await pageData.getTextContent();
        const textItems = textContent.items;
        let minX = 1000, minY = 1000, maxX = 0, maxY = 0;
        const lines = [];

        textItems.forEach(item => {
          const { str, width, height, transform } = item;
          const x = transform[4];
          const y = transform[5];
          const fontName = (item.fontName || '').toLowerCase();
          const isBold = fontName.includes('bold') || fontName.includes('-bd') || fontName.includes('700') || fontName.includes('medi');

          if (str.trim()) {
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x + width);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y + height);
          }

          let line = lines.find(l => Math.abs(l.y - y) < 5);
          if (!line) {
            line = { y, x, runs: [], fonts: new Set(), pageTextCount: textItems.length };
            lines.push(line);
          }
          line.runs.push({ text: str, font: fontName, x, properties: { bold: isBold, fontSize: height * 2 } });
          if (str.trim()) line.fonts.add(fontName);
        });

        pageInfos.push({ width: maxX, height: maxY });
        lines.sort((a, b) => b.y - a.y);
        
        const pageNum = pageInfos.length;
        lines.forEach(l => l.page = pageNum);
        allLines.push(...lines);
        
        return "";
      }
    };

    await pdf(pdfBuffer, options);

    let currentPara = null;
    allLines.forEach((line, lineIdx) => {
      const text = line.runs.map(r => r.text).join('').trim();
      if (text === "") return;

      const prevLine = allLines[lineIdx - 1];
      const isClose = prevLine && Math.abs(prevLine.y - line.y) < 35 && prevLine.page === line.page;

      if (isClose && currentPara) {
        const firstLineX = currentPara.startX || 0;
        const currentLineX = line.x || 0;
        if (currentLineX > firstLineX + 40) {
          currentPara.properties.hangingIndent = (currentLineX - firstLineX) * 20; 
        }

        currentPara.text += " " + text;
        currentPara.runs.push(...line.runs.map(r => ({ text: r.text, properties: r.properties })));
        currentPara.y = Math.min(currentPara.y, line.y);
      } else {
        // Alignment Heuristic for PDF
        const pageWidth = pageInfos[line.page - 1]?.width || 595;
        const lineCenterX = line.x + (line.width || 0) / 2;
        let alignment = 'left';
        if (Math.abs(lineCenterX - pageWidth / 2) < 50) alignment = 'center';
        else if (line.x > pageWidth / 2) alignment = 'right';

        currentPara = {
          text: text,
          index: paragraphs.length,
          page: line.page,
          y: line.y,
          startX: line.x,
          bbox: pageInfos[line.page - 1],
          runs: line.runs.map(r => ({ text: r.text, properties: r.properties })),
          properties: { 
            lineSpacing: 240, 
            hangingIndent: 0,
            alignment: alignment
          },
          isImagePage: line.pageTextCount < 10
        };
        paragraphs.push(currentPara);
      }
    });

    return {
      paragraphs: paragraphs,
      sectionProps: pageInfos[0] || { width: 612, height: 792 }
    };
  }
}

export default PdfParser;
