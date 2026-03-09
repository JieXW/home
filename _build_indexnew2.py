from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit
import html
import re

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
SRC = next(p for p in ROOT.glob("*.md") if p.name != "myweb.md")
OUT = ROOT / "WebStackPage.github.io-master" / "indexnew2.html"

TRACKING_QUERY_KEYS = {
    "_ga",
    "_gl",
    "_suid",
    "_channel_track_key",
    "gclid",
    "gbraid",
    "gad_campaignid",
    "gad_source",
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "utm_term",
    "utm_content",
    "track_id",
    "tt_from",
    "share_token",
}

GENERIC_TITLES = {
    "",
    "login",
    "登录",
    "home",
    "首页",
    "index",
    "practice",
    "title unavailable | site unreachable",
    "fetching title#3xyu",
    "stale request",
    "temporarily unavailable",
}

PRIMARY_META = OrderedDict(
    [
        (
            "常用工具",
            {
                "id": "tools",
                "icon": "fa-wrench",
                "subs": OrderedDict(
                    [
                        ("通用效率", "tools-general"),
                        ("云服务与存储", "tools-cloud"),
                        ("颜色与辅助", "tools-color"),
                        ("其他工具", "tools-other"),
                    ]
                ),
            },
        ),
        (
            "校园与USTC",
            {
                "id": "ustc",
                "icon": "fa-university",
                "subs": OrderedDict(
                    [
                        ("校园门户", "ustc-portal"),
                        ("研究生系统", "ustc-grad"),
                        ("校园服务", "ustc-service"),
                    ]
                ),
            },
        ),
        (
            "AI与Agent",
            {
                "id": "ai",
                "icon": "fa-magic",
                "subs": OrderedDict(
                    [
                        ("通用模型", "ai-chat"),
                        ("平台与开发", "ai-platform"),
                        ("MCP与Agent生态", "ai-agent"),
                        ("AI导航与发现", "ai-directory"),
                    ]
                ),
            },
        ),
        (
            "学术科研",
            {
                "id": "research",
                "icon": "fa-flask",
                "subs": OrderedDict(
                    [
                        ("检索与数据库", "research-search"),
                        ("写作与文献", "research-writing"),
                        ("生物与分子模拟", "research-bio"),
                        ("科研社区与资源", "research-community"),
                    ]
                ),
            },
        ),
        (
            "开发与技术",
            {
                "id": "dev",
                "icon": "fa-code",
                "subs": OrderedDict(
                    [
                        ("开发社区", "dev-community"),
                        ("教程与文档", "dev-docs"),
                        ("工具与平台", "dev-tools"),
                    ]
                ),
            },
        ),
        (
            "考试与证书",
            {
                "id": "exam",
                "icon": "fa-file-text-o",
                "subs": OrderedDict(
                    [
                        ("官方报名", "exam-register"),
                        ("语言与能力证书", "exam-cert"),
                    ]
                ),
            },
        ),
        (
            "招生与深造",
            {
                "id": "admission",
                "icon": "fa-graduation-cap",
                "subs": OrderedDict(
                    [
                        ("国内招生", "admission-domestic"),
                        ("海外PhD与奖学金", "admission-overseas"),
                    ]
                ),
            },
        ),
        (
            "求职与招聘",
            {
                "id": "jobs",
                "icon": "fa-briefcase",
                "subs": OrderedDict(
                    [
                        ("综合招聘", "jobs-general"),
                        ("校招与实习", "jobs-campus"),
                        ("央国企与公共就业", "jobs-public"),
                        ("行业招聘", "jobs-industry"),
                        ("求职辅助", "jobs-assist"),
                    ]
                ),
            },
        ),
        (
            "公考与时政",
            {
                "id": "public",
                "icon": "fa-newspaper-o",
                "subs": OrderedDict(
                    [
                        ("公考报名与资讯", "public-exam"),
                        ("政策与政务", "public-policy"),
                        ("时政媒体", "public-news"),
                    ]
                ),
            },
        ),
        (
            "社区与内容",
            {
                "id": "community",
                "icon": "fa-comments-o",
                "subs": OrderedDict(
                    [
                        ("内容社区", "community-media"),
                        ("阅读与语言", "community-read"),
                    ]
                ),
            },
        ),
        (
            "其他网站",
            {
                "id": "other",
                "icon": "fa-star-o",
                "subs": OrderedDict([("未细分", "other-misc")]),
            },
        ),
    ]
)


