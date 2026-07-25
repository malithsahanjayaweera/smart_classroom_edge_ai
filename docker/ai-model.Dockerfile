FROM python:3.12-slim
WORKDIR /app
COPY ai-model/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ai-model .
EXPOSE 8000
CMD ["python", "app.py"]
