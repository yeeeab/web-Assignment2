pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
# Swagger: http://<host>:8080/docs
