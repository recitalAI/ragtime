FROM node:18-slim

WORKDIR /app

# Copy the manifests first so `npm install` is cached across builds and only
# re-runs when dependencies change (previously the whole context was copied
# first, busting the layer cache on every source edit).
COPY package*.json ./
RUN npm install

# vue-cli-service comes from devDependencies; the global @vue/cli install
# was unnecessary and has been dropped.
COPY . .

CMD ["npm", "run", "serve"]
