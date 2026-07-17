# Hadi Zaatiti's website and CV

Personal site and CV of Hadi Zaatiti, Research Scientist at NYU Abu Dhabi, working on the modelling and simulation of dynamical systems across neuroscience, aerospace and autonomous transportation.

Live site: https://zaatiti.fr

## Structure

- Built with Jekyll. Profile details and page content live in `_config.yml`.
- `about.md` renders the About page (experience, education, skills, projects) from `_config.yml`.
- `_posts/` holds blog posts.
- `cv/` is the published CV: a web version at `/cv/` plus a downloadable PDF.
- `cv_src/` holds the CV source (Markdown plus a Typst template); the PDF and web CV are built from it.

## Building the CV (PDF and web)

The CV is generated from `cv_src/`:

    cd cv_src
    pip install pyyaml
    python build.py
    typst compile template.typ site/CV_Hadi_Zaatiti.pdf --root .

The GitHub Action in `.github/workflows/build-cv.yml` rebuilds and commits `cv/` automatically whenever `cv_src/` changes.

## Running the site locally

    docker compose -f docker-compose-dev.yml up --build

Then open http://localhost (served by nginx) or http://localhost:4000.

## Credits

Site scaffolding based on the open-source devlopr-jekyll theme (MIT), heavily customised.
