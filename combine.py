"""
Engine: combine a client Orion report with the market-content presentation and
re-number the pages cleanly. Importable by the web app (app.py) or runnable on
its own from the command line.

Result (matching the firm's manual Adobe process):
  - Page 1 of the Orion report (title/cover) -> no page number
  - Following Orion pages                     -> 1, 2, ...
  - All market-content slides                 -> continuing the count
  - Stray numbers baked into either source    -> removed
"""

import os
import shutil
import uuid
import argparse
import subprocess
import tempfile

import fitz  # PyMuPDF

# ----- How the finished file looks (measured from the firm's sample) ----------
NUMBER_FONT = "helv"        # Helvetica == ArialMT metrics
NUMBER_SIZE = 10.8
NUMBER_COLOR = (0x59 / 255, 0x59 / 255, 0x59 / 255)  # #595959 gray
NUMBER_RIGHT_X = 774.0
NUMBER_BASELINE_Y = 583.0
DEFAULT_ORION_PAGES = 3
# ------------------------------------------------------------------------------

SOFFICE_CANDIDATES = [
    "/opt/homebrew/bin/soffice",
    "/usr/local/bin/soffice",
    "/usr/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "soffice",
]


def find_soffice():
    for c in SOFFICE_CANDIDATES:
        if os.path.sep in c:
            if os.path.exists(c):
                return c
        elif shutil.which(c):
            return shutil.which(c)
    return None


def pptx_to_pdf(pptx_path, workdir):
    """Convert a .pptx to .pdf with LibreOffice and return the new path.

    Uses a unique LibreOffice user-profile per call so concurrent web requests
    don't collide on a shared profile lock.
    """
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice (soffice) was not found, so the PowerPoint cannot be "
            "converted to PDF. Install LibreOffice, or upload a PDF instead."
        )
    profile = f"file://{os.path.join(workdir, 'lo_profile_' + uuid.uuid4().hex)}"
    proc = subprocess.run(
        [
            soffice,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile}",
            "--convert-to", "pdf",
            "--outdir", workdir,
            pptx_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    base = os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf"
    out = os.path.join(workdir, base)
    if not os.path.exists(out):
        raise RuntimeError(
            "LibreOffice could not convert the PowerPoint.\n"
            + proc.stderr.decode("utf-8", "replace")[:500]
        )
    return out


def to_pdf(path, workdir):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return path
    if ext in (".pptx", ".ppt"):
        return pptx_to_pdf(path, workdir)
    raise RuntimeError(f"Unsupported file type '{ext}'. Use a .pdf or .pptx.")


def remove_old_numbers(page):
    """Erase page numbers already printed on the page so they don't double up."""
    W, H = page.rect.width, page.rect.height
    words = page.get_text("words")
    rects = []

    # bottom-right standalone digit tokens (slide / page numbers)
    for w in words:
        x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4].strip()
        if txt.isdigit() and x0 > W * 0.92 and y0 > H * 0.90:
            rects.append(fitz.Rect(x0, y0, x1, y1))

    # "Page N of M" in the top-right (Orion's header)
    for i in range(len(words) - 3):
        a, b, c, d = words[i], words[i + 1], words[i + 2], words[i + 3]
        if (
            a[4] == "Page" and b[4].isdigit() and c[4] == "of" and d[4].isdigit()
            and a[1] < H * 0.10 and a[0] > W * 0.60 and abs(a[1] - d[1]) < 4
        ):
            rects.append(fitz.Rect(min(a[0], d[0]), min(a[1], d[1]),
                                   max(a[2], d[2]), max(a[3], d[3])))

    for r in rects:
        page.add_redact_annot(r + (-1, -1, 1, 1), fill=(1, 1, 1))
    if rects:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)


def stamp_number(page, n):
    text = str(n)
    width = fitz.get_text_length(text, fontname=NUMBER_FONT, fontsize=NUMBER_SIZE)
    page.insert_text(
        (NUMBER_RIGHT_X - width, NUMBER_BASELINE_Y),
        text, fontname=NUMBER_FONT, fontsize=NUMBER_SIZE, color=NUMBER_COLOR,
    )


def combine(orion_path, content_path, output_path, orion_pages=DEFAULT_ORION_PAGES):
    """Build the combined, renumbered PDF. Returns (output_path, n_orion_pages)."""
    with tempfile.TemporaryDirectory() as workdir:
        content_pdf = to_pdf(content_path, workdir)
        orion = fitz.open(orion_path)
        content = fitz.open(content_pdf)

        n_orion = max(1, min(orion_pages, len(orion)))
        out = fitz.open()
        out.insert_pdf(orion, from_page=0, to_page=n_orion - 1)
        out.insert_pdf(content)

        for i, page in enumerate(out):
            remove_old_numbers(page)
            if i >= 1:                 # cover page stays unnumbered
                stamp_number(page, i)

        out.save(output_path, garbage=4, deflate=True)
        out.close(); orion.close(); content.close()
    return output_path, n_orion


def _cli():
    p = argparse.ArgumentParser(description="Combine an Orion report with the market deck.")
    p.add_argument("orion")
    p.add_argument("content")
    p.add_argument("output", nargs="?")
    p.add_argument("--orion-pages", type=int, default=DEFAULT_ORION_PAGES)
    a = p.parse_args()
    out = a.output or (os.path.splitext(a.orion)[0] + " - Combined.pdf")
    res, n = combine(a.orion, a.content, out, a.orion_pages)
    print(f"Saved: {res}  ({n} Orion pages + market content)")


if __name__ == "__main__":
    _cli()
