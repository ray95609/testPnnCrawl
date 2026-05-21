# 公視新聞專題與關聯新聞爬蟲 (PNN Hot Topic Crawler)

一個基於 Python 的輕量級網頁爬蟲，專門用於爬取公視新聞網（PTS News）的**熱門專題**（Hot Topic）基本資訊，並自動解析與下載該專題所有**關聯新聞**的詳細內容。

---

## 🚀 功能特點

- **自動獲取專題資訊**：直接請求公視 API，獲取專題名稱、時間等 metadata。
- **智慧解析關聯新聞**：
  1. 優先解析 HTML 中最精準的 `application/ld+json` (ItemList)。
  2. 若無則採用網頁文章連結備用解析（Regex 解析 `/article/{id}`）。
- **批次新聞詳情下載**：根據解析出的關聯新聞 ID，取得完整的 JSON 規格新聞內容。
- **優雅請求控制**：每次 API 請求間設置 0.5 秒的禮貌性延遲（Politeness delay），保護目標伺服器。
- **完美資料整合**：自動整合專題與新聞資料，輸出為單一精美 JSON 檔。

---

## 🛠️ 開發環境與安裝

### 1. 系統需求
- **Python 3.8+**
- 建議使用虛擬環境（如專案已有的 `.venv`）

### 2. 安裝依賴套件
在專案根目錄下，使用 `pip` 安裝必要的套件：

```bash
pip install -r requirements.txt
```

*主要依賴套件包括：*
- `requests` (發送 HTTP 請求)
- `beautifulsoup4` (解析 HTML 網頁)

---

## 💻 使用方法

本專案提供命令列工具 `crawl_pnn.py`。您可以使用以下參數進行客製化：

### 基本執行（預設專題 ID: 655）
```bash
python crawl_pnn.py
```
執行後將在根目錄生成 `output_655.json` 檔案。

### 自訂專題 ID
若要爬取其他專題（例如 ID 為 680 的專題）：
```bash
python crawl_pnn.py --id 680
```

### 自訂輸出路徑或檔名
```bash
python crawl_pnn.py --id 655 --output my_custom_output.json
```

---

## 📊 輸出 JSON 資料結構說明

爬蟲整合後的 JSON 結構如下：

```json
{
  "id": 655,
  "title": "專題名稱",
  "description": "專題描述...",
  "topics": [
    {
      "id": 123456,
      "title": "關聯新聞標題 1",
      "content": "新聞內文..."
    }
  ],
  "related_news": [
    {
      "id": 123456,
      "title": "關聯新聞標題 1",
      "content": "新聞內文..."
    }
  ]
}
```

> 💡 **備註**：`topics` 與 `related_news` 欄位皆包含相同的關聯新聞詳細內容列表，以相容於不同的資料處理管道。
