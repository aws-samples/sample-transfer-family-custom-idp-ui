# https://medium.com/@manuedavakandam/dockerize-your-vue-js-app-a-step-by-step-tutorial-for-seamless-deploymentinstall-vue-cli-globally-07e21d0b542b

#FROM --platform=linux/amd64 public.ecr.aws/docker/library/alpine:3.18.4 as build-stage
FROM public.ecr.aws/docker/library/alpine:3.18.4 AS build-stage
RUN apk add --update nodejs-current npm

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# get from ECR, private VPC
FROM public.ecr.aws/nginx/nginx:alpine-slim AS production-stage
#FROM --platform=linux/amd64 public.ecr.aws/nginx/nginx:alpine-slim as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh
# this will need to be TLS
EXPOSE 80
ENTRYPOINT ["/start.sh"]


