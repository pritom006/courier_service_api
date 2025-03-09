# Courier Service API

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [User Roles and Permissions](#user-roles-and-permissions)
- [Example Usage](#example-usage)
- [Running Tests](#running-tests)

## Overview
This is a RESTful API for a courier service that allows customers to create and track packages, couriers to update package status, and admins to manage users and packages. The API is built using Django REST Framework and uses JWT authentication for secure access.

## Features
- **User Authentication**: Register, login, and manage user profiles.
- **Role-Based Access Control**: Customers, Couriers, and Admins with different permissions.
- **Package Management**: Create, update, assign, track, and soft delete packages.
- **Package Status Updates**: Track package status in real-time.
- **JWT Authentication**: Secure API access using JSON Web Tokens.
- **Admin Management**: Manage users and packages efficiently.
- **Unit Test**: Unit Test using mock data.

## Installation

### Prerequisites
Ensure you have the following installed:
- Python (>=3.8)
- Django (>=3.2)
- Django REST Framework
- PostgreSQL/MySQL (or use SQLite for local testing)

### Steps to Install
```bash
# Clone the repository
git clone https://github.com/your-repo/courier-service-api.git
cd courier-service-api

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create a superuser (for admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

## API Endpoints

### Authentication
```http
POST /api/accounts/register/    # Register a new user
POST /api/accounts/login/       # Login to get JWT token
POST /api/accounts/token/refresh/ # Refresh JWT token
GET  /api/accounts/profile/     # Get current user profile
PUT  /api/accounts/profile/     # Update current user profile
```

### User Management (Admin only)
```http
GET  /api/accounts/users/       # List all users
POST /api/accounts/users/       # Create a new user
GET  /api/accounts/users/{id}/  # Get user details
PUT  /api/accounts/users/{id}/  # Update user
DELETE /api/accounts/users/{id}/ # Delete user
```

### Package Management

#### For Customers
```http
GET  /api/packages/                   # List all packages owned by the customer
POST /api/packages/                   # Create a new package
GET  /api/packages/{id}/              # Get details of a package
GET  /api/packages/track/?tracking_number=XXX # Track a package
```

#### For Couriers
```http
GET  /api/packages/                   # List all packages assigned to the courier
GET  /api/packages/{id}/              # Get package details
POST /api/packages/{id}/update_status/ # Update package status
```

#### For Admins
```http
GET  /api/packages/                   # List all packages
GET  /api/packages/{id}/              # Get package details
PATCH /api/packages/{id}/assign_courier/ # Assign a courier
PATCH /api/packages/{id}/soft_delete/  # Soft delete a package
PATCH /api/packages/{id}/restore/      # Restore a package
GET  /api/packages/deleted_packages/   # List all soft-deleted packages
```

### Package Status Updates
```http
GET /api/packages/{package_id}/status/ # List status updates for a package
```

## Authentication
The API uses JWT authentication. To authenticate:

1. Obtain a token via `POST /api/accounts/login/`.
2. Use the token in the Authorization header:
   ```http
   Authorization: Bearer <your_token>
   ```

## User Roles and Permissions
- **Customer**: Can create and track their own packages.
- **Courier Staff**: Can view and update assigned packages.
- **Admin**: Has full access, including assigning couriers and managing users.

## Example Usage

### Register a New Customer
```http
POST /api/accounts/register/
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "securepassword",
  "password2": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "user_role": "customer"
}
```

### Login and Get Token
```http
POST /api/accounts/login/
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "securepassword"
}
```

### Create a New Package (Customer)
```http
POST /api/packages/
Content-Type: application/json

{
  "description": "Electronics package",
  "weight": 2.5,
  "dimensions": "30x20x15",
  "pickup_address": "123 Pickup St, City, Country",
  "delivery_address": "456 Delivery Ave, City, Country"
}
```

### Assign a Courier to a Package (Admin)
```http
PATCH /api/packages/1/assign_courier/
Content-Type: application/json

{
  "courier": 2  # User ID of the courier
}
```

### Track a Package (Public Access)
```http
GET /api/packages/track/?tracking_number=PKG-ABC123XYZ
```

## Running Tests
```bash
# Run all test cases
python manage.py test

# Run specific app tests
python manage.py test packages.tests.test_views

# Run a specific test case
python manage.py test packages.tests.test_views.PackageViewSetTestCase.test_track_package_missing_tracking_number


   
