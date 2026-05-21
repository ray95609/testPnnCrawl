#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# 公視新聞網相關 URL 定義
BASE_HTML_URL = "https://news.pts.org.tw/hotTopic/{}"
HOT_TOPIC_API = "https://news.pts.org.tw/api/hotTopic/{}"
NEWS_API = "https://news.pts.org.tw/api/news/{}"

# 請求 Headers 設定，模擬瀏覽器以避免被阻擋
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_hot_topic_meta(hot_topic_id):
    """
    從 API 取得專題基本資料
    """
    url = HOT_TOPIC_API.format(hot_topic_id)
    print(f"[INFO] 正在取得專題基本資料 API: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] 取得專題基本資料失敗: {e}")
        return None

def extract_news_ids_from_html(hot_topic_id):
    """
    請求專題 HTML 頁面，並解析出所有關聯的新聞 ID
    """
    url = BASE_HTML_URL.format(hot_topic_id)
    print(f"[INFO] 正在請求專題首頁 HTML: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] 請求專題網頁失敗: {e}")
        return []
        
    soup = BeautifulSoup(response.text, "html.parser")
    news_ids = []
    
    # 方法 1：解析 HTML 中的 JSON-LD (最準確，通常包含 ItemList 關聯新聞)
    print("[INFO] 嘗試解析 ld+json ...")
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            # 尋找 ItemList 類型
            if data.get("@type") == "ItemList":
                elements = data.get("itemListElement", [])
                for item in elements:
                    item_url = item.get("url", "")
                    # 比對網址中的 article/{news_id}
                    match = re.search(r"article/(\d+)", item_url)
                    if match:
                        news_ids.append(int(match.group(1)))
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue

    # 方法 2：若 JSON-LD 沒有抓到任何連結，則備用解析網頁中的所有 article 連結
    if not news_ids:
        print("[WARNING] 未從 ld+json 找到關聯新聞，改為解析網頁中的文章連結...")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            match = re.search(r"/article/(\d+)", href)
            if match:
                news_ids.append(int(match.group(1)))

    # 去除重複的 ID 並保持原有順序
    unique_ids = list(dict.fromkeys(news_ids))
    print(f"[INFO] 解析完成，共找到 {len(unique_ids)} 篇關聯新聞 ID: {unique_ids}")
    return unique_ids

def get_news_detail(news_id):
    """
    從新聞 API 取得單篇新聞的詳細內容
    """
    url = NEWS_API.format(news_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] 取得新聞 {news_id} 詳細資料失敗: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="公視新聞專題與關聯新聞爬蟲")
    parser.add_argument("--id", type=int, default=655, help="專題的 ID (例如 655)")
    parser.add_argument("--output", type=str, default=None, help="輸出的 JSON 檔名 (預設為 output_{id}.json)")
    args = parser.parse_args()

    hot_topic_id = args.id
    output_filename = args.output if args.output else f"output_{hot_topic_id}.json"

    print(f"=== 開始執行爬蟲，目標專題 ID: {hot_topic_id} ===")

    # 1. 取得專題 Metadata
    topic_data = get_hot_topic_meta(hot_topic_id)
    if not topic_data:
        print("[FATAL] 無法取得專題主體資料，爬蟲終止。")
        sys.exit(1)

    # 2. 解析專題 HTML 獲取關聯新聞 IDs
    news_ids = extract_news_ids_from_html(hot_topic_id)
    if not news_ids:
        print("[WARNING] 沒有找到任何關聯新聞。")
        related_news_list = []
    else:
        # 3. 批次取得新聞詳細內容
        related_news_list = []
        total = len(news_ids)
        for index, news_id in enumerate(news_ids, 1):
            print(f"[INFO] 正在下載新聞詳情 ({index}/{total}): ID {news_id}")
            news_detail = get_news_detail(news_id)
            if news_detail:
                related_news_list.append(news_detail)
            
            # 禮貌延遲，避免過度頻繁請求
            time.sleep(0.5)

    # 4. 整合資料
    # 將爬回來的新聞存入 topics 欄位（覆寫），同時也保留在 related_news 欄位提供多元使用
    topic_data["topics"] = related_news_list
    topic_data["related_news"] = related_news_list

    # 5. 輸出成 JSON 檔案
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(topic_data, f, ensure_ascii=False, indent=2)
        print(f"\n[SUCCESS] 資料爬取與整合完成！已輸出至: {output_filename}")
    except Exception as e:
        print(f"[ERROR] 儲存 JSON 檔案失敗: {e}")

if __name__ == "__main__":
    main()
