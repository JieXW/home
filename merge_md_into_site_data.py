from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "WebStackPage.github.io-master"
DEFAULT_MD = ROOT / "常用网站2.md"
DATA_FILE = WEB_DIR / "site-data.js"
APPLY_SCRIPT = ROOT / "apply_site_data.py"

HOUSING_HOSTS = {
    "58.com",
    "beijing.ebaixing.com",
    "bj.fang.ke.com",
    "hf.lianjia.com",
    "m.anjuke.com",
    "www.ziroom.com",
    "ziroom.com",
    "sz.fang.com",
    "qfang.com",
    "www.qfang.com",
    "leyoujia.com",
    "www.leyoujia.com",
    "hf.centanet.com",
    "52mf.com",
    "www.52mf.com",
    "baletu.com",
    "www.baletu.com",
    "tj.zhuge.com",
    "sz.zufun.cn",
    "bj.5i5j.com",
    "sz.zuke.com",
    "shenzhen.fangdd.com",
    "wellcee.com",
    "www.wellcee.com",
    "airbnb.cn",
    "www.airbnb.cn",
    "mayi.com",
    "www.mayi.com",
    "xiaozhu.com",
    "www.xiaozhu.com",
    "douban.com",
    "www.douban.com",
}

SOURCE_URL_OVERRIDES = {
    "https://hr.leyoujia.com/hr_portal/common/redirect?url=/index": "https://www.leyoujia.com/",
    "https://hr.leyoujia.com/hr_portal/common/redirect?url=%2Findex": "https://www.leyoujia.com/",
    "https://www.douban.com/group/308599/?from=tag_all": "https://www.douban.com/group/308599/",
    "https://pan.quark.cn/list#/list/all": "https://pan.quark.cn/",
    "https://pan.baidu.com/disk/main#/index?category=all": "https://pan.baidu.com/",
    "https://wx.mail.qq.com/home/index?sid=zWtJR4xhOFUukWJ5AFQ1ZQAA#/list/1/1": "https://wx.mail.qq.com/",
    "https://mail.google.com/mail/u/0/#inbox": "https://mail.google.com/",
    "https://drive.google.com/drive/home?dmr=1&ec=wgc-drive-%5Bmodule%5D-goto": "https://drive.google.com/drive/my-drive",
    "http://job.mohrss.gov.cn/202008gx/index.jhtml": "http://job.mohrss.gov.cn/202008gx/index.jhtml",
}

TITLE_OVERRIDES = {
    "https://wx.mail.qq.com": "QQ邮箱",
    "https://mail.google.com": "Gmail",
    "https://pan.baidu.com": "百度网盘",
    "https://pan.quark.cn": "夸克网盘",
    "https://colab.research.google.com": "Google Colab",
    "https://www.58.com/zufang": "58同城租房",
    "http://beijing.ebaixing.com": "北京百姓网",
    "https://bj.fang.ke.com/loupan": "北京贝壳新房",
    "https://hf.lianjia.com": "合肥链家",
    "https://m.anjuke.com/bj": "安居客北京",
    "https://www.ziroom.com": "自如",
    "https://sz.fang.com": "房天下深圳",
    "https://www.qfang.com/index.html": "Q房网",
    "https://www.leyoujia.com": "乐有家",
    "https://hf.centanet.com": "合肥中原找房",
    "https://www.52mf.com": "魔方公寓",
    "https://www.baletu.com": "巴乐兔",
    "https://tj.zhuge.com": "天津诸葛找房",
    "https://sz.zufun.cn": "自如友家深圳租房",
    "https://bj.5i5j.com": "我爱我家北京",
    "https://sz.zuke.com": "深圳租客网",
    "https://shenzhen.fangdd.com": "房多多深圳",
    "https://www.wellcee.com": "Wellcee",
    "https://www.airbnb.cn": "爱彼迎",
    "https://www.mayi.com": "蚂蚁短租",
    "https://www.xiaozhu.com": "小猪短租",
    "https://www.douban.com/group/308599": "豆瓣租房小组",
    "https://aizex.net": "Aizex 合租面板",
    "https://mp.weixin.qq.com/s/VytjlpsOe5sqIsqCnmrBVg": "USTC电子证明说明",
    "https://ggfw.rlsbj.cq.gov.cn/wsbm/ksbm/bkui/business/webcenter/home/homeChoice.html": "重庆人社考试报名",
    "https://ggfw.hrss.gd.gov.cn/sydwbk/index.do": "广东事业单位报名系统",
    "http://www.apta.gov.cn": "安徽省人事考试网",
    "http://www.apta.gov.cn/Officer": "安徽人事考试网公务员专题",
    "https://rlsbj.cq.gov.cn": "重庆市人力资源和社会保障局",
    "http://www.cpta.com.cn/index.html": "中国人事考试网",
    "https://m12333.cn/platform/anhui.aspx": "安徽12333",
    "http://www.liuxuehr.com/index.html": "留学人才网",
    "https://www.acabridge.cn": "学术桥",
    "https://lxyc.cscse.edu.cn/index": "国家留学人才就业服务平台",
    "http://gx.51boshi.net": "博士招聘网",
    "https://www.gxrcyj.com": "高校人才引进网",
    "http://chinazhigui.com/h-nd-3351.html": "博士人才政策汇总",
    "https://www.gaoxiaojob.com/daily.html": "高校人才网每日职位",
    "https://www.acabridge.cn/yczc/zxzc": "学术桥引才政策",
    "https://www.zhaopinhui.net": "大学生招聘会网",
    "https://ggfw.hrss.gd.gov.cn/recruitment/internet/main": "广东公共求职招聘服务平台",
    "https://www.gov.cn": "中国政府网",
}

