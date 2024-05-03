# Visualizing Celery Task Queue

Use flower:

1. Launch virtual environment
2. pip install -r ./requirements.txt
3. pip install -r ./test-requirements.
4. docker compose up -d --build
5. celery --broker=redis://localhost:6379/ flower
6. Open browser to localhost:5555