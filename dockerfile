FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#working directory
WORKDIR /app


#install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


# copy the requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy the project
COPY . .

#expose port
EXPOSE 8000

CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000"]