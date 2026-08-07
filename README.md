# Finance Crawler Capability Probe

這個 repository 用可重現的 GitHub Actions 實驗，回答三個問題：

1. Crawl4AI 在 GitHub-hosted Ubuntu runner 能否正常啟動 Chromium？
2. 財經來源的 browser、JSON API、RSS 三條路徑，各自能成功到哪裡？
3. 失敗能否被正確分為封鎖、限流、TLS、逾時、robots 或內容不足，而不是誤報成功？

## 驗收契約

- 每個啟用來源必須產生一筆結果，不可靜默遺失。
- HTTP 200 不等於成功；內容長度及必要關鍵字也必須通過。
- 結果只保存 metadata、SHA-256 與最多 500 字元預覽，不鏡像完整受版權保護內容。
- browser 路徑必須啟用 robots.txt 檢查。
- workflow 目前只支援手動觸發；接上通知以前不建立排程。
- SEC EDGAR 需要帶姓名與聯絡 email 的 User-Agent，未配置前保持停用。

## 預定來源矩陣

來源定義在 `sources.yaml`，包含台灣官方資料、社群討論，以及 Crawl4AI 財經範例網站。每個來源都聲明 topic、transport、最低內容門檻與必要詞。

## 本機開發

```bash
python -m pip install -e '.[test]'
python -m playwright install chromium
pytest --cov --cov-report=term-missing
finance-crawler-probe --manifest sources.yaml --output artifacts
```

本專案將 Crawl4AI 明確列為核心依賴並保留上游歸屬；Crawl4AI 專案採 Apache 2.0 加額外 attribution 條款，公開使用時應依其 LICENSE 要求標示。
