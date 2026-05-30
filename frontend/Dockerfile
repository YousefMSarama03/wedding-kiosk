FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Accept VITE_API_URL at build time so the compiled bundle knows the backend URL.
# Set this in Railway: Variables > VITE_API_URL = https://backend-production-xxxx.up.railway.app
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

CMD ["npm", "run", "start"]
