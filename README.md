# 股市資訊系統 Stock Monitoring System

這是一個使用 Python 與 Streamlit 製作的股市資訊監控網站。使用者可以查看自選股的當日漲跌幅、近 7 日與近 30 日報酬率、K 線圖、累積報酬走勢、相關新聞情緒分析，並可設定價格警報。

目前版本已支援部署到 Streamlit Cloud。部署完成後，使用者可以直接用網址開啟網站，不需要安裝 Python，也不需要下載專案。

## 線上使用方式

請使用以下網址開啟網站：

```text
https://stock-information-monitoring-systemgit-em3jeru9rbsdfvrxrvk6bh.streamlit.app/
```

使用者只需要用手機、平板或電腦瀏覽器開啟這個網址即可使用，不需要安裝任何套件。

## 主要功能

- 自選股監控：支援台股 `.TW`、上櫃 `.TWO`、美股代號與指數代號，例如 `^TWII`。
- 報酬率比較：顯示當日漲跌幅、近 7 日平均/累積報酬率、近 30 日平均/累積報酬率。
- 視覺化圖表：使用 Plotly 顯示近 30 日 K 線圖與累積報酬曲線。
- 新聞情緒分析：抓取 Google News RSS 新聞，並使用 Gemini API 判斷正向、中性或負向。
- 判斷來源顯示：新聞表格會顯示該則新聞是由 Gemini API 判斷，或是因 API key、配額、格式等問題改用備援。
- 自動清除新聞快取：每次開啟新的網頁工作階段時，會自動清除一次新聞快取。
- Discord 價格提醒：可設定高價/低價門檻，觸發時推送 Discord Webhook。

## Gemini 配額說明

目前預設模型為：

```text
gemini-3.1-flash-lite
```

Gemini API 可能會受到免費額度、每分鐘請求數或每日請求數限制。

如果新聞表格出現 `HTTP 429`，代表目前 API 配額不足。這不是網站程式錯誤，而是 Google API 暫時拒絕更多請求。

目前程式已做以下保護：

- 每次只分析前 5 則新聞。
- 遇到 `HTTP 429` 後，本輪後續新聞不再繼續呼叫 Gemini API。
- 如果 Gemini 呼叫失敗，會自動改用備援判斷。
- 新聞表格會顯示 `判斷來源`，方便確認是否成功使用 Gemini。

## 專案檔案

- `app.py`：Streamlit 主程式。
- `README.md`：專案說明與使用方式。

## 新聞快取

目前版本會在每次開啟新的網頁工作階段時，自動清除一次新聞快取。左側側邊欄也保留「清除新聞快取」按鈕，方便測試 API key、模型或新聞結果。

## Discord Webhook 設定

Discord Webhook 是選用功能。若不設定，價格提醒只會顯示在網頁上。

設定方式：

1. 到 Discord 伺服器的頻道設定。
2. 選擇 Integrations。
3. 建立 Webhook。
4. 複製 Webhook URL。
5. 在網頁側邊欄貼上 Webhook URL。