TITLE_OVERRIDES = {
    "https://email.ustc.edu.cn": "USTC邮件系统",
    "https://i.ustc.edu.cn": "USTC信息门户",
    "https://ncre-bm.neea.edu.cn": "NCRE报名系统",
    "https://cet-bm.neea.edu.cn": "CET报名网",
    "https://www.researchgate.net": "ResearchGate",
    "https://stackoverflow.com": "Stack Overflow",
    "https://www.chsi.com.cn": "学信网",
    "https://www.csc.edu.cn": "国家留学网",
    "https://publish.acs.org": "ACS Publications",
    "https://cloud.siliconflow.cn": "硅基流动",
    "https://yuanbao.tencent.com": "腾讯元宝",
    "https://zotero-chinese.com/styles": "中文 CSL 样式",
    "https://drive.google.com/drive/my-drive": "Google 云端硬盘",
    "http://yjs.ustc.edu.cn": "USTC研究生教务",
    "https://www.gongkaoleida.com": "公考雷达",
    "https://www.gongkaoleida.com/exam/937035": "公考雷达职位详情",
    "https://www.gongkaoleida.com/user/remind": "公考雷达提醒",
    "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/home/gkhome.html": "国家公务员局报名系统",
    "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/article/articlelist.html?id=0000000062b7b2b60162bccd55ec0006&eid=0000000062b7b2b60162bccdd5860007": "国家公务员局公告",
    "http://subb.scs.gov.cn/pp/gkweb/core/web/ui/business/home/lxhome.html": "中央机关遴选和选调",
    "https://www.csc.edu.cn/chuguo/list/24": "国家留学网项目列表",
    "https://www.ciiczhaopin.com/campus/index": "中智校园招聘",
    "https://yz.tsinghua.edu.cn/zsxx/bszs/jzml.htm": "清华大学研究生招生网",
    "https://admission.pku.edu.cn/index.htm": "北京大学研究生招生网",
    "http://www.grs.zju.edu.cn/yjszs/main.htm": "浙江大学研究生招生网",
    "https://gsao.fudan.edu.cn": "复旦大学研究生招生网",
    "https://paper.people.com.cn/rmrb/pc/layout/202603/07/node_01.html": "人民日报",
}

HOST_TITLE_OVERRIDES = {
    "console.cloud.tencent.com": "腾讯云 COS",
    "oss.console.aliyun.com": "阿里云 OSS",
    "mail.ustc.edu": "USTC企业邮箱",
    "yjs1.ustc.edu.cn": "USTC研究生系统",
    "makebook.ustc.edu.cn": "USTC教材服务",
    "wvpn.ustc.edu.cn": "USTC WebVPN",
    "tool.lu": "在线工具",
    "paper2x.noedgeai.com": "Paper2X",
    "mcpmarket.cn": "MCP市场",
    "mcp.so": "MCP Servers",
    "mcphub.io": "MCP Hub",
    "metaso.cn": "秘塔AI搜索",
    "www.niupizhiyuan.com": "牛皮纸源",
    "niupizhiyuan.com": "牛皮纸源",
    "bbs.keinsci.com": "研之友论坛",
    "dict.cnki.net": "CNKI翻译助手",
    "my.feishu.cn": "飞书",
    "www.keybr.com": "Keybr",
    "keybr.com": "Keybr",
    "www.aminer.cn": "AMiner",
    "aminer.cn": "AMiner",
    "www.semanticscholar.org": "Semantic Scholar",
    "semanticscholar.org": "Semantic Scholar",
    "agent.minimaxi.com": "MiniMax Agent",
    "z-lib.cv": "Z-Library",
    "www.mohrss.gov.cn": "人力资源和社会保障部",
    "mohrss.gov.cn": "人力资源和社会保障部",
    "drive.google.com": "Google 云端硬盘",
}


@dataclass
class Site:
    title: str
    desc: str
    url: str
    host: str
    logo_url: str
    primary: str
    secondary: str


