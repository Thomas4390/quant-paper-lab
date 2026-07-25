---
description: Scaffold a new paper folder (paper.yaml, build_data.py, figures.py, page.py, animate.py, post.md)
---

Scaffold a new paper in this repo. The argument is the folder name, in snake_case, usually
`author_year` or `author1_author2_year`: `$ARGUMENTS`

Load the `paper-post` skill first. It owns the workflow and the gates, this command only
creates files.

Steps:

1. Refuse and ask for one if `$ARGUMENTS` is empty or not a valid Python identifier. The
   folder has to be importable, so hyphens are not allowed here. Hyphens belong in the
   `slug` and `url_path` fields inside `paper.yaml`.
2. Create `papers/$ARGUMENTS/` with these files, copying the structure of
   `papers/jegadeesh_titman_1993/` and stripping it down to placeholders:
   - `paper.yaml` with every key present and `claims` left empty with a comment saying they
     must be written before the figures
   - `build_data.py` with the download, parse and write skeleton, pointing at `data/`
   - `figures.py` importing only `lab.theme`, no Streamlit, no file reads
   - `page.py` following the header, tiles, figures, expander, disclaimer order
   - `animate.py` with the `--preview` flag wired up
   - `post.md` with the section headings and the pre-flight checklist
3. Do not invent the paper's metadata. Ask for the title, authors, year, journal and DOI, or
   leave clearly marked placeholders. Never guess a DOI.
4. Report the licence question from step 1 of the skill back to the user before any data
   work: which source, and is it publishable in a public repo.

Nothing is registered anywhere else. Navigation, the home index and the manifest all read
from `papers/*/paper.yaml`.
