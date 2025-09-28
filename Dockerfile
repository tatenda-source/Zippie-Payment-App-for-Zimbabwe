# Multi-stage build for production
FROM node:18-alpine AS frontend-builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build:prod

# Production stage
FROM node:18-alpine AS production

# Install serve globally
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=frontend-builder /app/build ./build

# Copy backend
COPY backend/ ./backend/

# Install backend dependencies
WORKDIR /app/backend
RUN npm ci --only=production

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose ports
EXPOSE 3000 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Start both frontend and backend
CMD ["sh", "-c", "cd /app/backend && npm start & serve -s /app/build -l 3000"]