def clean_text(text: str) -> str:
    text = text.replace("\\|", "|").replace("—", " - ").replace("–", " - ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_garbled(text: str) -> bool:
    if not text:
        return True
    low = text.lower().strip()
    if low in GENERIC_TITLES:
        return True
    if text.startswith("http://") or text.startswith("https://"):
        return True
    if "�" in text:
        return True
    allowed = 0
    for ch in text:
        if ch.isalnum() or ch in " -_|:,.!?'\"/\\()[]{}+&%~@#=，。！？：；、·（）" or "\u4e00" <= ch <= "\u9fff":
            allowed += 1
    return (allowed / max(1, len(text))) < 0.70


def host_of(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def prettify_host(host: str) -> str:
    plain_host = host_of("https://" + host if "://" not in host else host)
    main = plain_host.split(".")[0]
    if len(main) <= 4:
        return main.upper()
    parts = re.split(r"[-_]", main)
    label = " ".join(part[:1].upper() + part[1:] for part in parts if part)
    return label or plain_host


def root_url(url: str) -> str:
    split = urlsplit(url)
    return urlunsplit((split.scheme or "https", split.netloc, "/", "", ""))


def strip_query(url: str, drop_all: bool = False) -> str:
    split = urlsplit(url)
    if drop_all:
        return urlunsplit((split.scheme, split.netloc, split.path, "", ""))
    kept = []
    for key, value in parse_qsl(split.query, keep_blank_values=True):
        low = key.lower()
        if low in TRACKING_QUERY_KEYS or low.startswith("utm_"):
            continue
        kept.append((key, value))
    query = urlencode(kept)
    return urlunsplit((split.scheme, split.netloc, split.path, query, ""))


def stable_url(url: str) -> str:
    url = clean_text(url)
    split = urlsplit(url)
    host = split.netloc.lower()
    path = split.path

    if host == "email.ustc.edu.cn":
        return "https://email.ustc.edu.cn/"
    if host == "i.ustc.edu.cn":
        return "https://i.ustc.edu.cn/"
    if host == "mail.ustc.edu":
        return "https://mail.ustc.edu/"
    if host == "yjs1.ustc.edu.cn":
        return "https://yjs1.ustc.edu.cn/"
    if host == "ncre-bm.neea.edu.cn":
        return "https://ncre-bm.neea.edu.cn/"
    if host == "cet-bm.neea.edu.cn":
        return "https://cet-bm.neea.edu.cn/"
    if host == "zotero-chinese.com" and path.startswith("/styles/"):
        return "https://zotero-chinese.com/styles/"
    if host == "bbs.keinsci.com":
        return "http://bbs.keinsci.com/forum.php"
    if host == "dict.cnki.net":
        return "https://dict.cnki.net/index#"
    if host == "www.researchgate.net":
        return "https://www.researchgate.net/"
    if host == "publish.acs.org":
        return "https://publish.acs.org/"
    if host == "www.proquest.com":
        return "https://www.proquest.com/"
    if host == "yuanbao.tencent.com":
        return "https://yuanbao.tencent.com/"
    if host == "cloud.siliconflow.cn":
        return "https://cloud.siliconflow.cn/"
    if host == "my.feishu.cn" and path.startswith("/wiki/"):
        return "https://my.feishu.cn/"
    if host == "paper2x.noedgeai.com":
        return "https://paper2x.noedgeai.com/"
    if host == "bigmodel.cn":
        return "https://bigmodel.cn/"
    if host == "www.kimi.com" and path.startswith("/code"):
        return "https://www.kimi.com/code"

    url = strip_query(url)
    split = urlsplit(url)
    if any(key in split.query.lower() for key in ("sid=", "returnurl=", "accountid=", "forcecas=1")):
        return root_url(url)
    return url


def simplify_title(text: str, host: str) -> str:
    text = clean_text(text)
    if not text:
        return HOST_TITLE_OVERRIDES.get(host) or prettify_host(host)
    if host == "stackoverflow.com":
        return "Stack Overflow"
    if host == "chat.qwen.ai":
        return "Qwen Chat"
    if host == "grok.com":
        return "Grok"
    if host == "www.yingjiesheng.com":
        return "应届生求职"
    if host == "www.ncss.cn":
        return "国家大学生就业服务平台"
    if host == "www.iguopin.com":
        return "国聘"
    if host in HOST_TITLE_OVERRIDES:
        return HOST_TITLE_OVERRIDES[host]

    parts = [p.strip() for p in re.split(r"\s*[|｜\-]\s*", text) if p.strip()]
    if len(parts) > 1:
        non_generic = [p for p in parts if p.lower() not in GENERIC_TITLES]
        if non_generic:
            short = min(non_generic, key=len)
            if len(short) <= 28:
                return short
    text = re.sub(r"^(登录|首页)\s*", "", text, flags=re.I).strip(" -|")
    text = re.sub(r"\b(login|sign in|register|dashboard)\b", "", text, flags=re.I).strip(" -|")
    if text:
        return text[:36].rstrip(" -_|")
    return HOST_TITLE_OVERRIDES.get(host) or prettify_host(host)


def fetch_site_meta(url: str) -> tuple[str | None, str | None]:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, timeout=12, headers=headers)
    except Exception:
        return None, None

    if response.apparent_encoding:
        response.encoding = response.apparent_encoding

    html_text = response.text or ""
    soup = BeautifulSoup(html_text, "html.parser")
    candidates: list[str] = []

    for attr_name, attr_value in [
        ("property", "og:site_name"),
        ("name", "application-name"),
        ("name", "apple-mobile-web-app-title"),
        ("property", "og:title"),
    ]:
        meta = soup.find("meta", attrs={attr_name: attr_value})
        if meta and meta.get("content"):
            candidates.append(meta["content"])
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)

    host = host_of(url)
    title = None
    for candidate in candidates:
        cleaned = clean_text(candidate)
        if cleaned and cleaned.lower() not in GENERIC_TITLES:
            title = simplify_title(cleaned, host)
            break

    icon_url = None
    rel_priority = [
        "apple-touch-icon",
        "apple-touch-icon-precomposed",
        "shortcut icon",
        "icon",
        "mask-icon",
    ]
    for desired_rel in rel_priority:
        for link in soup.find_all("link"):
            rel = link.get("rel") or []
            rel_tokens = [rel.lower()] if isinstance(rel, str) else [token.lower() for token in rel]
            if desired_rel in " ".join(rel_tokens):
                href = link.get("href")
                if href:
                    icon_url = urljoin(response.url, href)
                    break
        if icon_url:
            break

    if not icon_url:
        icon_url = urljoin(response.url, "/favicon.ico")
    return title, icon_url


