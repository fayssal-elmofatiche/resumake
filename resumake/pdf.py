"""PDF conversion — WeasyPrint (from HTML) with fallback to docx2pdf (from Word)."""

from pathlib import Path


def convert_to_pdf_weasyprint(html_content: str, output_path: Path) -> Path:
    """Convert HTML string to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        from .console import err_console

        err_console.print("[red]Error:[/] 'weasyprint' package required for HTML-to-PDF generation.")
        err_console.print("Install with: [bold]uv tool install resumakeai --with weasyprint[/]")
        raise SystemExit(1)

    HTML(string=html_content).write_pdf(str(output_path))
    return output_path


def convert_to_pdf_docx2pdf(docx_path: Path) -> Path:
    """Convert a .docx file to PDF using docx2pdf."""
    try:
        from docx2pdf import convert
    except ImportError:
        from .console import err_console

        err_console.print("[red]Error:[/] 'docx2pdf' package required for DOCX-to-PDF generation.")
        err_console.print("Install with: [bold]uv tool install resumakeai --with docx2pdf[/]")
        raise SystemExit(1)

    pdf_path = docx_path.with_suffix(".pdf")
    convert(str(docx_path), str(pdf_path))
    return pdf_path


def convert_to_pdf_auto(
    source_path: Path,
    engine: str = "auto",
    html_content: str | None = None,
) -> Path:
    """Convert to PDF using the specified engine.

    Engines:
    - 'weasyprint': HTML → PDF via WeasyPrint (requires html_content)
    - 'docx2pdf': DOCX → PDF via docx2pdf
    - 'auto': try weasyprint first (if html_content provided), fall back to docx2pdf
    """
    pdf_path = source_path.with_suffix(".pdf")

    if engine == "weasyprint":
        if html_content is None:
            from .console import err_console

            err_console.print("[red]Error:[/] WeasyPrint engine requires HTML content.")
            raise SystemExit(1)
        return convert_to_pdf_weasyprint(html_content, pdf_path)

    if engine == "docx2pdf":
        return convert_to_pdf_docx2pdf(source_path)

    # auto: try weasyprint if html_content available
    if html_content is not None:
        try:
            return convert_to_pdf_weasyprint(html_content, pdf_path)
        except SystemExit:
            pass  # weasyprint not installed, fall back

    return convert_to_pdf_docx2pdf(source_path)
