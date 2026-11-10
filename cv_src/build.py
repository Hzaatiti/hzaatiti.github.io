#!/usr/bin/env python3
"""
Convert cv.md (the source of truth) into resume.json (consumed by template.typ).

You edit cv.md. This script regenerates resume.json. The GitHub Action runs it
automatically before compiling the PDF; locally, run `python build.py`.

cv.md conventions
-----------------
- YAML frontmatter holds header/contact fields.
- A blockquote (> ...) right after the frontmatter is the summary.
- `## Section` starts a section: Experience, Projects, Education, Skills,
  Languages.
- Experience/Education entries:  `### Title @ Organization`
      *start to end* · optional note        (dates line, ranges use "to";
                                             "present"/"now" => ongoing)
      one or more paragraph lines           -> entry summary
      - bullet lines                        -> highlights
  For education, the Title is split on the first comma into degree, field.
- Projects entries:  `### Name @ Partner or context`, an optional dates line,
  then a short paragraph.
- Bold lead-in: text before the first ": " in a bullet is rendered bold, so
  writing `- **Label:** text` looks good both on GitHub and in the PDF.
- Links: `[text](https://...)` works in summaries, bullets and project
  paragraphs, and stays clickable in both the PDF and the web CV.
"""

import json
import re
import sys
import pathlib

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("cv.md")
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("resume.json")

ONGOING = {"present", "now", "current", "ongoing", ""}


