# Installing Cambium

Cambium installs **directly from this GitHub repo** — no download, no copying files. Pick your app.
All steps are tested; the **Troubleshooting** section at the bottom lists the real Claude-app quirks people hit.

> Plugins require a **paid Claude plan** (Pro, Max, Team, or Enterprise).

---

## 1. Claude Desktop / Cowork (no terminal) — best for non-developers

### A. Easiest, no menu-hunting — `/create-cowork-plugin`  ⭐ start here
1. In a Cowork chat, type: **`/create-cowork-plugin`**
2. Paste the repo URL: `https://github.com/IFC-UIDAHO/Cambium_AI`
3. Choose **Repackage for Cowork → Full working bundle**.
4. Press **Install** (or **Save plugin**) on the card it produces.

This **bypasses the plugins menu entirely** — which matters, because the "Add marketplace" button is
unreliable in current builds (see Troubleshooting). It’s a **snapshot**; for updates use **B** or re-run this.

### B. Add the repo as a marketplace (updatable)
1. Open the **Cowork** tab, then **Customize → Plugins**.
2. Under **Personal plugins**, click **“+” → Add marketplace → Add from a repository**.
3. Paste: `https://github.com/IFC-UIDAHO/Cambium_AI.git`
4. Click **Browse plugins → Install** `cambium-institute`. Reload plugins if prompted.

Installs as **`cambium-institute@Cambium_AI`** (repo-tracked → you can **Sync/Update** later — see §3).

> **If the “+” only opens Anthropic’s catalog (no “Add marketplace”):** that’s a known build quirk — do **A**
> once first; the Personal-plugins / Add-marketplace flow then becomes available. (Docs say it should be there
> from the start; in practice it isn’t always.)

---

## 2. Claude Code (terminal)

Run the two commands on **separate lines** (type one, Enter, wait, then the next):

```
/plugin marketplace add https://github.com/IFC-UIDAHO/Cambium_AI.git
```
```
/plugin install cambium-institute
```
- At the scope prompt pick **“Install for you (user scope)”**, then run **`/reload-plugins`**.

**Gotchas (all real):**
- Use the **full HTTPS `.git` URL**, not `owner/repo` — the short form can resolve to **SSH** and fail
  (*“Host key verification failed”*).
- **Don’t paste both commands on one line** (*“Malformed input to a URL function”*).
- Launched from a protected dir (e.g. `C:\WINDOWS\system32`)? The *“in this repo only”* scope fails with
  **EPERM** — **user scope** avoids it.

---

## 3. Updating

- **Repo-marketplace installs (1B / Claude Code):** click **Update** (plugin card) or **Sync** (marketplace).
  It compares your version to GitHub and pulls anything new; **Update greys out when you’re current.**
- **Snapshot install (1A):** re-run `/create-cowork-plugin`.

**“Fully automatic daily updates” isn’t available here.** Hands-off sync-on-push is a **Team/Enterprise**
feature requiring a **private** repo; Cambium is public, so on personal plans updates are a **one-click Sync**.
Tip: **Watch** the GitHub repo for release notifications so you know when to sync.

---

## 4. Troubleshooting — known Claude-app quirks (not Cambium bugs)

| Symptom | What’s going on / fix |
|---|---|
| The **“+”** under Personal plugins only opens Anthropic’s curated **Directory** — no “Add marketplace.” | Build quirk. Use **§1A `/create-cowork-plugin`** once; the Add-marketplace flow then appears. ([feature still rolling out](https://github.com/anthropics/claude-code/issues/66184)) |
| Plugins **disappear after restarting** the desktop app. | Known bug — the marketplace persists but the plugin must be **re-installed**. ([#40600](https://github.com/anthropics/claude-code/issues/40600)) |
| Cowork plugin **marketplace is empty** (Windows). | Known Windows bug. Use **§1A** or Claude Code. ([#28853](https://github.com/anthropics/claude-code/issues/28853)) |
| *“Marketplace sync failed”* / *“Found 2 plugin.json.”* | The first is a private-repo issue (Cambium is public, so use the full HTTPS URL); the second was a Cambium packaging bug — **fixed** (one manifest at root). |
| `agents: Invalid input` on install. | Old packaging bug — **fixed** (agents auto-discovered from `agents/`). Re-sync the marketplace and reinstall. |

---

## 5. After it’s installed — just use it

No commands. Talk in plain English, one sentence at a time:
*“Here’s a grant call — should we go for it?”* · *“Give me three research ideas and rank them.”* · *“Draft the proposal.”*
Cambium routes the work to its councils and **stops at a gate** for your **approve / revise / reject**.
New here? Open **[`USE_CAMBIUM.md`](USE_CAMBIUM.md)**.

**Connectors it likes:** web search, code execution, a citation resolver. Connect these for full power;
Cambium tells you if a step needs one you haven’t set up.
