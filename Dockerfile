FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY complete_model.py dynamic_transformer.py fusion_strategies.py ./
COPY core ./core

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["uvicorn", "advanced_multimodal_ai.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
