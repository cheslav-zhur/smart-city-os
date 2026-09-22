# syntax=docker/dockerfile:1
# Hosted console only. Local desk stays Vite in Compose (`docs/dev.md`).

FROM node:24-bookworm-slim AS build
WORKDIR /src
RUN corepack enable && corepack prepare pnpm@10.34.5 --activate
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./
RUN pnpm build

FROM caddy:2.10-alpine
COPY apps/web/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /usr/share/caddy
ENV PORT=8080
ENV API_UPSTREAM=
EXPOSE 8080
