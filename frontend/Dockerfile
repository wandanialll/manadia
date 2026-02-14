# Build stage
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* yarn.lock* ./

RUN npm ci --omit=dev

COPY . .

RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install http-server
RUN npm install -g http-server

# Copy only the built dist folder
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["http-server", "dist", "-p", "3000", "-c-1"]
