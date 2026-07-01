# Presentation Combiner — Streamlit app

A web page where your boss uploads a **client Orion report** + the
**market-content presentation**, clicks a button, and downloads the finished,
page-numbered PDF. Deploys to a **permanent URL** on Streamlit Community Cloud
(free) that keeps working after you're gone.

---

## ⭐ Deploy it so it lives past your internship

The app runs on **Streamlit Community Cloud**, which serves it from a GitHub
repo. The app stays up as long as that repo and the Streamlit account exist — so
the one thing that matters is **whose accounts own it.**

> **Do this:** put the code in a **firm-owned GitHub account/organization** (not
> your personal one) and deploy from a Streamlit account the firm controls
> (e.g. a shared `ops@firm.com`). That way nothing breaks when your personal
> accounts are closed. If you must use your personal GitHub now, **transfer the
> repo to the firm before you leave** (GitHub: repo *Settings ▸ Transfer*).

### Step-by-step

1. **Put this folder in a GitHub repo.**
   - Create a repo (ideally under the firm's GitHub org).
   - Upload everything in this `Presentation Combiner (Streamlit)` folder to the
     repo root: `streamlit_app.py`, `combine.py`, `requirements.txt`,
     `packages.txt`, and the `.streamlit/` folder.
   - Do **not** upload `secrets.toml` (it's gitignored on purpose).

2. **Deploy on Streamlit Community Cloud.**
   - Go to <https://share.streamlit.io> and sign in with the GitHub account.
   - **Create app ▸ Deploy a public app from GitHub.**
   - Pick the repo, branch `main`, main file `streamlit_app.py`.
   - Click **Deploy**. First build takes a few minutes (it installs LibreOffice).

3. **Set the password.**
   - In the app's **⋮ ▸ Settings ▸ Secrets**, paste:
     ```toml
     APP_PASSWORD = "a-strong-password-you-choose"
     ```
   - Save. The app restarts with the login enabled.

4. **Share the URL.** You'll get something like
   `https://sam-presentation-combiner.streamlit.app`. Give your boss that link
   and the password. Done — works on any computer, no install.

> ⚠️ **Client data note:** these reports contain client account numbers/balances,
> and this is a public cloud host. Clear it with whoever owns compliance first.
> The app is password-protected and stores nothing, but the firm should sign off
> on client PDFs passing through Streamlit's servers. (If they'd rather keep data
> in-house, the `Presentation Combiner Web` folder has a Docker version for an
> internal server, and `Presentation Combiner` has an offline desktop version.)

---

## How your boss uses it

1. Open the link, enter the password.
2. Upload the **Orion report (PDF)** and the **market content (PowerPoint or PDF)**.
3. Click **Combine into one PDF** → download the finished file.

That's the whole thing.

---

## What it produces

Same as the old manual Adobe process, verified page-for-page against the sample:

1. First **3 pages** of the Orion report (title + 2 content pages).
2. All market-content slides after it.
3. Removes leftover numbers (Orion's "Page X of 14"; the deck's 3, 5, 6, 9, 12…).
4. Clean numbers bottom-right: cover blank, then **1, 2, 3, …** (Arial, gray).

The "Keep the first N pages" box (default 3) covers the rare case a report needs
a different number of lead pages.

---

## Run it locally first (optional, to try before deploying)

```bash
cd "Presentation Combiner (Streamlit)"
pip3 install -r requirements.txt
APP_PASSWORD=test123 python3 -m streamlit run streamlit_app.py
# opens http://localhost:8501  (password: test123)
```

Leave `APP_PASSWORD` unset to skip the login while testing.
(Local PPTX conversion uses the LibreOffice already installed on your Mac.)

---

## Files

| File | Purpose |
|------|---------|
| `streamlit_app.py` | The web app (upload, password, download). |
| `combine.py` | Engine: merge + remove old numbers + renumber. |
| `requirements.txt` | Python packages (Streamlit installs these). |
| `packages.txt` | System packages — installs **LibreOffice** on Streamlit Cloud so `.pptx` uploads convert. |
| `.streamlit/config.toml` | Theme + upload size limit. |
| `.streamlit/secrets.toml.example` | Template for the password secret. |
