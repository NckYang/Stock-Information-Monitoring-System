# 股市資訊監測系統 Stock Monitoring Dashboard

這是一個使用 Python 與 Streamlit 製作的股市資訊監控工具。使用者可以自訂股票清單，查看當日漲跌幅、近 7 日與近 30 日報酬率、K 線圖、累積報酬走勢、新聞列表，並可設定 Discord 價格提醒。新聞情緒分析可串接 Google Gemini API，讓模型依新聞標題、摘要與內文片段判斷正向、中性或負向。

## 主要功能

- 自選股監控：支援台股 `.TW`、上櫃 `.TWO`、美股代號與指數代號，例如 `^TWII`。
- 報酬率比較：顯示當日漲跌幅、近 7 日平均/累積報酬率、近 30 日平均/累積報酬率。
- 視覺化圖表：使用 Plotly 顯示近 30 日 K 線圖與累積報酬曲線。
- 新聞情緒分析：抓取 Google News RSS 新聞，並可使用 Gemini API 判斷新聞情緒。
- Discord 價格提醒：可設定高價/低價門檻，觸發時推送 Discord Webhook。

## 專案檔案

- `app.py`：Streamlit 主程式。
- `requirements.txt`：Python 套件清單。
- `start.bat`：Windows 一鍵啟動腳本。
- `Monitor.png`：專案展示截圖。
- `.streamlit/secrets.toml.example`：Streamlit secrets 範例，不要放真正金鑰。

## Windows 一鍵執行

1. 安裝 Python 3.9 以上版本。
2. 安裝時請勾選 `Add Python to PATH`。
3. 將整個專案資料夾複製到另一台電腦。
4. 雙擊 `start.bat`。
5. 第一次執行會自動建立虛擬環境並安裝套件，之後會啟動 Streamlit。

啟動後瀏覽器通常會開啟：

```text
http://localhost:8501
```

## 手動執行方式

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Windows Command Prompt:

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Gemini API Key 設定

如果沒有設定 Gemini API key，程式仍然可以執行，但新聞情緒會改用簡單關鍵字備援判斷。

如果要使用 Gemini 模型判斷新聞情緒，請到 Google AI Studio 申請 API key：

```text
https://aistudio.google.com/app/apikey
```

### 方法一：用環境變數

PowerShell:

```powershell
$env:GEMINI_API_KEY="你的 Gemini API Key"
streamlit run app.py
```

Command Prompt:

```bat
set GEMINI_API_KEY=你的 Gemini API Key
streamlit run app.py
```

macOS / Linux:

```bash
export GEMINI_API_KEY="你的 Gemini API Key"
streamlit run app.py
```

### 方法二：用 Streamlit secrets

1. 建立資料夾 `.streamlit`。
2. 複製 `.streamlit/secrets.toml.example` 為 `.streamlit/secrets.toml`。
3. 把內容改成：

```toml
GEMINI_API_KEY = "你的 Gemini API Key"
```

注意：`.streamlit/secrets.toml` 不要上傳到 GitHub，也不要交給別人。

## 切換 Gemini 模型

預設模型是：

```text
gemini-1.5-flash
```

可用環境變數切換：

```powershell
$env:GEMINI_MODEL="gemini-1.5-flash"
streamlit run app.py
```

## Discord Webhook 設定

Discord Webhook 是選用功能。若不設定，價格提醒只會顯示在網頁上。

簡要流程：

1. 到 Discord 伺服器的頻道設定。
2. 選擇「整合」或「Integrations」。
3. 建立 Webhook。
4. 複製 Webhook URL。
5. 在網站側邊欄貼上 Webhook URL，並設定價格提醒。

## 常見問題

### 找不到 python

請重新安裝 Python，並勾選 `Add Python to PATH`。

### 套件安裝失敗

請確認網路正常，並嘗試：

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Gemini 情緒分析沒有啟用

請確認是否有設定 `GEMINI_API_KEY`。沒有設定時，程式會自動使用關鍵字備援判斷。

### 其他電腦無法執行

請確認以下檔案都有複製：

- `app.py`
- `requirements.txt`
- `start.bat`
- `README.md`

不要只複製 `app.py`，因為缺少套件清單和啟動腳本會造成執行困難。
