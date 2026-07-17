// ============================================================================
//  CV template: reads resume.json and renders the PDF.
//  You normally DON'T need to edit this file: change your content in
//  resume.json instead. Come here only to tweak design (colors, fonts,
//  spacing). The knobs you're most likely to touch are right below.
// ============================================================================

#let data = json("resume.json")

// ---- Design knobs -----------------------------------------------------------
#let accent      = rgb("#2C4B8E")   // name, section headers, rules (royal navy)
#let accent-red  = rgb("#9E2B22")   // summary/emphasis lines and links (deep red)
#let org-color   = rgb("#565656")   // organisation / institution names (muted gray)
#let body-font   = "Libertinus Serif" // ships with Typst, always available
#let base-size   = 10pt
#let page-margin = (x: 1.7cm, y: 1.6cm)
// -----------------------------------------------------------------------------

#let months = (
  "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
  "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
)

// Format an ISO-ish date string ("2024-01", "2015") into a readable label.
// Empty / missing endDate becomes "Present".
#let fmt-date(d) = {
  if d == none or d == "" { return "Present" }
  let parts = str(d).split("-")
  if parts.len() >= 2 {
    months.at(parts.at(1), default: "") + " " + parts.at(0)
  } else {
    parts.at(0)
  }
}

#let daterange(start, end) = fmt-date(start) + " to " + fmt-date(end)

// A logo scaled to fit within a fixed box, right-aligned, so wide and tall
// logos share a consistent footprint in the margin.
#let logo-box(path) = box(width: 3.5cm, height: 1.4cm)[
  #align(right + horizon, image(path, fit: "contain", width: 100%, height: 100%))
]

// A larger logo for the entry's right column, centered in its cell.
#let logo-big(path) = box(width: 3.6cm, height: 2.3cm)[
  #align(center + horizon, image(path, fit: "contain", width: 100%, height: 100%))
]

// One row of the contact box: a small icon followed by its text.
#let icon-row(icon-path, body) = grid(
  columns: (1.2em, 1fr), column-gutter: 0.45em,
  align: (center + horizon, left + horizon),
  image(icon-path, width: 0.9em),
  body,
)

// Highlight convention: text before the first ": " is emphasised.
#let render-highlight(s) = {
  if ": " in s {
    let parts = s.split(": ")
    strong(parts.at(0)) + ": " + parts.slice(1).join(": ")
  } else {
    s
  }
}

// ---- Document & page setup --------------------------------------------------
#set document(
  title: data.basics.name + " CV",
  author: data.basics.name,
)
#set page(paper: "a4", margin: page-margin, numbering: none)
#set text(font: body-font, size: base-size, fill: rgb("#1a1a1a"), lang: "en", hyphenate: false)
#set par(justify: true, leading: 0.6em)
#show link: it => text(fill: accent-red, it)

// Section heading with a full-width accent rule beneath it.
#let section(title) = {
  v(0.7em)
  text(size: 11.5pt, weight: "bold", fill: accent, tracking: 0.4pt,
    upper(title))
  v(-0.35em)
  line(length: 100%, stroke: 0.6pt + accent)
  v(0.15em)
}

// ---- Header (three columns: name+summary | contact box | photo+caption) ------
#{
  let b = data.basics

  // LEFT: name + summary paragraph
  let left-col = {
    text(size: 24pt, weight: "bold", fill: black, b.name)
    if b.at("summary", default: "") != "" {
      v(0.45em)
      set text(size: 8.5pt, fill: rgb("#333333"))
      set par(justify: true, leading: 0.5em)
      b.summary
    }
  }

  // CENTER: bordered contact box with icons
  let rows = ()
  if b.at("affiliation", default: "") != "" {
    rows.push(icon-row("images/icons/house.svg", b.affiliation))
  }
  if b.at("phone", default: "") != "" {
    rows.push(icon-row("images/icons/phone.svg", b.phone.split(" · ").join(linebreak())))
  }
  if b.at("email", default: "") != "" {
    rows.push(icon-row("images/icons/envelope.svg", link("mailto:" + b.email, b.email)))
  }
  if b.at("age", default: "") != "" {
    rows.push(icon-row("images/icons/user.svg", b.age))
  }
  if b.at("citizenship", default: "") != "" {
    rows.push(icon-row("images/icons/flag.svg", b.citizenship))
  }
  if b.at("url", default: "") != "" {
    rows.push(icon-row("images/icons/globe.svg",
      link(b.url, b.url.replace("https://", "").replace("http://", ""))))
  }
  let contact-box = box(
    width: 6.2cm,
    fill: rgb("#eef3fb"), stroke: 0.7pt + accent, radius: 3pt, inset: 6pt,
    {
      set text(size: 8.6pt)
      rows.join(v(0.12em))
    },
  )

  // RIGHT: photo + caption
  let right-col = {
    if b.at("photo", default: "") != "" {
      box(radius: 4pt, clip: true, image(b.photo, width: 2.9cm))
    }
    if b.at("caption", default: "") != "" {
      v(0.3em)
      set par(justify: false, leading: 0.4em)
      align(center, text(size: 7.5pt, style: "italic", fill: rgb("#666666"), "*" + b.caption))
    }
  }

  grid(
    columns: (1fr, auto, 3.1cm),
    column-gutter: 1.0em,
    align: (left + top, left + top, center + top),
    left-col, contact-box, right-col,
  )
}

