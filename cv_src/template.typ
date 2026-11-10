// ============================================================================
//  CV template: reads resume.json and renders the PDF.
//  You normally DON'T need to edit this file: change your content in cv.md
//  and run build.py. Come here only to tweak design (colors, fonts, spacing).
//  The knobs you're most likely to touch are right below.
// ============================================================================

#let data = json("resume.json")

// ---- Design knobs -----------------------------------------------------------
#let accent      = rgb("#2C4B8E")   // name rule, section headers (royal navy)
#let accent-red  = rgb("#9E2B22")   // links (deep red)
#let ink         = rgb("#1B2432")   // body text
#let soft        = rgb("#5A6472")   // dates, organisations, footer
#let hair        = rgb("#C9D2DF")   // thin rules
#let body-font   = "Libertinus Serif" // ships with Typst, always available
#let base-size   = 9.5pt
#let page-margin = (left: 1.7cm, right: 1.7cm, top: 1.5cm, bottom: 1.7cm)
#let logo-col    = 1.75cm           // width of the logo column beside entries
// -----------------------------------------------------------------------------

#let months = (
  "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
  "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
)

// Format an ISO-ish date string ("2024-01", "2015") into a readable label.
// Empty / missing endDate becomes "present".
#let fmt-date(d) = {
  if d == none or d == "" { return "present" }
  let parts = str(d).split("-")
  if parts.len() >= 2 {
    months.at(parts.at(1), default: "") + " " + parts.at(0)
  } else {
    parts.at(0)
  }
}

#let daterange(start, end) = fmt-date(start) + " to " + fmt-date(end)

// Turn "[text](https://...)" inside a string into a clickable link.
#let rich(s) = {
  let out = ()
  let pos = 0
  for m in s.matches(regex("\[([^\]]+)\]\((https?://[^)\s]+)\)")) {
    out.push(s.slice(pos, m.start))
    out.push(link(m.captures.at(1), m.captures.at(0)))
    pos = m.end
  }
  out.push(s.slice(pos))
  out.join()
}

// Highlight convention: text before the first ": " is emphasised.
#let render-highlight(s) = {
  if ": " in s and "](" not in s.split(": ").at(0) {
    let parts = s.split(": ")
    strong(parts.at(0)) + ": " + rich(parts.slice(1).join(": "))
  } else {
    rich(s)
  }
}

// A logo scaled to fit a fixed box, so wide and tall logos share one footprint.
#let logo-box(path) = box(width: logo-col - 0.3cm, height: 0.95cm)[
  #align(left + top, image(path, fit: "contain", width: 100%, height: 100%))
]

// One row of the contact block: a small icon followed by its text.
#let icon-row(icon-path, body) = grid(
  columns: (1.1em, auto), column-gutter: 0.5em,
  align: (center + horizon, left + horizon),
  image(icon-path, width: 0.85em),
  body,
)

// ---- Document & page setup --------------------------------------------------
#set document(
  title: data.basics.name + " CV",
  author: data.basics.name,
)
#set page(
  paper: "a4", margin: page-margin,
  footer: context {
    set text(size: 7.8pt, fill: soft)
    grid(columns: (1fr, auto, 1fr), align: (left, center, right),
      data.basics.name + ", curriculum vitae",
      data.basics.at("caption", default: ""),
      [#counter(page).display() of #counter(page).final().first()],
    )
  },
)
#set text(font: body-font, size: base-size, fill: ink, lang: "en", hyphenate: false)
#set par(justify: false, leading: 0.58em, spacing: 0.7em)
#set list(indent: 0pt, body-indent: 0.55em, spacing: 0.52em,
  marker: text(fill: accent, size: 0.8em, baseline: -0.08em, sym.bullet))
#show link: it => text(fill: accent-red, it)

// Section heading with a hairline beneath it.
#let section(title) = {
  v(0.95em)
  block(below: 0.75em, breakable: false, {
    text(size: 12.5pt, weight: "semibold", fill: accent, title)
    v(-0.62em)
    line(length: 100%, stroke: 0.5pt + hair)
  })
}

// The shared entry layout: logo (or nothing) on the left, then a heading line
// with the dates set against the right margin, then the body.
#let entry(logo: "", title: [], dates: "", sub: none, body: none) = {
  block(breakable: false, below: 1.15em, grid(
    columns: (logo-col, 1fr),
    align: (left + top, left + top),
    if logo != "" { pad(top: 0.1em, logo-box(logo)) } else { [] },
    stack(dir: ttb,
      grid(columns: (1fr, auto), column-gutter: 1em, align: (left + top, right + top),
        text(size: 10.6pt, weight: "semibold", title),
        text(size: 8.6pt, fill: soft, dates),
      ),
      ..if sub != none { (v(0.5em), text(fill: soft, sub)) } else { () },
      ..if body != none { (v(0.68em), body) } else { () },
    ),
  ))
}

