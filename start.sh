#!/bin/bash
cd /app/api && uvicorn main:app --host 0.0.0.0 --port 8002 &
cd /app/frontend && streamlit run app.py --server.port 8080 --server.address 0.0.0.0
