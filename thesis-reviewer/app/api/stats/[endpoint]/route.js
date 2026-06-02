import { NextResponse } from 'next/server';

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Mapeo de endpoints permitidos del backend Python
const ALLOWED = {
  curiosities: '/ai/stats/curiosities',
  schools: '/ai/stats/schools',
  faculties: '/ai/stats/faculties',
  categories: '/ai/stats/categories',
  writing: '/ai/stats/writing',
  'top-errors': '/ai/stats/top-errors',
  insights: '/ai/insights',
};

export async function GET(request, { params }) {
  const { endpoint } = await params;
  const target = ALLOWED[endpoint];
  if (!target) {
    return NextResponse.json({ error: 'Endpoint no permitido' }, { status: 404 });
  }

  try {
    const url = new URL(request.url);
    const query = url.search || '';
    const response = await fetch(`${PYTHON_API_URL}${target}${query}`, {
      method: 'GET',
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (err) {
    return NextResponse.json(
      { error: `No se pudo contactar el backend Python: ${err.message}` },
      { status: 503 }
    );
  }
}