def generated_desc(title: str, primary: str, secondary: str, host: str) -> str:
    if primary == "常用工具":
        if secondary == "通用效率":
            return f"{title}，常用效率工具或在线服务入口。"
        if secondary == "云服务与存储":
            return f"{title}，云服务、控制台或在线存储入口。"
        if secondary == "颜色与辅助":
            return f"{title}，配色、查询或辅助小工具。"
        return f"{title}，常用工具站点。"
    if primary == "校园与USTC":
        if secondary == "校园门户":
            return f"{title}，校园门户或学校官方入口。"
        if secondary == "研究生系统":
            return f"{title}，研究生招生、培养或教务相关入口。"
        return f"{title}，校园服务与统一认证相关入口。"
    if primary == "AI与Agent":
        if secondary == "通用模型":
            return f"{title}，通用 AI 对话或助手服务。"
        if secondary == "平台与开发":
            return f"{title}，AI 平台、控制台或开发工具。"
        if secondary == "MCP与Agent生态":
            return f"{title}，MCP、Agent 或自动化生态资源。"
        return f"{title}，AI 工具导航或发现平台。"
    if primary == "学术科研":
        if secondary == "检索与数据库":
            return f"{title}，论文检索、数据库或科研检索入口。"
        if secondary == "写作与文献":
            return f"{title}，写作、翻译或参考文献相关工具。"
        if secondary == "生物与分子模拟":
            return f"{title}，生物信息、结构数据库或分子模拟资源。"
        return f"{title}，科研社区、论坛或学术资源站。"
    if primary == "开发与技术":
        return f"{title}，开发学习、技术社区或工程工具。"
    if primary == "考试与证书":
        return f"{title}，考试报名、成绩或证书相关入口。"
    if primary == "招生与深造":
        return f"{title}，招生、申请或深造信息入口。"
    if primary == "求职与招聘":
        return f"{title}，求职招聘、校招实习或就业服务平台。"
    if primary == "公考与时政":
        return f"{title}，公考信息、政策资讯或时政媒体入口。"
    if primary == "社区与内容":
        return f"{title}，内容社区、阅读或知识服务站点。"
    return f"{title}，常用站点入口。"


