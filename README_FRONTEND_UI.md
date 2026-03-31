# Justice Lens Frontend/UI Walkthrough (Block by Block)

This document explains the **frontend and UI logic only** in `justicelens.py`. It is written so the team can quickly understand how each UI block works and what it renders.

File: `justicelens.py`

---

**1) Page config and app identity**
`st.set_page_config(...)` sets the page title, icon, layout, and sidebar behavior. This must be the first Streamlit call so Streamlit knows how to render the page chrome.  
References: `justicelens.py:46`

---

**2) Global theme + UI CSS**
A large `<style>` block defines the entire visual system:
`--jl-*` variables for colors, shadows, radius; global font; layout spacing; button/input styles; chat styles; cards; report UI; and mobile breakpoints.  
References: `justicelens.py:59`

Key UI effects inside the CSS block:
- App background, typography, and page padding
- Sidebar skin + “Connected” badge styling
- Removal of Streamlit’s default fullscreen and toolbar controls
- Button and input focus styling
- Hero cards (`.jl-hero`), feature tiles (`.jl-feature`), and report panels (`.jl-report`)
- Chat message sizing and chat input styling
- Mobile-only elements and drawer sidebar behavior (media queries)

---

**2a) Buttons**
Primary buttons (`.stButton`, `.stFormSubmitButton`, `.stDownloadButton`) are styled with the blue primary color, rounded corners, and hover lift/shadow effects for a premium feel.  
References: `justicelens.py:164`

---

**2b) Inputs**
Text inputs and textareas use dark backgrounds, soft borders, and blue focus rings to match the theme and improve accessibility.  
References: `justicelens.py:182`

---

**2c) Theme + Colors**
Theme tokens live in `:root` as `--jl-*` variables. These define the dark base (`--jl-bg`), card surfaces (`--jl-card`), text/muted text, primary blues, borders, and shadows.  
References: `justicelens.py:66`

---

**2d) Design System / Cards**
Reusable UI blocks are defined via `.jl-hero`, `.jl-card`, `.jl-feature`, and `.jl-report` styles. This creates consistent spacing, borders, and visual hierarchy across all pages.  
References: `justicelens.py:194`

---

**2e) Mobile Responsiveness**
Media queries at `max-width: 700px` adjust typography, padding, chat message sizing, and enable mobile-only elements.  
References: `justicelens.py:317`

---

**3) Copy-to-clipboard JS for report blocks**
This `<script>` listens for clicks/touches on `.jl-copy-btn` and copies the base64 payload to the clipboard. It provides a quick “Copied” feedback state for 1.2s.  
References: `justicelens.py:554`

---

**4) Mobile sidebar toggle UI shell**
This block injects the hamburger button and an overlay backdrop used on small screens.  
References: `justicelens.py:605`

---

**5) PWA meta + manifest**
Adds manifest and mobile web‑app meta tags to improve installability and status‑bar styling.  
References: `justicelens.py:616`

---

**6) Mobile drawer behavior (JS)**
Custom JS toggles a CSS class on the top‑level `body` so the sidebar becomes a slide‑in drawer on mobile. It also closes the drawer when the user taps outside or interacts with sidebar controls.  
References: `justicelens.py:625`

---

**7) Service worker registration (PWA)**
Registers `/static/service-worker.js` and caches the `beforeinstallprompt` event so the app can later prompt for installation.  
References: `justicelens.py:673`

---

**8) Loading splash UI**
When the backend initializes, a splash container renders a centered “JUSTICE LENS” card and a progress bar with staged labels. This is purely UI while the app connects.  
References: `justicelens.py:707`

---

**9) Report rendering UI helper**
`_render_report_html` converts a plain‑text AI report into a styled HTML report:
sections become labeled blocks, action steps become a numbered visual list, and everything is wrapped in `.jl-report` containers. This is the core UI formatter for legal reports shown in chat.  
References: `justicelens.py:1200`

---

**10) Sidebar UI (login + navigation + projects)**
`show_sidebar()` builds the entire sidebar layout:
- Logo at top
- Login/Create Account tabs (for unauthenticated users)
- “Guest User” button
- Public navigation (AI Assistant, About, Terms, Cyber Rules 2026)
- When logged in: “Connected” badge, nav radio, chat controls, and session termination  
References: `justicelens.py:1418`

Important UI elements inside the sidebar:
- Tabs for authentication form fields and buttons  
  References: `justicelens.py:1433`
- Guest login button  
  References: `justicelens.py:1478`
- Resource navigation via radio group  
  References: `justicelens.py:1504`
- “Clear chat”, “Chats” project list, and “Create” button  
  References: `justicelens.py:1536`
