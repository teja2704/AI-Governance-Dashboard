# Dockerfile for the Node.js/Express frontend service.
# Build context: governance-dashboard-frontend/  (set Root Directory to this
# folder in the Railway service settings).

FROM node:20-alpine AS runtime

ENV NODE_ENV=production

WORKDIR /app

# Install production dependencies only
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy application source
COPY server.js ./
COPY public ./public

# Railway injects PORT at runtime; server.js reads process.env.PORT
EXPOSE 3000

CMD ["node", "server.js"]
