FROM python:3.11-slim

# opencv-python-headless still links against libglib
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements එක වෙනස් නොවුණොත් layer cache එක නැවත භාවිතා වෙන්න
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY app.py labels.txt metadata_properties.json model.onnx ./
COPY templates/ ./templates/
COPY static/ ./static/

# predict_frame එක debug_frame.jpg ලියන නිසා writable dir එකක් ඕන
RUN useradd -m appuser && chown appuser:appuser /app
USER appuser

EXPOSE 5001

# ONNX model එක worker එකකට ~5MB, 2 workers ට වඩා ඕන නෑ
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "60", "app:app"]
