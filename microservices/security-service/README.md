# Security Service

HIPAA-Compliant Security Service for Clinical Trials Platform

## Features

- **JWT Authentication** - Secure token-based authentication
- **Authorization** - Role-based access control (admin, data_analyst, clinician)
- **PHI Encryption** - Fernet (AES-128 CBC) authenticated encryption for Protected Health Information
- **PHI Detection** - Automatic detection and blocking of PHI in uploads
- **Audit Logging** - Comprehensive audit trail for HIPAA compliance
- **Zero Trust** - All access requires authentication and authorization

## Endpoints

- `POST /auth/login` - Authenticate and get JWT token
- `POST /auth/validate` - Validate JWT token (for API Gateway)
- `GET /auth/me` - Get current user info
- `POST /encryption/encrypt` - Encrypt PHI data
- `POST /encryption/decrypt` - Decrypt PHI data (requires authorization)
- `POST /phi/detect` - Detect PHI in data
- `POST /audit/log` - Create audit log entry
- `GET /audit/logs` - Retrieve audit logs (admin only)

## Default Users

- `admin` / `admin123` - Full access
- `analyst` / `analyst123` - Data analysis access
- `clinician` / `clinician123` - Clinical data access

## HIPAA Compliance

✅ Authentication required for all access  
✅ Encryption at rest for PHI  
✅ Immutable audit logging  
✅ PHI detection to prevent accidental exposure  
✅ Role-based authorization  

## Running Locally

```bash
cd security-service
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8005
```

## Docker

```bash
docker build -t security-service .
docker run -p 8005:8005 security-service
```

