FROM node:20-slim

WORKDIR /app

# Copy package.json and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend code
COPY frontend/ .

# Expose Vite dev server port
EXPOSE 5173

# Run the React app (with --host to expose it outside the container)
CMD ["npm", "run", "dev", "--", "--host"]
