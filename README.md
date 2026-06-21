# StudyMateAgent 🎓🤖

## 📋 Description
An intelligent AI agent that:
- 📄 Reads and understands documents (PDF, TXT, JSON)
- 🧠 Stores information in a vector database for quick retrieval
- ✅ Solves tests and quizzes based on the content
- 📱 Sends results directly to Telegram

Built with **Ollama + Python + FastAPI**, demonstrating **tool calling**, **RAG**, and **agentic workflows**.

## ✨ Features
- **File Processing**: Upload documents, agent reads and indexes them
- **Quiz Solving**: Answer questions based on document content
- **Tool Calling**: Weather, calculator, file operations, and more
- **Telegram Integration**: Get answers on your phone
- **Local LLM**: Runs completely offline with Ollama

## 🛠️ Tech Stack
- **Ollama** (qwen/llama models)
- **FastAPI** (backend)
- **ChromaDB** (vector storage)
- **python-telegram-bot** (messaging)
- **Streamlit** (UI)

## 🚀 Quick Start
```bash
git clone https://github.com/yourusername/StudyMateAgent
cd StudyMateAgent
pip install -r requirements.txt
python app.py
