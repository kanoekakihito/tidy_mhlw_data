"""
１）データソース
第58回厚生科学審議会予防接種・ワクチン分科会副反応検討部会、令和３年度第５回薬事・食品衛生審議会薬事分科会医薬品等安全対策部会安全対策調査会（合同開催）　資料
https://mhlw.go.jp/stf/newpage_18527.html

資料１－１－２ 予防接種法に基づく医療機関からの副反応疑い報告状況について（報告症例一覧）
https://www.mhlw.go.jp/content/10906000/000778300.pdf

２）IMABARI ZINE(@imabarizine)さんによる加工済みデータ
https://drive.google.com/file/d/1MUOKR0u8i_vkeG6NO4EaUrCgAqPgOWnn/view

＊加工時ソースはhttps://twitter.com/imabarizine/status/1395369121034866690
2021/05/23 22:48時点で確認したコード　ここから：

import camelot
import pandas as pd

tables = http://camelot.read_pdf("data.pdf", pages="2-end", split_text=True)

dfs = [table.df for table in tables]

df = pd.concat(dfs)

df.to_csv("data.csv", encoding="utf_8_sig", index=False, header=False)
...ここまで


３）本コード。2をインプットにして整然データを書き出します。


"""


import csv
import re
from tkinter.filedialog import askopenfilename, asksaveasfilename


input_filepath = askopenfilename()
with open(input_filepath, encoding="utf-8-sig") as input_file:
    input_content = [d for d in csv.DictReader(input_file)]
"""
調べた結果、
１）発生日、症状名(PT名)、転帰日、転帰内容の列は各C個の値が格納されている。これはすべての列で同行内なら値数Cが合致した。
２）２行だけNo（おそらく主キー）の列にNo（\n）※印の行を見つける。
  ※印の内容は備考で、
  「※１ No.4611とNo.4842は、同一事例について、接種医療機関（No.4611）及び搬送先医療機関（No.4842）それぞれから副反応疑い報告がなされたもの。
  資料1-1-1及び1-3における「死亡として報告された事例」においては1件として集計。
  また、資料1-1-1の集計においては、直接死亡を確認した搬送先医療機関からの報告内容に基づき分類している。」
  ・・・とのこと。勝手に触っていいのか分からないので手つかずにする。
３）単位「歳」はどう考えても平均取ったり等には邪魔。外す。
４）PT名とかSOCとかいうのは語彙が統一されているようだ（MedDRA）。上位カテゴリSOCと下位カテゴリPTとかいう風に見える。
    参考：https://www.meddra.org/how-to-use/support-documentation/japanese
    参考：https://admin.new.meddra.org/sites/default/files/guidance/file/intguide_24_0_Japanese.pdf
    上位概念SOCに対して、PTは複数のSOCに属するようなツリー型構造をしているようだ。
    
不明点）
１）PT名と症状名は列を分割すべきか？
２）列「症状名(PT名)」の値「そう痒症（そう痒症|そう痒症）」と値「そう痒症（そう痒症|そう痒症|そう痒症）」の違い。
    |は単なる区切り文字？順序に意味はあるか？繰り返し回数で強調などの意味はあるか？
　　列「症状名(PT名)」の値「悪心・嘔吐（悪心|嘔吐）」と値「悪心・嘔吐（嘔吐|悪心）」の違い。
３）列「症状名(PT名)」の値「皮疹・発疹・紅斑（発疹|紅斑）」は分解？そのまま？
　　分解するとしたら「皮疹（発疹）」「発疹（発疹）」「紅斑（発疹）」「皮疹（紅斑）」「発疹（紅斑）」「紅斑（紅斑）」でいいのか？

    →資料を見る限り複数の症状が１カテゴリに集約されていたりするようだ。
  例）皮疹・発疹・紅斑はもともと３つくらいのカテゴリだったのが１つにまとまっているらしい。
  とはいえ、症状名の語彙や
　　「そもそもこの症状名は誰がどう語彙を決めて誰が『これだな』と決めているんだろう」等のよく分からない点はあるが・・・。
  参照元: https://www.mhlw.go.jp/content/10906000/000778299.pdf p.8-

  →例えばレベルの話で、「皮疹・発疹・紅斑（発疹|紅斑）」は「皮疹」「発疹（発疹）」「紅斑（紅斑）」というのが考えうる。
  https://www.mhlw.go.jp/content/10906000/000778302.pdf

４）4611と4842は同一事例のため、ＩＤを統一した方が好ましいのかもしれないが・・・よく分からないのに手を加えるのはまずい気がする。


"""
tmp_content = []
input_keys = tuple(input_content[0].keys())
for d in input_content:
    if "\n" in d["No"]:
        d["特記事項"] = ""
        "No.4611とNo.4842は、"
        "同一事例について、接種医療機関（No.4611）及び搬送先医療機関（No.4842）それぞれから"
        "副反応疑い報告がなされたもの。"
        "資料1-1-1及び1-3における「死亡として報告された事例」においては1件として集計。"
        "また、資料1-1-1の集計においては、直接死亡を確認した搬送先医療機関からの報告内容に基づき分類している。"
        d["No"] = d["No"].split("\n")[0]
    else:
        d["特記事項"] = ""
    new_dict = dict()
    for key in input_keys + ("特記事項",):
        new_dict[key.replace("\n", "")] = d[key]
    new_dict["年齢"] = new_dict["年齢"].replace("歳", "")
    tmp_content.append(new_dict)

patient_attribute = (
    "No",
    "年齢",
    "性別",
    "接種日",
    "接種から発生までの日数",
    "ワクチン名",
    "製造販売業者",
    "ロット番号",
    "因果関係（報告医評価）",
    "重篤度（報告医評価）",
    "特記事項"
)
side_effect_attribute = ("発生日", "症状名（PT名）", "転帰日", "転帰内容")
output_content = []
for d in tmp_content:
    patient_dict = {key: d[key] for key in patient_attribute}
    side_effect_values = [
        d["発生日"].split("\n"),
        re.split("(?<=）)\n", d["症状名（PT名）"]),
        d["転帰日"].split("\n"),
        d["転帰内容"].split("\n")
        ]
    for row in zip(*side_effect_values):
        side_efect_dict = dict(zip(side_effect_attribute, map(lambda v: v.replace("\n", ""), row)))
        output_dict = dict()
        output_dict.update(patient_dict)
        output_dict.update(side_efect_dict)
        output_content.append(output_dict)

output_filepath = asksaveasfilename()
with open(output_filepath, mode="w", encoding="utf-8-sig") as output_file:
    csvfile = csv.DictWriter(output_file, output_content[0].keys(), lineterminator="\n")
    csvfile.writeheader()
    csvfile.writerows(output_content)
