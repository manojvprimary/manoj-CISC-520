# Stage 1: Build React app
FROM node:18 AS build

WORKDIR /app

# Copy only package files first (better caching)
COPY package*.json ./

RUN npm install

# Now copy rest of code
COPY . .

# Build
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]