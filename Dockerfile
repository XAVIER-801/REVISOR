# ─── STAGE 1: Dependencies ───
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
# Apuntamos a la carpeta del proyecto
COPY thesis-reviewer/package*.json ./
RUN npm ci

# ─── STAGE 2: Build ───
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY thesis-reviewer/ .

# Optimizaciones de construcción
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ─── STAGE 3: Runner ───
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiar archivos necesarios para standalone
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Crear carpetas necesarias
RUN mkdir -p /app/tmp && chown nextjs:nodejs /app/tmp
RUN mkdir -p /app/ocr-data && chown nextjs:nodejs /app/ocr-data

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
