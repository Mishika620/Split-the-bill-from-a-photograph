# Split the Bill From a Photograph

An OCR-powered bill splitting application that converts a bill photograph into structured bill data and calculates fair person-wise expenses based on actual item consumption.

## 📌 Overview

Splitting a restaurant or shopping bill manually can be inconvenient, especially when multiple people have different items.

**Split the Bill From a Photograph** allows users to:

1. Upload a photograph of a bill.
2. Extract bill information using OCR.
3. Review and correct extracted information.
4. Add multiple people.
5. Assign items to the people who consumed them.
6. Split shared items among multiple people.
7. Distribute tax and service charges proportionally according to actual consumption.
8. Validate the bill before calculating the final split.

The application follows a **human-in-the-loop workflow**, ensuring that OCR mistakes can be reviewed and corrected before the final calculation.

---

## ✨ Features

### 📷 Bill Image Upload

Supports common bill image formats:

- JPG
- JPEG
- PNG
- WEBP

### 🔎 OCR-Based Extraction

Uses **Tesseract OCR** to extract text from bill photographs.

The system attempts to identify:

- Item names
- Quantities
- Unit prices
- Item totals
- Subtotal
- Tax / GST
- Service charge
- Discount
- Printed total

### 🧾 Structured Bill Representation

Extracted bill information is converted into validated structured data using **Pydantic models**.

The system also maintains confidence scores for important extracted fields.

### 👤 Human Review

OCR results are displayed in a review interface before calculations are performed.

Users can correct:

- Item names
- Quantities
- Prices
- Subtotal
- Tax
- Service charge
- Discount
- Total

This prevents OCR errors from directly affecting the final bill calculation.

### 👥 Multiple People

Users can add multiple people participating in the bill.

### 🍕 Flexible Item Assignment

Each item can be assigned to:

- One person
- Multiple people
- Everyone

Shared items are divided equally among their assigned people.

### 💰 Consumption-Based Tax Splitting

Taxes and service charges are **not divided equally by headcount**.

Instead, they are distributed proportionally according to each person's actual item consumption.

### ⚠️ Bill Validation

Before splitting, the system validates the bill by checking:

```text
Sum of item totals = Printed subtotal

Subtotal + tax + service charge - discount = Printed total