def pick_desc(raw_title: str, title: str, host: str, primary: str, secondary: str) -> str:
    cleaned = clean_text(raw_title)
    lowered = cleaned.lower()
    if (
        is_garbled(cleaned)
        or cleaned == title
        or "登录" in cleaned
        or "login" in lowered
        or "register" in lowered
        or "site unreachable" in lowered
        or re.search(r"\b[a-z0-9-]+\.(com|cn|org|net|edu|ai)\b", lowered)
    ):
        return generated_desc(title, primary, secondary, host)
    cleaned = re.sub(r"^(登录|首页)\s*[-_:：]?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(login|sign in|register|dashboard)\b", "", cleaned, flags=re.I).strip(" -_|:")
    if not cleaned:
        return generated_desc(title, primary, secondary, host)
    return cleaned[:88] + ("..." if len(cleaned) > 88 else "")


def parse_sites() -> list[Site]:
    text = SRC.read_text(encoding="utf-8")
    matches = re.findall(r"\[(.*?)\]\((.*?)\)", text, re.S)

    dedup: OrderedDict[str, tuple[str, str]] = OrderedDict()
    for raw_title, raw_url in matches:
        url = clean_text(raw_url)
        if not url.startswith(("http://", "https://")):
            continue
        stable = stable_url(url).rstrip("/")
        if stable not in dedup:
            dedup[stable] = (clean_text(raw_title), stable)

    fetched_meta: dict[str, tuple[str | None, str | None]] = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        future_map = {pool.submit(fetch_site_meta, url): url for _, url in dedup.values()}
        for future in as_completed(future_map):
            url = future_map[future]
            try:
                title, logo = future.result()
            except Exception:
                title, logo = None, None
            fetched_meta[url] = (title, logo)

    sites: list[Site] = []
    for raw_title, stable in dedup.values():
        host = host_of(stable)
        fetched_title, fetched_logo = fetched_meta.get(stable, (None, None))
        title = TITLE_OVERRIDES.get(stable) or HOST_TITLE_OVERRIDES.get(host) or fetched_title
        if not title:
            title = simplify_title(raw_title if not is_garbled(raw_title) else host, host)
        primary, secondary = categorize(stable, title)
        desc = pick_desc(raw_title, title, host, primary, secondary)
        fallback_logo = "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote(stable, safe="")
        sites.append(
            Site(
                title=title,
                desc=desc,
                url=stable + ("/" if urlsplit(stable).path == "" else ""),
                host=host,
                logo_url=fetched_logo or fallback_logo,
                primary=primary,
                secondary=secondary,
            )
        )
    return sites


def contains_any(url: str, values: Iterable[str]) -> bool:
    return any(value in url for value in values)


