# Finance Crawler Capability Probe

這個 repository 用可重現的 GitHub Actions 實驗，回答三個問題：

1. Crawl4AI 在 GitHub-hosted Ubuntu runner 能否正常啟動 Chromium？
2. 財經來源的 browser、JSON API、RSS 三條路徑，直連與合規備援後各自能成功到哪裡？
3. 社群、新聞、官方資料、市場資料與聚合器的能力邊界是否不同？
4. 失敗能否被正確分為封鎖、需認證、限流、TLS、逾時、robots 或內容不足，而不是誤報成功？

## 驗收契約

- 每個啟用來源必須產生一筆結果，不可靜默遺失。
- HTTP 200 不等於成功；內容長度及必要關鍵字也必須通過。
- 同一 job 重複 1–3 次只表示「短時間重抓耐受度」，不稱為長期穩定性；預設只抓一次。
- 報表必須分開 `direct_first_pass` 與 `resolved_first_pass`，不得把直連阻擋與備援救回混為同一百分比。
- 同一社群的 Browser、API、RSS 以 `route_group` 合併，另外報告最終可取得率。
- 結果只保存 metadata、SHA-256 與最多 500 字元預覽，不鏡像完整受版權保護內容。
- browser 路徑必須啟用 robots.txt 檢查。
- workflow 目前只支援手動觸發；接上通知以前不建立排程。
- SEC EDGAR 需要帶姓名與聯絡 email 的 User-Agent，未配置前保持停用。

## 來源矩陣

來源定義在 `sources.yaml`，目前涵蓋台灣與國際社群、開發者社群、新聞、RSS、官方資料 API、市場資料 API，以及 Crawl4AI 財經範例網站。每個來源都聲明 topic、kind、transport、最低內容門檻、必要詞、來源脈絡與選源證據。

熱門社群的選擇依據、能力假設與合規邊界見 [`docs/source-selection.md`](docs/source-selection.md)。實際可用性以 GitHub Actions 產出的 `report.json` 為準，不以本文件或單次本機請求推定。

國外社群的全面矩陣獨立放在 [`foreign-community-sources.yaml`](foreign-community-sources.yaml)，避免官方資料探測與社群平台邊界互相稀釋。它包含可匿名實跑路徑及需要 OAuth、API key、會員或商業授權的 catalog-only 路徑；範圍定義與分層策略見 [`docs/foreign-community-landscape.md`](docs/foreign-community-landscape.md)。GitHub Actions 手動觸發時可選 `core` 或 `foreign_communities` scope。

`worker/` 是限定七個 feed ID 的 Cloudflare RSS relay：只在 GitHub 直連遇到 403、429 或 5xx 時啟用，不接受任意目標 URL，也不追隨上游重導。工作流程透過 repository variable `CF_RELAY_BASE_URL` 注入部署 URL；未設定時仍可重現純 GitHub 直連邊界。

## 本機開發

```bash
python -m pip install -e '.[test]'
python -m playwright install chromium
pytest --cov --cov-report=term-missing
finance-crawler-probe --manifest sources.yaml --output artifacts --repeat 2
CF_RELAY_BASE_URL=https://your-worker.workers.dev \
  finance-crawler-probe --manifest foreign-community-sources.yaml --output artifacts --repeat 1
```

本專案將 Crawl4AI 明確列為核心依賴並保留上游歸屬；Crawl4AI 專案採 Apache 2.0 加額外 attribution 條款，公開使用時應依其 LICENSE 要求標示。
