FROM node:slim

WORKDIR /opt/app/frontend/
COPY . .

RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]

