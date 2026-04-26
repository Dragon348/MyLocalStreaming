FROM node:20-alpine AS builder

WORKDIR /app

# Ensure NODE_ENV is not set to production during build
ENV NODE_ENV=development

COPY package.json package-lock.json* ./

# Install all dependencies including devDependencies for build
RUN npm install

COPY . .

# Build the application
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

# Build using the locally installed TypeScript and Vite
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
