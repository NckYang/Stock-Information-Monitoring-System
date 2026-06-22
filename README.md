# 股市資訊系統 Stock Monitoring System

這是一個使用 Python 與 Streamlit 製作的股市資訊監控網站。使用者可以自訂股票清單，查看當日漲跌幅、近 7 日與近 30 日報酬率、K 線圖、累積報酬走勢、新聞列表，並設定價格警報。新聞情緒分析可串接 Google Gemini API，讓模型依新聞標題、摘要與內文片段判斷正向、中性或負向。

目前版本預設使用 `gemini-2.5-flash-lite`，每次分析最多抓取 5 則新聞。若 Gemini API 配額不足或呼叫失敗，程式會自動改用備援判斷，避免整個網站無法使用。

## Windows 一鍵啟動

1. 安裝 Python 3.9 以上版本。
2. 安裝時請勾選 `Add Python to PATH`。
3. 將整個專案資料夾複製到電腦。
4. 設定Gemini API KEY (如果有的話)，若無API KEY則新聞情緒分析會使用備援方法，設定方法詳見下方
4. 雙擊 `start.bat`。
5. 第一次執行會自動建立虛擬環境並安裝套件，之後會啟動 Streamlit。

啟動後瀏覽器通常會開啟：

```text
http://localhost:8501
```

## Gemini API Key 設定

如果沒有設定 Gemini API key，程式仍然可以執行，但新聞情緒會改用備援判斷。

如果要使用 Gemini 模型判斷新聞情緒，請到 Google AI Studio 申請 API key：

```text
https://aistudio.google.com/app/apikey
```

### 使用 Streamlit secrets:

在已建立的資料夾 `.streamlit`中
將 `.streamlit/secrets.toml.example` 改名為 `.streamlit/secrets.toml`，並填入自己的 Gemini API key：

```toml
GEMINI_API_KEY = "你的 Gemini API Key"
GEMINI_MODEL = "gemini-2.5-flash-lite"
```



## Gemini 模型與配額

目前預設模型：

```text
gemini-2.5-flash-lite
```

程式會依序嘗試以下模型：

1. 使用者設定的模型，例如 `gemini-2.5-flash-lite`
2. `gemini-flash-latest`
3. `gemini-2.5-flash`

如果看到 `HTTP 429`，代表 Google API 配額或速率限制不足。這不是程式錯誤，而是目前 API key 的免費額度、每分鐘請求數或每日請求數達到限制。

為了降低配額消耗，目前程式做了以下處理：

- 每次只分析前 5 則新聞。
- 遇到 `HTTP 429` 後，本輪後續新聞不再繼續呼叫 Gemini API。
- 每則新聞表格會顯示 `判斷來源`。
- 如果 Gemini 回覆格式無法解析，會顯示更詳細的原因，例如 `finishReason` 或 `promptFeedback`。

## 主要功能

- 自選股監控：支援台股 `.TW`、上櫃 `.TWO`、美股代號與指數代號，例如 `^TWII`。
- 報酬率比較：顯示當日漲跌幅、近 7 日平均/累積報酬率、近 30 日平均/累積報酬率。
- 視覺化圖表：使用 Plotly 顯示近 30 日 K 線圖與累積報酬曲線。
- 新聞情緒分析：抓取 Google News RSS 新聞，並使用 Gemini API 判斷正向、中性或負向。
- 判斷來源顯示：新聞表格會顯示該則新聞是由 Gemini API 判斷，或是因 API key、配額、格式等問題改用備援。
- 自動清除新聞快取：每次開啟新的網頁工作階段時，會自動清除一次新聞快取，不需要手動按按鈕。
- Discord 價格提醒：可設定高價/低價門檻，觸發時推送 Discord Webhook。
- 跨裝置瀏覽：電腦執行網站後，同一個 Wi-Fi 內的手機也可以用瀏覽器開啟。

## 專案檔案

- `app.py`：Streamlit 主程式。
- `requirements.txt`：Python 套件清單。
- `start.bat`：Windows 一鍵啟動腳本。
- `README.md`：專案說明與執行方式。
- `.streamlit/secrets.toml.example`：Streamlit secrets 範例，不要放真正金鑰。
- `Monitor.png`：系統畫面截圖。



## 新聞快取

新聞情緒分析使用 Streamlit 快取，避免每次互動都重新抓新聞與呼叫 Gemini API。

目前版本會在每次開啟新的網頁工作階段時，自動清除一次新聞快取。左側側邊欄也保留「清除新聞快取」按鈕，方便測試 API key、模型或新聞結果。

## Discord Webhook 設定

Discord Webhook 是選用功能。若不設定，價格提醒只會顯示在網頁上。

設定方式：

1. 到 Discord 伺服器的頻道設定。
2. 選擇 Integrations。
3. 建立 Webhook。
4. 複製 Webhook URL。
5. 在網頁側邊欄貼上 Webhook URL。

## 常見問題

### 找不到 python

請確認已安裝 Python，且安裝時有勾選 `Add Python to PATH`。

### 套件安裝失敗

請確認網路連線正常，並重新執行：

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Gemini 情緒分析沒有啟用

請確認左側側邊欄是否顯示 `已讀取 GEMINI_API_KEY`。如果顯示未讀取，請重新設定環境變數或 `.streamlit/secrets.toml`。

### Gemini 出現 404

通常代表模型名稱不存在或該 API key 無法使用該模型。請確認 `GEMINI_MODEL` 是否為：

```text
gemini-2.5-flash-lite
```

也可以嘗試：

```text
gemini-flash-latest
```

### Gemini 出現 429

代表 API 配額或速率限制不足。可以等待配額重置、減少新聞分析數量、換用其他 API key，或改用備援判斷。



