FROM python:3.13
EXPOSE 8082
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]

ENV PYTHONUNBUFFERED=1

ENV AWS_REGION=""
ENV AWS_Q2=""
ENV JIRA_KEY=""
ENV EMAIL=""
ENV HOST=""
ENV PROJECT_ID=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
