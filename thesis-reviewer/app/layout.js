import './globals.css';

export const metadata = {
  title: 'Revisor de Tesis - Universidad Nacional del Altiplano',
  description: 'Sistema automatizado de revisión de formato de tesis para el Repositorio Institucional del Vicerrectorado de Investigación de la UNA Puno.',
  keywords: 'tesis, formato, revisión, UNA Puno, repositorio institucional, Universidad Nacional del Altiplano',
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <div className="app-container">
          <header className="header">
            <div className="header-logo">
              <div className="header-logo-icon">🎓</div>
              <div>
                <div className="header-title">Revisor de Tesis</div>
                <div className="header-subtitle">Universidad Nacional del Altiplano · Puno</div>
              </div>
            </div>
            <div className="header-badge">Repositorio Institucional v2.0</div>
          </header>
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
