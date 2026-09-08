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

The application is designed with a **human-in-the-loop workflow**, so OCR mistakes can be corrected before the final calculation.

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
- Prices
- Subtotal
- Tax / GST
- Service charge
- Discount
- Total

### 🧾 Structured Bill Representation

Extracted bill information is converted into validated structured data using **Pydantic models**.

Each important field also contains a confidence score.

### 👤 Human Review

Before splitting the bill, users can review and correct OCR-extracted information.

This prevents incorrect OCR values from directly affecting the final calculation.

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

The application checks whether:

```text
Sum of item prices = Printed subtotal