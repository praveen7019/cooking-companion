# Cooking Companion

A full-stack recipe sharing and private chef booking web application built with Django and MySQL. The platform connects three types of users — regular users, professional chefs, and administrators — through a single system.

## Features

- **Recipe Sharing** — Users can browse recipes and upload their own to share with the community
- **Private Chef Booking** — Users can book private chef services directly through the platform
- **Three User Roles** — Separate functionality for regular users, professional chefs, and administrators
- **REST API** — Recipe data is also exposed via a REST API built with Django REST Framework (GET/POST endpoints)

## Tech Stack

- **Backend:** Python, Django
- **API:** Django REST Framework (DRF)
- **Database:** MySQL
- **Frontend:** HTML5, CSS3
- **Other:** Django Admin, Django ORM

## Project Structure

cooking_companion/
├── cooking/ # Main app: models, views, logic
├── cooking_companion/ # Project settings and configuration
├── media/ # User-uploaded content (recipe images, etc.)
├── static/ # CSS, JS, static assets
├── templates/ # HTML templates
├── cooking_data.json # Sample/seed data
└── manage.py


## Getting Started

### Prerequisites
- Python 3.7+
- MySQL installed and running

### Setup

1. Clone the repository

git clone https://github.com/praveen7019/cooking-companion.git
cd cooking-companion


2. Install dependencies

pip install -r requirements.txt


3. Configure your MySQL database in `cooking_companion/settings.py` with your own credentials

4. Run migrations

python manage.py migrate


5. Start the development server

python manage.py runserver


6. Visit `http://127.0.0.1:8000/` in your browser

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/recipes/` | List all recipes |
| POST | `/api/recipes/` | Create a new recipe |

## Author

**Praveen Katare**
[LinkedIn](www.linkedin.com/in/praveen-katare) · [Email](mailto:praveen121@gmail.com)
