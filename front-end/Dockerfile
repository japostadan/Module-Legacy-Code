FROM nginx:alpine

# Vanilla-JS SPA, no build step. Hash-based routing (index.html#/...) means the
# default nginx static config is enough — no History-API try_files fallback.
# The custom server config adds the .mjs MIME mapping nginx lacks by default.
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy only the web assets (not node_modules, tests, or tooling).
COPY index.html index.css index.mjs logo.svg /usr/share/nginx/html/
COPY lib/ /usr/share/nginx/html/lib/
COPY components/ /usr/share/nginx/html/components/
COPY views/ /usr/share/nginx/html/views/
