# Split the Bill From a Photograph

An OCR-powered bill splitting application that converts a bill photograph into structured bill data and calculates fair person-wise expenses based on actual item consumption.

---

## 📌 Overview

Splitting a restaurant or shopping bill manually can be inconvenient, especially when multiple people have different items.

**Split the Bill From a Photograph** provides an end-to-end workflow that allows users to upload a photograph of a bill, extract its contents using OCR, review the extracted information, assign items to people, validate the bill, and calculate a fair person-wise split.

The application follows a **human-in-the-loop workflow**, ensuring that OCR mistakes can be reviewed and corrected before the final calculation.

### Application Workflow

```text
Upload Bill Photograph
        ↓
Image Preprocessing
        ↓
Tesseract OCR
        ↓
Bill Parsing
        ↓
Structured Pydantic Model
        ↓
Human Review & Correction
        ↓
Add People
        ↓
Assign Items
        ↓
Consumption-Based Calculation
        ↓
Bill Validation
        ↓
Person-Wise Final Amount
✨ Features
📷 Bill Image Upload

Supports common bill image formats:

JPG
JPEG
PNG
WEBP

Users can upload a photograph of a restaurant, shopping, or other printed bill.

🔎 OCR-Based Bill Extraction

The application uses Tesseract OCR to extract text from bill photographs.

The OCR pipeline attempts to identify:

Item names
Quantities
Unit prices
Item totals
Subtotal
Tax / GST
Service charge
Discount
Printed total

Image preprocessing is performed using OpenCV before OCR to improve text extraction.

🧾 Structured Bill Representation

Extracted information is converted into validated structured data using Pydantic models.

The bill model contains:

Items
Quantity
Unit price
Total price
Subtotal
Tax
Service charge
Discount
Total
Confidence scores

Confidence scores are maintained for important extracted fields so that uncertain OCR results can be identified during review.

👤 Human-in-the-Loop Review

OCR output is not directly trusted for the final calculation.

Before splitting the bill, users can review and correct extracted values such as:

Item names
Quantities
Prices
Subtotal
Tax
Service charge
Discount
Total

This allows human verification before financial calculations are performed.

👥 Multiple People

Users can add multiple people participating in the bill.

For example:

Alice
Bob
Charlie
🍕 Flexible Item Assignment

Each bill item can be assigned to:

One person
Multiple people
Everyone

For example:

Pizza       → Alice + Bob
Burger      → Bob
Fries       → Everyone

Shared items are divided equally among the people assigned to that item.

💰 Consumption-Based Tax Splitting

Taxes and service charges are not divided equally by headcount.

Instead, they are distributed proportionally according to each person's actual item consumption.

For example:

Alice consumption   = ₹500
Bob consumption     = ₹300
Charlie consumption = ₹200

Total consumption   = ₹1000

If the bill contains ₹180 tax:

Alice   → 50% → ₹90
Bob     → 30% → ₹54
Charlie → 20% → ₹36

This produces a more fair split when people consume different amounts.

⚠️ Bill Validation

The application validates the bill before performing the final split.

It checks:

Sum of item totals = Printed subtotal

and:

Subtotal + Tax + Service Charge - Discount = Printed total

If the values do not match, the application flags the bill for review instead of blindly trusting the printed total.

🏗️ System Architecture
                    ┌──────────────────────┐
                    │      Frontend        │
                    │ HTML / CSS / JS      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       Image Processing       OCR            Parser
          OpenCV           Tesseract       RapidFuzz
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  Pydantic Bill Model │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Human Review      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Item Assignment     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Split Calculator    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Person-Wise Results  │
                    └──────────────────────┘
🛠️ Tech Stack
Technology	Purpose
Python	Backend development
FastAPI	REST API and application backend
Pydantic	Data validation and structured bill models
OpenCV	Image preprocessing
Tesseract OCR	Text extraction from bill photographs
Pillow	Image handling
NumPy	Image processing operations
RapidFuzz	OCR text matching and fuzzy matching
SQLAlchemy	Database abstraction
SQLite	Local database
HTML	Frontend structure
CSS	Frontend styling
JavaScript	Frontend interaction
Pytest	Automated testing
📁 Project Structure
split the bill from a photograph/
│
├── app/
│   ├── api/
│   │   ├── routes.py
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── bill.py
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── calculator.py
│   │   ├── image_processing.py
│   │   ├── ocr.py
│   │   ├── parser.py
│   │   ├── validator.py
│   │   └── __init__.py
│   │
│   ├── templates/
│   │   └── index.html
│   │
│   ├── main.py
│   └── __init__.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── app.js
│
├── tests/
│   ├── test_api.py
│   ├── test_calculator.py
│   ├── test_ocr.py
│   ├── test_parser.py
│   └── test_validator.py
│
├── test_data/
│   ├── ground_truth/
│   ├── images/
│   └── evaluate.py
│
├── requirements.txt
├── run.py
├── .gitignore
└── README.md
⚙️ Installation & Setup
1. Clone the Repository
git clone https://github.com/Mishika620/Split-the-bill-from-a-photograph.git
cd Split-the-bill-from-a-photograph
2. Create a Virtual Environment
python -m venv .venv
3. Activate the Virtual Environment
Windows PowerShell
.venv\Scripts\Activate.ps1
4. Install Python Dependencies
python -m pip install -r requirements.txt
5. Install Tesseract OCR

Install Tesseract OCR on the system.

The application is configured to use:

C:\Program Files\Tesseract-OCR\tesseract.exe

The OCR service checks this path and configures Tesseract automatically when the executable exists.

▶️ How to Run

Start the application from the project root:

python run.py

The application will run locally.

Open the following URL in your browser:

http://127.0.0.1:8000

Then follow the workflow:

Upload → Review → Assign → Split
Typical Usage
Upload a bill photograph.
Wait for OCR extraction.
Review the extracted items and amounts.
Correct any OCR mistakes.
Add the people sharing the bill.
Assign each item to the appropriate person or people.
Validate the bill.
Calculate the final person-wise split.
🔌 API Endpoints
POST /extract

Uploads a bill image and extracts structured bill information using the OCR pipeline.

Input

A bill image in:

JPG
JPEG
PNG
WEBP
Output

Structured bill information including:

Items
Quantity
Prices
Subtotal
Tax
Service charge
Discount
Total
Confidence scores
POST /review

Accepts reviewed and corrected bill information and validates the structured bill data.

This endpoint represents the human-review stage of the workflow.

POST /split

Calculates person-wise bill amounts based on item consumption.

The calculation includes:

Item totals
Shared item allocation
Tax allocation
Service charge allocation
Discount allocation
Final amount per person
🧮 Bill Splitting Logic

The application calculates each person's consumption from the items assigned to them.

Individual Item

If an item costs ₹200 and is assigned only to Alice:

Alice → ₹200
Bob   → ₹0
Shared Item

If an item costs ₹300 and is assigned to Alice and Bob:

Alice → ₹150
Bob   → ₹150
Everyone

If an item costs ₹600 and three people are assigned:

Alice   → ₹200
Bob     → ₹200
Charlie → ₹200
Tax and Service Charge

Tax and service charges are distributed according to consumption proportion.

For example:

Alice   → ₹500 consumption
Bob     → ₹300 consumption
Charlie → ₹200 consumption

Consumption ratio:

Alice   → 50%
Bob     → 30%
Charlie → 20%

A ₹180 tax would therefore become:

Alice   → ₹90
Bob     → ₹54
Charlie → ₹36

The calculator also handles rounding differences so that the allocated amounts reconcile to the expected bill amount.

🧪 Testing

The project contains automated tests covering the main backend functionality.

Tests cover:

API endpoints
Bill splitting
Shared items
Multiple-person assignments
Consumption-based allocation
Rounding
Discounts
OCR parsing
Bill validation
Invalid bill totals
Unassigned items

Run the complete test suite:

python -m pytest
Current Test Result
15 passed, 2 warnings

The warnings are dependency deprecation warnings and do not represent test failures.

📊 OCR Evaluation

The project includes an evaluation framework using 12 bill images representing challenging real-world conditions.

The evaluation dataset includes:

Normal printed receipt
Dim lighting
Crumpled receipt
Steep camera angle
Faded thermal paper
Handwritten additions
Multiple scripts/languages
Long receipt
Low-resolution photograph
Shadows and glare
Multiple shared items
Incorrect printed total

Each evaluation case is associated with manually prepared ground-truth data.

📈 Current Evaluation Results
Metric	Result
Item detection	47.92%
Quantity detection	45.83%
Price detection	40.28%

These results demonstrate that OCR performance can vary significantly depending on image quality and bill conditions.

The application therefore uses a human-review stage before financial calculations are finalized.

⚠️ Handling Incorrect Printed Totals

The system does not blindly trust the printed total.

It independently calculates:

Expected Total =
Subtotal + Tax + Service Charge - Discount

and compares it with the printed total.

If there is a mismatch, the bill is flagged for review.

The evaluation dataset includes intentionally incorrect printed-total cases to test this validation behaviour.

🧩 What Is Mocked?

The core bill-processing and bill-splitting workflow is implemented and is not mocked.

The following components are simplified or local:

OCR

Tesseract OCR is executed locally instead of using a cloud OCR service.

Database

SQLite is used for local development rather than a production database.

Evaluation Dataset

The evaluation dataset contains bill photographs and manually prepared ground-truth JSON files for testing and comparison.

People

People participating in the bill are manually entered by the user.

Item Assignment

Users manually decide which person or people consumed each item.

Payment

No real payment gateway or financial transaction processing is implemented.

External Services

The project does not depend on:

Cloud OCR APIs
Payment gateways
Chatbots
External AI APIs

The OCR, parsing, validation, calculation, and review workflow run locally.

👤 Human-in-the-Loop Design

The project intentionally keeps a human verification step between OCR extraction and financial calculation.

OCR Extraction
      ↓
Confidence Scores
      ↓
Human Review
      ↓
Correction
      ↓
Validation
      ↓
Bill Splitting

This design reduces the risk of an OCR error directly producing an incorrect amount for a person.

⚠️ Limitations

OCR performance can vary depending on:

Image quality
Lighting
Camera angle
Receipt folds
Faded thermal printing
Handwritten additions
Multiple scripts
Shadows
Glare
Low-resolution photographs

The current parser is designed as a practical OCR pipeline and does not guarantee perfect extraction from every possible receipt.

For this reason, the human-review stage is an important part of the application.

🔮 Future Improvements

Potential future improvements include:

Advanced receipt-understanding models
Better perspective correction
Improved multilingual OCR
Better handwritten-text recognition
Automatic item-to-person assignment suggestions
Improved confidence calibration
More extensive real-world bill datasets
Cloud deployment
Persistent bill history
User authentication
Production-grade database support
Mobile application
Payment integration
🎯 Project Goals

This project demonstrates practical implementation of:

Computer vision based image preprocessing
OCR-based information extraction
Structured data validation
Confidence scoring
Human-in-the-loop AI workflows
Consumption-based financial calculations
REST API development using FastAPI
Automated testing using Pytest
OCR evaluation on challenging bill images
Validation of inconsistent financial data
🔐 Data & Privacy

Bill images are processed locally during development.

The application does not require a cloud OCR provider or external payment service.

Uploaded images used during processing are handled by the local application workflow and are not intended to be used as a permanent public dataset.
