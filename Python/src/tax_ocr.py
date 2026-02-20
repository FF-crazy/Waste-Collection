from pathlib import Path
import re
import shutil
import pymupdf as fitz
from rapidocr import RapidOCR

PDF_DIR = Path("./pdf")
PNG_DIR = Path("./png")
OUTPUT_DIR = Path("./output")

class Ocr:
    def __init__(self) -> None:
        if not PDF_DIR.exists():
            PDF_DIR.mkdir()
        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir()
        if not PNG_DIR.exists():
            PNG_DIR.mkdir()

    def pdf_to_pix(self, pdf_file):
        pdf_path = Path(pdf_file)
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_file}")

        output_path = PNG_DIR / f"{pdf_path.stem}.png"

        doc = fitz.open(pdf_path)
        try:
            page = doc.load_page(0)
            matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(output_path.as_posix())
        finally:
            doc.close()
        return output_path
    
    def convert_all_pdf(self):
        pdf_files = PDF_DIR.glob("*.pdf")
        for f in pdf_files:
            self.pdf_to_pix(f)

    def png_to_text(self, png_file):
        png_path = Path(png_file)
        if not png_path.is_file():
            raise FileNotFoundError(f"PNG not found: {png_file}")

        ocr_engine = RapidOCR()
        result = ocr_engine(png_path)

        texts = list(result.txts) if result.txts else []
        pairs = [
            {"text": text
            }
            for text in texts
        ]

        return {
            "image": png_path.as_posix(),
            "count": len(pairs),
            "results": pairs,
            "elapsed": result.elapse,
        }

    def extract_key_fields(self, texts):
        date = ""
        invoice_no = ""
        amount_small = ""
        last_name = ""

        for text in texts:
            if not date:
                m = re.search(r"开票日期[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)", text)
                if m:
                    date = m.group(1)

            if not invoice_no:
                m = re.search(r"发票号码[:：]\s*([0-9]{10,})", text)
                if m:
                    invoice_no = m.group(1)

            if not amount_small:
                m = re.search(r"（小写）\s*[¥￥]?\s*([0-9]+(?:\.[0-9]+)?)", text)
                if m:
                    amount_small = m.group(1)

            m = re.search(r"名称[:：]\s*(.+)", text)
            if m:
                last_name = m.group(1).strip()

        return {
            "开票日期": date,
            "发票号码": invoice_no,
            "小写金额": amount_small,
            "最后一个名称": last_name,
        }

    def _safe_filename_part(self, text):
        text = text.strip()
        if not text:
            return "unknown"
        text = re.sub(r"[\\/:*?\"<>|]", "_", text)
        text = re.sub(r"\s+", "_", text)
        return text

    def rename_all_pdfs(self):
        png_files = PNG_DIR.glob("*.png")
        for png_path in png_files:
            pdf_path = PDF_DIR / f"{png_path.stem}.pdf"
            if not pdf_path.is_file():
                continue

            debug = self.png_to_text(png_path)
            fields = self.extract_key_fields([item["text"] for item in debug["results"]])

            date = self._safe_filename_part(fields["开票日期"])
            amount = self._safe_filename_part(fields["小写金额"])
            name = self._safe_filename_part(fields["最后一个名称"])
            invoice_no = self._safe_filename_part(fields["发票号码"])

            new_name = f"{date}_{amount}_{name}_{invoice_no}.pdf"
            target_path = OUTPUT_DIR / new_name
            shutil.copy2(pdf_path, target_path)



def main():
    ocr = Ocr()
    ocr.convert_all_pdf()
    ocr.rename_all_pdfs()


if __name__ == "__main__":
    main()
