FROM python:slim

WORKDIR /opt/app/backend/
COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--debug"]

