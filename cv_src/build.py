#!/usr/bin/env python3
"""
Convert cv.md (the source of truth) into resume.json (consumed by template.typ).

You edit cv.md. This script regenerates resume.json. The GitHub Action runs it
automatically before compiling the PDF; locally, run `python build.py`.

cv.md conventions
-----------------
- YAML frontmatter holds header/contact fields.
- A blockquote (> ...) right after the frontmatter is the summary.
- `## Section` starts a section: Experience, Education, Skills, Languages.
- Experience/Education entries:  `### Title @ Organization`
      *start – end* · optional note        (dates line, en dash between them;
                                             "present"/"now" => ongoing)
      one or more paragraph lines           -> entry summary
      - bullet lines                        -> highlights
  For education, the Title is split on the first comma into degree, field.
- Bold lead-in: text before the first ": " in a bullet is rendered bold, so
  writing `- **Label:** text` looks good both on GitHub and in the PDF.
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
    """`*2024-01 – present* · Full-time` -> ('2024-01', '', 'Full-time')."""
    m = re.match(r"\*(.+?)\*(?:\s*·\s*(.+))?$", line.strip())
    if not m:
        return None
    span, note = m.group(1), (m.group(2) or "").strip()
    # Split on " to " or a whitespace-surrounded dash (the range separator),
    # so hyphens inside ISO dates like "2024-01" are preserved.
    parts = re.split(r"\s+(?:to|[–—-])\s+", span.strip(), maxsplit=1)
    start = parts[0].strip()
    end = parts[1].strip() if len(parts) > 1 else ""
    if end.lower() in ONGOING:
        end = ""
    return start, end, note


def parse_entries(lines, is_education):
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
        if is_education:
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
        "education": parse_entries(sections.get("education", []), is_education=True),
        "skills": parse_skills(sections.get("skills", [])),
        "languages": parse_languages(sections.get("languages", [])),
    }

    OUT.write_text(json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}  —  {len(resume['work'])} roles, "
          f"{len(resume['education'])} degrees, {len(resume['skills'])} skill groups, "
          f"{len(resume['languages'])} languages.")

    # ---- Render the web CV: a real, clickable HTML page from the same data.
    tpl = pathlib.Path("site/index.template.html")
    if tpl.exists():
        render_site(resume, fm, tpl)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def fmt_date_html(d):
    if not d:
        return "Present"
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
        return f"<strong>{esc(lead)}:</strong> {esc(rest)}"
    return esc(s)


def logo_html(path):
    if not path:
        return ""
    return f'<img class="logo" src="{esc(path)}" alt="">'


def logo_cell(path):
    """Right-hand logo column for an entry (empty string when there's no logo)."""
    if not path:
        return ""
    return f'<div class="entry-logo"><img class="logo" src="{esc(path)}" alt=""></div>'


def render_site(resume, fm, tpl):
    import shutil
    b = resume["basics"]

    # Contact line
    contact = []
    if b.get("email"):
        contact.append(f'<a href="mailto:{esc(b["email"])}">{esc(b["email"])}</a>')
    if b.get("phone"):
        contact.append(f'<span>{esc(b["phone"])}</span>')
    if fm.get("website"):
        host = re.sub(r"^https?://", "", fm["website"]).rstrip("/")
        contact.append(f'<a href="{esc(fm["website"])}">{esc(host)}</a>')
    loc = b.get("location", {})
    locstr = ", ".join(x for x in [loc.get("city", ""), loc.get("countryName", "")] if x)
    if locstr:
        contact.append(f'<span>{esc(locstr)}</span>')
    if b.get("citizenship"):
        contact.append(f'<span>{esc(b["citizenship"])}</span>')
    contact_html = '<span class="sep">·</span>'.join(contact)

    photo_html = ""
    if b.get("photo"):
        photo_html = f'<img class="avatar" src="{esc(b["photo"])}" alt="{esc(b["name"])}">'

    # Experience
    exp = []
    for j in resume["work"]:
        note = f' <span class="note">({esc(j["note"])})</span>' if j.get("note") else ""
        summary = f'<p class="summary">{esc(j["summary"])}</p>' if j.get("summary") else ""
        bullets = ""
        if j.get("highlights"):
            items = "".join(f"<li>{highlight_html(h)}</li>" for h in j["highlights"])
            bullets = f"<ul>{items}</ul>"
        cls = "entry" if j.get("logo") else "entry no-logo"
        exp.append(f'''<article class="{cls}">
        <div class="entry-body">
          <div class="entry-titles">
            <h3>{esc(j["position"])}{note}</h3>
            <div class="org">{esc(j["name"])}</div>
          </div>
          {summary}{bullets}
        </div>
        <div class="entry-aside">
          <span class="dates">{daterange_html(j.get("startDate",""), j.get("endDate",""))}</span>
          {logo_cell(j.get("logo",""))}
        </div>
      </article>''')

    # Education
    edu = []
    for e in resume["education"]:
        area = f', {esc(e["area"])}' if e.get("area") else ""
        note = f'<div class="edunote">{esc(e["note"])}</div>' if e.get("note") else ""
        cls = "entry" if e.get("logo") else "entry no-logo"
        edu.append(f'''<article class="{cls}">
        <div class="entry-body">
          <div class="entry-titles">
            <h3>{esc(e["studyType"])}<span class="area">{area}</span></h3>
            <div class="org">{esc(e["institution"])}</div>
            {note}
          </div>
        </div>
        <div class="entry-aside">
          <span class="dates">{daterange_html(e.get("startDate",""), e.get("endDate",""))}</span>
          {logo_cell(e.get("logo",""))}
        </div>
      </article>''')

    # Skills
    skills = []
    for s in resume["skills"]:
        kw = ", ".join(esc(k) for k in s.get("keywords", []))
        skills.append(f'<div class="skill-row"><div class="skill-name">{esc(s["name"])}</div>'
                      f'<div class="skill-kw">{kw}</div></div>')

    langs = '<span class="sep">·</span>'.join(
        f'{esc(l["language"])} <span class="muted">({esc(l["fluency"])})</span>'
        for l in resume["languages"])

    pubs = ""
    scholar = [p for p in b.get("profiles", []) if p.get("network") == "Google Scholar"]
    if scholar:
        pubs = (f'Full and up-to-date list of publications available on '
                f'<a href="{esc(scholar[0]["url"])}">Google Scholar</a>.')

    pdf_name = "CV_" + re.sub(r"\s+", "_", b["name"].strip()) + ".pdf"

    footer = []
    if b.get("email"):
        footer.append(f'<a href="mailto:{esc(b["email"])}">{esc(b["email"])}</a>')
    if fm.get("website"):
        footer.append(f'<a href="{esc(fm["website"])}">{esc(re.sub(r"^https?://","",fm["website"]).rstrip("/"))}</a>')
    if scholar:
        footer.append(f'<a href="{esc(scholar[0]["url"])}">Google Scholar</a>')

    html = (tpl.read_text(encoding="utf-8")
            .replace("{{NAME}}", esc(b["name"]))
            .replace("{{ROLE}}", esc(b.get("label", "")))
            .replace("{{PHOTO}}", photo_html)
            .replace("{{CONTACT}}", contact_html)
            .replace("{{SUMMARY}}", esc(b.get("summary", "")))
            .replace("{{EXPERIENCE}}", "\n".join(exp))
            .replace("{{EDUCATION}}", "\n".join(edu))
            .replace("{{SKILLS}}", "\n".join(skills))
            .replace("{{LANGUAGES}}", langs)
            .replace("{{PUBLICATIONS}}", pubs)
            .replace("{{PDF_NAME}}", pdf_name)
            .replace("{{FOOTER}}", '<span class="sep">·</span>'.join(footer)))
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
