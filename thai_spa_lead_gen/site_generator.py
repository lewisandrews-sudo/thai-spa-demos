# thai_spa_lead_gen/site_generator.py
import os
import re
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_MAP = {
    "dark-luxury":    "dark_luxury.html.j2",
    "warm-natural":   "warm_natural.html.j2",
    "modern-minimal": "modern_minimal.html.j2",
    "thai-tropical":  "thai_tropical.html.j2",
}


def hex_to_rgb(hex_color: str) -> str:
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r},{g},{b}"


def _make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    env.filters['hex_to_rgb'] = hex_to_rgb
    return env


def _render_template(env: Environment, template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)


def generate_site(
    lead: dict,
    brand: dict,
    output_dir: str,
    deploy_url: str = "",
) -> tuple[str, str]:
    """
    Generate starter and premium index.html files for a business.
    Also generates the admin dashboard and Netlify function for premium.

    Returns (starter_path, premium_path).
    """
    env = _make_env()

    slug = brand["slug"]
    template_name = TEMPLATE_MAP.get(brand.get("design_direction", "warm-natural"), "warm_natural.html.j2")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    # --- Load partials ---
    booking_styles = _render_template(env, "booking_styles.css.j2", {"brand": brand})
    booking_section = _render_template(env, "booking_widget.html.j2", {"brand": brand})
    booking_function_url = f"{deploy_url}/.netlify/functions/book"
    booking_scripts = _render_template(env, "booking_scripts.js.j2", {
        "brand": brand,
        "supabase_url": supabase_url,
        "supabase_anon_key": supabase_anon_key,
        "booking_function_url": booking_function_url,
    })

    base_context = {
        "lead": lead,
        "brand": brand,
        "deploy_url": deploy_url,
    }

    # --- STARTER ---
    starter_context = {**base_context, "is_premium": False, "booking_styles": "", "booking_section": "", "booking_scripts": ""}
    starter_html = _render_template(env, template_name, starter_context)

    starter_dir = os.path.join(output_dir, slug, "starter")
    os.makedirs(starter_dir, exist_ok=True)
    starter_path = os.path.join(starter_dir, "index.html")
    with open(starter_path, "w", encoding="utf-8") as f:
        f.write(starter_html)

    # --- PREMIUM ---
    premium_context = {
        **base_context,
        "is_premium": True,
        "booking_styles": f"<style>{booking_styles}</style>",
        "booking_section": booking_section,
        "booking_scripts": booking_scripts,
    }
    premium_html = _render_template(env, template_name, premium_context)

    premium_dir = os.path.join(output_dir, slug, "premium")
    os.makedirs(premium_dir, exist_ok=True)
    premium_path = os.path.join(premium_dir, "index.html")
    with open(premium_path, "w", encoding="utf-8") as f:
        f.write(premium_html)

    # --- ADMIN DASHBOARD ---
    admin_html = _render_template(env, "admin_dashboard.html.j2", {
        "brand": brand,
        "supabase_url": supabase_url,
        "supabase_anon_key": supabase_anon_key,
    })
    admin_dir = os.path.join(output_dir, slug, f"{slug}-admin")
    os.makedirs(admin_dir, exist_ok=True)
    with open(os.path.join(admin_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(admin_html)

    # --- NETLIFY FUNCTION (premium only) ---
    func_js = _render_template(env, "booking_function.js.j2", {"brand": brand})
    func_dir = os.path.join(premium_dir, "netlify", "functions")
    os.makedirs(func_dir, exist_ok=True)
    with open(os.path.join(func_dir, "book.js"), "w") as f:
        f.write(func_js)

    # Write netlify.toml for function routing
    netlify_toml = '[build]\n  functions = "netlify/functions"\n'
    with open(os.path.join(premium_dir, "netlify.toml"), "w") as f:
        f.write(netlify_toml)

    print(f"  Generated: {slug}/starter + {slug}/premium")
    return starter_path, premium_path
