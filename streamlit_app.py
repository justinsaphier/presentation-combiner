"""
Presentation Combiner — Streamlit app.

Upload a client Orion report + the market-content presentation, get back one
finished, page-numbered PDF. Deployed on Streamlit Community Cloud it gives a
permanent https://<name>.streamlit.app URL your boss can use on his own.

Uses the shared engine in combine.py.
"""

import os
import tempfile

import fitz  # PyMuPDF — used to render the preview images
import streamlit as st

from combine import combine, DEFAULT_ORION_PAGES

st.set_page_config(page_title="Presentation Combiner", page_icon="📊", layout="centered")


# ----------------------------- password gate ----------------------------------
def get_password():
    try:
        if "APP_PASSWORD" in st.secrets:
            return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    return os.environ.get("APP_PASSWORD")


def check_password():
    pw = get_password()
    if not pw:
        return True  # no password configured -> open (fine for local testing)
    if st.session_state.get("authed"):
        return True

    st.markdown("### 🔒 Sign in")
    with st.form("login"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if entered == pw:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


# ----------------------------- main UI ----------------------------------------
def main():
    st.title("Presentation Combiner")
    st.caption("Orion report + market content → one finished, page-numbered PDF")

    with st.expander("What this does", expanded=False):
        st.markdown(
            "- Keeps the **first few pages** of the Orion report (title page + content).\n"
            "- Adds **all** the market-content slides after it.\n"
            "- Removes the leftover page numbers in both files "
            "(Orion's *“Page X of 14”* and the deck's out-of-order slide numbers).\n"
            "- Stamps clean numbers, bottom-right: cover page blank, then **1, 2, 3, …**"
        )

    st.subheader("① Client Orion report")
    orion_file = st.file_uploader("Orion report (PDF)", type=["pdf"], key="orion")

    st.subheader("② Market content presentation")
    content_file = st.file_uploader(
        "Market content (PowerPoint or PDF)", type=["pptx", "ppt", "pdf"], key="content"
    )

    orion_pages = st.number_input(
        "Keep the first N pages of the Orion report",
        min_value=1, max_value=50, value=DEFAULT_ORION_PAGES, step=1,
        help="Default is 3 (title page + 2 content pages).",
    )

    if st.button("Combine into one PDF", type="primary", use_container_width=True,
                 disabled=not (orion_file and content_file)):
        with st.spinner("Combining and renumbering…"):
            try:
                orion_ext = os.path.splitext(orion_file.name)[1].lower()
                content_ext = os.path.splitext(content_file.name)[1].lower()
                with tempfile.TemporaryDirectory() as tmp:
                    orion_path = os.path.join(tmp, "orion" + orion_ext)
                    content_path = os.path.join(tmp, "content" + content_ext)
                    output_path = os.path.join(tmp, "combined.pdf")
                    with open(orion_path, "wb") as f:
                        f.write(orion_file.getbuffer())
                    with open(content_path, "wb") as f:
                        f.write(content_file.getbuffer())

                    combine(orion_path, content_path, output_path, int(orion_pages))
                    with open(output_path, "rb") as f:
                        pdf_bytes = f.read()

                download_name = (
                    os.path.splitext(orion_file.name)[0] or "Presentation"
                ) + " - Combined.pdf"

                # Render each page to a PNG so the preview shows on ANY browser
                # (embedded PDFs don't render on mobile Safari / some browsers).
                preview_imgs = []
                with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                    for page in doc:
                        preview_imgs.append(page.get_pixmap(dpi=110).tobytes("png"))

                # Store in session so the download click doesn't wipe the preview.
                st.session_state["result"] = {
                    "pdf": pdf_bytes, "name": download_name, "imgs": preview_imgs,
                }
            except Exception as e:  # noqa: BLE001
                st.session_state.pop("result", None)
                st.error(f"Something went wrong:\n\n{e}")
                st.info(
                    "Tip: if the PowerPoint won't convert, export it to PDF "
                    "(File ▸ Save As ▸ PDF) and upload that instead."
                )

    # ---- Result + preview (persists across reruns via session_state) ----------
    result = st.session_state.get("result")
    if result:
        st.success("Done — download your combined presentation below.")
        st.download_button(
            "⬇︎ Download combined PDF",
            data=result["pdf"],
            file_name=result["name"],
            mime="application/pdf",
            use_container_width=True,
        )
        st.divider()
        st.subheader(f"Preview — {len(result['imgs'])} pages")
        for i, img in enumerate(result["imgs"]):
            st.image(img, caption=f"Page {i + 1}", use_container_width=True)

    st.caption("Files are processed and discarded — nothing is stored.")


if __name__ == "__main__":
    if check_password():
        main()
