FROM python:3.7.3-stretch

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "cppbot.cppbot"]
