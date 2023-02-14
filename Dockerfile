FROM python:3.10
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
WORKDIR /app/app
ENTRYPOINT ["python"]
CMD ["main.py"]