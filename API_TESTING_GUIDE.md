# Payment Gateway API Testing Guide

This guide explains how to test all endpoints from signup to payment, including the KYC submission and admin verification flow.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Endpoints Overview](#api-endpoints-overview)
3. [Testing Flow](#testing-flow)
4. [Step-by-Step Testing](#step-by-step-testing)
5. [Webhook Testing](#webhook-testing)
6. [Admin Operations](#admin-operations)

---

## Prerequisites

### 1. Start the Django Server
```bash
python manage.py runserver
```

### 2. Create Database Migrations (if needed)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create a Superuser (Admin)
```bash
python manage.py createsuperuser
```
Enter email and password when prompted.

### 4. Tools for Testing
- **Postman** (recommended)
- **cURL** (command line)
- **HTTPie** (command line)

---

## API Endpoints Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/register` | POST | None | Merchant signup |
| `/api/auth/login` | POST | None | User login (JWT) |
| `/api/auth/forgot-password/` | POST | None | Request password reset |
| `/api/auth/reset-password/<token>/` | POST | None | Reset password |
| `/api/merchants/dashboard/` | GET | JWT | Merchant dashboard |
| `/api/merchants/kyc/submit/` | POST | JWT | Submit KYC documents |
| `/api/merchants/api-keys/` | GET | JWT | List merchant's API keys |
| `/api/merchants/api-keys/` | POST | JWT | Generate new API keys |
| `/api/merchants/api-keys/` | DELETE | JWT | Deactivate an API key |
| `/api/merchants/admin/merchants/` | GET | JWT (Admin) | List all merchants |
| `/api/merchants/admin/merchants/<id>/kyc/` | GET | JWT (Admin) | View merchant KYC |
| `/api/merchants/admin/merchants/<id>/kyc/` | POST | JWT (Admin) | Approve/Reject KYC |
| `/api/payments/initiate` | POST | API Key | Initiate payment |
| `/api/webhooks/flutterwave/` | POST | Signature | Flutterwave webhook |
| `/admin/` | GET | Session | Django Admin Panel |

---

## Testing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE TESTING FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. MERCHANT SIGNUP                                                          │
│     POST /api/auth/register                                                  │
│     └── Creates User + MerchantProfile (kyc_status=PENDING, is_enabled=False)│
│                                                                              │
│  2. MERCHANT LOGIN                                                           │
│     POST /api/auth/login                                                     │
│     └── Returns JWT access token                                             │
│                                                                              │
│  3. MERCHANT SUBMITS KYC                                                     │
│     POST /api/merchants/kyc/submit/                                          │
│     └── Creates MerchantKYC record with documents                            │
│                                                                              │
│  4. ADMIN REVIEWS KYC                                                        │
│     GET /api/merchants/admin/merchants/<id>/kyc/                             │
│     └── Admin views KYC details                                              │
│                                                                              │
│  5. ADMIN APPROVES KYC                                                       │
│     POST /api/merchants/admin/merchants/<id>/kyc/                            │
│     └── Sets kyc_status=APPROVED, is_enabled=True                            │
│                                                                              │
│  6. MERCHANT GENERATES API KEYS (Self-Service!)                              │
│     POST /api/merchants/api-keys/                                            │
│     └── Creates MerchantAPIKey, returns secret key (shown only once!)        │
│                                                                              │
│  7. MERCHANT INITIATES PAYMENT                                               │
│     POST /api/payments/initiate                                              │
│     └── Creates Transaction, returns Flutterwave checkout URL                │
│                                                                              │
│  8. CUSTOMER PAYS (External)                                                 │
│     └── Customer completes payment on Flutterwave                            │
│                                                                              │
│  9. WEBHOOK CONFIRMS PAYMENT                                                 │
│     POST /api/webhooks/flutterwave/                                          │
│     └── Updates Transaction status, moves pending → available balance        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Testing

### Step 1: Merchant Signup

**Endpoint:** `POST /api/auth/register`

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "merchant@example.com",
    "password": "securepassword123",
    "business_name": "My Awesome Store"
  }'
```

**Expected Response:**
```json
{
  "message": "Account created successfully"
}
```

---

### Step 2: Merchant Login

**Endpoint:** `POST /api/auth/login`

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "merchant@example.com",
    "password": "securepassword123"
  }'
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "role": "MERCHANT"
}
```

**Save the `access` token for subsequent requests!**

---

### Step 3: View Merchant Dashboard

**Endpoint:** `GET /api/merchants/dashboard/`

```bash
curl -X GET http://localhost:8000/api/merchants/dashboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response (before KYC):**
```json
{
  "email": "merchant@example.com",
  "role": "MERCHANT",
  "business_name": "My Awesome Store",
  "kyc_status": "PENDING",
  "is_enabled": false,
  "kyc_submitted": false,
  "kyc_details": null
}
```

---

### Step 4: Submit KYC Documents

**Endpoint:** `POST /api/merchants/kyc/submit/`

This endpoint accepts `multipart/form-data` for file uploads.

```bash
curl -X POST http://localhost:8000/api/merchants/kyc/submit/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "business_type=Individual" \
  -F "business_address=123 Main Street, Lagos, Nigeria" \
  -F "owner_full_name=John Doe" \
  -F "owner_date_of_birth=1990-05-15" \
  -F "document_type=NIN" \
  -F "document_number=12345678901" \
  -F "document_image=@/path/to/your/document.jpg"
```

**Required Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `business_type` | string | "Individual" or "Registered Business" |
| `business_address` | string | Full business address |
| `owner_full_name` | string | Owner's full legal name |
| `owner_date_of_birth` | date | Format: YYYY-MM-DD |
| `document_type` | string | "NIN", "PASSPORT", or "DRIVERS_LICENSE" |
| `document_number` | string | Document ID number |
| `document_image` | file | Image of the document |

**Expected Response:**
```json
{
  "message": "KYC submitted successfully. Awaiting admin review.",
  "kyc_id": 1,
  "submitted_at": "2026-01-16T20:00:00Z"
}
```

---

### Step 5: Admin Login

First, create an admin user if you haven't:
```bash
python manage.py createsuperuser
```

Then login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "adminpassword123"
  }'
```

**Note:** Make sure the admin user has `role="ADMIN"`. You can set this via Django Admin or shell:
```python
python manage.py shell
>>> from users.models import User
>>> user = User.objects.get(email="admin@example.com")
>>> user.role = "ADMIN"
>>> user.save()
```

---

### Step 6: Admin Lists All Merchants

**Endpoint:** `GET /api/merchants/admin/merchants/`

```bash
curl -X GET http://localhost:8000/api/merchants/admin/merchants/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "business_name": "My Awesome Store",
    "user_email": "merchant@example.com",
    "kyc_status": "PENDING",
    "is_enabled": false,
    "created_at": "2026-01-16T19:00:00Z"
  }
]
```

---

### Step 7: Admin Views Merchant KYC

**Endpoint:** `GET /api/merchants/admin/merchants/<merchant_id>/kyc/`

```bash
curl -X GET http://localhost:8000/api/merchants/admin/merchants/1/kyc/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "merchant_id": 1,
  "business_name": "My Awesome Store",
  "business_type": "Individual",
  "business_address": "123 Main Street, Lagos, Nigeria",
  "owner_full_name": "John Doe",
  "owner_date_of_birth": "1990-05-15",
  "document_type": "NIN",
  "document_number": "12345678901",
  "document_image": "/media/kyc_documents/document.jpg",
  "submitted_at": "2026-01-16T20:00:00Z",
  "reviewed_at": null,
  "review_notes": null
}
```

---

### Step 8: Admin Approves/Rejects KYC

**Endpoint:** `POST /api/merchants/admin/merchants/<merchant_id>/kyc/`

**To Approve:**
```bash
curl -X POST http://localhost:8000/api/merchants/admin/merchants/1/kyc/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "review_notes": "All documents verified successfully."
  }'
```

**Expected Response:**
```json
{
  "message": "Merchant KYC approved and account enabled",
  "merchant_id": 1,
  "kyc_status": "APPROVED",
  "is_enabled": true
}
```

**To Reject:**
```bash
curl -X POST http://localhost:8000/api/merchants/admin/merchants/1/kyc/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "review_notes": "Document image is blurry. Please resubmit."
  }'
```

---

### Step 9: Generate API Keys (Merchant Self-Service)

**Endpoint:** `POST /api/merchants/api-keys/`

Merchants can generate their own API keys after KYC is approved!

```bash
curl -X POST http://localhost:8000/api/merchants/api-keys/ \
  -H "Authorization: Bearer YOUR_MERCHANT_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "TEST"
  }'
```

**Expected Response:**
```json
{
  "message": "API keys generated successfully",
  "public_key": "pk_abc123def456",
  "secret_key": "sk_xyz789abc123def456ghi789jkl012mno345pqr678",
  "environment": "TEST",
  "warning": "SAVE YOUR SECRET KEY NOW! It will not be shown again."
}
```

**⚠️ IMPORTANT:** Save the `secret_key` immediately! It's hashed in the database and cannot be retrieved later.

---

### Step 9b: List Your API Keys

**Endpoint:** `GET /api/merchants/api-keys/`

```bash
curl -X GET http://localhost:8000/api/merchants/api-keys/ \
  -H "Authorization: Bearer YOUR_MERCHANT_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "public_key": "pk_abc123def456",
    "environment": "TEST",
    "is_active": true,
    "created_at": "2026-01-16T20:00:00Z"
  }
]
```

---

### Step 9c: Deactivate an API Key

**Endpoint:** `DELETE /api/merchants/api-keys/`

```bash
curl -X DELETE http://localhost:8000/api/merchants/api-keys/ \
  -H "Authorization: Bearer YOUR_MERCHANT_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_id": 1
  }'
```

**Expected Response:**
```json
{
  "message": "API key deactivated successfully",
  "key_id": 1
}
```

---

### Alternative: Generate API Keys via Django Admin

Admins can also generate keys for merchants:

1. Go to `http://localhost:8000/admin/`
2. Login with admin credentials
3. Navigate to **Merchants > Merchant API Keys**
4. Click **Add Merchant API Key**
5. Select the merchant
6. Choose environment (TEST or LIVE)

**Or use Django shell:**
```python
python manage.py shell
>>> from merchants.models import MerchantProfile, MerchantAPIKey
>>> from merchants.utils import generate_api_keys
>>> 
>>> merchant = MerchantProfile.objects.get(id=1)
>>> public_key, secret_key, secret_hash = generate_api_keys()
>>> 
>>> MerchantAPIKey.objects.create(
...     merchant=merchant,
...     public_key=public_key,
...     secret_key_hash=secret_hash,
...     environment="TEST",
...     is_active=True
... )
>>> 
>>> print(f"Public Key: {public_key}")
>>> print(f"Secret Key: {secret_key}")  # SAVE THIS! It won't be shown again!
```

---

### Step 10: Initiate Payment

**Endpoint:** `POST /api/payments/initiate`

**Authentication:** Use the merchant's secret API key (not JWT!)

```bash
curl -X POST http://localhost:8000/api/payments/initiate \
  -H "Authorization: Bearer sk_your_secret_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "currency": "NGN",
    "customer": {
      "email": "customer@example.com",
      "name": "Customer Name",
      "phone_number": "08012345678"
    }
  }'
```

**Expected Response:**
```json
{
  "checkout_url": "https://checkout.flutterwave.com/v3/hosted/pay/xxxxx",
  "reference": "TX-abc123def456"
}
```

**Note:** This endpoint requires:
- Merchant KYC to be APPROVED
- Merchant to be enabled (`is_enabled=True`)
- Valid, active API key

---

### Step 11: Customer Completes Payment

The customer is redirected to the `checkout_url` where they complete payment via Flutterwave.

---

### Step 10b: Initiate Crypto Payment

**Endpoint:** `POST /api/payments/crypto/initiate`

**Authentication:** Use the merchant's secret API key (not JWT!)

```bash
curl -X POST http://localhost:8000/api/payments/crypto/initiate \
  -H "Authorization: Bearer sk_your_secret_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100",
    "currency": "USDT",
    "network": "TRC20"
  }'
```

**Expected Response:**
```json
{
  "reference": "CR-abc123def456",
  "deposit_address": "TFiuq1PHu2A5D2cK5ZoMhvSqikZdwQxTCo",
  "network": "TRC20",
  "amount": "100",
  "currency": "USDT"
}
```

**Note:** This endpoint requires:
- Merchant KYC to be APPROVED
- Merchant to be enabled (`is_enabled=True`)
- Valid, active API key

---

### Step 10c: List Available Crypto Assets

**Endpoint:** `GET /api/payments/crypto/assets`

No authentication required.

```bash
curl -X GET http://localhost:8000/api/payments/crypto/assets
```

**Expected Response:**
```json
{
  "assets": [
    {
      "coin": "USDT",
      "name": "Tether USD",
      "networks": [
        {
          "network": "TRC20",
          "chainType": "TRC20",
          "minDeposit": "1",
          "confirmations": "20"
        },
        {
          "network": "ERC20",
          "chainType": "ERC20",
          "minDeposit": "10",
          "confirmations": "12"
        }
      ]
    }
  ],
  "count": 1
}
```

---

### Step 10d: Get Deposit Address

**Endpoint:** `GET /api/payments/crypto/address`

No authentication required.

```bash
curl -X GET "http://localhost:8000/api/payments/crypto/address?coin=USDT&network=TRC20"
```

**Expected Response:**
```json
{
  "coin": "USDT",
  "network": "TRC20",
  "address": "TFiuq1PHu2A5D2cK5ZoMhvSqikZdwQxTCo",
  "tag": null
}
```

---

### Step 11: Customer Completes Payment

For fiat payments, the customer is redirected to the `checkout_url` where they complete payment via Flutterwave.

For crypto payments, the customer sends crypto to the `deposit_address`. The payment is confirmed via Bybit webhook.

---

### Step 12: Webhook Confirmation

Flutterwave sends a webhook to your server when payment is completed.

**Endpoint:** `POST /api/webhooks/flutterwave/`

**For Testing (simulate webhook):**
```bash
curl -X POST http://localhost:8000/api/webhooks/flutterwave/ \
  -H "Content-Type: application/json" \
  -H "verif-hash: YOUR_FLUTTERWAVE_SECRET_KEY" \
  -d '{
    "event": "charge.completed",
    "data": {
      "tx_ref": "TX-abc123def456",
      "status": "successful",
      "amount": 5000,
      "currency": "NGN"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

---

## Webhook Testing

### Using ngrok for Local Testing

1. Install ngrok: https://ngrok.com/download
2. Start ngrok:
   ```bash
   ngrok http 8000
   ```
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Configure this URL in your Flutterwave dashboard:
   - Go to Settings > Webhooks
   - Set webhook URL to: `https://abc123.ngrok.io/api/webhooks/flutterwave/`

---

## Admin Operations

### Django Admin Panel

Access at: `http://localhost:8000/admin/`

**Available Models:**
- **Users > Users** - Manage all users
- **Merchants > Merchant Profiles** - View/edit merchant profiles
- **Merchants > Merchant API Keys** - Generate/manage API keys
- **Merchants > Merchant KYCs** - View KYC submissions
- **Payments > Transactions** - View all transactions
- **Wallets > Wallets** - View merchant balances
- **Webhooks > Webhook Logs** - View webhook history

---

## Error Responses

### Common Error Codes

| Status | Error | Cause |
|--------|-------|-------|
| 400 | Missing required fields | Request body incomplete |
| 401 | Invalid API key | API key not found or inactive |
| 401 | Invalid credentials | Wrong email/password |
| 403 | Unauthorized | User doesn't have required role |
| 404 | Not found | Resource doesn't exist |

### API Key Errors

If payment initiation fails with "Invalid API key":
1. Check merchant is enabled (`is_enabled=True`)
2. Check KYC is approved (`kyc_status="APPROVED"`)
3. Check API key is active (`is_active=True`)
4. Verify you're using the secret key (starts with `sk_`)

---

## Postman Collection

### Environment Variables

Create these variables in Postman:
```
base_url: http://localhost:8000
merchant_token: (set after login)
admin_token: (set after admin login)
api_secret_key: (set after generating API keys)
```

### Sample Requests

Import this collection structure:

```
Payment Gateway API
├── Auth
│   ├── Register Merchant
│   ├── Login
│   ├── Forgot Password
│   └── Reset Password
├── Merchant
│   ├── Dashboard
│   └── Submit KYC
├── Admin
│   ├── List Merchants
│   ├── View Merchant KYC
│   └── Approve/Reject KYC
├── Payments
│   └── Initiate Payment
└── Webhooks
    └── Flutterwave Webhook
```

---

## Quick Test Script

Save this as `test_flow.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== 1. Register Merchant ==="
curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@merchant.com","password":"test123456","business_name":"Test Store"}'

echo -e "\n\n=== 2. Login Merchant ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@merchant.com","password":"test123456"}')
echo $RESPONSE
TOKEN=$(echo $RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo -e "\n\n=== 3. View Dashboard ==="
curl -s -X GET "$BASE_URL/api/merchants/dashboard/" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Done! ==="
```

---

## Summary

1. **Merchant signs up** → Creates User + MerchantProfile
2. **Merchant logs in** → Gets JWT token
3. **Merchant submits KYC** → Creates MerchantKYC record
4. **Admin reviews KYC** → Views submitted documents
5. **Admin approves KYC** → Enables merchant account
6. **Admin generates API keys** → Merchant can accept payments
7. **Merchant initiates payment** → Creates transaction, gets checkout URL
8. **Customer pays** → Completes payment on Flutterwave
9. **Webhook confirms** → Updates transaction, credits wallet

The merchant can only accept payments after:
- ✅ KYC is APPROVED
- ✅ Account is ENABLED
- ✅ API keys are generated and active