// ---- Header: name, role, summary | contact | photo --------------------------
#{
  let b = data.basics
  let role = b.at("label", default: "").split(" · ")

  let left-col = stack(dir: ttb,
    text(size: 27pt, weight: "semibold", b.name),
    v(1.05em),
    text(size: 11.5pt, fill: accent, role.join(linebreak())),
    ..if b.at("summary", default: "") != "" { (v(1.1em), b.summary) } else { () },
  )

  let rows = ()
  if b.at("affiliation", default: "") != "" {
    rows.push(icon-row("images/icons/house.svg", b.affiliation))
  }
  if b.at("email", default: "") != "" {
    rows.push(icon-row("images/icons/envelope.svg", link("mailto:" + b.email, b.email)))
  }
  if b.at("phone", default: "") != "" {
    rows.push(icon-row("images/icons/phone.svg", b.phone.split(" · ").join(linebreak())))
  }
  if b.at("url", default: "") != "" {
    rows.push(icon-row("images/icons/globe.svg",
      link(b.url, b.url.replace("https://", "").replace("http://", ""))))
  }
  let personal = (b.at("citizenship", default: ""), b.at("age", default: "")).filter(x => x != "")
  if personal.len() > 0 {
    rows.push(icon-row("images/icons/user.svg", personal.join(", ")))
  }
  let contact = {
    set text(size: 8.8pt)
    set par(leading: 0.5em)
    stack(spacing: 0.62em, ..rows)
  }

  let photo = if b.at("photo", default: "") != "" {
    box(radius: 1.5pt, clip: true, image(b.photo, width: 2.45cm))
  } else { [] }

  grid(
    columns: (1fr, auto, auto),
    column-gutter: 1.5em,
    align: (left + top, left + top, right + top),
    left-col, pad(top: 0.5em, contact), photo,
  )
  v(0.1em)
  line(length: 100%, stroke: 1pt + accent)
}

// ---- Experience -------------------------------------------------------------
#if "work" in data and data.work.len() > 0 {
  section("Experience")
  for job in data.work {
    let dates = daterange(job.at("startDate", default: ""), job.at("endDate", default: ""))
    let note = job.at("note", default: "")
    entry(
      logo: job.at("logo", default: ""),
      title: job.position,
      dates: if note != "" { dates + ", " + lower(note) } else { dates },
      sub: job.name,
      body: {
        if job.at("summary", default: "") != "" { rich(job.summary) }
        if job.at("highlights", default: ()).len() > 0 {
          list(..job.highlights.map(h => render-highlight(h)))
        }
      },
    )
  }
}

// ---- Projects ---------------------------------------------------------------
#if "projects" in data and data.projects.len() > 0 {
  section("Projects")
  for p in data.projects {
    entry(
      logo: p.at("logo", default: ""),
      title: p.name,
      dates: if p.at("dated", default: false) {
        daterange(p.at("startDate", default: ""), p.at("endDate", default: ""))
      } else { "" },
      sub: p.at("entity", default: none),
      body: {
        if p.at("summary", default: "") != "" { rich(p.summary) }
        if p.at("highlights", default: ()).len() > 0 {
          list(..p.highlights.map(h => render-highlight(h)))
        }
      },
    )
  }
}

// ---- Education --------------------------------------------------------------
#if "education" in data and data.education.len() > 0 {
  section("Education")
  for ed in data.education {
    entry(
      logo: ed.at("logo", default: ""),
      title: {
        ed.studyType
        if ed.at("area", default: "") != "" { text(weight: "regular", ", " + ed.area) }
      },
      dates: daterange(ed.at("startDate", default: ""), ed.at("endDate", default: "")),
      sub: ed.institution,
      body: if ed.at("note", default: "") != "" { emph(ed.note) } else { none },
    )
  }
}

// ---- Skills -----------------------------------------------------------------
#if "skills" in data and data.skills.len() > 0 {
  section("Skills")
  grid(columns: (6.3cm, 1fr), column-gutter: 0.8em, row-gutter: 0.85em,
    ..data.skills.map(sk => (
      text(weight: "semibold", sk.name),
      sk.at("keywords", default: ()).join(", "),
    )).flatten()
  )
}

// ---- Languages --------------------------------------------------------------
#if "languages" in data and data.languages.len() > 0 {
  section("Languages")
  data.languages.map(l => l.language + " (" + lower(l.fluency) + ")").join(", ")
}

// ---- Publications link ------------------------------------------------------
#{
  let scholar = data.basics.at("profiles", default: ())
    .filter(p => p.at("network", default: "") == "Google Scholar")
  if scholar.len() > 0 {
    section("Publications")
    [The full, current list is on ]
    link(scholar.at(0).url)[Google Scholar]
    [.]
  }
}
