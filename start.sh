#!/bin/bash
# EFMD Gap Analysis Tool - Startup Script
# ========================================

echo "🎓 EFMD Gap Analysis Tool"
echo "========================="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys:"
    echo "   - SUPABASE_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GOOGLE_API_KEY"
    exit 1
fi

# Load environment
source .env

# Check required vars
if [ -z "$SUPABASE_KEY" ] || [ "$SUPABASE_KEY" = "your_service_role_key_here" ]; then
    echo "❌ SUPABASE_KEY not set in .env"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY not set in .env"
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Start mode selection
PS3="Select what to run: "
options=("API Server (FastAPI)" "Frontend (Streamlit)" "Both (Background)" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "API Server (FastAPI)")
            echo "🚀 Starting API on http://localhost:8002"
            cd api && uvicorn main:app --reload --port 8002
            break
            ;;
        "Frontend (Streamlit)")
            echo "🚀 Starting Frontend on http://localhost:8501"
            cd frontend && streamlit run app.py
            break
            ;;
        "Both (Background)")
            echo "🚀 Starting API on http://localhost:8002"
            cd api && uvicorn main:app --port 8002 &
            API_PID=$!
            cd ..
            sleep 2
            echo "🚀 Starting Frontend on http://localhost:8501"
            cd frontend && streamlit run app.py
            kill $API_PID
            break
            ;;
        "Quit")
            break
            ;;
        *) echo "Invalid option";;
    esac
done