DESC_OVERRIDES = {
    "https://wx.mail.qq.com": "QQ邮箱网页版入口，支持收发邮件、管理联系人与附件。",
    "https://mail.google.com": "Gmail 邮箱网页版入口，用于收发邮件与管理 Google 邮件账户。",
    "https://pan.baidu.com": "百度网盘，提供文件同步、分享与在线存储服务。",
    "https://pan.quark.cn": "夸克网盘，提供文件上传、管理、分享与在线存储服务。",
    "https://colab.research.google.com": "Google Colab，在线运行 Python 和 Jupyter Notebook 的开发平台。",
    "https://www.58.com/zufang": "58同城租房，本地租房、整租与合租房源信息平台。",
    "http://beijing.ebaixing.com": "北京百姓网，北京本地生活与分类信息平台，可查看租房与房产信息。",
    "https://bj.fang.ke.com/loupan": "贝壳北京新房平台，查看楼盘、新房房价与房产资讯。",
    "https://hf.lianjia.com": "链家合肥站，提供租房、二手房与房产信息服务。",
    "https://m.anjuke.com/bj": "安居客北京站，提供租房、二手房与新房信息。",
    "https://www.ziroom.com": "自如，提供整租、合租与公寓租住服务。",
    "https://sz.fang.com": "房天下深圳站，提供新房、二手房、租房与房产资讯服务。",
    "https://www.qfang.com/index.html": "Q房网，提供新房、二手房、租房与房产交易信息。",
    "https://www.leyoujia.com": "乐有家房产平台，提供二手房、新房与租房信息服务。",
    "https://hf.centanet.com": "中原找房合肥站，提供租房、二手房与房产信息服务。",
    "https://www.52mf.com": "魔方公寓，提供长租公寓与公寓租住服务。",
    "https://www.baletu.com": "巴乐兔租房平台，提供城市租房、整租与合租房源信息。",
    "https://tj.zhuge.com": "诸葛找房天津站，提供新房、二手房、租房与房价信息。",
    "https://sz.zufun.cn": "深圳租房平台，提供直租、整租与合租房源信息。",
    "https://bj.5i5j.com": "我爱我家北京站，提供租房、二手房与房产信息服务。",
    "https://sz.zuke.com": "深圳租客网，提供公寓、合租与房屋租赁信息。",
    "https://shenzhen.fangdd.com": "房多多深圳站，提供新房、租房与房产交易信息。",
    "https://www.wellcee.com": "Wellcee，提供城市租房、合租与共享居住信息。",
    "https://www.airbnb.cn": "爱彼迎，提供民宿、短租与特色住宿预订服务。",
    "https://www.mayi.com": "蚂蚁短租，提供民宿、公寓与短租房源预订服务。",
    "https://www.xiaozhu.com": "小猪短租，提供民宿、短租与特色住宿服务。",
    "https://www.douban.com/group/308599": "豆瓣租房小组，提供租房交流与房源信息分享。",
    "https://aizex.net": "Aizex 合租面板，用于查看和管理合租房源与居住协作信息。",
    "https://mp.weixin.qq.com/s/VytjlpsOe5sqIsqCnmrBVg": "中国科大研究生电子证明与成绩单下载功能说明。",
    "https://ggfw.rlsbj.cq.gov.cn/wsbm/ksbm/bkui/business/webcenter/home/homeChoice.html": "重庆人社考试报名入口，用于职业考试与招聘考试报名。",
    "https://ggfw.hrss.gd.gov.cn/sydwbk/index.do": "广东省事业单位公开招聘报名系统，提供考生报名与信息查询。",
    "http://www.apta.gov.cn": "安徽省人事考试网，提供考试公告、报名入口与成绩查询。",
    "http://www.apta.gov.cn/Officer": "安徽省公务员与相关考试专题入口。",
    "https://rlsbj.cq.gov.cn": "重庆市人社局官网，提供政策公告、办事服务与考试招聘信息。",
    "http://www.cpta.com.cn/index.html": "中国人事考试网，提供职业资格考试公告、报名与成绩查询。",
    "https://m12333.cn/platform/anhui.aspx": "安徽 12333 人社服务平台，提供社保、人事与就业公共服务入口。",
    "http://www.liuxuehr.com/index.html": "留学人才网，面向海归与高层次人才提供招聘信息。",
    "https://www.acabridge.cn": "学术桥，提供高校、科研机构与高层次人才招聘服务。",
    "https://lxyc.cscse.edu.cn/index": "国家留学人才就业服务平台，聚合央国企与重点单位招聘信息。",
    "http://gx.51boshi.net": "博士招聘网，提供高校、科研院所与高层次人才招聘信息。",
    "https://www.gxrcyj.com": "高校人才引进网，聚合高校人才引进与教师招聘信息。",
    "http://chinazhigui.com/h-nd-3351.html": "各地引进博士人才政策汇总，便于查看人才引进与支持政策。",
    "https://www.gaoxiaojob.com/daily.html": "高校人才网每日职位汇总，查看高校与科研岗位更新。",
    "https://www.acabridge.cn/yczc/zxzc": "学术桥引才政策栏目，汇总各地人才引进政策与资讯。",
    "https://www.zhaopinhui.net": "大学生招聘会网，汇总全国招聘会、校招与应届生求职信息。",
    "https://ggfw.hrss.gd.gov.cn/recruitment/internet/main": "广东公共求职招聘服务平台，提供职位检索、招聘活动与就业服务。",
    "https://www.gov.cn": "中国政府网，中央人民政府门户网站，发布政策文件与政务信息。",
}

