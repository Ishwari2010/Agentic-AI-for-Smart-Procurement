# Agentic AI for Smart Procurement

## Project Overview

Agentic AI for Smart Procurement is an AI-powered procurement automation system that extracts structured procurement information from invoices using OCR and Large Language Models (LLMs).

The application accepts invoices in PDF or image format, extracts the text using OCR, processes it using Google's Gemini LLM, validates the extracted data using Pydantic, and stores the structured information into a PostgreSQL database.

---

# Features

- Upload procurement invoices (PDF, PNG, JPG, JPEG)
- OCR-based text extraction using Tesseract OCR
- AI-powered information extraction using Google Gemini
- Automatic extraction of:
  - Requester Name
  - Item Description
  - Quantity
  - Estimated Cost
  - Total Estimated Cost
- Pydantic schema validation
- PostgreSQL database storage
- REST API using FastAPI
- Interactive Swagger UI

---

# Technology Stack

## Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic

## OCR

- Tesseract OCR
- pdf2image
- Pillow

## LLM

- Google Gemini API

## Database

- PostgreSQL 16
- pgAdmin 4

## Containerization

- Docker
- Docker Compose

---

# Project Structure

```
Agentic_AI_for_Smart_Procurement
│
├── backend
│   ├── app
│   │   ├── llm
│   │   │   ├── __init__.py
│   │   │   └── gemini_client.py
│   │   │
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── ocr.py
│   │   └── schemas.py
│   │
│   ├── uploads
│   ├── requirements.txt
│   └── test_gemini.py
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

# Prerequisites

Install the following software:

- Python 3.12+
- Git
- Docker
- Docker Compose
- PostgreSQL (or Docker PostgreSQL)
- pgAdmin 4
- Tesseract OCR
- Poppler
- VS Code (Recommended)

---

# Installation

## Clone Repository

```bash
git clone <repository-url>

cd Agentic_AI_for_Smart_Procurement
```

---

## Create Virtual Environment

```bash
cd backend

python3 -m venv venv
```

Activate

Linux

```bash
source venv/bin/activate
```

Windows

```cmd
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Install OCR Dependencies

## Install Tesseract

Ubuntu

```bash
sudo apt update

sudo apt install tesseract-ocr
```

Verify

```bash
tesseract --version
```

---

## Install Poppler

Ubuntu

```bash
sudo apt install poppler-utils
```

Verify

```bash
pdftoppm -v
```

---

# Google Gemini API Setup

Create a file named

```
backend/.env
```

Add

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/procurement_db

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

---

# PostgreSQL Setup

## Start Docker

```bash
docker compose up -d
```

Verify

```bash
docker ps
```

---

## Connect Using pgAdmin

Host

```
127.0.0.1
```

Port

```
5432
```

Username

```
postgres
```

Password

```
postgres
```

Database

```
procurement_db
```

---

# Create Database Tables

## procurement_requests

```sql
CREATE TABLE procurement_requests (
    id SERIAL PRIMARY KEY,
    requester_name VARCHAR(255),
    total_estimated_cost DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## procurement_items

```sql
CREATE TABLE procurement_items (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES procurement_requests(id),
    description VARCHAR(255),
    quantity INTEGER,
    estimated_cost DECIMAL(12,2)
);
```

---

# Run Backend

Navigate

```bash
cd backend
```

Activate environment

```bash
source venv/bin/activate
```

Run FastAPI

```bash
uvicorn app.main:app --reload
```

---

# API Documentation

Open

```
http://127.0.0.1:8000/docs
```

---

# API Endpoint

## Upload Invoice

```
POST /upload
```

Supported File Types

- PDF
- PNG
- JPG
- JPEG

---

# Application Workflow

```
Invoice Upload
        │
        ▼
OCR Agent (Tesseract)
        │
        ▼
Extract Raw Text
        │
        ▼
Gemini Information Extraction
        │
        ▼
Pydantic Validation
        │
        ▼
Store Request
        │
        ▼
Store Line Items
        │
        ▼
JSON Response
```

---

# Sample Response

```json
{
  "message": "Invoice processed successfully",
  "filename": "invoice.pdf",
  "structured_data": {
    "requester_name": "Rahul Sharma",
    "items": [
      {
        "description": "Arduino Uno Board",
        "quantity": 10,
        "estimated_cost": 5500
      }
    ],
    "total_estimated_cost": 18066
  },
  "request_id": 1
}
```

---

# Database Schema

## procurement_requests

| Column | Type |
|----------|----------|
| id | Integer |
| requester_name | String |
| total_estimated_cost | Decimal |
| created_at | Timestamp |

---

## procurement_items

| Column | Type |
|----------|----------|
| id | Integer |
| request_id | Integer |
| description | String |
| quantity | Integer |
| estimated_cost | Decimal |

---

# Current AI Agents

### OCR Agent

- Converts PDF/Image into text.

Technology

- Tesseract OCR

---

### Information Extraction Agent

Extracts

- Requester Name
- Item Description
- Quantity
- Estimated Cost
- Total Estimated Cost

Technology

- Google Gemini

---

# Future Work

- Inventory Intelligence Agent
- Vendor Intelligence Agent
- Risk Analysis Agent
- Approval Agent
- Notification Agent
- Reporting Dashboard
- Role-Based Authentication
- Kafka Integration
- Redis Cache
- Kubernetes Deployment

---

# Troubleshooting

## Tesseract Not Found

```bash
sudo apt install tesseract-ocr
```

---

## Poppler Missing

```bash
sudo apt install poppler-utils
```

---

## PostgreSQL Connection Error

Verify Docker

```bash
docker ps
```

Restart

```bash
docker compose up -d
```

---

## Gemini API Error

Verify

```
GEMINI_API_KEY
```

inside

```
backend/.env
```

---

## Missing Python Packages

```bash
pip install -r requirements.txt
```

---

# Authors

Developed as part of the **Agentic AI for Smart Procurement** project for intelligent procurement automation using OCR, LLMs, and PostgreSQL.
