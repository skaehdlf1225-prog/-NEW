#!/usr/bin/env python3
"""
단타 검색 데이터 생성기
전 종목 시세를 받아 단타 지표를 계산하고 docs/data.json 으로 저장합니다.
GitHub Actions 가 장중 5분마다 실행 → 앱(index.html)이 이 파일을 읽어 화면에 표시.

로컬 테스트:  pip install finance-datareader pykrx pandas && python scan.py
"""
import json
import os
from datetime import datetime, timedelta, timezone

import pandas as pd

KST = timezone(timedelta(hours=9))
OUT = os.path.join(os.path.dirname(__file__), "docs", "data.json")
MIN_AMOUNT_EOK = 10      # 거래대금 10억 미만은 저장 안 함 (단타 불가 수준)


def fetch_today() -> pd.DataFrame:
    import FinanceDataReader as fdr

    df = fdr.StockListing("KRX").rename(columns={
        "Code": "code", "Name": "name", "Market": "market",
        "Open": "open", "High": "high", "Low": "low", "Close": "close",
        "Changes": "change", "Volume": "volume", "Amount": "amount",
        "Marcap": "marcap"})
    df = df[df["market"].isin(["KOSPI", "KOSDAQ", "KOSDAQ GLOBAL"])].copy()
    df["market"] = df["market"].replace({"KOSDAQ GLOBAL": "KOSDAQ"})
    df["prev_close"] = df["close"] - df["change"]
    return df


def prev_volume() -> pd.Series:
    """전 영업일 거래량. 실패하면 빈 Series (거래량 배수만 빠짐)."""
    try:
        from pykrx import stock

        d = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")
        d = stock.get_nearest_business_day_in_a_week(d, prev=True)
        return pd.concat([stock.get_market_ohlcv(d, market=m)["거래량"]
                          for m in ("KOSPI", "KOSDAQ")])
    except Exception as e:
        print("전일 거래량 실패:", e)
        return pd.Series(dtype=float)


def tick_size(p: float) -> int:
    for lim, t in ((2000, 1), (5000, 5), (20000, 10), (50000, 50),
                   (200000, 100), (500000, 500)):
        if p < lim:
            return t
    return 1000


def upper_limit(prev: float) -> int:
    raw = prev * 1.3
    t = tick_size(raw)
    return int(raw // t * t)


def build(df: pd.DataFrame, pv: pd.Series) -> list[dict]:
    df = df[(df["prev_close"] > 0) & (df["volume"] > 0) & (df["open"] > 0)].copy()
    df["amount_eok"] = df["amount"] / 1e8
    df = df[df["amount_eok"] >= MIN_AMOUNT_EOK]

    df["rate"] = (df["close"] / df["prev_close"] - 1) * 100
    df["gap"] = (df["open"] / df["prev_close"] - 1) * 100
    df["from_open"] = (df["close"] / df["open"] - 1) * 100
    df["from_high"] = (df["close"] / df["high"] - 1) * 100
    df["range"] = (df["high"] / df["low"] - 1) * 100
    df["vol_ratio"] = df["volume"] / df["code"].map(pv)
    df["limit"] = df["prev_close"].map(upper_limit)
    df["spac"] = df["name"].str.contains("스팩")
    df["pref"] = ~df["code"].astype(str).str.endswith("0")

    s = (df["amount_eok"].clip(0, 1000) / 1000 * 30
         + df["rate"].clip(0, 30) / 30 * 25
         + df["vol_ratio"].fillna(1).clip(0, 10) / 10 * 20
         + (df["from_high"].clip(-10, 0) + 10) / 10 * 15
         + (df["from_open"] > 0) * 10)
    df["score"] = s.round(0)

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "c": str(r["code"]), "n": r["name"],
            "mk": "P" if r["market"] == "KOSPI" else "Q",   # P=코스피, Q=코스닥
            "p": int(r["close"]), "pc": int(r["prev_close"]),
            "o": int(r["open"]), "h": int(r["high"]), "l": int(r["low"]),
            "r": round(r["rate"], 2), "g": round(r["gap"], 2),
            "fo": round(r["from_open"], 2), "fh": round(r["from_high"], 2),
            "rg": round(r["range"], 2),
            "a": round(r["amount_eok"], 1),
            "mc": None if pd.isna(r["marcap"]) else round(r["marcap"] / 1e8),
            "vr": None if pd.isna(r["vol_ratio"]) else round(r["vol_ratio"], 2),
            "lim": int(r["limit"]), "sc": int(r["score"]),
            "sp": bool(r["spac"]), "pf": bool(r["pref"]),
        })
    return rows


def main():
    df = fetch_today()
    pv = prev_volume()
    rows = build(df, pv)
    data = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "total": int(len(df)),
        "has_vol": not pv.empty,
        "stocks": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{data['updated']}  {len(rows)}종목 저장 → {OUT}")


if __name__ == "__main__":
    main()
