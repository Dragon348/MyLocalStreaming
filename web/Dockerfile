FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./

# Install dependencies (use npm install if package-lock.json is missing or incompatible)
RUN npm ci || npm install

COPY . .

# Build the application
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

# Use npx to ensure we use the locally installed typescript
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
