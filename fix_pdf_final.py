    def generate_pdf(self, context: Dict, output_path: str = "/tmp/kp_dsk.pdf") -> str:
        from jinja2 import Template
        kp_text_for_pdf = context.get("_kp_text_for_pdf") or context.get("kp_text") or ""
        ctx = {
            "complex_name": context.get("complex_name", "ДСК"),
            "address": context.get("address", ""),
            "kp_id": context.get("kp_id", "-"),
            "kp_text": kp_text_for_pdf,
        }
        with open("/home/zhabee/dsk-ai-sales/backend/templates/kp_pdf.html", "r", encoding="utf-8") as f:
            html = Template(f.read()).render(**ctx)
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        return output_path
