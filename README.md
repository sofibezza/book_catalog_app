# book_catalog_app
docker-compose down -v
docker-compose up --build
docker-compose restart api
docker-compose logs api

{
  "email": "admin@test.com",
  "username": "admin",
  "password": "password123"
}

docker-compose exec api pytest app/tests/test_user.py -v

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzA4NDYyNzgsInN1YiI6Ijk0MmVjZjYxLTNiZDUtNGRmNy04ODZkLTU1NTQzYjUzZjJmYiJ9.xY6c0NmeNiNwu4IAr7VKDEYJEu_ofvOHysmGgCsAjag

docker-compose exec api pytest app/tests/test_integration_google.py -v -s
# Dentro de la carpeta /frontend
python -m http.server 3000
docker-compose exec api pytest
docker-compose exec api pytest --cov=app --cov-report=term-missing
