import json
import os
import re
import threading
import time

import requests
from bs4 import BeautifulSoup, element


def get_all_corona_list_pages():
    print("get_all_corona_list_pages()")
    response = requests.get("https://www.pref.yamanashi.jp/koucho/coronavirus/info_coronavirus_prevention.html")
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    contents = soup.find("div", {"id": "tmp_contents"})

    items = crawl("info_coronavirus_prevention.html")
    # print("info_coronavirus_prevention: " + str(len(items)))

    for a in contents.find_all("a"):
        href: str = a.get("href")
        if href is None or not href.startswith("/koucho/coronavirus/info_coronavirus_past"):
            continue
        # print(a.text, href[href.rfind("/") + 1:])
        items = {**items, **crawl(href[href.rfind("/") + 1:])}
        time.sleep(1)

    return items


def crawl(filename: str):
    response = requests.get("https://www.pref.yamanashi.jp/koucho/coronavirus/" + filename)
    if response.status_code != 200:
        exit(1)

    soup = BeautifulSoup(response.content, "html.parser")
    contents = soup.find("div", {"id": "tmp_contents"})

    rets = {}
    for h4 in contents.find_all("h4"):
        title = h4.text
        htmls = []
        for tag in h4.next_elements:
            if not isinstance(tag, element.Tag):
                continue
            if tag.name == "h4" or tag.name == "h3":
                break
            if tag.has_attr("class") and tag["class"][0] == "left":
                break
            if tag.name != "p":
                continue
            htmls.append(str(tag))

        symptom = get_symptom_date(htmls)
        details = get_details(htmls)

        m = re.match(r"県内([0-9]+)例目第([0-9]+)報", title)
        if m is not None:
            if m.group(1) not in rets:
                rets[m.group(1)] = {}
            rets[m.group(1)][m.group(2)] = {
                "title": title,
                "num": m.group(2),
                "symptom": symptom,
                "details": details,
                "htmls": htmls,
                "texts": list(map(lambda x: strip_tags(x).strip(), htmls))
            }
        else:
            if "other" not in rets:
                rets["other"] = {}
            rets["other"][title] = {
                "title": title,
                "num": None,
                "symptom": symptom,
                "details": details,
                "htmls": htmls,
                "texts": list(map(lambda x: strip_tags(x).strip(), htmls))
            }

    return rets


def get_details(texts: list):
    details = {
        "age": None,  # 年代
        "gender": None,  # 性別
        "residential_area": None,  # 居住地
        "living_area": None,  # 生活圏
        "occupation": None  # 職種
    }
    for text in texts:
        if details["age"] is None:
            details["age"] = get_regex_search_content(re.compile(r"年代[:：](.+)"), strip_tags(text))
        if details["gender"] is None:
            details["gender"] = get_regex_search_content(re.compile(r"性別[:：](.+)"), strip_tags(text))
        if details["residential_area"] is None:
            details["residential_area"] = get_regex_search_content(re.compile(r"居住地[:：](.+)"), strip_tags(text))
        if details["living_area"] is None:
            details["living_area"] = get_regex_search_content(re.compile(r"生活圏[:：](.+)"), strip_tags(text))
        if details["occupation"] is None:
            details["occupation"] = get_regex_search_content(re.compile(r"職業[:：](.+)"), strip_tags(text))

    return details


def strip_tags(text: str):
    p = re.compile(r"<[^>]*?>")
    return p.sub("", text)


def get_regex_search_content(regex, text):
    m = regex.search(text)
    if m is None:
        return None

    return m.group(1)


def get_symptom_date(texts: list):
    for text in texts:
        match = re.search(r"([0-9]+)月([0-9]+)日(.+)", text)
        if match is None:
            continue
        month = match.group(1)
        day = match.group(2)
        txt = match.group(3)

        if is_symptom(txt):
            return {"month": month, "day": day}


def is_symptom(txt):
    for text in [
        "発症",
        "鼻汁",
        "発熱",
        "咽頭痛",
        "咳",
        "異常",
        "倦怠感",
        "頭重感",
        "違和感",
        "頭痛",
        "悪寒",
        "鼻閉",
        "息苦しさ",
        "関節痛",
        "筋肉痛"
    ]:
        if text in txt:
            return True
    return False
