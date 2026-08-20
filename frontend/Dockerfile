FROM node:22-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
RUN pnpm install

COPY . .

EXPOSE 4200

CMD ["pnpm", "start", "--", "--host", "0.0.0.0", "--poll", "2000"]
