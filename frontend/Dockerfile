FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# Copy application code (overridden by volume mount in dev)
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
