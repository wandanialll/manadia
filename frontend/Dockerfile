# Build stage
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* yarn.lock* ./

RUN npm ci

COPY . .

RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install serve (supports SPA fallback)
RUN npm install -g serve

# Copy only the built dist folder
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "dist", "-l", "3000", "-s"]
