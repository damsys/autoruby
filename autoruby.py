import csv
import logging
import sys

from janome.tokenizer import Tokenizer


logging.basicConfig(level=logging.WARN, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# コマンドライン引数の取得
if len(sys.argv) != 5:
    print(
        "Usage: python autoruby.py SOURCE.csv OUTPUT.csv 対象カラム名 ふりがなカラム名",
        file=sys.stderr,
    )
    sys.exit(1)

input_csv = sys.argv[1]
output_csv = sys.argv[2]
target_col = sys.argv[3]
furi_col = sys.argv[4]

t = Tokenizer()


def to_hiragana(text):
    # 形態素解析して読み仮名を平仮名で返す
    return (
        "".join([token.reading for token in t.tokenize(text)])
        .replace("・", "")
        .replace("*", "")
    )


def katakana_to_hiragana(text):
    # Unicode のカタカナブロックをひらがなブロックに変換
    result = []
    for char in text:
        code = ord(char)
        # カタカナ（全角）の範囲: U+30A1〜U+30F6 → ひらがな U+3041〜U+3096
        # ただし、 「ヶ」だけは例外的な対応として「が」に変換する。
        if code == 0x30F6:
            result.append("が")
        elif 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(char)
    return ''.join(result)


def get_furigana(text):
    # janome で読みを取得し、ひらがなに変換
    reading = "".join(
        [
            token.reading if token.reading != "*" else token.surface
            for token in t.tokenize(text)
        ]
    )
    return katakana_to_hiragana(reading)


# CSV 読み込み
with open(input_csv, "r", encoding="cp932", newline="") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = rows[0]
try:
    target_idx = header.index(target_col)
except ValueError:
    print(f"指定されたカラム名が見つかりません: {target_col}", file=sys.stderr)
    sys.exit(1)

# ふりがなカラムの位置を決定
if furi_col in header:
    furi_idx = header.index(furi_col)
else:
    header.append(furi_col)
    furi_idx = len(header) - 1

# データ行の処理
new_rows = [header]
for row in rows[1:]:
    # 行が短い場合は拡張
    if len(row) < len(header):
        row += [""] * (len(header) - len(row))
    target_text = row[target_idx]
    furigana = get_furigana(target_text)
    row[furi_idx] = furigana
    new_rows.append(row)

# CSV 書き込み
with open(output_csv, "w", encoding="cp932", newline="") as f:
    writer = csv.writer(f)
    for row in new_rows:
        try:
            writer.writerow(row)
        except Exception:
            logger.error("Error writing CSV: %s", row)
            raise
 