def strip_inline(s: str) -> str:
    """Remove markdown emphasis markers, keeping the text content."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)     # **bold**
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"\1", s)  # *italic*
    s = re.sub(r"`(.+?)`", r"\1", s)            # `code`
    return s.strip()


def split_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        sys.exit("cv.md must start with a YAML frontmatter block delimited by ---")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def parse_dateline(line: str):
    """`*2024-01 to present* · Full-time` -> ('2024-01', '', 'Full-time')."""
    m = re.match(r"\*(.+?)\*(?:\s*·\s*(.+))?$", line.strip())
    if not m:
        return None
    span, note = m.group(1), (m.group(2) or "").strip()
    # Split on " to " or a whitespace-surrounded dash (the range separator),
    # so hyphens inside ISO dates like "2024-01" are preserved.
    parts = re.split(r"\s+(?:to|-)\s+", span.strip(), maxsplit=1)
    start = parts[0].strip()
    end = parts[1].strip() if len(parts) > 1 else ""
    if end.lower() in ONGOING:
        end = ""
    return start, end, note


def parse_entries(lines, is_education, is_project=False):
    entries = []
    cur = None
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("### "):
            if cur:
                entries.append(cur)
            title, _, org = line[4:].partition("@")
            cur = {"_title": title.strip(), "org": org.strip(),
                   "start": "", "end": "", "note": "", "logo": "",
                   "summary": [], "highlights": []}
        elif cur is None:
            continue
        elif line.strip().startswith("<!--"):
            m = re.search(r"logo:\s*(.+?)\s*-->", line)
            if m:
                cur["logo"] = m.group(1).strip()
        elif line.strip().startswith("*") and cur["start"] == "" and not cur["highlights"]:
            dl = parse_dateline(line)
            if dl:
                cur["start"], cur["end"], cur["note"] = dl
        elif line.strip().startswith("- "):
            cur["highlights"].append(strip_inline(line.strip()[2:]))
        elif line.strip():
            cur["summary"].append(strip_inline(line.strip()))
    if cur:
        entries.append(cur)

    out = []
    for e in entries:
        summary = " ".join(e["summary"]).strip()
        if is_project:
            out.append({
                "name": e["_title"],
                "entity": e["org"],
                "startDate": e["start"],
                "endDate": e["end"],
                "dated": bool(e["start"]),
                "logo": e["logo"],
                "summary": summary,
                "highlights": e["highlights"],
            })
        elif is_education:
            degree, _, field = e["_title"].partition(",")
            out.append({
                "studyType": degree.strip(),
                "area": field.strip(),
                "institution": e["org"],
                "note": summary,           # thesis / description line
                "startDate": e["start"],
                "endDate": e["end"],
                "logo": e["logo"],
            })
        else:
            out.append({
                "position": e["_title"],
                "name": e["org"],
                "note": e["note"],
                "startDate": e["start"],
                "endDate": e["end"],
                "logo": e["logo"],
                "summary": summary,
                "highlights": e["highlights"],
            })
    return out


def parse_skills(lines):
    skills = []
    for line in lines:
        m = re.match(r"-\s*(.+?):\s*(.+)$", strip_inline(line.strip()))
        if m:
            skills.append({
                "name": m.group(1).strip(),
                "keywords": [k.strip() for k in m.group(2).split(",") if k.strip()],
            })
    return skills


def parse_languages(lines):
    text = " ".join(l.strip() for l in lines if l.strip())
    langs = []
    for chunk in re.split(r"\s*·\s*|\s*,\s*", text):
        m = re.match(r"(.+?)\s*\((.+?)\)", chunk.strip())
        if m:
            langs.append({"language": m.group(1).strip(), "fluency": m.group(2).strip()})
    return langs


def main():
    text = SRC.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    # Summary = first blockquote in the body.
    summary = ""
    qm = re.search(r"^>\s*(.+)$", body, re.M)
    if qm:
        summary = strip_inline(qm.group(1).strip())

    # Location "City, Country" -> {city, countryName}
    location = {}
    if fm.get("location"):
        city, _, country = str(fm["location"]).rpartition(",")
        if city:
            location = {"city": city.strip(), "countryName": country.strip()}
        else:
            location = {"city": country.strip()}

    profiles = []
    if fm.get("website"):
        profiles.append({"network": "Website", "url": fm["website"]})
    if fm.get("scholar"):
        profiles.append({"network": "Google Scholar", "url": fm["scholar"]})

    basics = {
        "name": fm.get("name", ""),
        "label": fm.get("label", ""),
        "affiliation": fm.get("affiliation", ""),
        "email": fm.get("email", ""),
        "phone": str(fm.get("phone", "")),
        "url": fm.get("website", ""),
        "citizenship": fm.get("citizenship", ""),
        "age": str(fm.get("age", "")),
        "caption": fm.get("caption", ""),
        "photo": fm.get("photo", ""),
        "summary": summary,
        "location": location,
        "profiles": profiles,
    }

    # Split body into `## Section` blocks.
    sections = {}
    cur_name, cur_lines = None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if cur_name:
                sections[cur_name] = cur_lines
            cur_name, cur_lines = line[3:].strip().lower(), []
        elif cur_name:
            cur_lines.append(line)
    if cur_name:
        sections[cur_name] = cur_lines

    resume = {
        "basics": basics,
        "work": parse_entries(sections.get("experience", []), is_education=False),
        "projects": parse_entries(sections.get("projects", []), is_education=False,
                                  is_project=True),
        "education": parse_entries(sections.get("education", []), is_education=True),
        "skills": parse_skills(sections.get("skills", [])),
        "languages": parse_languages(sections.get("languages", [])),
    }

    OUT.write_text(json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}: {len(resume['work'])} roles, {len(resume['projects'])} projects, "
          f"{len(resume['education'])} degrees, {len(resume['skills'])} skill groups, "
          f"{len(resume['languages'])} languages.")

    # ---- Render the web CV: a real, clickable HTML page from the same data.
    tpl = pathlib.Path("site/index.template.html")
    if tpl.exists():
        render_site(resume, fm, tpl)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def inline_html(s):
    """Escape text, then turn [text](url) into a real link."""
    return LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', esc(s))


def fmt_date_html(d):
    if not d:
        return "present"
    parts = str(d).split("-")
    months = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May",
              "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct",
              "11": "Nov", "12": "Dec"}
    if len(parts) >= 2:
        return f"{months.get(parts[1], '')} {parts[0]}"
    return parts[0]


def daterange_html(a, b):
    return f"{fmt_date_html(a)} to {fmt_date_html(b)}"


def highlight_html(s):
    if ": " in s:
        lead, rest = s.split(": ", 1)
        if "](" not in lead:
            return f"<strong>{esc(lead)}:</strong> {inline_html(rest)}"
    return inline_html(s)


def logo_html(path, name=""):
    if not path:
        return ""
    return f'<img class="logo" src="{esc(path)}" alt="{esc(name)}">'


def row(note, text, cls="row"):
    """One line of the page grid: a margin note on the left, the text on the right."""
    return (f'<div class="{cls}">\n        <div class="note">{note}</div>\n'
            f'        <div class="text">{text}</div>\n      </div>')


def render_site(resume, fm, tpl):
    import shutil
    b = resume["basics"]

    # Contact lines
    contact = []
    if b.get("email"):
        contact.append(f'<a href="mailto:{esc(b["email"])}">{esc(b["email"])}</a>')
    for ph in [p.strip() for p in str(b.get("phone", "")).split("·") if p.strip()]:
        contact.append(esc(ph))
    loc = b.get("location", {})
    locstr = ", ".join(x for x in [loc.get("city", ""), loc.get("countryName", "")] if x)
    if locstr:
        contact.append(esc(locstr))
    if b.get("citizenship"):
        contact.append(esc(b["citizenship"]))
    contact_html = "".join(f"<li>{c}</li>" for c in contact)

    photo_html = ""
    if b.get("photo"):
        photo_html = f'<img src="{esc(b["photo"])}" alt="Portrait of {esc(b["name"])}">'

    role_html = "<br>".join(esc(p.strip()) for p in str(b.get("label", "")).split("·"))

    # Experience
    exp = []
    for j in resume["work"]:
        kind = f'<br>{esc(j["note"])}' if j.get("note") else ""
        note = (f'<span class="years">{daterange_html(j.get("startDate",""), j.get("endDate",""))}'
                f'{kind}</span>{logo_html(j.get("logo",""), j["name"])}')
        summary = f'<p class="sum">{inline_html(j["summary"])}</p>' if j.get("summary") else ""
        bullets = ""
        if j.get("highlights"):
            items = "".join(f"<li>{highlight_html(h)}</li>" for h in j["highlights"])
            bullets = f'<ul class="dots">{items}</ul>'
        exp.append(row(note, f'<h3>{esc(j["position"])}</h3><p class="where">{esc(j["name"])}</p>'
                             f'{summary}{bullets}', "row entry"))

    # Projects
    proj = []
    for p in resume.get("projects", []):
        dates = daterange_html(p["startDate"], p["endDate"]) if p.get("dated") else ""
        note = "<br>".join(x for x in [esc(p.get("entity", "")),
                                       f'<span class="years">{dates}</span>' if dates else ""] if x)
        summary = f'<p class="sum">{inline_html(p["summary"])}</p>' if p.get("summary") else ""
        bullets = ""
        if p.get("highlights"):
            items = "".join(f"<li>{highlight_html(h)}</li>" for h in p["highlights"])
            bullets = f'<ul class="dots">{items}</ul>'
        proj.append(row(note, f'<h3>{esc(p["name"])}</h3>{summary}{bullets}', "row entry"))

    # Education
    edu = []
    for e in resume["education"]:
        area = f', {esc(e["area"])}' if e.get("area") else ""
        thesis = f'<p class="thesis">{esc(e["note"])}</p>' if e.get("note") else ""
        note = (f'<span class="years">{daterange_html(e.get("startDate",""), e.get("endDate",""))}</span>'
                f'{logo_html(e.get("logo",""), e["institution"])}')
        edu.append(row(note, f'<h3>{esc(e["studyType"])}{area}</h3>'
                             f'<p class="where">{esc(e["institution"])}</p>{thesis}', "row entry"))

    # Skills
    skills = []
    for s in resume["skills"]:
        kw = ", ".join(esc(k) for k in s.get("keywords", []))
        skills.append(row(esc(s["name"]), f"<p>{kw}</p>"))

    langs = ", ".join(f'{esc(l["language"])} ({esc(l["fluency"]).lower()})'
                      for l in resume["languages"])

    pubs = ""
    scholar = [p for p in b.get("profiles", []) if p.get("network") == "Google Scholar"]
    if scholar:
        pubs = (f'The full, current list is on '
                f'<a href="{esc(scholar[0]["url"])}">Google Scholar</a>.')

    pdf_name = "CV_" + re.sub(r"\s+", "_", b["name"].strip()) + ".pdf"

    html = (tpl.read_text(encoding="utf-8")
            .replace("{{NAME}}", esc(b["name"]))
            .replace("{{ROLE_PLAIN}}", esc(str(b.get("label", "")).replace(" · ", ", ")))
            .replace("{{ROLE}}", role_html)
            .replace("{{PHOTO}}", photo_html)
            .replace("{{CONTACT}}", contact_html)
            .replace("{{SUMMARY}}", esc(b.get("summary", "")))
            .replace("{{EXPERIENCE}}", "\n      ".join(exp))
            .replace("{{PROJECTS}}", "\n      ".join(proj))
            .replace("{{EDUCATION}}", "\n      ".join(edu))
            .replace("{{SKILLS}}", "\n      ".join(skills))
            .replace("{{LANGUAGES}}", langs)
            .replace("{{PUBLICATIONS}}", pubs)
            .replace("{{PDF_NAME}}", pdf_name))
    pathlib.Path("site/index.html").write_text(html, encoding="utf-8")

    # Copy images into the site so the web page and PDF share one source.
    src_imgs = pathlib.Path("images")
    if src_imgs.exists():
        dst = pathlib.Path("site/images")
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src_imgs, dst)

    # Tell the CI what to name the compiled PDF.
    pathlib.Path("site/pdfname.txt").write_text(pdf_name, encoding="utf-8")
    print(f"Wrote site/index.html and copied images; PDF name: {pdf_name}")


if __name__ == "__main__":
    main()
