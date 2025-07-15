# BookIt - Software Engineering Final Project @ SBU

For more information check out these documents:
- [SRS](https://docs.google.com/document/d/1UHQgTUsOSGOWSVyBtMnNYZ6GYWXY5MkWfRVygMvlYpw/edit?usp=sharing)
- [Vision](https://docs.google.com/document/d/1Xyg2xgQR84RJb9wJa4oiCPBzqWFED5uBhvqvfu7Ru6I/edit?usp=sharing)
- [Architecture](https://docs.google.com/document/d/1bm0Obf1ToxnMo0e59fDQZ9svjzfdMSQTaQ2ksWXhJ3g/edit?usp=sharing)

This repository contains the backend implementation of our hotel management system using the Django framework. BookIt registers customers and hotel managers. Hotel managers can add their hotels and rooms and analyze reports of their income and hotel status. Customers can filter hotels, check popular ones, and reserve rooms.

## Technology Stack
- Django
- PostgreSQL as database
- JWT authentication
- Django REST Framework

## Installation

1. Create a `.env` file in the root directory:
   ```
   DEBUG=1
   SECRET_KEY=
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=
   CORS_ALLOWED_ORIGINS=
   SERVER_URL=
   
   # PostgreSQL
   POSTGRES_DB=hotel_db
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   REDIS_HOST=redis
   
   # Django Database
   DATABASE_URL=postgres://postgres:postgres@postgres:5432/hotel_db
   
   # Email Configuration
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=
   EMAIL_HOST_PASSWORD=
   
   DJANGO_SUPERUSER_EMAIL=
   DJANGO_SUPERUSER_PASSWORD=
   ```

2. Run Docker Desktop program

3. Run this command in the root directory:
   ```
   docker-compose up --build
   ```
4. For using APIs check out *http://localhost:8000/swagger/*

   You can use the APIs with postman or the swagger interface.

## UML Diagram
<img width="862" height="866" alt="UML Diagram" src="https://github.com/user-attachments/assets/82ba850f-6d10-42f0-9047-f4ef6071bdac" />

## Class Diagram
<img width="746" height="786" alt="Class Diagram" src="https://github.com/user-attachments/assets/a9b9a42a-d6fa-4b6a-9b79-9a2adf75524d" />

## Team Members

**Backend**:
- Sahar Shah Rajabian
- Rozhan Mirzaei

**Frontend**:
- Samira Ahmadnejad
- Kimia Rohanifar

**DevOps**:
- Barbod Coliaie