def categorize(url: str, title: str) -> tuple[str, str]:
    target = f"{url} {title}".lower()

    if contains_any(
        target,
        [
            "greasyfork.org",
            "wondercv.com",
            "ipip.net",
            "tool.lu",
            "sms-activate.org",
            "paper2x.noedgeai.com",
            "keybr.com",
            "jyshare.com",
            "tools.nwumba.cn",
            "www.niupizhiyuan.com",
        ],
    ):
        return "常用工具", "通用效率"
    if contains_any(
        target,
        [
            "console.cloud.tencent.com/cos",
            "aliyun.com/overview",
            "drive.google.com",
            "cloud.siliconflow.cn",
            "autodl.com",
            "my.feishu.cn/drive",
        ],
    ):
        return "常用工具", "云服务与存储"
    if contains_any(
        target,
        [
            "sojson.com/rgb",
            "w3school.com.cn/tags/html_ref_colornames",
            "ipaddress.my",
            "geogebra.org",
        ],
    ):
        return "常用工具", "颜色与辅助"
    if contains_any(target, ["ustc.edu.cn", "ustc.life", "i.ustc.edu.cn"]):
        if contains_any(target, ["yz.ustc.edu.cn", "gradschool.ustc.edu.cn", "yjs.ustc.edu.cn", "yjs1.ustc.edu.cn"]):
            return "校园与USTC", "研究生系统"
        if contains_any(target, ["email.ustc.edu.cn", "mail.ustc.edu", "makebook.ustc.edu.cn", "wvpn.ustc.edu.cn", "job.ustc.edu.cn"]):
            return "校园与USTC", "校园服务"
        return "校园与USTC", "校园门户"
    if contains_any(
        target,
        [
            "claude.ai",
            "chat.qwen.ai",
            "chat.deepseek.com",
            "grok.com",
            "gemini.google.com",
            "kimi.com/",
            "yiyan.baidu.com",
            "yuanbao.tencent.com",
        ],
    ):
        return "AI与Agent", "通用模型"
    if contains_any(
        target,
        [
            "platform.deepseek.com",
            "bigmodel.cn",
            "bailian.console.aliyun.com",
            "opencode.ai",
            "agent.minimaxi.com",
            "rait-09.github.io/obsidian-agent-client",
            "notebooklm.google.com",
            "toolify.ai",
        ],
    ):
        return "AI与Agent", "平台与开发"
    if contains_any(target, ["mcpmarket.cn", "mcp.so", "mcphub.io", "skillhub.club", "copaw", "modelscope.cn/studios/jiexiwang/copaw"]):
        return "AI与Agent", "MCP与Agent生态"
    if contains_any(target, ["metaso.cn", "chatgpt.yundongfang.com", "amz123.com/ai", "ai-bot.cn", "faxianai.com", "lastexam.ai"]):
        return "AI与Agent", "AI导航与发现"
    if contains_any(
        target,
        [
            "scholar.google.com",
            "semanticscholar.org",
            "ncbi.nlm.nih.gov",
            "aminer.cn",
            "researchgate.net",
            "proquest.com",
            "c61.oversea.cnki.net",
            "codeocean.com",
        ],
    ):
        return "学术科研", "检索与数据库"
    if contains_any(
        target,
        [
            "home-for-researchers.com",
            "zotero.org/styles",
            "zotero-chinese.com/styles",
            "dict.cnki.net",
            "typeset.io",
            "acs.org",
            "publish.acs.org",
        ],
    ):
        return "学术科研", "写作与文献"
    if contains_any(
        target,
        [
            "wwpdb.org",
            "rcsb.org",
            "charmm-gui.org",
            "mackerell.umaryland.edu",
            "mdtutorials.com",
            "jerkwin.github.io",
            "cancer.sanger.ac.uk/cosmic",
        ],
    ):
        return "学术科研", "生物与分子模拟"
    if contains_any(
        target,
        [
            "muchong.com",
            "keinsci.com",
            "phys.libretexts.org",
            "z-lib.cv",
        ],
    ):
        return "学术科研", "科研社区与资源"
    if contains_any(target, ["linux.do", "juejin.cn", "github.com", "stackoverflow.com", "weibo.com"]):
        return "开发与技术", "开发社区"
    if contains_any(target, ["runoob.com", "itheima.com", "linux-command-manual", "plotly.com/graphing-libraries"]):
        return "开发与技术", "教程与文档"
    if contains_any(target, ["git-scm.com", "anaconda.org/anaconda/networkx", "plotly.com", "codeocean.com"]):
        return "开发与技术", "工具与平台"
    if contains_any(target, ["ncre-bm.neea.edu.cn", "cet-bm.neea.edu.cn", "toefl.neea.edu.cn", "neea.edu.cn"]):
        return "考试与证书", "官方报名"
    if contains_any(target, ["cltt.org", "ruankao.org.cn", "osta.org.cn"]):
        return "考试与证书", "语言与能力证书"
    if contains_any(target, ["yz.tsinghua.edu.cn", "admission.pku.edu.cn", "grs.zju.edu.cn", "gsao.fudan.edu.cn", "yz.chsi.com.cn"]):
        return "招生与深造", "国内招生"
    if contains_any(target, ["scholarshipdb.net", "nature.com/naturecareers", "academicpositions.com", "jobs.ac.uk/phd", "daad.de", "csc.edu.cn"]):
        return "招生与深造", "海外PhD与奖学金"
    if contains_any(target, ["zhaopin.com", "51job.com", "chinahr.com", "liepin.com", "zhipin.com", "58.com/quanzhizhaopin", "job5156.com", "jobcn.com", "job36.com", "job168.com"]):
        return "求职与招聘", "综合招聘"
    if contains_any(target, ["yingjiesheng.com", "yjbys.com", "211zph.com", "haitou.cc", "shixiseng.com", "qiuzhifangzhou.com"]):
        return "求职与招聘", "校招与实习"
    if contains_any(target, ["iguopin.com", "ncss.cn", "ciiczhaopin.com", "ciicscjob.com", "jobonline.cn", "jybzp.chsi.com.cn", "job.mohrss.gov.cn", "12333.gov.cn"]):
        return "求职与招聘", "央国企与公共就业"
    if contains_any(target, ["job9151.com", "qgsydw.com", "yinhangzhaopin.com", "gaoxiaojob.com", "job910.com", "talent.sciencenet.cn", "21wecan.com", "doctorjob.com.cn", "jobmd.cn", "healthr.com"]):
        return "求职与招聘", "行业招聘"
    if contains_any(target, ["nowcoder.com", "maimai.cn", "jobui.com", "tianyancha.com", "qcc.com"]):
        return "求职与招聘", "求职辅助"
    if contains_any(target, ["gongkaoleida.com", "fenbi.com", "huatu.com", "eoffcn.com", "qzzn.com", "gwy.com", "saduck.top", "bm.scs.gov.cn", "subb.scs.gov.cn"]):
        return "公考与时政", "公考报名与资讯"
    if contains_any(target, ["mohrss.gov.cn", "sasac.gov.cn", "edu.cn/edu/zhao_sheng_kao_shi/gong_wu_yuan", "people.com.cn/gb/88733/115371", "www.chsi.com.cn"]):
        return "公考与时政", "政策与政务"
    if contains_any(target, ["paper.people.com.cn", "banyuetan.org", "tophub.today", "gongkaoleida.com/user/remind"]):
        return "公考与时政", "时政媒体"
    if contains_any(target, ["zhihu.com", "bilibili.com", "17foreign.com"]):
        return "社区与内容", "内容社区"
    if contains_any(target, ["weread.qq.com", "eudic.net", "vocabulary.com", "pdawiki.com", "magazinelib.com", "mypitaya.com"]):
        return "社区与内容", "阅读与语言"
    return "其他网站", "未细分"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_menu(grouped: OrderedDict[str, OrderedDict[str, list[Site]]]) -> str:
    parts = []
    for primary, secondary_map in grouped.items():
        meta = PRIMARY_META[primary]
        parts.extend(
            [
                "                    <li>",
                f'                        <a href="#{meta["id"]}" class="smooth">',
                f'                            <i class="fa {meta["icon"]}"></i>',
                f'                            <span class="title">{primary}</span>',
                "                        </a>",
                "                        <ul>",
            ]
        )
        for secondary in secondary_map:
            parts.extend(
                [
                    "                            <li>",
                    f'                                <a href="#{meta["subs"][secondary]}" class="smooth">',
                    f'                                    <span class="title">{secondary}</span>',
                    "                                </a>",
                    "                            </li>",
                ]
            )
        parts.extend(["                        </ul>", "                    </li>"])
    return "\n".join(parts)


