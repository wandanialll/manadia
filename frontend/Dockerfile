# Build stage - with better caching
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* ./

# Install dependencies
RUN npm ci --only=production && \
    npm ci

# Copy source code
COPY . .

# Build
RUN npm run build

# Production stage - serve with http-server
FROM node:20-alpine

WORKDIR /app

# Install http-server globally
RUN npm install -g http-server@14.1.1

# Copy built app from builder
COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Serve the dist folder
CMD ["http-server", "dist", "-p", "3000", "-c-1", "--gzip"]
