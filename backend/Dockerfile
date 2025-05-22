FROM python:3.10
WORKDIR /app
RUN pip install gunicorn==20.1.0
COPY foodgram_api/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "foodgram_api", "foodgram_api.wsgi"]