FROM odoo:19.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --break-system-packages --no-cache-dir pytesseract Pillow
USER odoo
