````markdown
# Calorie Analyzer – Plate Analysis App

A web application that analyzes food photos and **estimates calories**, and (optionally) **carbs & sugars** using:

- OpenAI Vision API for food recognition
- A custom `CALORIE_DB` with kcal / carbs / sugar per 100 g
- A small Flask backend + HTML/JS frontend

> All values are **approximate** and are not medical advice.

---

## Features

- Upload a photo of your meal and get a **list of detected foods**.
- Adjust products and grams manually.
- See **total calories** for the plate.
- Turn on **Glucose Balance+** to also see:
  - carbs per product and total,
  - sugars per product and total.
- Interface languages: **RU / UA / EN** (switcher in the top right).
- If the model can’t confidently detect items, you can always select products manually from the list.

---

## Installation (local)

### 1. Clone the repository

```bash
git clone <YOUR_REPO_URL>
cd <project-folder>
````

### 2. (Optional) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS / Linux
# .\venv\Scripts\activate  # Windows (PowerShell)
```

### 3. Install dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes Flask, OpenAI SDK and other needed packages.

### 4. Set up OpenAI API key

Get your API key in the OpenAI dashboard and export it as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

On Windows (PowerShell):

```powershell
setx OPENAI_API_KEY "your-api-key-here"
```

> The app **never** expects the key to be hardcoded in the source – only via environment variable.

### 5. Run the app locally

```bash
python3 app.py
```

By default Flask runs on:

```text
http://127.0.0.1:5002
```

Open this URL in your browser and test the app.

---

## Usage

1. Open the main page in your browser.
2. Upload a plate photo.
3. The app calls OpenAI Vision and gets a list of generic English food names.
4. These names are mapped to items from `CALORIE_DB`.
5. You can:

   * change products,
   * adjust grams,
   * add new items from the list.
6. The app calculates for each item and for the whole plate:

   * calories (always),
   * carbs & sugars (when **Glucose Balance+** is enabled).

Glucose Balance+ mode:

* when OFF – you see only calories;
* when ON – additional columns for carbs and sugars appear for each product + totals.

---

## Environment Variables

Required:

* `OPENAI_API_KEY` – your OpenAI API key.

Optional:

* `FLASK_ENV` – `development` or `production` (for local debugging).

For more detailed notes on the key and setup you can also check `OPENAI_SETUP.md` (if present in the repo).

---

## Project Structure

Typical structure of the project:

```text
.
├── app.py               # Flask backend (entrypoint)
├── CALORIE_DB           # Python file with CALORIE_DB dict (kcal / carbs / sugar per 100 g)
├── templates/
│   └── index.html       # Frontend UI (HTML + JS, i18n + Glucose Balance+)
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── OPENAI_SETUP.md      # Extra notes on OpenAI setup (optional)
└── uploads/             # Temporary upload directory (auto-created, not committed)
```

The `uploads/` directory is created at runtime for temporary storage of uploaded images; it should **not** be committed to the repository.

---

## Deployment to Vercel

You can deploy this Flask app to Vercel as a serverless function.

### 1. Prepare the repository

Make sure the repository contains at least:

* `app.py`
* `CALORIE_DB`
* `templates/index.html`
* `requirements.txt`
* `README.md`
* `.gitignore`
* optionally: `OPENAI_SETUP.md`, `static/` if you use separate CSS/JS

Your `requirements.txt` should pin working versions. For example:

```txt
Flask==3.0.0
Pillow==10.1.0
Werkzeug==3.0.1
requests==2.31.0
openai>=1.55.3,<2.0.0
httpx>=0.27.0,<0.28.0
```

Commit and push everything to GitLab (or another git provider).

### 2. Import project in Vercel

1. Go to Vercel and click **Add New Project**.
2. Import your Git repository (GitLab/GitHub/etc.).
3. Vercel will automatically detect a Python/Flask app:

   * **Build Command**: leave empty.
   * **Output Directory**: leave empty.
4. Ensure that `app.py` is in the repo root and contains:

   ```python
   app = Flask(__name__)
   ```

   Vercel uses this `app` object as the entrypoint for the serverless function.

### 3. Set environment variables on Vercel

In your Vercel project settings:

1. Open **Settings → Environment Variables**.

2. Add:

   * `OPENAI_API_KEY = your-api-key-here`

3. Save the changes.

### 4. Deploy

1. Click **Deploy** (or push to the main branch and let Vercel auto-deploy).
2. The first build may take a few minutes while Vercel installs dependencies from `requirements.txt` and builds the function.
3. After a successful deployment you will get a URL like:

   ```text
   https://your-project-name.vercel.app
   ```

Open that URL to use the app online.

---

## Notes & Limitations

* Calorie, carbs, and sugar values are based on averaged data from `CALORIE_DB` and are **approximate**.
* The app is **not** a medical device and does not replace professional medical advice or a personal diabetes management plan.
* Recognition quality depends on the quality and clarity of the photo.
* If recognition is uncertain, the user can always select and adjust products manually.

---

If you extend the app (user accounts, history, more metrics, etc.), keep this README updated so others can still run and deploy it easily.
