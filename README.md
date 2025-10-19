
# 🐙 Jelliemon

Jelliemon is a Django-based application containerized with Docker for simple setup and consistent environment management.

---

## 🚀 Getting Started

Follow these steps to run **Jelliemon** locally:

### 1. Clone the Repository

```bash
git clone https://github.com/kamleshmundel/jelliemon.git
```


### 2. Navigate to the Project Directory

```bash
cd jelliemon
```

### 3. Configure Environment Variables

Create a `.env` file in the project root using the provided sample:

```bash
cp .env.sample .env
```

Then edit `.env` and update the values as needed.

### 4. Build Docker Containers

```bash
docker compose build
```

### 5. Start the Containers

```bash
docker compose up -d
```

### 6. Access the Application

Visit the app at:
👉 **http://localhost:8000**

---

## 🧩 Notes

- Ensure Docker and Docker Compose are installed and running.
- To stop the containers:
  ```bash
  docker compose down
  ```
- To view logs:
  ```bash
  docker compose logs -f
  ```

---

## 🛠️ Tech Stack

- **Backend:** Django (Python 3.12)
- **Containerization:** Docker & Docker Compose
- **Environment Management:** `.env` configuration

---

Made with 💙 by the Jelliemon Team.

```

```