LOGO_OVERRIDES = {
    "https://hf.centanet.com": "https://www.google.com/s2/favicons?sz=64&domain_url=https%3A%2F%2Fhf.centanet.com%2F",
    "https://www.leyoujia.com": "https://www.google.com/s2/favicons?sz=64&domain_url=https%3A%2F%2Fwww.leyoujia.com%2F",
}


def load_build_module():
    spec = importlib.util.spec_from_file_location("_build_indexnew2", ROOT / "_build_indexnew2.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load _build_indexnew2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_site_data(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.SITE_DATA\s*=\s*([\s\S]*?);\s*$", text)
    payload = match.group(1) if match else text
    return json.loads(payload)


def write_site_data(path: Path, payload: dict) -> None:
    path.write_text("window.SITE_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def parse_markdown_links(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(r"\[(.*?)\]\((.*?)\)", text, re.S)
    links: list[tuple[str, str]] = []
    for raw_title, raw_url in matches:
        title = raw_title.strip()
        url = raw_url.strip()
        if url.startswith(("http://", "https://")):
            links.append((title, url))
    return links


def normalize_source_url(url: str) -> str:
    return SOURCE_URL_OVERRIDES.get(url.strip(), url.strip())


def canonical_key(build, url: str) -> str:
    return build.stable_url(normalize_source_url(url)).rstrip("/")


def canonical_output_url(url: str) -> str:
    return url + ("/" if urlsplit(url).path == "" else "")


def fallback_logo(url: str) -> str:
    return "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote(url, safe="")


def classify_site(build, stable_url: str, title: str) -> tuple[str, str]:
    host = build.host_of(stable_url)
    if host in HOUSING_HOSTS:
        return "生活服务", "租房与房产"
    if host in {"wx.mail.qq.com", "mail.google.com", "pan.baidu.com", "pan.quark.cn"}:
        return "常用工具", "云服务与存储"
    if host in {"colab.research.google.com"}:
        return "开发与技术", "工具与平台"
    if host in {"ggfw.rlsbj.cq.gov.cn", "ggfw.hrss.gd.gov.cn", "apta.gov.cn"}:
        return "公考与时政", "公考报名与资讯"
    if host in {"rlsbj.cq.gov.cn", "gov.cn", "www.gov.cn", "m12333.cn"}:
        return "公考与时政", "政策与政务"
    if host in {"cpta.com.cn"}:
        return "考试与证书", "官方报名"
    if host in {"liuxuehr.com", "acabridge.cn", "lxyc.cscse.edu.cn", "gx.51boshi.net", "gxrcyj.com", "zhaopinhui.net"}:
        return "求职与招聘", "行业招聘" if host != "zhaopinhui.net" else "校招与实习"
    if stable_url == "https://aizex.net":
        return "生活服务", "租房与房产"
    if stable_url == "https://mp.weixin.qq.com/s/VytjlpsOe5sqIsqCnmrBVg":
        return "校园与USTC", "研究生系统"
    return build.categorize(stable_url, title)


def ensure_template(payload: dict, primary: str, secondary: str) -> None:
    templates = payload.setdefault("templates", {})
    order = payload.setdefault("order", {"primaries": [], "secondaries": {}})
    primaries = order.setdefault("primaries", [])
    secondaries = order.setdefault("secondaries", {})

    if primary not in templates:
        templates[primary] = []
    if secondary and secondary not in templates[primary]:
        templates[primary].append(secondary)

    if primary not in secondaries:
        secondaries[primary] = []
    if secondary and secondary not in secondaries[primary]:
        secondaries[primary].append(secondary)

    if primary not in primaries:
        if "常用工具" in primaries:
            primaries.insert(primaries.index("常用工具") + 1, primary)
        else:
            primaries.append(primary)


def main() -> None:
    md_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_MD
    if not md_path.exists():
        raise SystemExit(f"Markdown file not found: {md_path}")
    if not DATA_FILE.exists():
        raise SystemExit(f"site-data.js not found: {DATA_FILE}")

    build = load_build_module()
    payload = parse_site_data(DATA_FILE)
    sites = payload.setdefault("sites", [])
    existing_map = {}
    for site in sites:
        url = site.get("url", "")
        if not url:
            continue
        existing_map[canonical_key(build, url)] = site
    next_id = max((int(site.get("id", 0)) for site in sites), default=0) + 1

    added = 0
    updated = 0
    for raw_title, raw_url in parse_markdown_links(md_path):
        stable = canonical_key(build, raw_url)
        if not stable:
            continue

        stable_out = canonical_output_url(stable)
        host = build.host_of(stable)
        fetched_title, fetched_logo = build.fetch_site_meta(stable_out)
        title = (
            TITLE_OVERRIDES.get(stable)
            or build.TITLE_OVERRIDES.get(stable)
            or build.HOST_TITLE_OVERRIDES.get(host)
            or fetched_title
        )
        if not title:
            title = build.simplify_title(raw_title if not build.is_garbled(raw_title) else host, host)

        primary, secondary = classify_site(build, stable, title)
        desc = DESC_OVERRIDES.get(stable) or build.pick_desc(raw_title, title, host, primary, secondary)
        logo_url = LOGO_OVERRIDES.get(stable) or fetched_logo or fallback_logo(stable_out)

        site_payload = {
            "primary": primary,
            "secondary": secondary,
            "title": title,
            "desc": desc,
            "url": stable_out,
            "host": host,
            "logo_url": logo_url,
        }

        existing_site = existing_map.get(stable)
        if existing_site:
            existing_site.update(site_payload)
            updated += 1
        else:
            sites.append({"id": next_id, **site_payload})
            existing_map[stable] = sites[-1]
            next_id += 1
            added += 1

        ensure_template(payload, primary, secondary)

    write_site_data(DATA_FILE, payload)
    subprocess.run([sys.executable, str(APPLY_SCRIPT), str(DATA_FILE)], cwd=str(ROOT), check=True)
    print(f"Merged markdown: {md_path}")
    print(f"Added sites: {added}")
    print(f"Updated sites: {updated}")
    print(f"Updated data: {DATA_FILE}")
    print(f"Updated html: {WEB_DIR / 'indexnew2.html'}")


if __name__ == "__main__":
    main()
