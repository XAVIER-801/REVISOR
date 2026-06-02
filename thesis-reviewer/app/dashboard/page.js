'use client';

import { useState, useEffect } from 'react';
import {
  BarChart3, TrendingUp, AlertTriangle, Award, Activity,
  Building2, GraduationCap, Trophy, Target, Zap, BookOpen,
  ArrowUpRight, ArrowDownRight
} from 'lucide-react';

export default function Dashboard() {
  const [curiosities, setCuriosities] = useState(null);
  const [schools, setSchools] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [categories, setCategories] = useState({});
  const [topErrors, setTopErrors] = useState([]);
  const [writing, setWriting] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [cur, sch, fac, cat, te, wr] = await Promise.all([
          fetch('/api/stats/curiosities').then((r) => r.json()),
          fetch('/api/stats/schools?min_thesis=1&limit=20').then((r) => r.json()),
          fetch('/api/stats/faculties?min_thesis=1').then((r) => r.json()),
          fetch('/api/stats/categories').then((r) => r.json()),
          fetch('/api/stats/top-errors?n=15').then((r) => r.json()),
          fetch('/api/stats/writing?limit=10').then((r) => r.json()),
        ]);
        setCuriosities(cur);
        setSchools(sch.ranking || []);
        setFaculties(fac.ranking || []);
        setCategories(cat.categories || {});
        setTopErrors(te.top_errors || []);
        setWriting(wr.ranking || []);
        setLoading(false);
      } catch (e) {
        setError(e.message);
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) {
    return (
      <main className="container-crypto" style={{ paddingTop: '8rem', textAlign: 'center' }}>
        <div className="ocr-pulse" style={{ margin: '0 auto' }}></div>
        <h2 style={{ marginTop: '2rem' }}>Cargando estadísticas del corpus...</h2>
      </main>
    );
  }

  if (error) {
    return (
      <main className="container-crypto" style={{ paddingTop: '8rem' }}>
        <h2 style={{ color: '#FF4D4D' }}>Error al cargar el dashboard</h2>
        <p style={{ color: '#94A3B8' }}>{error}</p>
      </main>
    );
  }

  if (!curiosities || curiosities.total_thesis === 0) {
    return (
      <main className="container-crypto" style={{ paddingTop: '8rem', textAlign: 'center' }}>
        <BookOpen size={80} style={{ color: '#45F5E5', opacity: 0.3, margin: '0 auto 2rem' }} />
        <h1 style={{ fontSize: '3rem', fontWeight: 900, marginBottom: '1rem' }}>
          Dashboard sin datos aún
        </h1>
        <p style={{ color: '#94A3B8', fontSize: '1rem', maxWidth: '600px', margin: '0 auto' }}>
          El sistema aún no ha procesado tesis. Cada vez que un estudiante audita
          su tesis, el sistema aprende. Las estadísticas aparecerán aquí
          progresivamente.
        </p>
      </main>
    );
  }

  const totalCategories = Object.entries(categories).sort((a, b) => b[1].errors - a[1].errors);
  const maxCatErrors = Math.max(...totalCategories.map(([, v]) => v.errors), 1);

  return (
    <main className="container-crypto animate-reveal" style={{ paddingTop: '5rem', paddingBottom: '5rem' }}>
      {/* HERO */}
      <section style={{ marginBottom: '4rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(69, 245, 229, 0.08)', padding: '0.5rem 1.25rem', borderRadius: '50px', marginBottom: '2rem', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
          <Activity size={16} className="text-accent" />
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#45F5E5', textTransform: 'uppercase', letterSpacing: '0.2em' }}>Dashboard del corpus aprendido</span>
        </div>
        <h1 style={{ fontSize: '4rem', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: '1.05', marginBottom: '1rem' }}>
          Estadísticas <span className="text-gradient">curiosas</span> del repositorio
        </h1>
        <p style={{ color: '#94A3B8', fontSize: '1rem', maxWidth: '700px' }}>
          Análisis en tiempo real basado en {curiosities.total_thesis} tesis auditadas. Mientras más
          tesis se procesan, más interesantes son los patrones que el sistema descubre.
        </p>
      </section>

      {/* MÉTRICAS DESTACADAS */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', marginBottom: '4rem' }}>
        <MetricCard
          icon={<BookOpen size={28} />}
          label="Tesis Procesadas"
          value={curiosities.total_thesis}
          color="#45F5E5"
        />
        <MetricCard
          icon={<Target size={28} />}
          label="Score Promedio Global"
          value={`${curiosities.global_avg_score}/100`}
          color="#9D50FF"
        />
        <MetricCard
          icon={<AlertTriangle size={28} />}
          label="Errores Totales"
          value={curiosities.total_errors_across_corpus.toLocaleString()}
          color="#FF4D4D"
        />
        <MetricCard
          icon={<Trophy size={28} />}
          label="Mejor Score Registrado"
          value={`${curiosities.max_score}/100`}
          color="#FFC107"
        />
        <MetricCard
          icon={<TrendingUp size={28} />}
          label="Errores por Tesis (Promedio)"
          value={curiosities.avg_errors_per_thesis}
          color="#3772FF"
        />
        <MetricCard
          icon={<Award size={28} />}
          label="Score Mediano"
          value={curiosities.median_score}
          color="#45F5E5"
        />
      </section>

      {/* DATO CURIOSO PRINCIPAL */}
      <section className="card-elite" style={{ padding: '2.5rem', marginBottom: '4rem', background: 'linear-gradient(135deg, rgba(69, 245, 229, 0.05), rgba(157, 80, 255, 0.05))', border: '1px solid rgba(69, 245, 229, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <Zap size={32} className="text-accent" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 900 }}>Dato curioso del corpus</h2>
        </div>
        <p style={{ fontSize: '1rem', color: '#CBD5E1', lineHeight: '1.7' }}>
          La regla más violada es <strong style={{ color: '#45F5E5' }}>"{curiosities.most_violated_rule.rule}"</strong>{' '}
          de la categoría <strong>{curiosities.most_violated_rule.category}</strong> con{' '}
          <strong style={{ color: '#FFC107' }}>{curiosities.most_violated_rule.count} ocurrencias</strong>{' '}
          en todo el corpus. La categoría más problemática es{' '}
          <strong style={{ color: '#FF4D4D' }}>{curiosities.most_problematic_category}</strong>.
        </p>
      </section>

      {/* RANKING FACULTADES */}
      {faculties.length > 0 && (
        <section style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Building2 size={28} className="text-accent" />
            Ranking de Facultades
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.85rem', marginBottom: '2rem' }}>
            Ordenadas por puntaje promedio de cumplimiento de las normas UNAP.
          </p>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {faculties.map((f, i) => (
              <RankingRow
                key={i}
                position={i + 1}
                title={f.faculty}
                subtitle={`${f.thesis_count} tesis registradas`}
                score={f.avg_score}
                detail={`${f.total_errors} errores totales`}
              />
            ))}
          </div>
        </section>
      )}

      {/* RANKING ESCUELAS */}
      {schools.length > 0 && (
        <section style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <GraduationCap size={28} className="text-accent" />
            Ranking de Escuelas Profesionales
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.85rem', marginBottom: '2rem' }}>
            Top {schools.length} escuelas por puntaje promedio. Las que escriben mejor según el sistema.
          </p>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {schools.slice(0, 10).map((s, i) => (
              <RankingRow
                key={i}
                position={i + 1}
                title={s.school}
                subtitle={s.faculty || 'Facultad no determinada'}
                score={s.avg_score}
                detail={`${s.thesis_count} tesis | ${s.avg_errors} errores promedio`}
              />
            ))}
          </div>
        </section>
      )}

      {/* DISTRIBUCIÓN POR CATEGORÍA */}
      {totalCategories.length > 0 && (
        <section style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <BarChart3 size={28} className="text-accent" />
            Áreas problemáticas del corpus
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.85rem', marginBottom: '2rem' }}>
            Distribución de errores totales por categoría de auditoría.
          </p>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {totalCategories.slice(0, 12).map(([cat, data]) => (
              <div key={cat} className="category-card" style={{ padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.9rem' }}>{cat}</span>
                  <span style={{ fontSize: '0.85rem', color: '#FF4D4D', fontWeight: 900 }}>
                    {data.errors} errores / {data.warnings} alertas
                  </span>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{
                    width: `${(data.errors / maxCatErrors) * 100}%`,
                    background: 'linear-gradient(90deg, #FF4D4D, #FFC107)',
                  }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* TOP ERRORES */}
      {topErrors.length > 0 && (
        <section style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={28} className="text-accent" />
            Errores más comunes
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.85rem', marginBottom: '2rem' }}>
            Los errores que se repiten más en el corpus. Si estás cometiendo alguno de estos, no estás solo — pero corregirlos te pondrá por encima del promedio.
          </p>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {topErrors.slice(0, 10).map((e, i) => (
              <div key={i} className="category-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.9rem', marginBottom: '0.2rem' }}>
                    #{i + 1}. {e.rule}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    {e.category}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: '#FF4D4D' }}>{e.count}</div>
                  <div style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 700 }}>OCURRENCIAS</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* MEJORES Y PEORES TESIS */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '4rem' }}>
        <div className="card-elite" style={{ padding: '2rem', borderColor: 'rgba(69, 245, 229, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Trophy size={24} style={{ color: '#45F5E5' }} />
            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: '#45F5E5', textTransform: 'uppercase', letterSpacing: '0.2em' }}>Mejor tesis registrada</span>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 900, color: '#45F5E5', marginBottom: '0.5rem' }}>
            {curiosities.best_thesis.score}/100
          </div>
          <div style={{ color: '#CBD5E1', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
            {curiosities.best_thesis.school || 'Escuela no determinada'}
          </div>
          <div style={{ color: '#64748B', fontSize: '0.75rem' }}>
            {curiosities.best_thesis.filename}
          </div>
        </div>
        <div className="card-elite" style={{ padding: '2rem', borderColor: 'rgba(255, 77, 77, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <ArrowDownRight size={24} style={{ color: '#FF4D4D' }} />
            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: '#FF4D4D', textTransform: 'uppercase', letterSpacing: '0.2em' }}>Score más bajo</span>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 900, color: '#FF4D4D', marginBottom: '0.5rem' }}>
            {curiosities.worst_thesis.score}/100
          </div>
          <div style={{ color: '#CBD5E1', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
            {curiosities.worst_thesis.school || 'Escuela no determinada'}
          </div>
          <div style={{ color: '#64748B', fontSize: '0.75rem' }}>
            {curiosities.worst_thesis.filename}
          </div>
        </div>
      </section>
    </main>
  );
}

function MetricCard({ icon, label, value, color }) {
  return (
    <div className="category-card" style={{ padding: '1.5rem' }}>
      <div style={{ color, marginBottom: '1rem' }}>{icon}</div>
      <div style={{ fontSize: '0.7rem', color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '2rem', fontWeight: 900, color, lineHeight: '1' }}>
        {value}
      </div>
    </div>
  );
}

function RankingRow({ position, title, subtitle, score, detail }) {
  const scoreColor = score >= 80 ? '#45F5E5' : score >= 60 ? '#FFC107' : '#FF4D4D';
  return (
    <div className="category-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.25rem 1.5rem' }}>
      <div style={{ minWidth: '50px', textAlign: 'center', fontSize: '1.5rem', fontWeight: 900, color: position <= 3 ? '#45F5E5' : '#64748B' }}>
        #{position}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 800, fontSize: '0.95rem', marginBottom: '0.25rem' }}>{title}</div>
        <div style={{ color: '#94A3B8', fontSize: '0.75rem' }}>{subtitle}</div>
      </div>
      <div style={{ textAlign: 'right', minWidth: '120px' }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 900, color: scoreColor, lineHeight: '1' }}>
          {score}
        </div>
        <div style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 700, textTransform: 'uppercase', marginTop: '0.25rem' }}>
          {detail}
        </div>
      </div>
    </div>
  );
}
