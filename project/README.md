# Ragtime Project Setup

## Backend Setup and Execution

1. **Navigate to the backend directory:**
   ```bash
   cd ragtime-project/backend
   ```
2. **Create a virtual environment (optional but recommended):**

```
python -m venv venv
```

3. **Activate the virtual environment & Install the required dependencies:**

```python
pip install -r requirements.txt
```

4. **install the right Ragtime version :**

Go to the ragtime-package-2 and install the version there instead of the one available on GitHub, as it hasn't been updated yet.

```python
cd ragtime-package-2

pip install -e .
```

5. **Set up environment variables:**

Create a .env file in the backend directory.
Add the necessary environment variables (e.g., API keys, database URLs).
The APIs :

```
FLASK_SECRET_KEY=1aa1bcdcb4867f4502d0a22df1169b19da7cbd197dbb6db6
LSA_PASSWORD=pK06]q6~a|R;n
LSA_USERNAME=gilles@recital.ai
ALBERT_USERNAME=youssouf_boudouia
ALBERT_EMAIL=youssouf@recital.ai
ALBERT_PASSWORD=pwd?etaLABreciTAL24
MISTRAL_API_KEY=3NJDrczjoXVMltqPp0CJbMyKCB4p5862
```

5. **Start the backend server:**

```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 240 wsgi:application
```

## Frontend Setup and Execution

1. **Navigate to the frontend directory:**
   open a new terminal window and go to the ragtime-project

   ```bash
   cd ragtime-project
   ```

2. **Install the required npm packages:**

   ```bash
   npm install
   ```

3. **Start the frontend development server:**
   ```bash
   npm run serve
   ```

The frontend development server will typically be accessible at [http://localhost:8080](http://localhost:8080) (the exact URL will be shown in the console output).

---

## Additional Notes

- Ensure that you have Python (3.9+) and Node.js installed on your system (in my case i was using Python 3.12).
- The backend uses Flask and requires certain environment variables to be set. Refer to the `.env.example` file (if available) for the required variables.
- Ensure that necessary ports (5000 for backend, 8080 for frontend) are open and not being used by other applications.
