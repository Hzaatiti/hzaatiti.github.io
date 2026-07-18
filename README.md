# Hadi Zaatiti's website and CV

A lightweight static site: plain HTML, CSS and a little JavaScript, no build step or framework. Served directly by GitHub Pages.

## Pages
- `index.html` is the home page (hero, about, skills, contact).
- `projects.html` documents projects and experience (Geomstats, NeuroWaves, and earlier roles).
- `cv/` is the CV: a web version at `/cv/` plus a downloadable PDF.
- `assets/` holds the stylesheet, script and images.

## The CV (PDF and web)
The CV is generated from `cv_src/` with a Typst template:

    cd cv_src
    pip install pyyaml
    python build.py
    typst compile template.typ site/CV_Hadi_Zaatiti.pdf --root .

The GitHub Action in `.github/workflows/build-cv.yml` rebuilds and commits `/cv/` automatically whenever `cv_src/` changes.

## Local preview
No build needed. Either open `index.html` in a browser, or serve the folder:

    python -m http.server 8000

then visit http://localhost:8000
