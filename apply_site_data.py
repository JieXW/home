from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import html
import json
import re
import sys


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "WebStackPage.github.io-master"
DEFAULT_DATA = WEB_DIR / "site-data.js"
DEFAULT_HTML = WEB_DIR / "indexnew2.html"
EXPORT_DATA_RE = re.compile(r"^site-data(?: \(\d+\)| - 副本(?: \(\d+\))?)?\.js$", re.IGNORECASE)


def pick_latest_data_file() -> Path:
    exported = sorted(
        (
            path
            for path in WEB_DIR.glob("site-data*.js")
            if path.is_file() and path.name != DEFAULT_DATA.name and EXPORT_DATA_RE.match(path.name)
        ),
        key=lambda path: (path.stat().st_mtime, path.name.lower()),
        reverse=True,
    )
    if exported:
        return exported[0]
    return DEFAULT_DATA


def parse_site_data(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.SITE_DATA\s*=\s*([\s\S]*?);\s*$", text)
    payload = match.group(1) if match else text
    return json.loads(payload)


def infer_templates(sites):
    templates = {}
    for site in sites:
        primary = site.get("primary", "").strip()
        secondary = site.get("secondary", "").strip()
        if not primary:
            continue
        templates.setdefault(primary, [])
        if secondary and secondary not in templates[primary]:
            templates[primary].append(secondary)
    return templates


def infer_order(sites, templates):
    primaries = []
    secondaries = {}
    for site in sites:
        primary = site.get("primary", "").strip()
        secondary = site.get("secondary", "").strip()
        if not primary:
            continue
        if primary not in primaries:
            primaries.append(primary)
        secondaries.setdefault(primary, [])
        if secondary and secondary not in secondaries[primary]:
            secondaries[primary].append(secondary)
    for primary, items in templates.items():
        if primary not in primaries:
            primaries.append(primary)
        secondaries.setdefault(primary, [])
        for secondary in items:
            if secondary not in secondaries[primary]:
                secondaries[primary].append(secondary)
    return {"primaries": primaries, "secondaries": secondaries}


def normalize_data(raw):
    if isinstance(raw, list):
        templates = infer_templates(raw)
        return {"sites": raw, "templates": templates, "order": infer_order(raw, templates)}
    sites = raw.get("sites", [])
    templates = raw.get("templates") or infer_templates(sites)
    order = raw.get("order") or raw.get("templateOrder") or infer_order(sites, templates)
    return {"sites": sites, "templates": templates, "order": order}


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def build_html(bundle):
    sites = bundle["sites"]
    order = bundle["order"]

    grouped = {}
    for site in sites:
        grouped.setdefault(site["primary"], {})
        grouped[site["primary"]].setdefault(site["secondary"], [])
        grouped[site["primary"]][site["secondary"]].append(site)

    primary_keys = [item for item in order.get("primaries", []) if item in grouped]
    primary_keys.extend(item for item in grouped if item not in primary_keys)

    menu_parts = []
    content_parts = []
    for primary in primary_keys:
        secondary_map = grouped[primary]
        secondary_order = order.get("secondaries", {}).get(primary, [])
        secondary_keys = [item for item in secondary_order if item in secondary_map]
        secondary_keys.extend(item for item in secondary_map if item not in secondary_keys)

        menu_parts.append(
            f"""
                    <li>
                        <a href="#{esc(primary)}" class="smooth">
                            <i class="fa fa-folder-open-o"></i>
                            <span class="title">{esc(primary)}</span>
                        </a>
                        <ul>
                            {''.join(f'<li><a href="#{esc(primary)}-{esc(secondary)}" class="smooth"><span class="title">{esc(secondary)}</span></a></li>' for secondary in secondary_keys)}
                        </ul>
                    </li>"""
        )

        section = [f'<h4 class="text-gray"><i class="linecons-tag" style="margin-right: 7px;" id="{esc(primary)}"></i>{esc(primary)}</h4>']
        for secondary in secondary_keys:
            items = secondary_map[secondary]
            cards = []
            for site in items:
                fallback = "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote(site["url"], safe="")
                cards.append(
                    f"""
                <div class="col-sm-3 col-xs-6">
                    <div class="xe-widget xe-conversations box2 label-info" onclick="window.open('{esc(site['url'])}', '_blank')" data-toggle="tooltip" data-placement="bottom" title="" data-original-title="{esc(site['url'])}">
                        <div class="xe-comment-entry">
                            <a class="xe-user-img site-logo-wrap">
                                <img data-src="{esc(site.get('logo_url', fallback))}" data-fallback="{fallback}" class="lozad site-logo" width="44" height="44" alt="{esc(site['title'])}" onerror="if(this.dataset.fallback && this.src !== this.dataset.fallback) {{ this.src = this.dataset.fallback; }}">
                            </a>
                            <div class="xe-comment">
                                <a href="#" class="xe-user-name overflowClip_1">
                                    <strong>{esc(site['title'])}</strong>
                                </a>
                                <p class="overflowClip_2">{esc(site['desc'])}</p>
                            </div>
                        </div>
                    </div>
                </div>"""
                )
            section.append(
                f"""
            <div class="section-subtitle" id="{esc(primary)}-{esc(secondary)}">
                <span>{esc(secondary)}</span>
                <small>({len(items)})</small>
            </div>
            <div class="row">
                {''.join(cards)}
            </div>
            <br />"""
            )
        content_parts.append("\n".join(section))

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>我的网址导航</title>
    <link rel="icon" type="image/x-icon" href="./favicon.ico">
    <link rel="shortcut icon" href="./favicon.ico">
    <link rel="icon" type="image/png" sizes="64x64" href="./assets/images/favicon.png">
    <link rel="apple-touch-icon" sizes="192x192" href="./assets/images/icon-192.png">
    <link rel="manifest" href="./site.webmanifest">
    <meta name="theme-color" content="#f5f6f7">
    <meta name="msapplication-TileColor" content="#f5f6f7">
    <meta name="msapplication-TileImage" content="./assets/images/icon-192.png">
    <link rel="stylesheet" href="http://fonts.googleapis.com/css?family=Arimo:400,700,400italic">
    <link rel="stylesheet" href="./assets/css/fonts/linecons/css/linecons.css">
    <link rel="stylesheet" href="./assets/css/fonts/fontawesome/css/font-awesome.min.css">
    <link rel="stylesheet" href="./assets/css/bootstrap.css">
    <link rel="stylesheet" href="./assets/css/xenon-core.css">
    <link rel="stylesheet" href="./assets/css/xenon-components.css">
    <link rel="stylesheet" href="./assets/css/xenon-skins.css">
    <link rel="stylesheet" href="./assets/css/nav.css">
    <script src="./assets/js/jquery-1.11.1.min.js"></script>
    <style>
        .sidebar-menu .main-menu > li > a {{ display:flex; align-items:center; gap:10px; }}
        .sidebar-menu .main-menu > li > a > i {{ width:16px; text-align:center; flex:0 0 16px; }}
        .sidebar-menu .main-menu > li > a .title {{ display:block; flex:1 1 auto; line-height:1.45; }}
        .sidebar-menu .main-menu > li > ul > li > a {{ display:flex; align-items:center; min-height:34px; padding-left:38px; position:relative; }}
        .sidebar-menu .main-menu > li > ul > li > a::before {{ content:""; position:absolute; left:22px; top:50%; width:5px; height:5px; border-radius:50%; background:rgba(255,255,255,.45); transform:translateY(-50%); }}
        .section-subtitle {{ display:flex; gap:8px; align-items:baseline; color:#666; font-size:16px; font-weight:700; margin:10px 0 12px; }}
        .section-subtitle small {{ color:#999; font-size:12px; }}
        .site-logo-wrap {{ width:44px; height:44px; display:inline-flex; align-items:center; justify-content:center; border-radius:12px; background:linear-gradient(180deg,#fff,#f5f7fb); box-shadow:0 6px 18px rgba(22,34,51,.08); overflow:hidden; flex:0 0 44px; }}
        .site-logo {{ width:100%; height:100%; object-fit:contain; padding:6px; }}
    </style>
</head>
<body class="page-body">
    <div class="page-container">
        <div class="sidebar-menu toggle-others fixed">
            <div class="sidebar-menu-inner">
                <header class="logo-env">
                    <div class="logo">
                        <a href="./indexnew2.html" class="logo-expanded"><img src="./assets/images/logo@2x.png" width="100%" alt="" /></a>
                        <a href="./indexnew2.html" class="logo-collapsed"><img src="./assets/images/logo-collapsed@2x.png" width="40" alt="" /></a>
                    </div>
                </header>
                <ul id="main-menu" class="main-menu">
{''.join(menu_parts)}
                </ul>
            </div>
        </div>
        <div class="main-content">
            <nav class="navbar user-info-navbar" role="navigation">
                <ul class="user-info-menu left-links list-inline list-unstyled"><li class="hidden-sm hidden-xs"><a href="#" data-toggle="sidebar"><i class="fa-bars"></i></a></li></ul>
            </nav>
            {''.join(content_parts)}
        </div>
    </div>
    <script type="text/javascript">
    $(document).ready(function() {{
        const observer = lozad();
        observer.observe();

        $('a.smooth').click(function(ev) {{
            ev.preventDefault();
            public_vars.$mainMenu.add(public_vars.$sidebarProfile).toggleClass('mobile-is-visible');
            ps_destroy();
            $('html, body').animate({{
                scrollTop: $($(this).attr('href')).offset().top - 30
            }}, {{
                duration: 500,
                easing: 'swing'
            }});
        }});
    }});

    $('a.smooth').click(function(e) {{
        $('#main-menu li').each(function() {{
            $(this).removeClass('active');
        }});
        $(this).parent('li').addClass('active');
        e.preventDefault();
    }});
    </script>
    <script src="./assets/js/bootstrap.min.js"></script>
    <script src="./assets/js/TweenMax.min.js"></script>
    <script src="./assets/js/resizeable.js"></script>
    <script src="./assets/js/joinable.js"></script>
    <script src="./assets/js/xenon-api.js"></script>
    <script src="./assets/js/xenon-toggles.js"></script>
    <script src="./assets/js/xenon-custom.js"></script>
    <script src="./assets/js/lozad.js"></script>
</body>
</html>
"""


def main():
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pick_latest_data_file()
    if not source.exists():
        raise SystemExit(f"Source file not found: {source}")

    bundle = normalize_data(parse_site_data(source))
    DEFAULT_DATA.write_text("window.SITE_DATA = " + json.dumps(bundle, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    DEFAULT_HTML.write_text(build_html(bundle), encoding="utf-8")
    print(f"Source data: {source}")
    print(f"Updated data: {DEFAULT_DATA}")
    print(f"Updated html: {DEFAULT_HTML}")


if __name__ == "__main__":
    main()

