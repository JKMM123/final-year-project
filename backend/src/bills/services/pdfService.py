import os
import pdfkit
from globals.utils.logger import logger
from globals.config.config import WKHTMLTOPDF_BIN, WKHTMLTOIMAGE_BIN
import imgkit
import os
from io import BytesIO
from db.postgres.tables.bills import Bills
from sqlalchemy.orm import Session
from sqlalchemy import update
from db.gcs.gcsService import GCSManager
from globals.config.config import BUCKET_NAME
from zoneinfo import ZoneInfo
from datetime import datetime
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from db.postgres.tables.users import Users
from db.postgres.tables.fixes import Fixes
from db.postgres.tables.meters import Meters

import asyncio
from pathlib import Path
import base64

from pathlib import Path as _Path
import os as _os
import tempfile as _tempfile


class PDFService:
    def __init__(self):
        self.gcs_manager = GCSManager()

    timezone = ZoneInfo("Asia/Beirut")
    imgkit_config = None
    pdfkit_config = None

    @classmethod
    def _get_pdfkit_config(cls):
        """Simple cross-platform config using environment variable"""
        if WKHTMLTOPDF_BIN:
            logger.info(f"Using wkhtmltopdf from environment: {WKHTMLTOPDF_BIN}")
            return pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_BIN)
        else:
            logger.info("Using default wkhtmltopdf configuration (system PATH)")
            return None

    @classmethod
    def _get_imgkit_config(cls):
        """Config for wkhtmltoimage"""
        if cls.imgkit_config:
            return cls.imgkit_config

        if WKHTMLTOIMAGE_BIN:
            logger.info(f"Using wkhtmltoimage from environment: {WKHTMLTOIMAGE_BIN}")
            cls.imgkit_config = imgkit.config(wkhtmltoimage=WKHTMLTOIMAGE_BIN)
            return cls.imgkit_config

        logger.info("Using default wkhtmltoimage configuration (system PATH)")
        return imgkit.config()

    @classmethod
    def html_to_image_bytes(cls, html: str, config, base_url) -> BytesIO:
        """Convert HTML to JPG and return bytes"""
        try:

            # options = {
            #     "format": "jpg",
            #     "quality": "95",
            #     "encoding": "UTF-8",
            #     "enable-local-file-access": None,
            #     "quiet": None,
            #     "width": 1600,
            #     "zoom": 2,
            # }
            options = {
                "format": "jpg",
                "quality": "75",  # reduced from 95
                "encoding": "UTF-8",
                "enable-local-file-access": None,
                "quiet": None,
                "width": 1100,  # reduced from 1600
                "zoom": 2,  # reduced zoom
            }
            html_to_render = html
            if base_url:
                if "<head>" in html:
                    html_to_render = html.replace(
                        "<head>", f'<head><base href="{base_url}">', 1
                    )
                else:
                    html_to_render = f'<base href="{base_url}">{html}'
            raw = imgkit.from_string(
                html_to_render, False, options=options, config=config
            )
            return BytesIO(raw)
        except Exception as e:
            logger.error(f"error in html_to_image_bytes: {e}")
            raise

    @classmethod
    def generate_single_bill_jpg_sync(
        cls,
        bill_data: dict,
        usage_template,
        fixed_template,
        session: Session,
    ):
        """Process a single bill with optimized error handling"""
        try:
            # Skip if already processed
            if bill_data.get("blob_name"):
                logger.debug(
                    f"Bill {bill_data.get('bill_id')} already has image, skipping"
                )
                return

            config = cls.imgkit_config or cls._get_imgkit_config()

            # Determine template and base URL
            pkg = bill_data.get("package_type", "usage")
            if pkg == "usage":
                html = usage_template.render(bill_data)
                base = Path(usage_template.filename).parent.as_uri() + "/"
            else:
                html = fixed_template.render(bill_data)
                base = Path(fixed_template.filename).parent.as_uri() + "/"

            # Render to image
            img_buf = cls.html_to_image_bytes(html, config, base)
            img_buf.seek(0)

            # Upload to GCS
            bill_id = str(bill_data["bill_id"])
            blob_name = f"bills/{bill_id}.jpg"

            cls.gcs_manager.upload_buffer(
                BUCKET_NAME,
                img_buf,
                blob_name,
                "image/jpeg",
            )

            # Update database immediately
            session.execute(
                update(Bills)
                .where(Bills.bill_id == bill_id)
                .values(blob_name=blob_name)
            )
            session.commit()

            logger.debug(f"Successfully processed bill {bill_id}")

        except Exception as e:
            session.rollback()
            logger.error(
                f"Failed to process bill {bill_data.get('bill_id', 'unknown')}: {e}"
            )
            raise

    @classmethod
    def html_to_pdf_bytes(cls, html: str, config, base_url) -> bytes:
        """Convert HTML to PDF bytes"""
        options = {
            "encoding": "UTF-8",
            "page-size": "A4",  # Use standard A4 for printers
            "margin-top": "5mm",
            "margin-right": "0mm",
            "margin-bottom": "0mm",
            "margin-left": "0mm",
            "disable-smart-shrinking": None,
            "print-media-type": None,
            "enable-local-file-access": None,
            "disable-external-links": None,
        }
        try:

            html_to_render = html
            if base_url:
                if "<head>" in html:
                    html_to_render = html.replace(
                        "<head>", f'<head><base href="{base_url}">', 1
                    )
                else:
                    html_to_render = f'<base href="{base_url}">{html}'

            return pdfkit.from_string(
                html_to_render, output_path=False, options=options, configuration=config
            )
        except Exception as e:
            logger.error(f"error in html_to_pdf_bytes: {e}")
            raise e

    @classmethod
    def generate_combined_bills_pdf(
        cls,
        bills_data,
        usage_template,
        fixed_template,
        bills_per_page: int = 4,
    ):
        """
        Render each bill HTML to an image, arrange 4 images per page in a single HTML,
        convert to one PDF, upload to GCS, and return the signed download URL.
        """
        try:
            if not bills_data:
                logger.info("No bills to render for combined PDF.")
                return None

            img_config = cls.imgkit_config or cls._get_imgkit_config()
            pdf_config = cls.pdfkit_config or cls._get_pdfkit_config()

            pages_html_parts = []
            total = len(bills_data)
            logger.info(
                f"Preparing {total} bills as images for combined PDF (4 per page)."
            )

            with _tempfile.TemporaryDirectory() as tmpdir:
                img_paths = []

                # Render all bills to JPEG files once
                for idx, bill_data in enumerate(bills_data):
                    pkg = bill_data.get("package_type", "usage")
                    if pkg == "usage":
                        bill_html = usage_template.render(bill_data)
                        base = _Path(usage_template.filename).parent.as_uri() + "/"
                    else:
                        bill_html = fixed_template.render(bill_data)
                        base = _Path(fixed_template.filename).parent.as_uri() + "/"

                    img_buf = cls.html_to_image_bytes(bill_html, img_config, base)
                    img_path = _os.path.join(tmpdir, f"bill_{idx+1}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_buf.getvalue())
                    img_paths.append(_Path(img_path).as_uri())

                # Build pages with file:// images
                for i in range(0, total, bills_per_page):
                    group_paths = img_paths[i : i + bills_per_page]
                    image_cells = [
                        f'<div class="cell"><img src="{uri}" /></div>'
                        for uri in group_paths
                    ]
                    while len(image_cells) < bills_per_page:
                        image_cells.append('<div class="cell"></div>')

                    page_html = f"""
                    <section class="page">
                        <div class="grid">
                            {''.join(image_cells)}
                        </div>
                    </section>
                    """
                    pages_html_parts.append(page_html)

                full_html = f"""
                <html>
                <head>
                    <meta charset="utf-8" />
                    <style>
                        @page {{ size: A4; margin: 5mm 0 0 0; }}
                        html, body {{ margin: 0; padding: 0; }}
                        .page {{
                            page-break-after: always;
                        }}
                        .page:last-child {{
                            page-break-after: auto;
                        }}
                        .grid {{
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            grid-auto-rows: 1fr;
                            gap: 6mm;
                            padding: 6mm;
                            box-sizing: border-box;
                        }}
                        .cell {{
                            width: 100%;
                            overflow: hidden;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                        .cell img {{
                            width: 100%;
                            height: auto;
                            display: block;
                        }}
                    </style>
                </head>
                <body>
                    {''.join(pages_html_parts)}
                </body>
                </html>
                """

                # More aggressive PDF image compression
                pdf_options = {
                    "encoding": "UTF-8",
                    "page-size": "A4",
                    "margin-top": "5mm",
                    "margin-right": "0mm",
                    "margin-bottom": "0mm",
                    "margin-left": "0mm",
                    "enable-local-file-access": None,
                    "disable-smart-shrinking": None,
                    "image-quality": "70",  # downsample images in PDF
                    "image-dpi": "150",  # target image DPI
                    "dpi": "150",  # overall render DPI
                    # "grayscale": None,       # uncomment if color not needed
                    "lowquality": None,  # smaller PDF output
                }
                pdf_bytes = pdfkit.from_string(
                    full_html,
                    output_path=False,
                    options=pdf_options,
                    configuration=pdf_config,
                )

            blob_name = f"pdf/combined_bills_{datetime.now(cls.timezone).strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            buf = BytesIO(pdf_bytes)
            buf.seek(0)

            cls.gcs_manager.upload_buffer(
                BUCKET_NAME,
                buffer=buf,
                destination_blob_name=blob_name,
                content_type="application/pdf",
            )

            download_url = cls.gcs_manager.generate_signed_url(
                BUCKET_NAME, blob_name, expiration_minutes=60 * 24
            )

            logger.info(f"Uploaded combined PDF: {blob_name}")
            return download_url

        except Exception as e:
            logger.error(f"Failed to generate combined bills PDF: {e}")
            return None
