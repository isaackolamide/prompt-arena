FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose Vite dev port
EXPOSE 5173

# Run the development server
CMD ["npm", "run", "dev"]
