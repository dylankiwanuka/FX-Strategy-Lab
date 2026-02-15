from src.data.loader import DataRequest, download_ohlc
from src.data.cleaning import clean_ohlc

req = DataRequest(
    symbol="EURUSD=X",
    start="2024-01-01",
    end="2024-03-01",
    interval="1d",
)

raw = download_ohlc(req)
clean = clean_ohlc(raw)

print("RAW:", raw.shape, raw.index.min(), raw.index.max())
print("CLEAN:", clean.shape, clean.index.min(), clean.index.max())
print(clean.head())
