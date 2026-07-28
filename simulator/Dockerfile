FROM python:3.11.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash kronvel

COPY --chown=kronvel:kronvel . .

USER kronvel

EXPOSE 9400

CMD ["python", "dcgm_sim.py"]
