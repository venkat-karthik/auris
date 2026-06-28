# 🚀 Auris Local Startup & Development Guide

This guide provides step-by-step instructions to set up, configure, and run the **Auris Voice AI Platform** on your local machine.

---

## 📋 Prerequisites & Runtimes

Ensure you have the following installed on your host system:
1. **Docker & Docker Compose**: For database, caching, and storage.
2. **Python 3.12**: Do not use Python 3.13 or 3.14 as they lack pre-compiled binary wheels for database dependencies.
3. **Node.js (LTS)** and **npm**: For the web studio interface.

---

## 🛠️ Step-by-Step Setup

### 1. Start Docker Containers
Open Docker Desktop on your machine. Then, run the following command in the root directory to spin up the containerized database (PostgreSQL + pgvector), caching queue (Redis), and object storage (MinIO):
```bash
docker compose up postgres redis minio -d
```
> [!NOTE]
> The database image has been updated to `pgvector/pgvector:pg16` in [docker-compose.yml](file:///d:/Auris/docker-compose.yml) to natively support database vector embeddings.

---

### 2. Configure Backend Environment
Copy the example environment configuration to `.env` in the backend directory:
```powershell
cp backend/.env.example backend/.env
```
Open [backend/.env](file:///d:/Auris/backend/.env) and enter your credentials (e.g. `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`). For basic dashboard exploration, these keys can be left blank or as default values.

---

### 3. Setup Python Virtual Environment & Install Dependencies
Navigate to the `backend` folder, create a Python 3.12 virtual environment, and install the library dependencies:
```powershell
cd backend

# Create the virtual environment using Python 3.12
py -3.12 -m venv .venv

# Activate and install dependencies (Windows Powershell)
.venv\Scripts\pip install -r requirements.txt
```

---

### 4. Run Database Migrations
Run the database migrations inside the virtual environment to initialize the Postgres tables and vector extensions:
```powershell
.venv\Scripts\alembic upgrade head
```

---

### 5. Launch the FastAPI Backend Server
Start the backend API server locally on port `8000`:
```powershell
.venv\Scripts\uvicorn app.main:app --port 8000 --reload
```
*   **API Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
*   **Interactive Swagger Documentation**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### 6. Install & Start the Next.js Frontend Console
Open a new terminal window in the `frontend` folder, install Node modules, and run the Next.js dev server:
```powershell
cd frontend
npm install
npm run dev
```
*   **Web Studio URL**: [http://localhost:3000](http://localhost:3000)

---

## 🔑 Signup & Login Flow
There are no default credentials in the database. To log in:
1. Navigate to [http://localhost:3000/auth/signup](http://localhost:3000/auth/signup) in your browser.
2. Complete the signup form.
3. The server prints a **6-digit verification code** to the terminal logs of your running backend.
4. Enter the code in your browser to verify your account and automatically log in to the dashboard.