def build_cards(items: list[Site]) -> str:
    cards = []
    for item in items:
        fallback_logo = "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote(item.url, safe="")
        cards.append(
            f"""                <div class="col-sm-3 col-xs-6">
                    <div class="xe-widget xe-conversations box2 label-info" onclick="window.open('{esc(item.url)}', '_blank')" data-toggle="tooltip" data-placement="bottom" title="" data-original-title="{esc(item.url)}">
                        <div class="xe-comment-entry">
                            <a class="xe-user-img site-logo-wrap">
                                <img data-src="{esc(item.logo_url)}" data-fallback="{fallback_logo}" class="lozad site-logo" width="44" height="44" alt="{esc(item.title)}" onerror="if(this.dataset.fallback && this.src !== this.dataset.fallback) {{ this.src = this.dataset.fallback; }}">
                            </a>
                            <div class="xe-comment">
                                <a href="#" class="xe-user-name overflowClip_1">
                                    <strong>{esc(item.title)}</strong>
                                </a>
                                <p class="overflowClip_2">{esc(item.desc)}</p>
                            </div>
                        </div>
                    </div>
                </div>"""
        )
    return "\n".join(cards)


def build_page(sites: list[Site]) -> str:
    grouped: OrderedDict[str, OrderedDict[str, list[Site]]] = OrderedDict()
    for primary, meta in PRIMARY_META.items():
        secondary_map = OrderedDict((secondary, []) for secondary in meta["subs"])
        for site in sites:
            if site.primary == primary:
                secondary_map[site.secondary].append(site)
        secondary_map = OrderedDict((k, v) for k, v in secondary_map.items() if v)
        if secondary_map:
            grouped[primary] = secondary_map

    total = len(sites)
    menu_html = build_menu(grouped)
    content_parts = []
    for primary, secondary_map in grouped.items():
        meta = PRIMARY_META[primary]
        primary_count = sum(len(items) for items in secondary_map.values())
        content_parts.append(
            f"""            <h4 class="text-gray"><i class="linecons-tag" style="margin-right: 7px;" id="{meta["id"]}"></i>{primary} <small>({primary_count})</small></h4>"""
        )
        for secondary, items in secondary_map.items():
            content_parts.append(
                f"""            <div class="section-subtitle" id="{meta["subs"][secondary]}">
                <span>{secondary}</span>
                <small>({len(items)})</small>
            </div>
            <div class="row">
{build_cards(items)}
            </div>
            <br />"""
            )

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="author" content="Codex" />
    <title>我的网址导航</title>
    <meta name="keywords" content="常用网站,网址导航,WebStack,AI,学术,求职,公考,工具">
    <meta name="description" content="从常用网站.md 自动整理生成的个人网址导航页。">
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
        .sidebar-menu .main-menu > li > a {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .sidebar-menu .main-menu > li > a > i {{
            width: 16px;
            text-align: center;
            flex: 0 0 16px;
        }}
        .sidebar-menu .main-menu > li > a .title {{
            display: block;
            flex: 1 1 auto;
            line-height: 1.45;
        }}
        .sidebar-menu .main-menu > li > ul {{
            padding: 4px 0 10px;
        }}
        .sidebar-menu .main-menu > li > ul > li > a {{
            display: flex;
            align-items: center;
            min-height: 34px;
            padding-left: 38px;
            position: relative;
        }}
        .sidebar-menu .main-menu > li > ul > li > a::before {{
            content: "";
            position: absolute;
            left: 22px;
            top: 50%;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.45);
            transform: translateY(-50%);
        }}
        .sidebar-menu .main-menu > li > ul > li > a .title {{
            display: block;
            width: 100%;
            line-height: 1.45;
        }}
        .section-subtitle {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            color: #666;
            font-size: 16px;
            font-weight: 700;
            margin: 10px 0 12px;
            padding-left: 2px;
        }}
        .section-subtitle small {{
            color: #999;
            font-size: 12px;
        }}
        .site-logo-wrap {{
            width: 44px;
            height: 44px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: linear-gradient(180deg, #ffffff, #f5f7fb);
            box-shadow: 0 6px 18px rgba(22, 34, 51, 0.08);
            overflow: hidden;
            flex: 0 0 44px;
        }}
        .site-logo {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            padding: 6px;
        }}
    </style>
