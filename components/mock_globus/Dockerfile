FROM python:3.10-slim

WORKDIR /app

COPY mock_globus.py /app/mock_globus.py

RUN pip install Flask

EXPOSE 5000

CMD ["python", "mock_globus.py"]
