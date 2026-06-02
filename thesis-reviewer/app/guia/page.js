'use client';

import { useState } from 'react';
import {
  Upload, FileText, CheckCircle, Eye, Download,
  AlertCircle, BookOpen, Layers, Activity, ChevronRight,
  Shield, Sparkles, Type, AlignLeft, ListChecks, Brain,
  HelpCircle, ArrowRight, MousePointer2
} from 'lucide-react';

export default function Guia() {
  const [openFaq, setOpenFaq] = useState(null);

  const steps = [
    {
      num: '01',
      icon: <Upload size={28} />,
      title: 'Sube tu tesis en formato Word',
      body: 'Arrastra tu archivo .docx (Word) a la pantalla principal o haz clic en "Subir Tesis". El sistema acepta archivos hasta 50 MB. Si tu archivo es .doc antiguo, también funciona, se convierte automáticamente.',
      tip: 'Asegúrate de cerrar el archivo en Word antes de subirlo.',
    },
    {
      num: '02',
      icon: <Activity size={28} />,
      title: 'Espera a que el motor analice',
      body: 'El motor experto Python recorre 30+ auditores: portada, índices, capítulos, tablas, figuras, viñetas, anexos, hoja de jurados, ortografía, citas y mucho más. Esto suele tardar 30 segundos a 2 minutos según el tamaño.',
      tip: 'No cierres la pestaña hasta ver el reporte. Tu archivo se elimina automáticamente del servidor por privacidad.',
    },
    {
      num: '03',
      icon: <Eye size={28} />,
      title: 'Revisa el reporte interactivo',
      body: 'En la web tendrás un dashboard con tu puntaje de cumplimiento, errores críticos, advertencias y observaciones por categoría. Puedes filtrar y ver cada hallazgo con su contexto.',
      tip: 'Haz clic en una categoría del dashboard para ver solo esas observaciones.',
    },
    {
      num: '04',
      icon: <Download size={28} />,
      title: 'Descarga el Word auditado',
      body: 'Recibirás tu mismo documento de vuelta con comentarios al margen estilo Turnitin: resaltado rojo = error crítico, amarillo = advertencia, verde = sugerencia ortográfica. Cada comentario te dice exactamente qué corregir.',
      tip: 'Abre el archivo en Word de escritorio para ver los comentarios al margen de forma óptima.',
    },
    {
      num: '05',
      icon: <CheckCircle size={28} />,
      title: 'Corrige y vuelve a subir',
      body: 'Aplica las correcciones en tu Word original. Cuando estés listo, vuelve a subir el archivo para verificar que el puntaje subió y que ya no quedan errores críticos.',
      tip: 'El objetivo es llegar al menos a 90/100 antes del depósito en el Repositorio Institucional.',
    },
  ];

  const colorLegend = [
    {
      color: '#FF4D4D',
      label: 'Rojo (Error crítico)',
      desc: 'Bloquea el depósito en el Repositorio Institucional. Debes corregirlo obligatoriamente.',
    },
    {
      color: '#FFC107',
      label: 'Amarillo (Advertencia)',
      desc: 'Aspecto a mejorar para una tesis de alta calidad. No bloquea el depósito pero se recomienda corregir.',
    },
    {
      color: '#22c55e',
      label: 'Verde (Sugerencia ortográfica)',
      desc: 'Posible error tipográfico detectado por el corrector ortográfico. Revisa y corrige si aplica.',
    },
    {
      color: '#14b8a6',
      label: 'Turquesa (Observación menor)',
      desc: 'Observaciones de estilo y formato de baja prioridad. Considéralas pero no son críticas.',
    },
  ];

  const features = [
    { icon: <Layers />, title: '30+ auditores especializados', desc: 'Portada, índices, capítulos (nivel 1-5), tablas, figuras, viñetas, anexos obligatorios, citas, ortografía y más.' },
    { icon: <Brain />, title: 'IA propia (sin servicios pagos)', desc: 'Sistema de aprendizaje progresivo que mejora con cada tesis. Detecta patrones y da sugerencias personalizadas.' },
    { icon: <Type />, title: 'OCR de documentos escaneados', desc: 'Reconoce texto en imágenes (Hoja de Jurados, Turnitin, Autorización) usando Tesseract OCR.' },
    { icon: <Shield />, title: 'Privacidad total', desc: 'Tu archivo se procesa en memoria efímera y se elimina inmediatamente. No queda copia en el servidor.' },
    { icon: <AlignLeft />, title: 'Comentarios estilo Turnitin', desc: 'Cada error tiene un comentario formal al margen con regla, hallazgo, requerido y sugerencia.' },
    { icon: <Sparkles />, title: 'Detecta evasión Turnitin', desc: 'Encuentra texto en cuadros de texto o capturas de pantalla — técnicas para esquivar verificadores de similitud.' },
  ];

  const faqs = [
    {
      q: '¿El sistema reemplaza al revisor humano?',
      a: 'No. El sistema verifica formato y estructura según la Guía UNAP 2.0. La revisión de contenido académico (originalidad, rigor metodológico, profundidad) sigue siendo responsabilidad de tu asesor y los jurados.',
    },
    {
      q: '¿Puedo usar el sistema antes de la versión final?',
      a: 'Sí, y se recomienda. Mientras más temprano detectes los errores de formato, menos trabajo tendrás al cierre. Puedes usarlo tantas veces como quieras.',
    },
    {
      q: '¿Qué pasa si mi tesis tiene fórmulas matemáticas o tablas complejas?',
      a: 'El motor detecta fórmulas (OMML) y las trata como elementos especiales, sin auditarlas como texto. Las tablas se evalúan en su estructura y formato, no en el contenido numérico.',
    },
    {
      q: '¿Detecta plagio?',
      a: 'No directamente. Para verificar similitud usa Turnitin. Pero sí detecta técnicas comunes de evasión: texto en cuadros de texto y capturas de pantalla con texto.',
    },
    {
      q: '¿Por qué algunos comentarios aparecen como verdes y no como errores?',
      a: 'Los verdes son sugerencias ortográficas (faltas tipográficas detectadas por el corrector). No son errores que bloqueen el depósito, pero corregirlas eleva la calidad. Algunos pueden ser falsos positivos en términos técnicos.',
    },
    {
      q: '¿Funciona con tesis de Maestría y Doctorado?',
      a: 'Sí. La Guía UNAP aplica a Pregrado, Maestría, Doctorado y Segundas Especialidades. El sistema detecta automáticamente el tipo de grado de tu portada.',
    },
    {
      q: '¿Mi tesis queda guardada en el servidor?',
      a: 'No. El archivo se procesa en memoria efímera y se elimina inmediatamente después. Solo guardamos estadísticas anónimas (puntaje, tipo de errores) para mejorar el sistema.',
    },
    {
      q: '¿Por qué obtengo un score tan bajo?',
      a: 'El sistema es estricto: cada regla de la Guía UNAP cuenta. Una tesis bien formateada típicamente obtiene 85+. Lo importante no es el número en sí, sino que no queden errores críticos (rojos) sin corregir.',
    },
  ];

  return (
    <main className="container-crypto animate-reveal" style={{ paddingTop: '5rem', paddingBottom: '5rem' }}>
      {/* HERO */}
      <section style={{ textAlign: 'center', marginBottom: '6rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(69, 245, 229, 0.08)', padding: '0.6rem 1.5rem', borderRadius: '50px', marginBottom: '2.5rem', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
          <HelpCircle size={18} className="text-accent" />
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#45F5E5', textTransform: 'uppercase', letterSpacing: '0.2em' }}>Guía de Uso Paso a Paso</span>
        </div>
        <h1 style={{ fontSize: '4.5rem', fontWeight: 900, letterSpacing: '-0.05em', lineHeight: '1.05', marginBottom: '1.5rem' }}>
          Aprende a usar <span className="text-gradient">RepoStyle</span><br />
          en 5 pasos simples
        </h1>
        <p style={{ fontSize: '1.05rem', color: '#94A3B8', maxWidth: '700px', margin: '0 auto 3rem', lineHeight: '1.7' }}>
          Audita tu tesis contra las normas oficiales de la Guía de Presentación 2.0 del Vicerrectorado de Investigación UNAP. Sin instalar nada, en menos de 5 minutos.
        </p>
        <a href="/" className="btn-crypto animate-glow" style={{ padding: '1.2rem 3rem', fontSize: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.75rem' }}>
          Empezar ahora <ArrowRight size={20} />
        </a>
      </section>

      {/* STEPS */}
      <section style={{ marginBottom: '6rem' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          Proceso de auditoría
        </h2>
        <p style={{ color: '#94A3B8', marginBottom: '3rem' }}>
          Cinco pasos. Sin instalación. Sin registro.
        </p>
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {steps.map((s, i) => (
            <StepCard key={i} step={s} />
          ))}
        </div>
      </section>

      {/* LEYENDA DE COLORES */}
      <section style={{ marginBottom: '6rem' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          Leyenda de colores en el Word auditado
        </h2>
        <p style={{ color: '#94A3B8', marginBottom: '3rem' }}>
          Cuando descargues tu Word auditado, verás resaltados de distintos colores y comentarios al margen. Significan esto:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {colorLegend.map((c, i) => (
            <div key={i} className="category-card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: c.color, boxShadow: `0 0 12px ${c.color}80` }} />
                <span style={{ fontWeight: 900, fontSize: '0.9rem' }}>{c.label}</span>
              </div>
              <p style={{ color: '#94A3B8', fontSize: '0.85rem', lineHeight: '1.6' }}>
                {c.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CAPACIDADES */}
      <section style={{ marginBottom: '6rem' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          ¿Qué audita exactamente?
        </h2>
        <p style={{ color: '#94A3B8', marginBottom: '3rem' }}>
          30+ auditores especializados cubren cada aspecto de la Guía UNAP 2.0.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
          {features.map((f, i) => (
            <div key={i} className="category-card" style={{ padding: '2rem' }}>
              <div style={{ color: '#45F5E5', marginBottom: '1rem' }}>{f.icon}</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 900, marginBottom: '0.5rem' }}>{f.title}</h3>
              <p style={{ color: '#94A3B8', fontSize: '0.85rem', lineHeight: '1.6' }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CONSEJOS RAPIDOS */}
      <section style={{ marginBottom: '6rem' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          Errores más comunes que te van a aparecer
        </h2>
        <p style={{ color: '#94A3B8', marginBottom: '3rem' }}>
          Adelántate. Estos son los errores que el 80% de las tesis tienen.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {[
            { title: 'Doble espacio entre palabras', tip: 'Usa Ctrl+H para reemplazar "  " (dos espacios) por " " (uno) en todo el documento.' },
            { title: 'Enters múltiples en lugar de Salto de página', tip: 'Borra los enters consecutivos y usa Ctrl+Enter para insertar un salto de página real.' },
            { title: 'Sangría francesa incorrecta en niveles 3-5', tip: 'Nivel 3: Izq 1.25 / Francesa 1.25. Niveles 4-5: Izq 2.5 / Francesa 1.5.' },
            { title: 'CAPÍTULO sin tilde', tip: 'Escribe "CAPÍTULO" siempre con tilde. Lo mismo para "TÍTULO".' },
            { title: '"Palabras clave:" sin negrita', tip: 'La etiqueta "Palabras clave:" debe estar en negrita. Las palabras clave en sí: primera letra mayúscula, separadas por comas, orden alfabético.' },
            { title: 'Margen izquierdo incorrecto', tip: 'Debe ser exactamente 3.5 cm (es el de encuadernación). Los otros tres márgenes son 2.5 cm.' },
            { title: 'Nota: o Fuente: sin cursiva', tip: 'La palabra "Nota:" o "Fuente:" debajo de tablas y figuras debe estar en cursiva, con dos puntos, sin negrita.' },
            { title: 'Tabla centrada en lugar de izquierda', tip: 'Las tablas y figuras van alineadas a la izquierda. La sangría de su título es la que las posiciona según el nivel.' },
          ].map((c, i) => (
            <div key={i} className="category-card" style={{ padding: '1.5rem' }}>
              <h4 style={{ fontWeight: 800, fontSize: '0.9rem', marginBottom: '0.5rem', color: '#FFC107' }}>{c.title}</h4>
              <p style={{ color: '#94A3B8', fontSize: '0.8rem', lineHeight: '1.6' }}>{c.tip}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section style={{ marginBottom: '6rem' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          Preguntas frecuentes
        </h2>
        <p style={{ color: '#94A3B8', marginBottom: '3rem' }}>
          Resuelve dudas antes de empezar.
        </p>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {faqs.map((f, i) => (
            <div
              key={i}
              className="category-card"
              style={{ padding: '1.5rem 2rem', cursor: 'pointer' }}
              onClick={() => setOpenFaq(openFaq === i ? null : i)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>{f.q}</span>
                <ChevronRight
                  size={20}
                  style={{
                    transition: 'transform 0.3s',
                    transform: openFaq === i ? 'rotate(90deg)' : 'rotate(0deg)',
                    color: '#45F5E5',
                  }}
                />
              </div>
              {openFaq === i && (
                <p style={{ color: '#94A3B8', fontSize: '0.9rem', lineHeight: '1.7', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  {f.a}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="card-elite" style={{ padding: '4rem 2rem', textAlign: 'center', background: 'linear-gradient(135deg, rgba(69, 245, 229, 0.05), rgba(157, 80, 255, 0.05))', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
        <Sparkles size={48} className="text-accent" style={{ margin: '0 auto 2rem' }} />
        <h2 style={{ fontSize: '2.5rem', fontWeight: 900, marginBottom: '1rem' }}>
          ¿Listo para auditar tu tesis?
        </h2>
        <p style={{ color: '#94A3B8', maxWidth: '500px', margin: '0 auto 2rem' }}>
          Sin registro. Sin instalación. Tu archivo se procesa de forma privada y se elimina inmediatamente.
        </p>
        <a href="/" className="btn-crypto animate-glow" style={{ padding: '1.2rem 3rem', fontSize: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.75rem' }}>
          Empezar ahora <MousePointer2 size={20} />
        </a>
      </section>
    </main>
  );
}

function StepCard({ step }) {
  return (
    <div className="card-elite" style={{ padding: '2rem 2.5rem', display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2rem', alignItems: 'start' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ background: 'rgba(69, 245, 229, 0.08)', borderRadius: '16px', padding: '1.25rem', color: '#45F5E5', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
          {step.icon}
        </div>
        <div style={{ fontSize: '0.85rem', fontWeight: 900, color: '#64748B', letterSpacing: '0.15em' }}>{step.num}</div>
      </div>
      <div>
        <h3 style={{ fontSize: '1.4rem', fontWeight: 900, marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
          {step.title}
        </h3>
        <p style={{ color: '#CBD5E1', fontSize: '0.95rem', lineHeight: '1.7', marginBottom: '1rem' }}>
          {step.body}
        </p>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', padding: '1rem 1.25rem', background: 'rgba(255, 193, 7, 0.06)', borderLeft: '3px solid #FFC107', borderRadius: '0 8px 8px 0' }}>
          <AlertCircle size={16} style={{ color: '#FFC107', marginTop: '2px', flexShrink: 0 }} />
          <p style={{ color: '#FFC107', fontSize: '0.85rem', fontWeight: 600, lineHeight: '1.5' }}>
            <strong>Consejo:</strong> {step.tip}
          </p>
        </div>
      </div>
    </div>
  );
}
