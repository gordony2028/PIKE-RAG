# Deploying PIKE-RAG to Railway

This guide walks you through deploying the PIKE-RAG web application to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Azure OpenAI Account**: Set up Azure OpenAI service or standard OpenAI API
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)

## Quick Deployment Steps

### 1. Connect Your Repository

1. Go to [railway.app](https://railway.app) and click "Start a New Project"
2. Choose "Deploy from GitHub repo" (or your git provider)
3. Select your PIKE-RAG repository
4. Railway will automatically detect the Python application

### 2. Set Environment Variables

In the Railway dashboard, go to your project's Variables tab and add:

**For Azure OpenAI:**
```
OPENAI_API_TYPE=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
RAILWAY_ENVIRONMENT=production
FLASK_ENV=production
```

**For Standard OpenAI API:**
```
OPENAI_API_KEY=your-openai-api-key
RAILWAY_ENVIRONMENT=production
FLASK_ENV=production
```

### 3. Deploy

Railway will automatically build and deploy your application using the configuration files:
- `railway.toml` - Railway deployment configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Process definitions
- `requirements-production.txt` - Python dependencies

## Configuration Files Overview

### `railway.toml`
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements-production.txt"

[deploy]
startCommand = "python webapp/app.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### `nixpacks.toml`
Configures the build environment with Python 3.10, required system packages, and directory setup.

### `requirements-production.txt`
Contains all necessary dependencies including Flask, gunicorn, and PIKE-RAG components.

## Application Features

The deployed web application includes:
- **Question Answering**: Ask questions and get AI-powered responses
- **Health Check**: `/api/health` endpoint for monitoring
- **Example Questions**: Pre-built examples across different categories
- **Caching**: Automatic response caching for efficiency
- **Logging**: Comprehensive logging for debugging

## API Endpoints

- `GET /` - Web interface
- `POST /api/ask` - Submit questions
- `GET /api/health` - Health check
- `GET /api/examples` - Get example questions

## Environment Configuration

The application automatically detects Railway environment and handles:
- Dynamic port binding (Railway sets `PORT` environment variable)
- Environment variable loading from multiple sources
- Production vs development mode detection
- Automatic directory creation for logs and cache

## Monitoring and Logs

- **Railway Logs**: View real-time logs in the Railway dashboard
- **Health Checks**: Use `/api/health` endpoint to monitor service status
- **Application Logs**: Stored in `webapp/logs/` directory
- **Cache Files**: LLM response cache stored in `webapp/logs/webapp_cache.db`

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all dependencies in `requirements-production.txt` are valid
   - Ensure Python 3.10 compatibility

2. **Environment Variable Issues**
   - Verify all required variables are set in Railway dashboard
   - Check variable names match exactly (case-sensitive)

3. **API Connection Issues**
   - Validate Azure OpenAI endpoint and API key
   - Ensure API version is supported
   - Check network connectivity and firewall rules

4. **Memory Issues**
   - Consider upgrading Railway plan for more memory
   - Monitor resource usage in Railway dashboard

### Debug Steps

1. **Check Railway Logs**:
   - Go to your project in Railway dashboard
   - Click on "Deployments" tab
   - View build and runtime logs

2. **Test Health Endpoint**:
   ```bash
   curl https://your-app.railway.app/api/health
   ```

3. **Test API Endpoint**:
   ```bash
   curl -X POST https://your-app.railway.app/api/ask \
        -H "Content-Type: application/json" \
        -d '{"question": "What is AI?"}'
   ```

## Local Testing

Before deploying, test the Railway configuration locally:

```bash
# Install production dependencies
pip install -r requirements-production.txt

# Set environment variables
export RAILWAY_ENVIRONMENT=development
export FLASK_ENV=development
export PORT=5001

# Run the application
python webapp/app.py
```

## Security Notes

- Never commit API keys or sensitive data to your repository
- Use Railway's environment variables for all secrets
- The application includes CORS support for web interfaces
- Consider adding authentication for production use
- Monitor API usage to prevent unexpected costs

## Scaling

Railway automatically handles:
- HTTP/HTTPS termination
- Load balancing
- Auto-scaling based on traffic
- Zero-downtime deployments

For high-traffic applications, consider:
- Adding Redis for distributed caching
- Using a managed database service
- Implementing rate limiting
- Adding CDN for static assets

## Cost Optimization

- Railway offers a generous free tier
- Monitor resource usage in the dashboard
- Consider caching strategies to reduce API calls
- Use environment-based scaling policies

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- PIKE-RAG Issues: [GitHub Issues](https://github.com/microsoft/PIKE-RAG/issues)
- Railway Community: [Railway Discord](https://railway.app/discord)