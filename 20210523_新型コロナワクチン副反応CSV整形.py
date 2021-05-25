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
from functools import reduce
from itertools import zip_longest
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
　　「そもそもこの症状名は誰がどう語彙を決めているんだろう」等のよく分からない点はあるが・・・。
  参照元: https://www.mhlw.go.jp/content/10906000/000778299.pdf p.8-

  →例えばレベルの話で、「皮疹・発疹・紅斑（発疹|紅斑）」は「皮疹」「発疹（発疹）」「紅斑（紅斑）」というのが考えうる。
  あるいは「発疹（発疹）」「紅斑（紅斑）」のみ残して「皮疹」は消しちゃうとか。
  https://www.mhlw.go.jp/content/10906000/000778302.pdf



"""

# print(frozenset([i for i in map(lambda d: d["No"], input_content) if "\n" in i]))
# 主キー列に\n※が入っていることがある。

tmp_content = []
input_keys = tuple(input_content[0].keys())
note = "No.4611とNo.4842は、同一事例について、接種医療機関（No.4611）及び搬送先医療機関（No.4842）それぞれから副反応疑い報告がなされたもの。資料1-1-1及び1-3における「死亡として報告された事例」においては1件として集計。また、資料1-1-1の集計においては、直接死亡を確認した搬送先医療機関からの報告内容に基づき分類している。"
for d in input_content:
    new_dict = dict()
    for key, value in d.items():
        if key == "No":
            if("\n" in d["No"]):
                new_dict["No"] = d["No"].split("\n")[0]
                new_dict["特記事項"] = note
            else:
                new_dict["No"] = d["No"]
                new_dict["特記事項"] = ""

        elif key == "年齢":
            new_dict["年齢"] = d["年齢"].replace("歳", "")
        else:
            new_dict[key.replace("\n", "")] = value
    tmp_content.append(new_dict)

assert all([d["No"].isdigit() for d in tmp_content]) == True, "No列に数字以外の文字が含まれています。"


"""
for key in tmp_content[0].keys():
    print(key, frozenset(map(lambda d: d[key], tmp_content)))
"""
"""
for key in ["発生日", "転帰日"]:
    values = map(lambda d: set(d[key].split("\n")), tmp_content)
    assert all([re.fullmatch("\d{4}/\d{2}/\d{2}", date) for date in reduce(lambda a, b: a|b, values)]) == True, \
           f"{key}列に日付以外の文字が含まれています。"
"""
"""
symptoms = set()
for d in tmp_content:
    symptoms |= {v.replace("\n", "") for v in re.split("(?<=[）)]\n)", d["症状名（PT名）"])}
assert all([re.fullmatch("[^（(]+[(（][^）)]+[)）]", s) for s in symptoms]) == True, \
           f"{key}列に形式「症状名（PT名）」以外の文字列が含まれています。"

"""

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
assert frozenset(patient_attribute + side_effect_attribute) == frozenset(tmp_content[0].keys()), "新しい列が含まれています。"

split_content = []
for d in tmp_content:
    new_dict = {key: d[key] for key in patient_attribute}
    new_dict["発生日"] = tuple(d["発生日"].split("\n"))
    new_dict["症状名（PT名）"] = tuple(map(lambda v: v.replace("\n", ""),
                                        re.split("(?<=[\)）])\n", d["症状名（PT名）"])))
    new_dict["転帰日"] = tuple(d["転帰日"].split("\n"))
    new_dict["転帰内容"] = tuple(d["転帰内容"].split("\n"))
    split_content.append(new_dict)


output_content = []
for d in split_content:
    patient_dict = {key: d[key] for key in patient_attribute}
    side_effect_values = tuple(map(lambda key: d[key], side_effect_attribute))
    for row in zip_longest(*side_effect_values, fillvalue=""):
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
