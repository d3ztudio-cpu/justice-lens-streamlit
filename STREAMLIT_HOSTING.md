# Streamlit Hosting (Justice Lens)

This project is designed to run as a Streamlit app (`justicelens.py`).

## 1) Local run

1. Create/activate a virtualenv
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.streamlit/secrets.toml` (do **not** commit it) with:

- `GROQ_API_KEY`
- `PINECONE_KEY`
- `FIREBASE_WEB_API_KEY`
- `firebase` service account JSON (for `firebase_admin`)

4. Run:

```bash
streamlit run justicelens.py
```

## 2) Free hosting on Streamlit Community Cloud

1. Push your repo to GitHub.
2. Go to Streamlit Community Cloud and create a new app.
3. Select your GitHub repo + branch.
4. Set **Main file path** to: `justicelens.py`
5. In the app’s **Secrets** settings, paste the same values you have in `.streamlit/secrets.toml`.
6. Deploy.

## Notes

- Never put API keys in your code or in GitHub.
- The app uses Pinecone + a HuggingFace embedding model; first boot can take time because it may download models.
