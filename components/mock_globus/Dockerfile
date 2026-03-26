FROM python:3.10-slim

WORKDIR /app

COPY mock_globus.py /app/mock_globus.py

RUN pip install Flask gunicorn

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "mock_globus:app"]