</head>
<body class="page-body">
    <div class="page-container">
        <div class="sidebar-menu toggle-others fixed">
            <div class="sidebar-menu-inner">
                <header class="logo-env">
                    <div class="logo">
                        <a href="./indexnew2.html" class="logo-expanded">
                            <img src="./assets/images/logo@2x.png" width="100%" alt="" />
                        </a>
                        <a href="./indexnew2.html" class="logo-collapsed">
                            <img src="./assets/images/logo-collapsed@2x.png" width="40" alt="" />
                        </a>
                    </div>
                    <div class="mobile-menu-toggle visible-xs">
                        <a href="#" data-toggle="sidebar">
                            <i class="fa-bars"></i>
                        </a>
                    </div>
                </header>
                <ul id="main-menu" class="main-menu">
{menu_html}
                </ul>
            </div>
        </div>
        <div class="main-content">
            <nav class="navbar user-info-navbar" role="navigation">
                <ul class="user-info-menu left-links list-inline list-unstyled">
                    <li class="hidden-sm hidden-xs">
                        <a href="#" data-toggle="sidebar">
                            <i class="fa-bars"></i>
                        </a>
                    </li>
                </ul>
                <ul class="user-info-menu right-links list-inline list-unstyled">
                    <li class="hidden-sm hidden-xs">
                        <a href="./cn/index.html" target="_blank">
                            <i class="fa-external-link"></i> 原版页面
                        </a>
                    </li>
                </ul>
            </nav>
{chr(10).join(content_parts)}
            <footer class="main-footer sticky footer-type-1">
                <div class="footer-inner">
                    <div class="footer-text">
                        Generated from <strong>{esc(SRC.name)}</strong> on 2026-03-08
                    </div>
                    <div class="go-up">
                        <a href="#" rel="go-top">
                            <i class="fa-angle-up"></i>
                        </a>
                    </div>
                </div>
            </footer>
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


def main() -> None:
    sites = parse_sites()
    html_text = build_page(sites)
    OUT.write_text(html_text, encoding="utf-8")
    print(f"Generated: {OUT}")
    print(f"Source: {SRC.name}")
    print(f"Unique sites: {len(sites)}")
    for primary, meta in PRIMARY_META.items():
        count = sum(1 for site in sites if site.primary == primary)
        if count:
            print(f"{primary}: {count}")


if __name__ == "__main__":
    main()

