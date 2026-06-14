# 使用Python 3.12 官方映像檔
FROM python:3.12

# 創建映像檔工作區域,後續動作都將以此為相對路徑展開, 並且所有命令都將在此目錄內執行
WORKDIR /app

# 複製 requirements.txt 檔案到容器，將本機專案的 requirements.txt 複製到容器的 /app 目錄下。
COPY requirements.txt .

# 安裝依賴
#--no-cache-dir 參數可減少安裝過程中產生的暫存檔案，減少 Docker 映像大小。
RUN pip install --no-cache-dir -r requirements.txt

# COPY twstock /app, 將本機專案目錄複製到 Image 中
# 分兩次複製的目的是要符合docker layer設計的目的, 可以加速docker開啟與建立
COPY . .

# 執行命令,開始創建 docker
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]