#!/usr/bin/env python3
"""Cambium - project scaffolder (v3.1).

Usage:
    python3 tools/new_project.py "<project name>"

Creates projects/<slug>/ from templates/project/, adds the v3 lifecycle folders,
copies the root-level v3 templates in, and appends a row to projects/REGISTRY.md.
No external dependencies - stdlib only.
"""
import os, re, shutil, sys

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT     = os.path.dirname(SCRIPT_DIR)
TEMPLATE_DIR  = os.path.join(REPO_ROOT, "templates", "project")
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
PROJECTS_DIR  = os.path.join(REPO_ROOT, "projects")
REGISTRY      = os.path.join(PROJECTS_DIR, "REGISTRY.md")

V3_DIRS  = ["agent_outputs", "synthesis", "results", "conduct", "compliance"]
V3_FILES = ["USER_PROFILE.md", "IDEA_INBOX.md", "COLLAB_WORKSPACE.md",
            "POST_AWARD_PLAN.md", "REPRODUCIBILITY_CHECKLIST.md", "DATA_MANAGEMENT_PLAN.md"]

def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def next_id(registry_path):
    if not os.path.exists(registry_path):
        return "001"
    count = 0
    with open(registry_path, encoding="utf-8") as f:
        for line in f:
            st = line.strip()
            if st.startswith("|"):
                cells = [c.strip() for c in st.split("|") if c.strip()]
                if cells and cells[0].isdigit():
                    count += 1
    return str(count + 1).zfill(3)

def ensure_registry(registry_path):
    if os.path.exists(registry_path):
        return
    header = ("# Projects Registry\n"
              "*Status: Intake | Ideation | Proposal | Submitted | Approved | Development | Reporting | Closed.*\n\n"
              "| ID | Project | Field | Status | Phase / next gate | Folder |\n"
              "|---|---|---|---|---|---|\n")
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(header)
    print("[new_project] Created %s" % registry_path)

def append_registry_row(registry_path, pid, name, folder):
    row = "| %s | %s | | Intake | fill USER_PROFILE then `read rfp <file>` | %s/ |\n" % (pid, name, folder)
    with open(registry_path, "a", encoding="utf-8") as f:
        f.write(row)

def copy_template(src, dst, project_name):
    TEXT_EXTS = {".md", ".txt", ".yml", ".yaml", ".csv", ".json", ".py"}
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(dest_dir, exist_ok=True)
        for fname in files:
            sf = os.path.join(root, fname); df = os.path.join(dest_dir, fname)
            if os.path.splitext(fname)[1].lower() in TEXT_EXTS:
                with open(sf, encoding="utf-8", errors="replace") as f:
                    c = f.read().replace("<Project Name>", project_name)
                with open(df, "w", encoding="utf-8") as f:
                    f.write(c)
            else:
                shutil.copy2(sf, df)

def add_v3_scaffold(dst, project_name):
    for d in V3_DIRS:
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    for fname in V3_FILES:
        src = os.path.join(TEMPLATES_DIR, fname)
        if not os.path.exists(src):
            continue
        dest = os.path.join(dst, fname)
        if os.path.exists(dest):
            continue
        with open(src, encoding="utf-8", errors="replace") as f:
            c = f.read().replace("<Project Name>", project_name).replace("<Your Name>", project_name)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(c)

def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('Usage: python3 tools/new_project.py "<project name>"'); return 1
    project_name = sys.argv[1].strip()
    slug = slugify(project_name)
    if not slug:
        print("[new_project] ERROR: empty slug - use letters/numbers."); return 1
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    ensure_registry(REGISTRY)
    pid = next_id(REGISTRY)
    folder = "%s-%s" % (pid, slug)
    dst = os.path.join(PROJECTS_DIR, folder)
    if os.path.exists(dst):
        print("[new_project] Folder already exists: %s" % dst); return 1
    if not os.path.isdir(TEMPLATE_DIR):
        print("[new_project] ERROR: template not found at %s" % TEMPLATE_DIR); return 1
    copy_template(TEMPLATE_DIR, dst, project_name)
    add_v3_scaffold(dst, project_name)
    append_registry_row(REGISTRY, pid, project_name, folder)
    print("\n[new_project] Project created: %s" % dst)
    print("[new_project] Registry row added: ID=%s name='%s'" % (pid, project_name))
    print("\nNext steps:")
    print("  0. Fill USER_PROFILE.md so Cambium knows your expertise (Gate G0).")
    print("  1. Place your RFP in %s/ (or say `rfp in <file>`)." % dst)
    print("  2. Say `read rfp <filename>` to start RFP intake (produces 00_rfp_brief.md).")
    print("  3. Approve or decline at Gate G1 (Director decision).")
    print("  4. See GETTING_STARTED.md and LIFECYCLE_V3.md for the full path.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
