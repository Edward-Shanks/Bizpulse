# Environment Variables Setup Guide

This guide lists all environment variables needed for both frontend and backend.

## Backend `.env` File

Create or update `backend/.env` with the following variables:

### Required Variables

```env
# MongoDB Configuration (REQUIRED)
MONGO_URL=mongodb://localhost:27017
DB_NAME=bizpulse

# Environment Mode (REQUIRED)
# Set to 'development' for dev mode, 'production' for production
ENVIRONMENT=development

# JWT Configuration
JWT_SECRET=thrive-brands-biz-pulse-secret-2024
# JWT_EXPIRATION_HOURS is optional (defaults to 24 hours)
# JWT_EXPIRATION_HOURS=24

# CORS Configuration
# For development: http://localhost:3000
# For production: your production frontend URL
CORS_ORIGINS=http://localhost:3000
```

### Optional Variables

```env
# Azure Blob Storage (Optional - for future use)
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=your_container_name
AZURE_BLOB_PATH=your_blob_path

# LLM Configuration (Optional)
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key

# Ollama Configuration (Optional - for local LLM)
OLLAMA_BASE_URL=http://localhost:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
LLM_PROVIDER=ollama

# Ollama Multiple Instances (Optional - for load balancing)
# Format: comma-separated URLs
OLLAMA_ENDPOINTS=http://localhost:11434,http://localhost:11435,http://localhost:11436,http://localhost:11437

# SMTP Configuration (Optional - for password reset emails in production)
# Only needed if you want to send actual emails in production
# In development, emails are just logged to console
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Environment-Specific Notes

**Development Mode (`ENVIRONMENT=development`):**
- Signup endpoint is enabled
- User management endpoint is enabled
- Password reset emails are logged to console (not sent)
- More detailed error messages

**Production Mode (`ENVIRONMENT=production`):**
- Signup endpoint is disabled
- User management endpoint is disabled
- Password reset emails are sent via SMTP (if configured)
- Generic error messages for security

---

## Frontend `.env` File

Create or update `frontend/.env` with the following variables:

### Required Variables

```env
# Backend API URL (REQUIRED)
# For development: http://localhost:8000
# For production: your production backend URL
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Environment Detection

The frontend automatically detects the environment using `NODE_ENV`:

- **Development**: When running `npm start` or `npm run dev`
  - Signup route is visible
  - User management route is visible
  - Development features are enabled

- **Production**: When running `npm run build` and serving the build
  - Signup route is hidden
  - User management route is hidden
  - Only production features are available

**Note**: `NODE_ENV` is automatically set by React scripts. You don't need to set it manually in `.env`.

---

## Complete Example Files

### `backend/.env` (Development)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=bizpulse

# Environment
ENVIRONMENT=development

# JWT
JWT_SECRET=thrive-brands-biz-pulse-secret-2024

# CORS
CORS_ORIGINS=http://localhost:3000

# Ollama (if using local LLM)
OLLAMA_BASE_URL=http://localhost:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_ENDPOINTS=http://localhost:11434,http://localhost:11435,http://localhost:11436,http://localhost:11437
```

### `backend/.env` (Production)

```env
# MongoDB
MONGO_URL=mongodb://your-production-mongodb-url
DB_NAME=bizpulse

# Environment
ENVIRONMENT=production

# JWT (Use a strong, unique secret in production!)
JWT_SECRET=your-strong-random-secret-key-here

# CORS
CORS_ORIGINS=https://your-production-frontend-url.com

# SMTP (for password reset emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Ollama (if using local LLM)
OLLAMA_BASE_URL=http://your-ollama-server:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
```

### `frontend/.env` (Development)

```env
REACT_APP_BACKEND_URL=http://localhost:8000
# Optional: Explicitly set development mode (fallback if NODE_ENV not detected)
REACT_APP_ENVIRONMENT=development
```

### `frontend/.env` (Production)

```env
REACT_APP_BACKEND_URL=https://your-production-backend-url.com
```

---

## Quick Setup Checklist

### Backend Setup:
- [ ] Create `backend/.env` file
- [ ] Set `MONGO_URL` and `DB_NAME`
- [ ] Set `ENVIRONMENT=development` (or `production`)
- [ ] Set `CORS_ORIGINS` to match your frontend URL
- [ ] (Optional) Configure SMTP for production password resets
- [ ] (Optional) Configure Ollama endpoints if using local LLM

### Frontend Setup:
- [ ] Create `frontend/.env` file
- [ ] Set `REACT_APP_BACKEND_URL` to match your backend URL
- [ ] Restart frontend server after changes

---

## Important Notes

1. **Never commit `.env` files to version control** - They contain sensitive information
2. **Use different secrets for development and production**
3. **In production, use strong, randomly generated JWT secrets**
4. **SMTP configuration is optional** - In development, password reset emails are just logged
5. **Frontend `NODE_ENV` is automatically set** - Don't set it manually in `.env`

---

## Troubleshooting

### Backend not reading `.env` file:
- Make sure the file is named exactly `.env` (not `.env.txt`)
- Make sure the file is in the `backend/` directory
- Restart the backend server after changes

### Frontend not reading `.env` file:
- Make sure the file is named exactly `.env` (not `.env.txt`)
- Make sure the file is in the `frontend/` directory
- Variable names must start with `REACT_APP_`
- Restart the frontend server after changes

### Environment detection not working:
- Backend: Check that `ENVIRONMENT` is set to exactly `development` or `production` (case-insensitive)
- Frontend: `NODE_ENV` is automatically set by React - check your `package.json` scripts

