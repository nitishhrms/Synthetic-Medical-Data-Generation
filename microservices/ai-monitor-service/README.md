# AI Medical Monitor Service

Simple AI-powered medical monitor that reviews clinical trial data and raises queries.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional - works without API keys in demo mode):
```bash
export OPENAI_API_KEY="your-key-here"
# OR
export ANTHROPIC_API_KEY="your-key-here"

export EDC_SERVICE_URL="http://localhost:8001"
```

3. Run the service:
```bash
python -m uvicorn src.main:app --reload --port 8008
```

## Features

- **Subject Review**: AI reviews individual subject data
- **Study Review**: AI reviews all subjects in a study
- **Auto-Post Queries**: Automatically posts findings as queries to EDC

## Demo Mode

If no API key is provided, the service runs in demo mode with mock findings.

## API Endpoints

- `GET /health` - Health check
- `POST /review/subject` - Review single subject
- `POST /review/study` - Review all subjects in study
- `POST /review/study/post-queries` - Review and post queries to EDC
