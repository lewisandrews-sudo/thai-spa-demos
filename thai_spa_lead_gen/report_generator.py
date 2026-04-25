# thai_spa_lead_gen/report_generator.py
import os
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


@dataclass
class ReportRow:
    lead: dict
    brand: dict
    starter_url: str | None
    premium_url: str | None


def generate_report(
    rows: list[ReportRow],
    output_path: str,
    area: str = "bangkok",
    business_type: str = "all",
    open_browser: bool = False,
) -> str:
    """
    Render the HTML report from all pipeline results.
    Returns the output path.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("report.html.j2")

    html = template.render(
        results=rows,
        run_date=datetime.now().strftime("%d %b %Y, %H:%M"),
        area=area,
        business_type=business_type,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nReport saved: {output_path}")
    if open_browser:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")

    return output_path
