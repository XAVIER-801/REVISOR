import './globals.css';

export const metadata = {
  title: 'RepoStyle | Auditoria Digital UNAP',
  description: 'Validación inteligente de tesis para Pregrado, Posgrado y Segundas Especialidades.',
  icons: {
    icon: '/images/logo_geometric.png',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <img src="/images/rectorado.jpg" alt="" className="bg-institutional-watermark" />
        
        <div className="crypto-glow">
           <div className="glow-spot spot-1"></div>
           <div className="glow-spot spot-2"></div>
        </div>

        <header className="header-crypto">
          <div className="container-crypto" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {/* LOGO AREA */}
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="flex items-center gap-3">
                <img src="/images/logo_geometric.png" alt="Logo" style={{ height: '40px' }} />
                <span style={{ fontSize: '1.4rem', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: '1' }}>RepoStyle</span>
              </div>
              <span style={{ fontSize: '0.65rem', color: '#45F5E5', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em', marginTop: '0.3rem', paddingLeft: '3px' }}>
                Auditor de Formato
              </span>
            </div>
            
            {/* NAV LINKS - CENTERED */}
            <nav className="nav-links-wrap hidden md:flex">
              <a href="/" className="nav-link">Inicio</a>
              <a href="/guia" className="nav-link">Guía</a>
              <a href="/dashboard" className="nav-link">Estadísticas</a>
              <a href="https://repositorio.unap.edu.pe/home" target="_blank" className="nav-link">Repositorio</a>
              <a href="https://vriunap.pe/" target="_blank" className="nav-link">VRI UNAP</a>
            </nav>

            {/* ACTION BUTTON - RIGHT */}
            <a href="/admin" className="btn-crypto" style={{ padding: '0.6rem 1.5rem', fontSize: '0.8rem', borderRadius: '12px', textDecoration: 'none' }}>Acceso VRI</a>
          </div>
        </header>

        {children}

        <footer className="footer-minimal">
           <div className="container-crypto">
              <div className="flex justify-between items-center mb-10">
                 {/* LOGOS WRAP WITH SPACING */}
                 <div className="footer-logo-wrap">
                    <img src="/images/logo-vri.png" alt="VRI" style={{ height: '32px', opacity: 0.7 }} />
                    <img src="/images/unap_bg_3.png" alt="UNAP" style={{ height: '45px', opacity: 0.7 }} />
                 </div>
                 
                 {/* FOOTER LINKS WITH SPACING */}
                 <div className="footer-links-wrap">
                    <a href="#" className="nav-link" style={{ fontSize: '0.7rem' }}>Privacidad</a>
                    <a href="#" className="nav-link" style={{ fontSize: '0.7rem' }}>Términos</a>
                    <a href="#" className="nav-link" style={{ fontSize: '0.7rem' }}>Contacto</a>
                 </div>
              </div>
              <div className="pt-8 border-t border-white/5 text-center">
                 <p style={{ color: '#475569', fontSize: '0.75rem', fontWeight: 600 }}>
                    © 2025 Vicerrectorado de Investigación - Universidad Nacional del Altiplano
                 </p>
              </div>
           </div>
        </footer>
      </body>
    </html>
  );
}
