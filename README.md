# Hadi Zaatiti's website and CV

A lightweight static site: plain HTML, CSS and a little JavaScript, no build step or framework. Served directly by GitHub Pages.

## Pages
- `index.html` is the home page (introduction, current work, earlier roles, tools, contact).
- `projects.html` documents the projects (epilepsy with Cleveland Clinic Abu Dhabi, NeuroWaves, Geomstats) and earlier roles.
- `cv/` is the CV: a web version at `/cv/` plus a downloadable PDF.
- `assets/` holds the stylesheet, script, images and fonts. The Libertinus fonts are served from `assets/fonts/`, so the site makes no third-party requests.

## The CV (PDF and web)
The CV is generated from `cv_src/cv.md`, the single source for both the PDF (Typst template) and the web page at `/cv/`. Sections are Experience, Projects, Education, Skills and Languages, and `[text](https://...)` links work in any paragraph or bullet.

    cd cv_src
    pip install pyyaml
    python build.py
    typst compile template.typ site/CV_Hadi_Zaatiti.pdf --root .

The GitHub Action in `.github/workflows/build-cv.yml` rebuilds and commits `/cv/` automatically whenever `cv_src/` changes.

## Local preview
No build needed. Either open `index.html` in a browser, or serve the folder:

    python -m http.server 8000

then visit http://localhost:8000
