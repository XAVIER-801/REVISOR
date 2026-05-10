import { createWorker, createScheduler } from 'tesseract.js';

/**
 * OCR Engine - Processes images to extract text using a pool of workers
 */
class OCREngine {
  constructor() {
    this.scheduler = null;
    this.initialized = false;
    this.workerCount = 2; // Reduced to 2 for better stability on Windows
    this.isInitializing = false;
  }

  async _init() {
    if (this.initialized || this.isInitializing) return;
    this.isInitializing = true;
    
    try {
      this.scheduler = createScheduler();
      
      for (let i = 0; i < this.workerCount; i++) {
        // En Next.js/Node, a veces Tesseract falla al autodetectar el worker.
        // Intentamos una inicialización básica.
        const worker = await createWorker('spa'); 
        this.scheduler.addWorker(worker);
      }
      
      this.initialized = true;
      console.log('OCR Engine: Ready with', this.workerCount, 'workers');
    } catch (error) {
      console.error('OCR Engine Initialization Failed:', error);
      this.initialized = false;
    } finally {
      this.isInitializing = false;
    }
  }

  /**
   * Recognize text from a buffer (Buffer, Uint8Array, etc.)
   */
  async recognize(imageBuffer) {
    // Si el OCR falla en inicializar, no bloqueamos el sistema
    try {
      if (!this.initialized && !this.isInitializing) {
        await this._init();
      }

      if (!this.initialized) {
        console.warn('OCR requested but engine not ready. Skipping image.');
        return '';
      }

      // Añadimos un timeout manual de 10 segundos por imagen (Velocidad Turbo)
      const ocrPromise = this.scheduler.addJob('recognize', imageBuffer);
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('OCR Timeout')), 10000)
      );

      const result = await Promise.race([ocrPromise, timeoutPromise]);
      return result.data.text;
    } catch (error) {
      console.error('OCR Recognition Error:', error.message);
      return ''; // Devolvemos vacío pero permitimos que el sistema siga
    }
  }

  /**
   * Terminate the scheduler and all workers
   */
  async terminate() {
    if (this.initialized && this.scheduler) {
      await this.scheduler.terminate();
      this.initialized = false;
    }
  }
}

const ocrEngine = new OCREngine();
export default ocrEngine;
