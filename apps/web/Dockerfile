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
RUN apk add --no-cache python3
COPY apps/web/Caddyfile /etc/caddy/Caddyfile
COPY apps/web/token_proxy.py /usr/local/bin/token_proxy.py
COPY apps/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=build /src/dist /usr/share/caddy
ENV PORT=8080
ENV API_UPSTREAM=
ENV TOKEN_PROXY_PORT=8090
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
