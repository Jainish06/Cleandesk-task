# ==============================================================================
# CleanDesk Next.js Frontend Dockerfile
# ==============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Set environment variables and build args for Next.js build
ARG NEXT_PUBLIC_API_URL=https://instasim-f9b2.onrender.com
ARG NEXT_PUBLIC_WS_URL=wss://instasim-f9b2.onrender.com/ws/inbox

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build Next.js application
RUN npm run build

# ==============================================================================
# Production Runner
# ==============================================================================
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
