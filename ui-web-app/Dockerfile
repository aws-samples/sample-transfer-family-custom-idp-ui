FROM public.ecr.aws/docker/library/alpine:3.18.4 AS build-stage
RUN apk add --update nodejs-current npm

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM public.ecr.aws/nginx/nginx:alpine-slim AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80
ENTRYPOINT ["/start.sh"]


