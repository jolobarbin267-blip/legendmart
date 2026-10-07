# LegendMart - MLBB Account Marketplace (FULL ENGLISH VERSION)

A Flask marketplace for buying/selling MLBB accounts, with **admin moderation** (Approve / Decline / Delete).

## Features
- Register/Login (passwords encrypted)
- Seller uploads account (photos, rank, skins, price) -> **Pending** status
- **Admin reviews**: Approve (goes live), Decline, or Delete
- Browse/Search/Filter (by rank, max price)
- Account detail with direct payment buttons (GCash/Maya/PayPal, copy-to-clipboard)
- Seller Dashboard (edit/delete own listings, see status)
- Admin Panel (pending count badge in navbar, stats, all users, all listings)
- Auto-created admin account
- Black gaming theme + typewriter animation + 3D tilt cards + hover buttons
- Responsive (mobile hamburger menu)
- Ready for GitHub + Render

## Admin Login (default)
- **Email:** `admin@legendmart.com`
- **Password:** `Admin123`

Change these in `app.py` (top): `ADMIN_EMAIL` and `ADMIN_PASSWORD`, or set env vars `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

## Run Locally
```
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## How the moderation flow works
1. Seller registers -> uploads account -> status = **Pending** (NOT visible to public)
2. Admin logs in -> Admin Panel -> sees Pending list -> clicks **Approve** / **Decline** / **Delete**
3. Approved listings appear on Home + Browse. Declined ones go back to seller (can edit & re-submit).

## Deploy to Render
1. Push to GitHub (files in .gitignore are excluded)
2. Render -> New Web Service -> connect repo
3. Build: `pip install -r requirements.txt` | Start: `gunicorn app:app`
4. Env vars: `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `DATABASE_URL` (create a free PostgreSQL DB on Render and paste its URL)
5. Deploy

> Note: SQLite and uploaded files don't persist on Render's free tier — use PostgreSQL + a disk or cloud storage (Cloudinary/S3) for production.

## Disclaimer
Selling MLBB accounts violates Moonton's Terms of Service. Use responsibly. Not affiliated with Moonton.