- “TERMINATE SESSION” button  
  References: `justicelens.py:1571`

---

**11) Public resource pages (logged‑out)**
When a user is not logged in and chooses About/Terms/Cyber Rules 2026 from the sidebar, the main area renders a hero header and a card with formatted content.  
References: `justicelens.py:1591`

---

**12) Logged‑out landing screen**
When logged out and on the main view:
- Center logo and hero card
- Mobile‑only LOGIN button that opens a mobile login area  
References: `justicelens.py:1679`

---

**13) Mobile login panel**
On small screens, a hidden login panel becomes visible. It contains tabs for Login/Create Account and a Guest button.  
References: `justicelens.py:1696`

---

**14) Feature tiles (optional UI block)**
There is a 3‑column “feature tile” section prepared but currently commented out. It demonstrates how to render “Always On”, “Grounded”, and “Tactical” tiles using `.jl-feature`.  
References: `justicelens.py:1867`

---

**15) Welcome card + quick action buttons**
The main chat area begins with a welcome card and four quick‑start buttons (UPI scam, account hacked, Section 66F, privacy violation). These buttons prefill the chat with example prompts.  
References: `justicelens.py:1923`

---

**16) Chat message rendering**
Each chat message uses Streamlit’s `st.chat_message`:
- User messages render as plain markdown
- Assistant messages render either as a structured report (`_render_report_html`) or as safe text
- A “Translate” link is added under assistant messages  
References: `justicelens.py:1959`

---

**17) Chat input + cooldown UI**
The chat input field is shown at the bottom:
- If a cooldown is active, the input is disabled and an info banner appears
- Otherwise, it accepts user input and triggers response handling  
References: `justicelens.py:1989`

---

**18) Page‑style content for logged‑in views**
When logged in, the app can render these content pages:
- Vision & Mission  
  References: `justicelens.py:2008`
- About  
  References: `justicelens.py:2028`
- Terms  
  References: `justicelens.py:2054`
- Cyber Rules 2026  
  References: `justicelens.py:2080`

Each of these uses `.jl-card` HTML blocks for clean typography and spacing.

---

**19) Admin Dashboard UI**
Admins see a dashboard with:
- Metric cards (total, active, banned, guest users)
- Chat retention settings (auto-delete after 15/30/60 days) + manual cleanup
- Per-user "Delete Chats" action and global "Delete ALL Chats" control (admin-only)
- Search + status filter controls
- CSV download button
- User directory list with Ban/Unban and Delete buttons  
References: `justicelens.py:2107`

---

## Quick mental model (frontend‑only)
- **CSS defines the visual system** (colors, cards, chat, mobile).  
- **JS adds interactivity** (copy, mobile sidebar drawer, service worker).  
- **Sidebar drives navigation** and login/guest access.  
 - **Main area renders cards and chat** based on login state and selected view.

If you want this exported to a `.docx`, tell me and I can generate it from this Markdown.

---

**20) Authentication method (UI + flow)**
The app uses Firebase Email/Password auth with two pieces:
- UI: Login/Create Account forms in the sidebar (and a mobile variant) collect email/password.  
  References: `justicelens.py:1433`, `justicelens.py:1708`
- Sign‑in: `authenticate()` calls Firebase Identity Toolkit REST API `accounts:signInWithPassword` using `FIREBASE_WEB_API_KEY`.  
  References: `justicelens.py:826`
- User profile: On success, the Firebase Admin SDK (`auth.get_user`) retrieves the user profile and stores a session user object.  
  References: `justicelens.py:833`
- Guest access: “Guest User” creates a temporary UID in session without a password.  
  References: `justicelens.py:1478`, `justicelens.py:1746`
- User sync: `sync_user()` writes the session user to Firestore with `last_active`.  
  References: `justicelens.py:837`

In UI terms: the login buttons only show/hide forms and set session state; the actual credentials are verified against Firebase, then the sidebar switches to the “connected” view.

---

**21) Hosting methods and procedure**
Hosting guidance is documented in `STREAMLIT_HOSTING.md`. Summary:
- Local run
  1. Create a virtualenv and install requirements.
  2. Add `.streamlit/secrets.toml` with `GROQ_API_KEY`, `PINECONE_KEY`, `FIREBASE_WEB_API_KEY`, and a `firebase` service account JSON.
  3. Run `streamlit run justicelens.py`.
- Streamlit Community Cloud
  1. Push the repo to GitHub.
  2. Create a new Streamlit app and set **Main file path** to `justicelens.py`.
  3. Paste the same secrets into the app’s Secrets config and deploy.

References: `STREAMLIT_HOSTING.md`