// ---- Experience -------------------------------------------------------------
#if "work" in data and data.work.len() > 0 {
  section("Experience")
  for job in data.work {
    grid(
      columns: (1fr, 3.8cm), column-gutter: 0.8em,
      align: (left + top, center + horizon),
      // LEFT: dates (top-right) + org + title, then summary + bullets
      {
        grid(columns: (1fr, auto), column-gutter: 0.6em, align: (left + top, right + top),
          {
            text(size: 11pt, fill: org-color, job.name)
            linebreak()
            text(weight: "bold", size: 10.5pt, job.position)
          },
          {
            let dates = daterange(job.at("startDate", default: ""), job.at("endDate", default: ""))
            let note = job.at("note", default: "")
            let lbl = if note != "" { dates + " · " + note } else { dates }
            text(size: 8pt, fill: rgb("#666666"), tracking: 0.3pt, smallcaps(lbl))
          },
        )
        if job.at("summary", default: "") != "" {
          v(0.2em)
          text(size: 9.5pt, fill: accent-red, job.summary)
        }
        if job.at("highlights", default: ()).len() > 0 {
          v(0.2em)
          set text(size: 9.5pt)
          list(indent: 0.4em, spacing: 0.5em,
            ..job.highlights.map(h => render-highlight(h)))
        }
      },
      // RIGHT: logo, vertically centered against the whole entry
      if job.at("logo", default: "") != "" { logo-big(job.logo) } else { [] },
    )
    v(0.7em)
  }
}

// ---- Education --------------------------------------------------------------
#if "education" in data and data.education.len() > 0 {
  section("Education")
  for ed in data.education {
    grid(
      columns: (1fr, 3.8cm), column-gutter: 0.8em,
      align: (left + top, center + horizon),
      {
        grid(columns: (1fr, auto), column-gutter: 0.6em, align: (left + top, right + top),
          {
            text(weight: "bold", ed.studyType)
            if ed.at("area", default: "") != "" { text(", " + ed.area) }
            linebreak()
            text(size: 10pt, fill: org-color, ed.institution)
            if ed.at("note", default: "") != "" {
              linebreak()
              text(size: 9pt, style: "italic", fill: accent-red, ed.note)
            }
          },
          text(size: 8pt, fill: rgb("#666666"), tracking: 0.3pt,
            smallcaps(daterange(ed.at("startDate", default: ""), ed.at("endDate", default: "")))),
        )
      },
      if ed.at("logo", default: "") != "" { logo-big(ed.logo) } else { [] },
    )
    v(0.6em)
  }
}

// ---- Skills -----------------------------------------------------------------
#if "skills" in data and data.skills.len() > 0 {
  section("Skills")
  set text(size: 9.5pt)
  for sk in data.skills {
    grid(columns: (5.6cm, 1fr), column-gutter: 0.6em, row-gutter: 0.4em,
      text(weight: "bold", fill: accent, sk.name),
      sk.at("keywords", default: ()).join(", "),
    )
    v(0.25em)
  }
}

// ---- Languages --------------------------------------------------------------
#if "languages" in data and data.languages.len() > 0 {
  section("Languages")
  set text(size: 9.5pt)
  data.languages
    .map(l => l.language + " (" + l.fluency + ")")
    .join([   #text(fill: accent)[•]   ])
}

// ---- Publications link ------------------------------------------------------
#{
  let scholar = data.basics.at("profiles", default: ())
    .filter(p => p.at("network", default: "") == "Google Scholar")
  if scholar.len() > 0 {
    section("Publications")
    set text(size: 9.5pt)
    [Full and up-to-date list of publications available on ]
    link(scholar.at(0).url)[Google Scholar]
    [.]
  }
}
