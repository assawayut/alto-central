# Alto Central Frontend - Production Dockerfile
# Multi-stage build: Node.js for building, nginx for serving
#
# Build context should be the repo root to access shared config:
#   docker build -f alto-central-frontend/Dockerfile .

# =============================================================================
# Stage 1: Build the React application
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy shared config first (needed for build - sites.yaml alias)
COPY config /config

# Copy package files for dependency installation
COPY alto-central-frontend/package.json alto-central-frontend/package-lock.json ./

# Install dependencies (use npm install for lower memory usage)
RUN npm install --legacy-peer-deps

# Copy frontend source code
COPY alto-central-frontend/ .

# Build the application with limited memory
ENV NODE_OPTIONS="--max-old-space-size=512"
RUN npm run build

# =============================================================================
# Stage 2: Serve with nginx
# =============================================================================
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY alto-central-frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user for nginx
RUN adduser -D -H -u 1001 -s /sbin/nologin nginx-user && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx-user:nginx-user /var/run/nginx.pid

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
