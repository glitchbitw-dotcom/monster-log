import json
import random
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ===== 基本設定 =====
SAVE_FILE = Path(__file__).parent / "save.json"
MAX_LEVEL = 99
POINTS_PER_LEVEL = 10  # レベルアップでもらえるポイント（Lv29まで）
POINTS_STEPS = [(60, 20), (30, 15)]  # (このレベル以上, もらえるポイント)
STAT_CAP = {"hp_max": 3000, "mp_max": 999, "atk": 999, "dfn": 999, "spd": 999}  # 自分のモンスターの上限
EXP_RATE = 2 / 3  # もらえる経験値の倍率
ENEMY_GROW = 0.2  # 敵の1レベルごとの伸び（Lv30まで）
ENEMY_GROW_HIGH = 0.15  # 敵の1レベルごとの伸び（Lv31から）
RARE_RATE = 0.03  # レア枠の出現率
AUTO_INTERVAL = 1.0  # 自動周回で1回進むごとの待ち時間（秒）
LINEUP_SIZE = 8  # エリアに入るたびに選ばれる出現モンスターの数
# 探索で起きること（合計100%）
EXPLORE_EVENTS = {"モンスター": 73, "アイテム": 7, "けいけん": 10, "なにもなし": 10}
assert sum(EXPLORE_EVENTS.values()) == 100
EVOLVE_RATE = 1.2  # 進化したときの能力の倍率
BOX_SIZE = 20  # 1箱に入る数
BOX_COUNT = 5  # 箱の数
PARTY_MAX = BOX_SIZE * BOX_COUNT  # なかまの最大数（100体）
CATCH_BOOST = 1.1  # つかまえたモンスターの能力の倍率（野生よりちょっと強く）
TEAM_MAX = 3  # 探索に連れて行けるパーティーの数
AUTO_SWITCH = 0.2  # 自動周回：HPがこの割合以下で次のなかまに交代
BENCH_EXP = 0.5
BOSS_BOOST = {"hp_max": 1.6, "atk": 1.25, "dfn": 1.15, "spd": 1.15}  # ボスの強さ
LOSE_GOLD = 0.1  # 全滅したときに落とすお金の割合
GOLD_RATE = 1.5  # 戦闘でもらえるお金の倍率
GENTLE_GAP = 8  # てかげん：先頭が敵よりこのレベル以上高いときだけ使える
GENTLE_MP = 5  # てかげんで使うMP
CATCH_AREA_BONUS = 10  # 先のエリアを1つ開放するごとに、前のエリアのモンスターの捕獲率 +10%  # 控えのなかまがもらうけいけんの割合
PUBLIC_MODE = True  # 公開版：セーブはファイルに書かず、遊ぶ人ごとに「書き出す／読み込む」で手元に保存する
DEMO_MODE = False  # デモ版：自分のモンスターのHP・MPが減らない（False で通常に戻る）

# 左が右に強い（最後の水は最初の火に強い）
ELEMENTS = ["火", "草", "土", "雷", "水"]
ELEMENT_COLORS = {"火": "#c0583f", "草": "#4f8a4b", "土": "#8a6d3b", "雷": "#b8952b", "水": "#3b6ea8", "全": "#5a4a7a"}
ALL_ELEMENT = "全"  # 全属性：相性の有利・不利がない（ボス専用）
PREFIX = {"火": "ファイヤー", "草": "リーフ", "土": "ロック", "雷": "サンダー", "水": "アクア"}
STAT_NAMES = {"hp_max": "HP", "mp_max": "MP", "atk": "こうげき", "dfn": "ぼうぎょ", "spd": "すばやさ"}
POINT_VALUE = {"hp_max": 3, "mp_max": 2, "atk": 1, "dfn": 1, "spd": 1}  # 1ポイントで上がる量

# ===== モンスター（属性5 × 種族60 = 300体 ＋ レア専用5種族 = 25体） =====
# 種族ごとの得意な能力（2つ）
TYPES = {
    "スライム": ("hp_max", "dfn"), "ラット": ("spd", "atk"), "バット": ("spd", "atk"),
    "ラビット": ("spd", "hp_max"), "フロッグ": ("hp_max", "spd"),
    "バード": ("spd", "atk"), "スネーク": ("atk", "spd"), "フォックス": ("spd", "atk"),
    "モール": ("dfn", "atk"), "ビートル": ("dfn", "atk"), "スパイダー": ("atk", "spd"),
    "リザード": ("atk", "hp_max"), "クラブ": ("dfn", "hp_max"), "ゴブリン": ("atk", "hp_max"),
    "ボア": ("hp_max", "atk"), "ゴーレム": ("dfn", "hp_max"), "キャット": ("spd", "atk"),
    "ウルフ": ("spd", "atk"), "ディア": ("spd", "hp_max"), "ホーク": ("spd", "atk"),
    "オウル": ("dfn", "spd"), "インプ": ("atk", "spd"), "フェアリー": ("spd", "dfn"),
    "タートル": ("hp_max", "dfn"), "シャーク": ("atk", "spd"), "ゴースト": ("spd", "dfn"),
    "マンティス": ("atk", "spd"), "スコーピオン": ("atk", "dfn"), "ナイト": ("dfn", "atk"),
    "ベア": ("hp_max", "atk"), "ホース": ("spd", "hp_max"), "ライオン": ("atk", "hp_max"),
    "タイガー": ("atk", "spd"), "イーグル": ("spd", "atk"), "ガーゴイル": ("dfn", "atk"),
    "ドラゴン": ("atk", "hp_max"), "キメラ": ("atk", "dfn"), "ワイバーン": ("spd", "atk"),
    "グリフォン": ("spd", "dfn"), "フェニックス": ("hp_max", "spd"),
    # v2.7で追加した20種族
    "ビー": ("spd", "atk"), "バタフライ": ("spd", "hp_max"), "ワーム": ("hp_max", "atk"), "マミー": ("dfn", "hp_max"),
    "クロコダイル": ("atk", "hp_max"), "ウィスプ": ("spd", "dfn"), "マンドレイク": ("hp_max", "dfn"),
    "ペンギン": ("dfn", "hp_max"), "イエティ": ("hp_max", "atk"), "マンモス": ("hp_max", "dfn"),
    "ハーピー": ("spd", "atk"), "ミノタウロス": ("atk", "hp_max"), "マーマン": ("atk", "spd"),
    "ジェリー": ("hp_max", "dfn"), "セイレーン": ("spd", "dfn"), "スフィンクス": ("dfn", "atk"),
    "ミミック": ("dfn", "atk"), "アヌビス": ("atk", "spd"), "エンジェル": ("hp_max", "spd"), "ヴァルキリー": ("atk", "spd"),
    # レア専用（レアとしてだけ出る）
    "カーバンクル": ("dfn", "spd"), "ケットシー": ("spd", "atk"), "ユニコーン": ("spd", "hp_max"),
    "キリン": ("spd", "atk"), "ケルベロス": ("atk", "hp_max"),
}
RARE_TYPES = ["カーバンクル", "ケットシー", "ユニコーン", "キリン", "ケルベロス"]
ELEMENT_BONUS = {"火": ("atk", 1), "草": ("hp_max", 2), "土": ("dfn", 1), "雷": ("spd", 1), "水": ("hp_max", 3)}

# 進化の姿（3つ＝2回進化、2つ＝1回進化）
EVO = {
    "スライム": ["スライム", "キングスライム"], "ラット": ["ラット", "ビッグラット"],
    "バット": ["バット", "ヴァンパイアバット"], "ラビット": ["ラビット", "ホーンラビット"],
    "フロッグ": ["フロッグ", "トードキング"], "バード": ["バード", "グランバード"],
    "スネーク": ["スネーク", "サーペント", "ナーガ"], "フォックス": ["フォックス", "シルバーフォックス", "キュウビ"],
    "モール": ["モール", "ドリルモール"], "ビートル": ["ビートル", "キングビートル"],
    "スパイダー": ["スパイダー", "タランチュラ", "アラクネ"], "リザード": ["リザード", "リザードマン", "リザードキング"],
    "クラブ": ["クラブ", "キングクラブ"], "ゴブリン": ["ゴブリン", "ホブゴブリン", "ゴブリンロード"],
    "ボア": ["ボア", "ワイルドボア"], "ゴーレム": ["ゴーレム", "アイアンゴーレム", "タイタン"],
    "キャット": ["キャット", "パンサー"], "ウルフ": ["ウルフ", "ダイアウルフ", "フェンリル"],
    "ディア": ["ディア", "エルク"], "ホーク": ["ホーク", "ファルコン"],
    "オウル": ["オウル", "セージオウル"], "インプ": ["インプ", "デーモン", "アークデーモン"],
    "フェアリー": ["フェアリー", "ピクシー", "ティターニア"], "タートル": ["タートル", "アーマータートル", "アイランドタートル"],
    "シャーク": ["シャーク", "メガロドン"], "ゴースト": ["ゴースト", "レイス", "リッチ"],
    "マンティス": ["マンティス", "ブレードマンティス"], "スコーピオン": ["スコーピオン", "デススコーピオン"],
    "ナイト": ["ナイト", "パラディン", "ホーリーナイト"], "ベア": ["ベア", "グリズリー"],
    "ホース": ["ホース", "ペガサス"], "ライオン": ["ライオン", "キングレオ"],
    "タイガー": ["タイガー", "サーベルタイガー"], "イーグル": ["イーグル", "グランイーグル"],
    "ガーゴイル": ["ガーゴイル", "グレーターガーゴイル"], "ドラゴン": ["ドラゴン", "グランドラゴン", "エンシェントドラゴン"],
    "キメラ": ["キメラ", "マンティコア"], "ワイバーン": ["ワイバーン", "ドレイク", "ワイアーム"],
    "グリフォン": ["グリフォン", "ロイヤルグリフォン"], "フェニックス": ["フェニックス", "ネオフェニックス"],
    "ビー": ["ビー", "キラービー", "クイーンビー"], "バタフライ": ["バタフライ", "モルフォ"],
    "ワーム": ["ワーム", "サンドワーム", "ギガントワーム"], "マミー": ["マミー", "ファラオ"],
    "クロコダイル": ["クロコダイル", "キングクロコ"], "ウィスプ": ["ウィスプ", "ウィルオウィスプ"],
    "マンドレイク": ["マンドレイク", "アルラウネ"], "ペンギン": ["ペンギン", "エンペラーペンギン"],
    "イエティ": ["イエティ", "サスカッチ"], "マンモス": ["マンモス", "ギガマンモス"],
    "ハーピー": ["ハーピー", "ハーピークイーン"], "ミノタウロス": ["ミノタウロス", "アステリオス"],
    "マーマン": ["マーマン", "トリトン", "ポセイドン"], "ジェリー": ["ジェリー", "マンオウォー"],
    "セイレーン": ["セイレーン", "ローレライ"], "スフィンクス": ["スフィンクス", "アンドロスフィンクス"],
    "ミミック": ["ミミック", "パンドラ"], "アヌビス": ["アヌビス", "オシリス"],
    "エンジェル": ["エンジェル", "アークエンジェル", "セラフィム"], "ヴァルキリー": ["ヴァルキリー", "ブリュンヒルデ"],
    "カーバンクル": ["カーバンクル", "ジュエルビースト"], "ケットシー": ["ケットシー", "キャットキング"],
    "ユニコーン": ["ユニコーン", "スレイプニル"], "キリン": ["キリン", "ゴッドキリン"],
    "ケルベロス": ["ケルベロス", "ヘルケルベロス", "ガルム"],
}
EVO_LEVELS = {3: [25, 70], 2: [50]}

# 技：(1つ目の技, 2つ目の技, 2つ目の種類)  名前は「属性＋技」になる
MOVES = {
    "スライム": ("タックル", "リジェネ", "heal"), "ラット": ("ニブル", "ラッシュ", "attack"),
    "バット": ("ソニック", "ドレイン", "heal"), "ラビット": ("キック", "ステップ", "buff"),
    "フロッグ": ("タン", "スプラッシュ", "attack"), "バード": ("ウィング", "ストーム", "attack"),
    "スネーク": ("バイト", "スクイーズ", "attack"), "フォックス": ("フェイント", "ミラージュ", "buff"),
    "モール": ("ディグ", "ドリル", "attack"), "ビートル": ("ホーン", "ガード", "buff"),
    "スパイダー": ("ネット", "ポイズン", "attack"), "リザード": ("テイル", "バースト", "attack"),
    "クラブ": ("シザー", "シェル", "buff"), "ゴブリン": ("スラッシュ", "ウォークライ", "buff"),
    "ボア": ("チャージ", "スタンピード", "attack"), "ゴーレム": ("パンチ", "フォートレス", "buff"),
    "キャット": ("スクラッチ", "ハント", "attack"), "ウルフ": ("ファング", "ハウル", "buff"),
    "ディア": ("アントラー", "ヒール", "heal"), "ホーク": ("ダイブ", "ゲイル", "attack"),
    "オウル": ("フェザー", "ウィズダム", "buff"), "インプ": ("ショット", "カース", "attack"),
    "フェアリー": ("ダスト", "ブレッシング", "heal"), "タートル": ("シェルバッシュ", "リカバー", "heal"),
    "シャーク": ("ジョー", "メイルストロム", "attack"), "ゴースト": ("タッチ", "ホラー", "attack"),
    "マンティス": ("カッター", "ギロチン", "attack"), "スコーピオン": ("スティング", "デスニードル", "attack"),
    "ナイト": ("ランス", "シールド", "buff"), "ベア": ("クロー", "ハンマー", "attack"),
    "ホース": ("ストンプ", "ギャロップ", "attack"), "ライオン": ("クラッシュ", "ロア", "buff"),
    "タイガー": ("ブレイド", "レイジ", "attack"), "イーグル": ("タロン", "スカイダイブ", "attack"),
    "ガーゴイル": ("ストーン", "アイギス", "buff"), "ドラゴン": ("ブレス", "メテオ", "attack"),
    "キメラ": ("トライバイト", "カオス", "attack"), "ワイバーン": ("エアロ", "テンペスト", "attack"),
    "グリフォン": ("ストライク", "ロイヤルウィング", "attack"), "フェニックス": ("フレア", "リバース", "heal"),
    "ビー": ("ニードル", "スウォーム", "attack"), "バタフライ": ("リンプン", "ヒーリング", "heal"),
    "ワーム": ("グラインド", "アースクエイク", "attack"), "マミー": ("バンデージ", "カタコンベ", "buff"),
    "クロコダイル": ("スナップ", "デスロール", "attack"), "ウィスプ": ("フラッシュ", "ファントム", "attack"),
    "マンドレイク": ("ルート", "スクリーム", "attack"), "ペンギン": ("スライド", "アイスアーマー", "buff"),
    "イエティ": ("ナックル", "アバランチ", "attack"), "マンモス": ("タスク", "アースブレイク", "attack"),
    "ハーピー": ("シャウト", "トルネード", "attack"), "ミノタウロス": ("アックス", "バーサーク", "buff"),
    "マーマン": ("トライデント", "タイダルウェイブ", "attack"), "ジェリー": ("テンタクル", "リフレッシュ", "heal"),
    "セイレーン": ("ボイス", "セレナーデ", "heal"), "スフィンクス": ("リドル", "オラクル", "buff"),
    "ミミック": ("チョンプ", "トラップ", "attack"), "アヌビス": ("ジャッジ", "デスゲート", "attack"),
    "エンジェル": ("ホーリー", "サンクチュアリ", "heal"), "ヴァルキリー": ("スピア", "ラグナ", "attack"),
    "カーバンクル": ("ジュエル", "リフレクト", "buff"), "ケットシー": ("パウ", "ファンタジア", "attack"),
    "ユニコーン": ("ホーリーホーン", "キュア", "heal"), "キリン": ("ライトニング", "テンライ", "attack"),
    "ケルベロス": ("トリプルファング", "ヘルフレイム", "attack"),
}
SKILL1 = {"kind": "attack", "power": 1.6, "mp": 5}
SKILL2 = {"attack": {"kind": "attack", "power": 2.5, "mp": 15}, "heal": {"kind": "heal", "mp": 12}, "buff": {"kind": "buff", "mp": 10}}
# 能力アップの技：上がる能力・上がる割合・効く攻撃の回数（最大3回）
BUFFS = {
    "ラビット": {"stats": ["spd", "atk"], "rate": 0.3, "turns": 2},
    "フォックス": {"stats": ["atk", "spd"], "rate": 0.25, "turns": 3},
    "ビートル": {"stats": ["dfn"], "rate": 0.5, "turns": 3},
    "クラブ": {"stats": ["dfn"], "rate": 0.4, "turns": 2},
    "ゴブリン": {"stats": ["atk"], "rate": 0.4, "turns": 2},
    "ゴーレム": {"stats": ["dfn", "atk"], "rate": 0.3, "turns": 3},
    "ウルフ": {"stats": ["atk", "spd"], "rate": 0.35, "turns": 2},
    "オウル": {"stats": ["dfn", "spd"], "rate": 0.25, "turns": 3},
    "ナイト": {"stats": ["atk", "dfn"], "rate": 0.3, "turns": 3},
    "ライオン": {"stats": ["atk"], "rate": 0.5, "turns": 2},
    "ガーゴイル": {"stats": ["dfn"], "rate": 0.6, "turns": 1},
    "マミー": {"stats": ["dfn"], "rate": 0.45, "turns": 2},
    "ペンギン": {"stats": ["dfn"], "rate": 0.4, "turns": 3},
    "ミノタウロス": {"stats": ["atk"], "rate": 0.45, "turns": 2},
    "スフィンクス": {"stats": ["atk", "dfn"], "rate": 0.3, "turns": 3},
    "カーバンクル": {"stats": ["dfn", "spd"], "rate": 0.35, "turns": 2},
}
assert all(MOVES[t][2] == "buff" for t in BUFFS) and all(t in BUFFS for t in MOVES if MOVES[t][2] == "buff")
assert all(b["turns"] <= 3 for b in BUFFS.values())
# 敵が技を使う確率（敵はMPなし）：種族ごとに8〜20%
_RATES = [0.08, 0.11, 0.14, 0.17, 0.20]
SKILL_RATE = {t: _RATES[i % 5] for i, t in enumerate(MOVES)}

_all_moves = [w for a, b, _ in MOVES.values() for w in (a, b)]
assert len(_all_moves) == len(set(_all_moves)), "技の名前が重なっている"
assert set(TYPES) == set(EVO) == set(MOVES) and all(len(v) in EVO_LEVELS for v in EVO.values())
_all_forms = [f for v in EVO.values() for f in v]
assert len(_all_forms) == len(set(_all_forms)), "進化の名前が重なっている"


def build_species():
    species = {}
    for t, strong in TYPES.items():
        for el, pre in PREFIX.items():
            s = {"element": el, "type": t, "mp_max": 20}
            for key, base in [("hp_max", 40), ("atk", 10), ("dfn", 10), ("spd", 10)]:
                if key in strong:
                    rate = 1.25 if key == "hp_max" else 1.35
                else:
                    rate = 0.9 if key == "hp_max" else 0.85
                s[key] = round(base * rate)
            bkey, bval = ELEMENT_BONUS[el]
            s[bkey] += bval
            species[pre + t] = s
    # 最初の5体は個別に調整
    starters = {
        "ファイヤードラゴン": (40, 14, 8, 10),
        "リーフフォックス": (44, 10, 10, 10),
        "ロックゴーレム": (46, 10, 14, 6),
        "サンダーウルフ": (36, 11, 8, 15),
        "アクアタートル": (52, 10, 10, 8),
    }
    for name, (hp, atk, dfn, spd) in starters.items():
        species[name].update({"hp_max": hp, "atk": atk, "dfn": dfn, "spd": spd})
    return species


SPECIES = build_species()

# 種族のグループ（ずかん・ボックスの「種族」）
GROUPS = {
    "猫獣種": ["キャット", "ライオン", "タイガー", "ケットシー"],
    "狼獣種": ["ウルフ", "フォックス", "ケルベロス"],
    "鼠獣種": ["ラット", "ラビット", "モール"],
    "巨獣種": ["ベア", "ボア", "マンモス", "イエティ", "ミノタウロス"],
    "蹄獣種": ["ディア", "ホース", "ユニコーン", "キリン"],
    "鳥獣種": ["バード", "ホーク", "オウル", "イーグル", "ペンギン", "ハーピー"],
    "巨蟲種": ["ビートル", "スパイダー", "マンティス", "スコーピオン", "ビー", "バタフライ", "ワーム"],
    "水獣種": ["フロッグ", "クラブ", "タートル", "シャーク", "ジェリー", "クロコダイル"],
    "鱗獣種": ["スネーク", "リザード"],
    "ドラゴン種": ["ドラゴン", "ワイバーン"],
    "幻獣種": ["キメラ", "グリフォン", "フェニックス", "スフィンクス", "カーバンクル"],
    "精霊種": ["スライム", "フェアリー", "ウィスプ", "マンドレイク"],
    "神霊種": ["インプ", "ゴースト", "マミー", "アヌビス", "ガーゴイル", "バット", "ミミック", "ゴーレム"],
    "亜人種": ["ゴブリン", "ナイト", "マーマン", "セイレーン", "エンジェル", "ヴァルキリー"],
}
GROUP_OF = {t: g for g, ts in GROUPS.items() for t in ts}
assert set(GROUP_OF) == set(TYPES) and sum(len(v) for v in GROUPS.values()) == len(TYPES), "グループ分けがずれている"
GROUP_ORDER = list(GROUPS) + ["ボス"]

# ===== ボス（200体とは別の専用モンスター・エリアに1体） =====
# 名前 → 属性・能力のもと(HP, こうげき, ぼうぎょ, すばやさ)・専用技
BOSSES = {
    "ハラッパオオウサギ": {"element": "草", "base": (46, 10, 9, 14), "move": ("ふみならし", "attack", 1.8)},
    "モリノオオジカ": {"element": "草", "base": (46, 12, 10, 12), "move": ("もりのいやし", "heal", None)},
    "イワクイムカデ": {"element": "土", "base": (46, 11, 13, 9), "move": ("いわのよろい", "buff", None)},
    "イカズチワシ": {"element": "雷", "base": (38, 14, 8, 15), "move": ("らいめいおとし", "attack", 2.0)},
    "ミズチ": {"element": "水", "base": (42, 13, 10, 12), "move": ("うずしお", "attack", 2.0)},
    "カザンリュウ": {"element": ALL_ELEMENT, "base": (62, 18, 11, 10), "move": ("ようがんのいぶき", "attack", 2.2)},
    "イセキノマモリビト": {"element": ALL_ELEMENT, "base": (66, 21, 17, 14), "move": ("こだいのいかり", "buff", None)},
    "ミツバチジョオウ": {"element": "草", "base": (44, 11, 9, 14), "move": ("じょおうのはり", "attack", 1.8)},
    "スナクジラ": {"element": "土", "base": (54, 11, 12, 8), "move": ("すなあらし", "attack", 1.9)},
    "ヌマノオオガエル": {"element": "水", "base": (50, 12, 11, 11), "move": ("ぬまのいやし", "heal", None)},
    "ユキオオカミ": {"element": "水", "base": (44, 14, 9, 15), "move": ("ふぶきのきば", "attack", 2.0)},
    "カマイタチ": {"element": "雷", "base": (40, 16, 9, 17), "move": ("しんくうぎり", "attack", 2.1)},
    "ウミノオオダコ": {"element": "水", "base": (60, 16, 13, 11), "move": ("たこつぼのかまえ", "buff", None)},
    "ソラクジラ": {"element": "雷", "base": (66, 16, 13, 11), "move": ("らいうんのしお", "attack", 2.2)},
    "テンクウノオウ": {"element": ALL_ELEMENT, "base": (68, 17, 15, 15), "move": ("ほしふるさばき", "attack", 2.4)},
}
BOSS_SKILL_RATE = 0.12  # ボスが専用技を使う確率
GROUP_OF.update({_name: "ボス" for _name in BOSSES})
for _name, _b in BOSSES.items():
    _hp, _atk, _dfn, _spd = _b["base"]
    SPECIES[_name] = {"element": _b["element"], "type": _name, "mp_max": 20, "hp_max": _hp, "atk": _atk, "dfn": _dfn, "spd": _spd}
    EVO[_name] = [_name]  # ボスは進化しない
    SKILL_RATE[_name] = BOSS_SKILL_RATE
BUFFS["イワクイムカデ"] = {"stats": ["dfn"], "rate": 0.5, "turns": 2}
BUFFS["イセキノマモリビト"] = {"stats": ["atk"], "rate": 0.5, "turns": 2}
BUFFS["ウミノオオダコ"] = {"stats": ["dfn"], "rate": 0.5, "turns": 2}
EVO_LEVELS[1] = []
# 前のバージョンのボス → 新しいボス（倒した回数を引きつぐ）
OLD_BOSSES = {
    "ファイヤースライム": "ハラッパオオウサギ", "リーフスパイダー": "モリノオオジカ", "ファイヤーゴーレム": "イワクイムカデ",
    "サンダーホーク": "イカズチワシ", "アクアシャーク": "ミズチ", "ファイヤーライオン": "カザンリュウ",
    "ファイヤーフェニックス": "イセキノマモリビト",
}
# ===== 性格（ポイントを振ったときの伸び方） =====
# 名前 → (伸びやすい能力, 伸びにくい能力)。伸びやすいは1.5倍、伸びにくいは0.5倍
NATURES = {
    "ゆうかん": ("atk", "spd"), "いじっぱり": ("atk", "mp_max"), "ずぶとい": ("dfn", "atk"), "しんちょう": ("dfn", "spd"),
    "おくびょう": ("spd", "atk"), "せっかち": ("spd", "dfn"), "がんばりや": ("hp_max", "spd"), "おおらか": ("hp_max", "mp_max"),
    "かしこい": ("mp_max", "hp_max"), "まじめ": (None, None),
}
NATURE_UP, NATURE_DOWN = 1.5, 0.5
# 性格で変わる最終進化：種族 → (別の最終進化, 条件の性格, さらに1割上がる能力)
BRANCH = {
    "スライム": ("ジャイアントスライム", ("ゆうかん", "いじっぱり"), "atk"),
    "フォックス": ("テンコ", ("かしこい",), "mp_max"),
    "ゴーレム": ("フォートレスゴーレム", ("ずぶとい", "しんちょう"), "dfn"),
    "ウルフ": ("ハティ", ("おくびょう", "せっかち"), "spd"),
    "フェアリー": ("オベロン", ("かしこい", "おおらか"), "mp_max"),
    "ドラゴン": ("カオスドラゴン", ("ゆうかん", "いじっぱり"), "atk"),
}
BRANCH_BOOST = 1.1
BRANCH_NATURE_WEIGHT = 1 / 3  # 進化先が変わる性格は、ほかの性格の3分の1の出やすさ（その種族だけ）
assert all(n in NATURES for _, ns, _ in BRANCH.values() for n in ns)


def nature_mult(m, key):
    up, down = NATURES.get(m.get("nature", "まじめ"), (None, None))
    return NATURE_UP if key == up else (NATURE_DOWN if key == down else 1.0)


def roll_nature(t):
    """ランダムな性格（進化先が変わる種族は、その性格だけ出にくい）"""
    rare = BRANCH[t][1] if t in BRANCH else ()
    names = list(NATURES)
    return random.choices(names, weights=[BRANCH_NATURE_WEIGHT if n in rare else 1 for n in names])[0]


def is_branch(t, stage, nature):
    return t in BRANCH and stage == len(EVO[t]) - 1 and nature in BRANCH[t][1]


# ずかん：姿ごとに1体（属性×種族×進化の姿 ＋ ボス）。姿の名前 → (種族の名前, 進化の段階)
FORM_INFO = {}
for _t in TYPES:
    for _stage, _form in enumerate(EVO[_t]):
        for _el, _pre in PREFIX.items():
            FORM_INFO[_pre + _form] = (_pre + _t, _stage)
    if _t in BRANCH:
        for _el, _pre in PREFIX.items():
            FORM_INFO[_pre + BRANCH[_t][0]] = (_pre + _t, len(EVO[_t]) - 1)
for _name in BOSSES:
    FORM_INFO[_name] = (_name, 0)
DEX_ORDER = [PREFIX[e] + f for t in TYPES for e in ELEMENTS
             for f in EVO[t] + ([BRANCH[t][0]] if t in BRANCH else [])] + list(BOSSES)  # 進化の流れの順（進化前→進化1→進化2→別の進化）
assert len(DEX_ORDER) == len(set(DEX_ORDER)) == len(FORM_INFO)

STARTERS = ["ファイヤードラゴン", "リーフフォックス", "ロックゴーレム", "サンダーウルフ", "アクアタートル"]

# ===== アイテム =====
# kind：hp＝HP回復 / mp＝MP回復 / seed＝能力がずっと上がる / net＝つかまえる / key＝エリア開放
# net の値：(HP満タンのときの確率%, HPが残りわずかのときの確率%, つかまえやすいレベルの上限)
ITEMS = {
    "きずぐすり": ("hp", 15), "いいきずぐすり": ("hp", 40), "すごいきずぐすり": ("hp", 100), "まんたんのくすり": ("hp", 9999),
    "まりょくのみず": ("mp", 10), "いいまりょくのみず": ("mp", 25), "すごいまりょくのみず": ("mp", 40), "まりょくのしずく": ("mp", 9999),
    "ちからのたね": ("seed", ("atk", 2)), "まもりのたね": ("seed", ("dfn", 2)),
    "すばやさのたね": ("seed", ("spd", 2)), "いのちのたね": ("seed", ("hp_max", 6)), "まりょくのたね": ("seed", ("mp_max", 4)),
    "ふつうのネット": ("net", (10, 60, 20)), "いいネット": ("net", (15, 70, 50)), "すごいネット": ("net", (20, 80, 99)),
    "湖のカギ": ("key", None), "火山の通行証": ("key", None), "しんでんのカギ": ("key", None),
    "そらのはね": ("key", None), "遺跡の石板": ("key", None), "てんくうのかぎ": ("key", None),
}


def item_effect(name):
    kind, value = ITEMS[name]
    if kind in ("hp", "mp"):
        label = "HP" if kind == "hp" else "MP"
        return f"{label}全回復" if value >= 9999 else f"{label} +{value}"
    if kind == "seed":
        return f"{STAT_NAMES[value[0]]}がずっと +{value[1]}"
    if kind == "net":
        return f"モンスターをつかまえる（〜Lv.{value[2]}向け、戦闘中に使う）"
    if kind == "mat":
        return f"モンスターのドロップ品（売値 {value}G、装備の材料にもなる）"
    if kind == "equip":
        return f"装備：{equip_text(name)}（育成タブで進化したモンスターに付ける）"
    return "エリア開放に使う"


# ショップ：名前 → (値段, 並ぶようになるエリア番号)
SHOP = {
    "きずぐすり": (10, 0), "まりょくのみず": (10, 0),
    "いいきずぐすり": (40, 3), "いいまりょくのみず": (40, 3),
    "すごいきずぐすり": (150, 7), "すごいまりょくのみず": (150, 7),
    "ふつうのネット": (50, 0), "いいネット": (200, 3), "すごいネット": (600, 7),
    "まんたんのくすり": (800, 10), "まりょくのしずく": (600, 10),
}
SHOP_MAX = 99  # 1回で買える・売れる最大数

# ===== 装備（進化したモンスターに1つ付けられる。各装備は1つまで持てる） =====
EQUIPS = {
    "ビートルヘルム": {"stats": {"dfn": 8}, "gold": 150, "mats": {"ビートルのつの": 3}},
    "ゴブリンクラブ": {"stats": {"atk": 8}, "gold": 150, "mats": {"ゴブリンのこんぼう": 3}},
    "フェアリーのペンダント": {"stats": {"mp_max": 30}, "gold": 400, "mats": {"フェアリーのりんぷん": 5}},
    "ホークのかざりばね": {"stats": {"spd": 15}, "gold": 500, "mats": {"ホークのはね": 5}},
    "ウルフファング": {"stats": {"atk": 15, "spd": -5}, "gold": 500, "mats": {"ウルフのきば": 5}},
    "タートルシールド": {"stats": {"dfn": 20, "spd": -5}, "gold": 800, "mats": {"タートルのこうら": 5}},
    "イエティのマント": {"stats": {"hp_max": 120, "spd": -10}, "gold": 1500, "mats": {"イエティのけがわ": 5}},
    "ミノタウロスのおおおの": {"stats": {"atk": 40, "dfn": -15}, "gold": 3000, "mats": {"ミノタウロスのおの": 5}},
    "ドラゴンのよろい": {"stats": {"hp_max": 150, "dfn": 30}, "gold": 10000, "mats": {"ドラゴンのうろこ": 8, "カザンリュウのあかし": 1}},
    "てんしのわ": {"stats": {k: 20 for k in ("hp_max", "mp_max", "atk", "dfn", "spd")}, "gold": 20000,
                 "mats": {"エンジェルのわっか": 5, "テンクウノオウのあかし": 1}},
}
for _n in EQUIPS:
    ITEMS[_n] = ("equip", None)


def equip_text(name):
    stats = EQUIPS[name]["stats"]
    if len(stats) == 5 and len(set(stats.values())) == 1:
        return f"全能力 +{next(iter(stats.values()))}"
    return "、".join(f"{STAT_NAMES[k]} {v:+d}" for k, v in stats.items())


def equip_area(name):
    """材料がそろうエリア（そこが開放されるとショップに並ぶ）"""
    aids = []
    for mat in EQUIPS[name]["mats"]:
        t = next(t for t, n in MATERIALS.items() if n == mat)
        aids.append(next(i for i, a in enumerate(AREAS) if a["boss"] == t) if t in BOSSES else TYPE_AREA[t])
    return max(aids)


def owns_equip(data, name):
    return data["items"].get(name, 0) > 0 or any(pm.get("equip") == name for pm in data["party"])
SELL_FIXED = {"まんたんのくすり": 300, "まりょくのしずく": 300}  # ショップにないものの売値（たねは下で500G）

# ずかん報酬：登録数（つかまえた数＋倒したボスの数）→ もらえるもの
SEEDS = ["ちからのたね", "まもりのたね", "すばやさのたね", "いのちのたね", "まりょくのたね"]
DEX_REWARDS = [
    (5, {"きずぐすり": 5}, 100),
    (10, {"まりょくのみず": 5}, 300),
    (20, {"いいきずぐすり": 5, "ちからのたね": 1}, 500),
    (30, {"いいまりょくのみず": 5, "まもりのたね": 1}, 1000),
    (50, {"すごいきずぐすり": 3, "すばやさのたね": 2}, 2000),
    (75, {"すごいまりょくのみず": 3, "いのちのたね": 2}, 3000),
    (100, {"まんたんのくすり": 2, **{n: 1 for n in SEEDS}}, 5000),
    (150, {"まりょくのしずく": 2, **{n: 2 for n in SEEDS}}, 8000),
    (200, {"まんたんのくすり": 3, "まりょくのしずく": 3, **{n: 3 for n in SEEDS}}, 12000),
    (250, {"すごいネット": 5, **{n: 3 for n in SEEDS}}, 20000),
    (300, {n: 5 for n in SEEDS}, 30000),
    (400, {"まんたんのくすり": 5, "まりょくのしずく": 5, **{n: 5 for n in SEEDS}}, 40000),
    (500, {n: 7 for n in SEEDS}, 50000),
    (600, {n: 8 for n in SEEDS}, 60000),
    (700, {n: 10 for n in SEEDS}, 80000),
    (790, {n: 15 for n in SEEDS}, 100000),
]
assert all(n in ITEMS for _, items, _ in DEX_REWARDS for n in items)


# ドロップ表（どれも合計100%。"なし"＝何も落とさない）
# 通常モンスター：HP回復10%・MP回復10%（全エリア共通、グレードの内訳だけエリアで変える）
BOSS_DROP = {"なし": 10, "いいきずぐすり": 30, "いいまりょくのみず": 30, "すごいきずぐすり": 15, "すごいまりょくのみず": 15}
RARE_DROP = {
    "ポイント+5": 25, "ちからのたね": 10, "まもりのたね": 10, "すばやさのたね": 10,
    "いのちのたね": 10, "まりょくのたね": 5, "まんたんのくすり": 15, "まりょくのしずく": 15,
}

# ===== エリア =====
# unlock の書き方：("clear", エリア番号, 回数) / ("kill", 種族, 体数) / ("boss", エリア番号, 回数) / ("key", アイテム名)
AREAS = [
    {"name": "はじまりの草原", "lv": (1, 5), "stages": 10, "gold": (1, 3), "power": 0.6,
     "types": ["スライム", "ラット", "ラビット", "フロッグ"], "boss": "ハラッパオオウサギ", "rares": [],
     "key_drop": None, "unlock": []},
    {"name": "ひだまりの森", "lv": (5, 10), "stages": 12, "gold": (3, 6), "power": 0.72,
     "types": ["バード", "フォックス", "ビートル", "スパイダー"], "boss": "モリノオオジカ",
     "rares": ["ファイヤーカーバンクル", "アクアカーバンクル"], "key_drop": None,
     "unlock": [("clear", 0, 1)]},
    {"name": "そよかぜの花畑", "lv": (10, 15), "stages": 15, "gold": (5, 10), "power": 0.76,
     "types": ["ビー", "バタフライ", "フェアリー", "モール"], "boss": "ミツバチジョオウ",
     "rares": ["サンダーカーバンクル", "ロックカーバンクル"], "key_drop": None,
     "unlock": [("clear", 1, 1)]},
    {"name": "いわかげの洞窟", "lv": (15, 20), "stages": 18, "gold": (8, 15), "power": 0.8,
     "types": ["バット", "ゴブリン", "ゴーレム", "リザード"], "boss": "イワクイムカデ",
     "rares": ["リーフカーバンクル", "アクアケットシー"], "key_drop": None,
     "unlock": [("clear", 2, 1), ("kill", "ビートル", 10)]},
    {"name": "すなぼこりの砂漠", "lv": (20, 26), "stages": 22, "gold": (12, 22), "power": 0.83,
     "types": ["スコーピオン", "スネーク", "ワーム", "マミー"], "boss": "スナクジラ", "rares": [],
     "key_drop": None, "unlock": [("clear", 3, 1), ("boss", 1, 3)]},
    {"name": "いかずちの丘", "lv": (26, 32), "stages": 26, "gold": (16, 30), "power": 0.86,
     "types": ["ウルフ", "ディア", "ホーク", "ボア"], "boss": "イカズチワシ",
     "rares": ["ファイヤーケットシー", "リーフケットシー"], "key_drop": ("ディア", "湖のカギ", 8),
     "unlock": [("clear", 4, 2), ("kill", "ゴブリン", 20)]},
    {"name": "きりの沼地", "lv": (32, 38), "stages": 30, "gold": (22, 38), "power": 0.89,
     "types": ["インプ", "クロコダイル", "ウィスプ", "マンドレイク"], "boss": "ヌマノオオガエル",
     "rares": ["サンダーケットシー", "ロックケットシー"], "key_drop": None,
     "unlock": [("clear", 5, 2), ("boss", 3, 3)]},
    {"name": "しずくの湖", "lv": (38, 44), "stages": 34, "gold": (30, 50), "power": 0.92,
     "types": ["タートル", "シャーク", "ゴースト", "ナイト"], "boss": "ミズチ",
     "rares": ["リーフユニコーン", "サンダーユニコーン"], "key_drop": ("ナイト", "火山の通行証", 4),
     "unlock": [("clear", 6, 2), ("key", "湖のカギ")]},
    {"name": "こおりの雪原", "lv": (44, 50), "stages": 38, "gold": (38, 62), "power": 0.94,
     "types": ["オウル", "ペンギン", "イエティ", "マンモス"], "boss": "ユキオオカミ",
     "rares": ["ファイヤーユニコーン", "ロックユニコーン"], "key_drop": ("ペンギン", "しんでんのカギ", 4),
     "unlock": [("clear", 7, 3), ("kill", "スコーピオン", 30)]},
    {"name": "かぜなりの渓谷", "lv": (50, 56), "stages": 42, "gold": (45, 75), "power": 0.96,
     "types": ["マンティス", "キャット", "ハーピー", "ミノタウロス"], "boss": "カマイタチ",
     "rares": ["アクアユニコーン", "ファイヤーキリン"], "key_drop": ("ハーピー", "そらのはね", 3),
     "unlock": [("clear", 8, 3), ("boss", 5, 5)]},
    {"name": "ほのおの火山", "lv": (56, 63), "stages": 46, "gold": (55, 90), "power": 0.98,
     "types": ["ベア", "ライオン", "タイガー", "ガーゴイル"], "boss": "カザンリュウ",
     "rares": ["アクアキリン", "サンダーキリン"], "key_drop": ("ガーゴイル", "遺跡の石板", 2),
     "unlock": [("clear", 9, 4), ("kill", "ゴースト", 30), ("key", "火山の通行証")]},
    {"name": "ふかみの海底神殿", "lv": (63, 70), "stages": 52, "gold": (65, 105), "power": 1.0,
     "types": ["クラブ", "マーマン", "ジェリー", "セイレーン"], "boss": "ウミノオオダコ", "rares": [],
     "key_drop": None, "unlock": [("clear", 10, 4), ("boss", 7, 5), ("key", "しんでんのカギ")]},
    {"name": "そらの浮島", "lv": (70, 78), "stages": 58, "gold": (75, 120), "power": 1.03,
     "types": ["ホース", "イーグル", "グリフォン", "スフィンクス"], "boss": "ソラクジラ",
     "rares": ["リーフキリン", "ロックキリン"], "key_drop": None,
     "unlock": [("clear", 11, 5), ("kill", "マンティス", 40), ("key", "そらのはね")]},
    {"name": "はての遺跡", "lv": (78, 88), "stages": 66, "gold": (90, 145), "power": 1.06,
     "types": ["キメラ", "ワイバーン", "ミミック", "アヌビス"], "boss": "イセキノマモリビト",
     "rares": ["ファイヤーケルベロス", "アクアケルベロス"], "key_drop": ("アヌビス", "てんくうのかぎ", 2),
     "unlock": [("clear", 12, 5), ("kill", "タイガー", 50), ("key", "遺跡の石板")]},
    {"name": "ほしふる天空城", "lv": (88, 99), "stages": 80, "gold": (110, 180), "power": 1.1,
     "types": ["ドラゴン", "フェニックス", "エンジェル", "ヴァルキリー"], "boss": "テンクウノオウ",
     "rares": ["リーフケルベロス", "サンダーケルベロス", "ロックケルベロス"], "key_drop": None,
     "unlock": [("clear", 13, 6), ("boss", 12, 5), ("key", "てんくうのかぎ")]},
]
# 通常モンスターのドロップ：HP回復10%・MP回復10%（ふつう・いい・すごい の内訳だけエリアで変える）
_DROP_SPLIT = [(8, 2, 0), (7, 3, 0), (6, 4, 0), (5, 4, 1), (4.5, 4.5, 1), (4, 4.5, 1.5), (3.5, 5, 1.5), (3, 5, 2),
               (2.5, 5, 2.5), (2, 5.5, 2.5), (2, 5, 3), (1.5, 5, 3.5), (1, 5, 4), (1, 5, 4), (0.5, 4.5, 5)]
for _a, (_n, _g, _s) in zip(AREAS, _DROP_SPLIT):
    _a["drop"] = {"なし": 80}
    for _k, _v in [("きずぐすり", _n), ("まりょくのみず", _n), ("いいきずぐすり", _g), ("いいまりょくのみず", _g),
                   ("すごいきずぐすり", _s), ("すごいまりょくのみず", _s)]:
        if _v:
            _a["drop"][_k] = _v
assert len(_DROP_SPLIT) == len(AREAS)
# 前のバージョン（7エリア）の番号 → 今の番号
OLD_AREA_INDEX = {0: 0, 1: 1, 2: 3, 3: 5, 4: 7, 5: 10, 6: 13}

for _a in AREAS:
    _a.setdefault("power", 1.0)  # 敵の強さの倍率（序盤エリアは弱め）
    assert _a["boss"] in BOSSES
    _a["pool"] = [PREFIX[el] + t for t in _a["types"] for el in ELEMENTS if PREFIX[el] + t not in STARTERS]
    _a["commons"] = [n for n in _a["pool"] if n != _a["boss"] and n not in _a["rares"]]
    assert abs(sum(_a["drop"].values()) - 100) < 1e-9
    assert all(SPECIES[r]["type"] in RARE_TYPES for r in _a["rares"])
_normal_types = [t for a in AREAS for t in a["types"]]
assert sorted(_normal_types) == sorted(t for t in TYPES if t not in RARE_TYPES), "種族のエリア割り当てがずれている"
_all_rares = [r for a in AREAS for r in a["rares"]]
assert len(_all_rares) == len(set(_all_rares)) == len(RARE_TYPES) * len(ELEMENTS), "レアの割り当てがずれている"
assert sum(BOSS_DROP.values()) == 100 and sum(RARE_DROP.values()) == 100

TYPE_AREA = {t: i for i, a in enumerate(AREAS) for t in a["types"]}

# ===== モンスター固有のドロップ品（種族ごとに1つ。売れる・装備の材料） =====
MATERIALS = {
    "スライム": "スライムゼリー", "ラット": "ラットのしっぽ", "バット": "バットのつばさ", "ラビット": "ラビットのわたげ",
    "フロッグ": "フロッグのぬめり", "バード": "バードのはね", "スネーク": "スネークのぬけがら", "フォックス": "フォックスのけがわ",
    "モール": "モールのつめ", "ビートル": "ビートルのつの", "スパイダー": "スパイダーのいと", "リザード": "リザードのうろこ",
    "クラブ": "クラブのこうら", "ゴブリン": "ゴブリンのこんぼう", "ボア": "ボアのきば", "ゴーレム": "ゴーレムのいし",
    "キャット": "キャットのひげ", "ウルフ": "ウルフのきば", "ディア": "ディアのつの", "ホーク": "ホークのはね",
    "オウル": "オウルのはね", "インプ": "インプのしっぽ", "フェアリー": "フェアリーのりんぷん", "タートル": "タートルのこうら",
    "シャーク": "シャークのは", "ゴースト": "ゴーストのぬの", "マンティス": "マンティスのかま", "スコーピオン": "スコーピオンのどく",
    "ナイト": "ナイトのたて", "ベア": "ベアのけがわ", "ホース": "ホースのたてがみ", "ライオン": "ライオンのたてがみ",
    "タイガー": "タイガーのきば", "イーグル": "イーグルのはね", "ガーゴイル": "ガーゴイルのいし", "ドラゴン": "ドラゴンのうろこ",
    "キメラ": "キメラのつの", "ワイバーン": "ワイバーンのつばさ", "グリフォン": "グリフォンのはね", "フェニックス": "フェニックスのはね",
    "ビー": "ビーのはちみつ", "バタフライ": "バタフライのはね", "ワーム": "ワームのつち", "マミー": "マミーのほうたい",
    "クロコダイル": "クロコダイルのかわ", "ウィスプ": "ウィスプのひかり", "マンドレイク": "マンドレイクのね", "ペンギン": "ペンギンのはね",
    "イエティ": "イエティのけがわ", "マンモス": "マンモスのきば", "ハーピー": "ハーピーのはね", "ミノタウロス": "ミノタウロスのおの",
    "マーマン": "マーマンのうろこ", "ジェリー": "ジェリーのしょくしゅ", "セイレーン": "セイレーンのかみ", "スフィンクス": "スフィンクスのいし",
    "ミミック": "ミミックのたからばこ", "アヌビス": "アヌビスのつえ", "エンジェル": "エンジェルのわっか", "ヴァルキリー": "ヴァルキリーのやり",
    "カーバンクル": "カーバンクルのほうせき", "ケットシー": "ケットシーのすず", "ユニコーン": "ユニコーンのつの",
    "キリン": "キリンのたてがみ", "ケルベロス": "ケルベロスのくさり",
}
for _b in BOSSES:
    MATERIALS[_b] = _b + "のあかし"
MAT_RATE = {"normal": 0.25, "rare": 0.5, "boss": 1.0}  # ドロップ品を落とす確率
_LAST = len(AREAS) - 1
for _t, _name in MATERIALS.items():
    if _t in BOSSES:
        _aid = next(i for i, a in enumerate(AREAS) if a["boss"] == _t)
        _price = round((200 + 800 * _aid / _LAST) / 10) * 10  # ボスのあかし：200〜1000G
    elif _t in RARE_TYPES:
        _price = 500
    else:
        _price = round(5 + 95 * TYPE_AREA[_t] / _LAST)
    ITEMS[_name] = ("mat", _price)
assert set(MATERIALS) == set(TYPES) | set(BOSSES) and len(set(MATERIALS.values())) == len(MATERIALS)
assert not set(MATERIALS.values()) & set(MOVES)
assert all(m in ITEMS for e in EQUIPS.values() for m in e["mats"]), "装備の材料の名前がずれている"
# 開放条件に関わる系統（倒す対象・カギを落とす系統）は顔ぶれに必ず入れる
TARGET_TYPES = {c[1] for a in AREAS for c in a["unlock"] if c[0] == "kill"}
TARGET_TYPES |= {a["key_drop"][0] for a in AREAS if a["key_drop"]}
STAT_SCALE = 60  # バー表示の最大値の目安（能力値がこれを超えるとバーは満タン）


def strong_against(el):
    return ELEMENTS[(ELEMENTS.index(el) + 1) % 5]


def weak_against(el):
    return ELEMENTS[(ELEMENTS.index(el) - 1) % 5]


def element_multiplier(attack_el, defend_el):
    if ALL_ELEMENT in (attack_el, defend_el):  # 全属性は相性なし
        return 1.0
    if strong_against(attack_el) == defend_el:
        return 1.5
    if weak_against(attack_el) == defend_el:
        return 0.7
    return 1.0


# ===== 進化・技 =====
def type_of(m):
    return SPECIES[m["species"]]["type"]


def stage_for_level(t, level):
    return sum(level >= lv for lv in EVO_LEVELS[len(EVO[t])])


def form_name(species, stage, nature=None):
    if species in BOSSES:
        return species
    s = SPECIES[species]
    if is_branch(s["type"], stage, nature):
        return PREFIX[s["element"]] + BRANCH[s["type"]][0]
    return PREFIX[s["element"]] + EVO[s["type"]][stage]


def can_evolve(m):
    return m["stage"] < stage_for_level(type_of(m), m["level"])


def is_final(m):
    return m["stage"] >= len(EVO[type_of(m)]) - 1


def next_evolution(m):
    """次に進化するレベル（最終進化なら None）"""
    levels = EVO_LEVELS[len(EVO[type_of(m)])]
    return levels[m["stage"]] if m["stage"] < len(levels) else None


def skills_of(m):
    t = type_of(m)
    if t in BOSSES:  # ボスは専用技だけ
        move, kind, power = BOSSES[t]["move"]
        s = dict(SKILL2[kind], name=move, **BUFFS.get(t, {}))
        if power:
            s["power"] = power
        return [s]
    pre = PREFIX[m["element"]]
    move1, move2, kind2 = MOVES[t]
    skills = [dict(SKILL1, name=pre + move1)]
    if is_final(m):
        skills.append(dict(SKILL2[kind2], name=pre + move2, **BUFFS.get(t, {})))
    return skills


def skill_desc(s):
    if s["kind"] == "attack":
        return f"威力{s['power']}倍の攻撃 ／ MP{s['mp']}"
    if s["kind"] == "heal":
        return f"HPを最大の4割回復 ／ MP{s['mp']}"
    return f"{buff_label(s)}（{s['turns']}回の攻撃のあいだ） ／ MP{s['mp']}"


def buff_label(b):
    return "・".join(STAT_NAMES[k] for k in b["stats"]) + f" +{round(b['rate'] * 100)}%"


def second_skill_preview(m):
    move1, move2, kind2 = MOVES[type_of(m)]
    return dict(SKILL2[kind2], name=PREFIX[m["element"]] + move2, **BUFFS.get(type_of(m), {}))


# ===== セーブ =====
def new_data():
    return {
        "party": [], "active": 0, "log": [],
        "items": {"きずぐすり": 3, "まりょくのみず": 3}, "gold": 0,
        "battle": None, "area": 0, "in_area": False,
        "progress": {}, "clears": {}, "kills": {}, "used_keys": [], "opened": [], "dex": [], "seen": [], "team": [0], "dex_claimed": [],
    }


def load_data(raw=None):
    data = new_data()
    if raw is not None:  # 読み込んだセーブ
        data.update(raw)
    elif not PUBLIC_MODE and SAVE_FILE.exists():
        try:
            data.update(json.loads(SAVE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    # 前のバージョンのセーブを使えるように補う
    by_element = {SPECIES[s]["element"]: s for s in STARTERS}
    for m in data["party"]:
        m.setdefault("points", 0)
        if m.get("species") not in SPECIES:
            m["species"] = m["name"] if m["name"] in SPECIES else by_element[m["element"]]
        if "stage" not in m:
            m["stage"] = 0
            m["mp_max"] = round(20 * (1 + 0.2 * (m["level"] - 1)))
            m["mp"] = m["mp_max"]
            while m["stage"] < stage_for_level(SPECIES[m["species"]]["type"], m["level"]):
                m["stage"] += 1
                for key in STAT_NAMES:
                    m[key] = round(m[key] * EVOLVE_RATE)
            m["hp"], m["mp"] = m["hp_max"], m["mp_max"]
        m.pop("full", None)
        if not m.get("nature"):  # 性格がない前のモンスターにはランダムで付ける
            m["nature"] = roll_nature(SPECIES[m["species"]]["type"])
            if is_branch(SPECIES[m["species"]]["type"], m["stage"], m["nature"]):
                key = BRANCH[SPECIES[m["species"]]["type"]][2]
                m[key] = round((m[key] - bonus_of(m, key)) * BRANCH_BOOST) + bonus_of(m, key)
        m["name"] = form_name(m["species"], m["stage"], m["nature"])
        if not m.get("pt_v2"):  # ポイントが増えた分を前のセーブにも足す
            m["points"] += total_points(m["level"]) - POINTS_PER_LEVEL * (m["level"] - 1)
            m["pt_v2"] = True
        while m["stage"] > stage_for_level(type_of(m), m["level"]):  # 進化レベルが上がった分、進化前に戻す
            m["stage"] -= 1
            for key in STAT_NAMES:
                b = bonus_of(m, key)
                m[key] = max(1, round((m[key] - b) / EVOLVE_RATE)) + b
            m["hp"], m["mp"] = m["hp_max"], m["mp_max"]
            m["name"] = form_name(m["species"], m["stage"], m.get("nature"))
        cap_stats(m)
    if data["battle"] and ("area" not in data["battle"] or "mp" not in data["battle"]["enemy"]):
        data["battle"] = None
    if data["battle"]:
        data["battle"]["buff"] = {k: int(v) for k, v in data["battle"].get("buff", {"p": 0, "e": 0}).items()}
    data["items"] = {k: v for k, v in data["items"].items() if k in ITEMS}
    data.setdefault("opened", [])
    data.setdefault("dex", [])
    data.setdefault("seen", [])
    data.setdefault("dex_claimed", [])
    fix_team(data)
    if not data.get("boss_v2"):  # 前のボスを倒した回数を新しいボスに引きつぐ
        for old, new in OLD_BOSSES.items():
            n = count(data["kills"], old)
            if n:
                bump(data["kills"], new, n)
                if new not in data["dex"]:
                    data["dex"].append(new)
        data["boss_v2"] = True
    if data["party"] and not data.get("dex_starter"):  # 最初に選んだモンスターもずかんに入れる
        sp = data["party"][0]["species"]
        if sp not in data["dex"]:
            data["dex"].insert(0, sp)
        data["dex_starter"] = True
    if not data.get("area_v2"):  # 7エリア → 15エリアで番号が変わった分を移す
        conv = lambda k: str(OLD_AREA_INDEX.get(int(k), int(k)))
        old_opened = set(data["opened"]) | {k for k, v in data["clears"].items() if v} | {k for k, v in data["progress"].items() if v}
        old_opened |= {str(data.get("area", 0))}
        for key in ("progress", "clears"):
            data[key] = {conv(k): v for k, v in data[key].items()}
        data["opened"] = sorted({conv(k) for k in old_opened} - {"0"})
        data["area"] = OLD_AREA_INDEX.get(data.get("area", 0), 0)
        if data["battle"]:
            data["battle"]["area"] = OLD_AREA_INDEX.get(data["battle"]["area"], 0)
        if data.get("auto"):
            data["auto"]["area"] = OLD_AREA_INDEX.get(data["auto"]["area"], 0)
        data["area_v2"] = True
    for k in list(data["progress"]):  # ステージ数が減ったエリアはボスの手前までにする
        if int(k) < len(AREAS):
            data["progress"][k] = min(data["progress"][k], AREAS[int(k)]["stages"] - 1)
    if not data.get("seen_v1"):  # これまでに倒したモンスターを「出会った」として登録
        for name in data["kills"]:
            if name in SPECIES and name not in data["seen"]:
                data["seen"].append(name)
        data["seen_v1"] = True
    if not data.get("dex_v2"):  # ずかんを姿ごとにした分：いまボックスにいるモンスターの姿を登録
        for pm in data["party"]:
            if pm["name"] not in data["dex"]:
                data["dex"].append(pm["name"])
        data["dex_v2"] = True
    data["dex"] = [n for n in data["dex"] if n in FORM_INFO]
    data["seen"] = [n for n in data["seen"] if n in FORM_INFO]
    for name in data["dex"]:  # つかまえたものは出会ったことにもなる
        if name not in data["seen"]:
            data["seen"].append(name)
    return data


def save_data(data):
    if PUBLIC_MODE:  # 公開版は画面を開いているあいだだけ覚えておく（書き出しで手元に保存）
        return
    SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_log(data, text):
    data["log"].insert(0, text)
    data["log"] = data["log"][:10]


def battle_log(data, text):
    data["battle"]["log"].append(text)
    data["battle"]["log"] = data["battle"]["log"][-8:]


def count(d, key):
    return d.get(str(key), 0)


def bump(d, key, n=1):
    d[str(key)] = d.get(str(key), 0) + n


# ===== モンスター =====
def make_monster(species, level=1, kind="normal", power=1.0):
    base = SPECIES[species]
    stage = stage_for_level(base["type"], level)
    grow = grow_rate(level) * power * EVOLVE_RATE ** stage
    boost = dict(BOSS_BOOST) if kind == "boss" else {}
    nature = None if kind == "boss" else roll_nature(base["type"])
    if is_branch(base["type"], stage, nature):
        boost = {BRANCH[base["type"]][2]: BRANCH_BOOST}
    stats = {k: max(1, round(base[k] * grow * boost.get(k, 1))) for k in STAT_NAMES}
    return {
        "name": form_name(species, stage, nature), "species": species, "element": base["element"], "kind": kind,
        "level": level, "stage": stage, "exp": 0, "points": 0, "pt_v2": True, "nature": nature,
        "hp_max": stats["hp_max"], "hp": stats["hp_max"], "mp_max": stats["mp_max"], "mp": stats["mp_max"],
        "atk": stats["atk"], "dfn": stats["dfn"], "spd": stats["spd"],
    }


def points_for_level(level):
    for lv, pt in POINTS_STEPS:
        if level >= lv:
            return pt
    return POINTS_PER_LEVEL


def total_points(level):
    """Lv1からこのレベルまでにもらえるポイントの合計"""
    return sum(points_for_level(lv) for lv in range(2, level + 1))


def grow_rate(level):
    """敵の強さの伸び（Lv30をこえるとゆるやかになる）"""
    if level <= 30:
        return 1 + ENEMY_GROW * (level - 1)
    return 1 + ENEMY_GROW * 29 + ENEMY_GROW_HIGH * (level - 30)


def seed_bonus(m, key):
    """たねで上がった分"""
    return m.get("bonus", {}).get(key, 0)


def bonus_of(m, key):
    """たね・装備で上がった分（進化の1.2倍はかけない、表示はまとめて出す）"""
    return seed_bonus(m, key) + m.get("equip_delta", {}).get(key, 0)


def plus_text(m, key):
    b = bonus_of(m, key)
    return f'<span class="plus">（{b:+d}）</span>' if b else ""


def stat_cap(m, key):
    """上限（装備で上がった分は上限の外）"""
    return STAT_CAP[key] + max(0, m.get("equip_delta", {}).get(key, 0))


def cap_stats(m):
    """自分のモンスターの能力を上限におさめる"""
    for key in STAT_CAP:
        m[key] = min(m[key], stat_cap(m, key))
    m["hp"] = min(m["hp"], m["hp_max"])
    m["mp"] = min(m["mp"], m["mp_max"])


def exp_rate(my_level, enemy_level):
    """自分より5レベル以上低い相手からは、けいけんが減る"""
    diff = my_level - enemy_level
    if diff < 5:
        return 1.0
    return max(0.1, 0.5 ** ((diff - 4) / 3))


def exp_needed(level):
    return round(8 * level ** 1.5) + 2


def evolve(data, m):
    old = m["name"]
    m["stage"] += 1
    for key in STAT_NAMES:
        b = bonus_of(m, key)
        m[key] = round((m[key] - b) * EVOLVE_RATE) + b
    cap_stats(m)
    m["name"] = form_name(m["species"], m["stage"], m.get("nature"))
    text = "全能力 1.2倍"
    if is_branch(type_of(m), m["stage"], m.get("nature")):  # 性格で変わる進化先：さらに1割
        key = BRANCH[type_of(m)][2]
        b = bonus_of(m, key)
        m[key] = round((m[key] - b) * BRANCH_BOOST) + b
        cap_stats(m)
        text += f"、{STAT_NAMES[key]}はさらに1割アップ（{m['nature']}）"
    add_log(data, f"◆ {old}は{m['name']}に進化した！ {text}")
    if m["name"] not in data.setdefault("dex", []):  # 進化させた姿もずかんに登録
        data["dex"].append(m["name"])
        add_log(data, f"◆ {m['name']}をずかんに登録した！")
    if is_final(m):
        add_log(data, f"◆ {m['name']}は「{skills_of(m)[1]['name']}」を覚えた！")


def pick_monster(data, idx):
    """idx があればそのモンスター、なければ先頭"""
    if idx is not None and 0 <= idx < len(data["party"]):
        return data["party"][idx]
    return active_monster(data)


def do_evolve(data, idx=None):
    m = pick_monster(data, idx)
    if can_evolve(m):
        evolve(data, m)


def gain_exp(data, m, amount):
    if m["level"] >= MAX_LEVEL:
        return
    m["exp"] += amount
    leveled = False
    while m["level"] < MAX_LEVEL and m["exp"] >= exp_needed(m["level"]):
        m["exp"] -= exp_needed(m["level"])
        m["level"] += 1
        pt = points_for_level(m["level"])
        m["points"] += pt
        leveled = True
        add_log(data, f"★ {m['name']}はレベル{m['level']}になった！ ポイント +{pt}")
        if m["level"] in EVO_LEVELS[len(EVO[type_of(m)])]:
            add_log(data, f"◆ {m['name']}は進化できるようになった！（育成画面から進化できる）")
    if leveled:
        m["hp"], m["mp"] = m["hp_max"], m["mp_max"]
    if m["level"] >= MAX_LEVEL:
        m["exp"] = 0


def active_monster(data):
    return data["party"][data["active"]]


def fix_team(data):
    """パーティー（最大3体）の番号を正しくする。戦うモンスターは必ず入れる"""
    n = len(data["party"])
    team = []
    for i in data.get("team", []):
        if isinstance(i, int) and 0 <= i < n and i not in team:
            team.append(i)
    if n and data["active"] not in team:
        team.insert(0, data["active"])
    data["team"] = team[:TEAM_MAX]


def team_members(data):
    return [data["party"][i] for i in data["team"]]


def heal_team(data):
    for pm in team_members(data):
        pm["hp"], pm["mp"] = pm["hp_max"], pm["mp_max"]


def send_next(data):
    """戦っているモンスターが倒れたら、HPが残っている次のなかまを出す。出せたら True"""
    down = active_monster(data)
    for i in data["team"]:
        if data["party"][i]["hp"] > 0:
            data["active"] = i
            data["battle"]["buff"]["p"] = 0
            battle_log(data, f"{down['name']}はたおれた！ {data['party'][i]['name']}が出た！")
            return True
    return False


def switch_in_battle(data, idx):
    """自動周回の交代（ターンは使わない）"""
    old = active_monster(data)
    data["active"] = idx
    data["battle"]["buff"]["p"] = 0
    battle_log(data, f"{old['name']}をもどして、{data['party'][idx]['name']}を出した。")


def give_item(data, name, n=1):
    data["items"][name] = data["items"].get(name, 0) + n


def roll(table):
    names = list(table)
    return random.choices(names, weights=[table[n] for n in names])[0]


# ===== エリア開放 =====
def cond_text(data, cond):
    """条件の説明文・現在の数・必要な数"""
    kind = cond[0]
    if kind == "clear":
        _, aid, n = cond
        return f"{AREAS[aid]['name']}を{n}回クリア", count(data["clears"], aid), n
    if kind == "kill":
        _, t, n = cond
        done = sum(v for k, v in data["kills"].items() if k in SPECIES and SPECIES[k]["type"] == t)
        return f"{AREAS[TYPE_AREA[t]]['name']}の{t}を{n}体倒す（進化後も含む）", done, n
    if kind == "boss":
        _, aid, n = cond
        boss = AREAS[aid]["boss"]
        return f"{AREAS[aid]['name']}のボス（{boss}）を{n}回倒す", count(data["kills"], boss), n
    _, item = cond
    where = next(f"{a['name']}の{a['key_drop'][0]}" for a in AREAS if a["key_drop"] and a["key_drop"][1] == item)
    return f"「{item}」を使う（{where}がまれに落とす）", int(item in data["used_keys"]), 1


def is_unlocked(data, aid):
    if str(aid) in data.get("opened", []):  # 一度開放したエリアはずっと遊べる
        return True
    return all(cur >= need for _, cur, need in (cond_text(data, c) for c in AREAS[aid]["unlock"]))


def check_unlocks(data):
    """新しく条件を満たしたエリアをお知らせする"""
    for i, area in enumerate(AREAS):
        if area["unlock"] and str(i) not in data["opened"] and is_unlocked(data, i):
            data["opened"].append(str(i))
            add_log(data, f"◆ 新しいエリア「{area['name']}」が開放された！")


# ===== 行動 =====
def do_allocate(data, key, n, idx=None):
    m = pick_monster(data, idx)
    room = stat_cap(m, key) - m[key]
    per = POINT_VALUE[key] * nature_mult(m, key)  # 性格で1.5倍・0.5倍
    n = min(n, m["points"], int(-(-room // per)))
    if n <= 0:
        return
    m["points"] -= n
    frac = m.setdefault("frac", {})
    raw = per * n + frac.get(key, 0)  # 0.5の端数はためておく
    up = int(raw)
    frac[key] = round(raw - up, 2)
    up = min(up, room)
    m[key] += up
    if key == "hp_max":
        m["hp"] += up
    elif key == "mp_max":
        m["mp"] += up
    add_log(data, f"{m['name']}の{STAT_NAMES[key]} +{up}（{n}ポイント）")


def can_change_team(data):
    return not data["battle"] and not data.get("auto", {}).get("running")


def do_switch(data, idx):
    """戦うモンスター（先頭）を入れ替える。パーティーにいなければ、今の先頭と入れ替えてパーティーに入れる"""
    if not can_change_team(data) or not 0 <= idx < len(data["party"]):
        return
    if idx not in data["team"]:
        data["team"][data["team"].index(data["active"])] = idx
    data["active"] = idx
    m = active_monster(data)
    add_log(data, f"{m['name']}（Lv.{m['level']}）を先頭（戦うモンスター）にした。")


def do_team_add(data, idx):
    if not can_change_team(data) or idx in data["team"] or len(data["team"]) >= TEAM_MAX or not 0 <= idx < len(data["party"]):
        return
    data["team"].append(idx)
    add_log(data, f"{data['party'][idx]['name']}をパーティーに入れた。")


def do_team_remove(data, idx):
    if not can_change_team(data) or idx not in data["team"] or idx == data["active"]:
        return
    data["team"].remove(idx)
    add_log(data, f"{data['party'][idx]['name']}をパーティーから外した。")


def do_release(data, idx):
    """なかまをにがす（戦っているモンスターはにがせない）"""
    if idx == data["active"] or not 0 <= idx < len(data["party"]) or not can_change_team(data):
        return
    if data["party"][idx].get("equip"):
        give_item(data, data["party"][idx]["equip"])
    m = data["party"].pop(idx)
    if idx < data["active"]:
        data["active"] -= 1
    data["team"] = [i - (i > idx) for i in data["team"] if i != idx]
    fix_team(data)
    add_log(data, f"{m['name']}（Lv.{m['level']}）をにがした。")


def reward_text(items, gold):
    items = dict(items)
    parts = []
    seed_counts = {items.get(n) for n in SEEDS}
    if len(seed_counts) == 1 and None not in seed_counts:  # たね5種が同じ数ならまとめて書く
        k = seed_counts.pop()
        for n in SEEDS:
            items.pop(n)
        parts.append(f"たね5種×{k}")
    parts = [f"{n}×{k}" for n, k in items.items()] + parts
    return "、".join(parts) + f"、{gold}G"


def do_claim_reward(data, need):
    """ずかん報酬を受け取る"""
    row = next((r for r in DEX_REWARDS if r[0] == need), None)
    if not row or need in data["dex_claimed"] or len(data["dex"]) < need:
        return
    _, items, gold = row
    for n, k in items.items():
        give_item(data, n, k)
    data["gold"] += gold
    data["dex_claimed"].append(need)
    add_log(data, f"◆ ずかん報酬（登録{need}）を受け取った：{reward_text(items, gold)}")


def sell_price(name):
    """売値。売れないもの（カギ）は None"""
    kind, value = ITEMS[name]
    if kind == "key":
        return None
    if kind == "mat":
        return value
    if kind == "equip":
        return EQUIPS[name]["gold"] // 2
    if name in SHOP:
        return SHOP[name][0] // 2
    if kind == "seed":
        return 500
    return SELL_FIXED.get(name)


def apply_equip(m, name, sign):
    """装備の能力を足す（sign=1）／もどす（sign=-1）"""
    if sign > 0:
        delta = {}
        for k, v in EQUIPS[name]["stats"].items():
            new = max(1, m[k] + v)
            delta[k] = new - m[k]
            m[k] = new
        m["equip"], m["equip_delta"] = name, delta
    else:
        for k, v in m.get("equip_delta", {}).items():
            m[k] = max(1, m[k] - v)
        m["equip"], m["equip_delta"] = None, {}
    m["hp"] = max(1, min(m["hp"] + (m.get("equip_delta", {}).get("hp_max", 0) if sign > 0 else 0), m["hp_max"]))
    m["mp"] = min(m["mp"], m["mp_max"])


def do_equip(data, name, idx):
    if data["battle"] or not 0 <= idx < len(data["party"]) or data["items"].get(name, 0) <= 0:
        return
    m = data["party"][idx]
    if m["stage"] < 1:
        return
    if m.get("equip"):
        old = m["equip"]
        apply_equip(m, old, -1)
        give_item(data, old)
    apply_equip(m, name, 1)
    data["items"][name] -= 1
    if data["items"][name] <= 0:
        del data["items"][name]
    add_log(data, f"{m['name']}に{name}を付けた。（{equip_text(name)}）")


def do_unequip(data, idx):
    if data["battle"] or not 0 <= idx < len(data["party"]):
        return
    m = data["party"][idx]
    if not m.get("equip"):
        return
    name = m["equip"]
    apply_equip(m, name, -1)
    give_item(data, name)
    add_log(data, f"{m['name']}から{name}を外した。")


def can_buy_equip(data, name):
    e = EQUIPS[name]
    if owns_equip(data, name):
        return False, "もう持っている"
    if not shop_open(data, equip_area(name)):
        return False, f"「{AREAS[equip_area(name)]['name']}」が開放されると並ぶ"
    if data["gold"] < e["gold"]:
        return False, "お金が足りない"
    if any(data["items"].get(m, 0) < n for m, n in e["mats"].items()):
        return False, "材料が足りない"
    return True, ""


def do_buy_equip(data, name):
    ok, _ = can_buy_equip(data, name)
    if not ok:
        return
    e = EQUIPS[name]
    data["gold"] -= e["gold"]
    for m, n in e["mats"].items():
        data["items"][m] -= n
        if data["items"][m] <= 0:
            del data["items"][m]
    give_item(data, name)
    add_log(data, f"{name}を買った。（-{e['gold']}G、材料：{'、'.join(f'{m}×{n}' for m, n in e['mats'].items())}）")


def do_sell(data, name, n):
    price = sell_price(name)
    n = max(0, min(int(n), SHOP_MAX, data["items"].get(name, 0)))
    if not price or n <= 0:
        return
    total = price * n
    data["items"][name] -= n
    if data["items"][name] <= 0:
        del data["items"][name]
    data["gold"] += total
    a = data.get("auto")
    if a and a["running"]:  # 自動周回の結果で「拾った」「獲得」と混ざらないように記録する
        a.setdefault("sold", {})
        a["sold"][name] = a["sold"].get(name, 0) + n
        a["earned"] = a.get("earned", 0) + total
    add_log(data, f"{name}を{n}個売った。（+{total}G）")


def shop_open(data, aid):
    return aid == 0 or str(aid) in data["opened"] or is_unlocked(data, aid)


def do_buy(data, name, n):
    price, aid = SHOP[name]
    n = max(0, min(int(n), SHOP_MAX))
    if n <= 0 or not shop_open(data, aid):
        return
    total = price * n
    if data["gold"] < total:
        add_log(data, f"お金が足りない（{total}G 必要）。")
        return
    data["gold"] -= total
    data["items"][name] = data["items"].get(name, 0) + n
    a = data.get("auto")
    if a and a["running"]:  # 自動周回の結果で「拾った」と混ざらないように記録する
        a.setdefault("bought", {})
        a["bought"][name] = a["bought"].get(name, 0) + n
        a["spent"] = a.get("spent", 0) + total
    add_log(data, f"{name}を{n}個買った。（-{total}G）")


def do_use_until_full(data, name, idx=None):
    """満タンになるまで（または持ち物がなくなるまで）同じ回復アイテムを使う"""
    kind = ITEMS[name][0]
    if kind not in ("hp", "mp") or data["battle"]:
        return
    m = pick_monster(data, idx)
    cur, mx = ("hp", "hp_max") if kind == "hp" else ("mp", "mp_max")
    used, before = 0, m[cur]
    while m[cur] < m[mx] and data["items"].get(name, 0) > 0:
        m[cur] = min(m[mx], m[cur] + ITEMS[name][1])
        data["items"][name] -= 1
        used += 1
    if data["items"].get(name, 1) <= 0:
        del data["items"][name]
    if used:
        a = data.get("auto")
        if a and a["running"]:
            a.setdefault("manual_used", {})
            a["manual_used"][name] = a["manual_used"].get(name, 0) + used
        add_log(data, f"{name}を{used}個使った。{'HP' if kind == 'hp' else 'MP'} {before} → {m[cur]}/{m[mx]}")


def do_use_item(data, name, idx=None):
    """アイテムを使う。使えたら True（戦闘中は先頭のモンスターに使う）"""
    m = active_monster(data) if data["battle"] else pick_monster(data, idx)
    log = battle_log if data["battle"] else add_log
    if data["items"].get(name, 0) <= 0:
        log(data, f"{name}を持っていない。")
        return False
    kind, value = ITEMS[name]
    if kind in ("hp", "mp"):
        cur, mx, label = ("hp", "hp_max", "HP") if kind == "hp" else ("mp", "mp_max", "MP")
        if m[cur] >= m[mx]:
            log(data, f"{label}はもう満タンだ。")
            return False
        m[cur] = min(m[mx], m[cur] + value)
        log(data, f"{name}を使った。{label} {m[cur]}/{m[mx]}")
    elif kind == "seed":
        key, up = value
        up = min(up, stat_cap(m, key) - m[key])
        if up <= 0:
            log(data, f"{STAT_NAMES[key]}はもう上限だ。")
            return False
        m[key] += up
        m.setdefault("bonus", {})
        m["bonus"][key] = seed_bonus(m, key) + up
        if key == "hp_max":
            m["hp"] += up
        elif key == "mp_max":
            m["mp"] += up
        log(data, f"{name}を使った。{STAT_NAMES[key]}がずっと +{up}")
    else:
        if name in data["used_keys"]:
            log(data, f"{name}はもう使っている。")
            return False
        data["used_keys"].append(name)
        log(data, f"{name}を使った。")
    data["items"][name] -= 1
    if data["items"][name] <= 0:
        del data["items"][name]
    a = data.get("auto")
    if a and a["running"] and not data["battle"]:  # 周回中に持ち物から使った分（結果の「拾った」に混ぜない）
        a.setdefault("manual_used", {})
        a["manual_used"][name] = a["manual_used"].get(name, 0) + 1
    if kind == "key":
        check_unlocks(data)
    return True


def make_lineup(aid):
    commons = AREAS[aid]["commons"]
    must = [random.choice([n for n in commons if SPECIES[n]["type"] == t])
            for t in AREAS[aid]["types"] if t in TARGET_TYPES]
    rest = [n for n in commons if n not in must]
    return must + random.sample(rest, min(len(rest), LINEUP_SIZE - len(must)))


def do_enter_area(data):
    data["in_area"] = True
    data.pop("clear_notice", None)
    data["lineup"] = make_lineup(data["area"])
    add_log(data, f"{AREAS[data['area']]['name']}に入った。")


def do_leave_area(data):
    data["in_area"] = False
    data.pop("clear_notice", None)
    add_log(data, f"{AREAS[data['area']]['name']}から出た。（{stage_text(data, data['area'])} のところから再開できる）")


def do_explore(data):
    m = active_monster(data)
    event = roll(EXPLORE_EVENTS)
    if event == "モンスター":
        start_battle(data)
    elif event == "アイテム":
        item = roll({k: v for k, v in AREAS[data["area"]]["drop"].items() if k != "なし"})
        give_item(data, item)
        add_log(data, f"探索中に{item}を見つけた！")
    elif event == "けいけん":
        amount = max(1, round((m["level"] ** 1.5 + 2) * EXP_RATE * exp_rate(m["level"], AREAS[data["area"]]["lv"][1])))
        add_log(data, f"探索で少し強くなった。けいけん +{amount}")
        gain_exp(data, m, amount)
    else:
        add_log(data, "探索したが、何も見つからなかった。")


# ===== 戦闘 =====
def start_battle(data):
    aid = data["area"]
    area = AREAS[aid]
    stage = count(data["progress"], aid)  # クリア済みのステージ数
    lo, hi = area["lv"]
    if stage == area["stages"] - 1:
        enemy = make_monster(area["boss"], min(MAX_LEVEL, hi + 1), kind="boss", power=area["power"])
        text = f"ボスの{enemy['name']}（Lv.{enemy['level']}）があらわれた！"
    else:
        level = round(lo + (hi - lo) * stage / max(1, area["stages"] - 2)) + random.randint(-1, 0)
        level = max(lo, min(hi, level))
        if area["rares"] and random.random() < RARE_RATE:
            enemy = make_monster(random.choice(area["rares"]), level, kind="rare", power=area["power"])
            text = f"レアモンスターの{enemy['name']}（Lv.{level}）があらわれた！"
        else:
            lineup = [n for n in data.get("lineup", []) if n in area["commons"]] or area["commons"]
            enemy = make_monster(random.choice(lineup), level, power=area["power"])
            text = f"野生の{enemy['name']}（Lv.{level}）があらわれた！"
    data["battle"] = {"enemy": enemy, "area": aid, "buff": {"p": 0, "e": 0}, "log": [text]}
    if enemy["name"] not in data["seen"]:  # 出会った時点でずかんに記録（姿ごと）
        data["seen"].append(enemy["name"])


def buffed(data, m, side, key):
    """能力アップ込みの能力値"""
    spec = BUFFS.get(type_of(m))
    if data["battle"] and data["battle"]["buff"][side] > 0 and spec and key in spec["stats"]:
        return m[key] * (1 + spec["rate"])
    return m[key]


def attack(data, attacker, defender, side, power=1.0, move=None, keep1=False):
    """side は攻撃する側（"p"＝自分 / "e"＝敵）"""
    buff = data["battle"]["buff"]
    other = "e" if side == "p" else "p"
    a = buffed(data, attacker, side, "atk")
    d = buffed(data, defender, other, "dfn")
    mult = element_multiplier(attacker["element"], defender["element"])
    dmg = max(1, round(a * a / (a + d) * 1.5 * power * mult * random.uniform(0.85, 1.0)))
    if keep1:  # てかげん：HPを必ず1残す
        dmg = max(0, min(dmg, defender["hp"] - 1))
    if not (DEMO_MODE and side == "e"):
        defender["hp"] = max(0, defender["hp"] - dmg)
    text = f"{attacker['name']}の{move or 'こうげき'}！ {defender['name']}に{dmg}ダメージ"
    if mult > 1:
        text += "（こうかばつぐん 1.5倍）"
    elif mult < 1:
        text += "（いまひとつ 0.7倍）"
    battle_log(data, text)
    if buff[side] > 0:
        buff[side] -= 1
        if buff[side] == 0:
            battle_log(data, f"{attacker['name']}の能力アップが切れた。")


def use_skill(data, user, target, skill, side):
    if side == "p" and not DEMO_MODE:  # 敵はMPを使わない
        user["mp"] -= skill["mp"]
    if skill["kind"] == "attack":
        attack(data, user, target, side, skill["power"], skill["name"])
    elif skill["kind"] == "heal":
        amount = round(user["hp_max"] * 0.4)
        user["hp"] = min(user["hp_max"], user["hp"] + amount)
        battle_log(data, f"{user['name']}の{skill['name']}！ HPを{amount}回復した")
    else:
        data["battle"]["buff"][side] = skill["turns"]
        battle_log(data, f"{user['name']}の{skill['name']}！ {buff_label(skill)}（{skill['turns']}回の攻撃のあいだ）")


def enemy_action(data):
    m = active_monster(data)
    enemy = data["battle"]["enemy"]
    usable = []
    for s in skills_of(enemy):
        if s["kind"] == "heal" and enemy["hp"] > enemy["hp_max"] * 0.6:
            continue
        if s["kind"] == "buff" and data["battle"]["buff"]["e"] > 0:
            continue
        usable.append(s)
    if usable and random.random() < SKILL_RATE[type_of(enemy)]:
        use_skill(data, enemy, m, random.choice(usable), "e")
    else:
        attack(data, enemy, m, "e")


def flee_chance(m, enemy):
    if enemy.get("kind") == "boss":
        return max(10, min(60, 30 + (m["spd"] - enemy["spd"]) * 2))
    return max(20, min(95, 50 + (m["spd"] - enemy["spd"]) * 3))


def catch_bonus(data, enemy):
    """開放ボーナス：そのモンスターが出るエリアより先の開放済みエリア1つにつき +10%"""
    if enemy.get("kind") == "boss":
        return 0
    t = SPECIES[enemy["species"]]["type"]
    home = TYPE_AREA.get(t, data["battle"]["area"] if data.get("battle") else 0)
    return CATCH_AREA_BONUS * sum(1 for i in range(home + 1, len(AREAS)) if is_unlocked(data, i))


def can_gentle(m, enemy):
    """てかげんが使えるか、使えない理由"""
    if enemy.get("kind") in ("boss", "rare"):
        return False, "レア・ボスには使えない"
    if m["level"] - enemy["level"] < GENTLE_GAP:
        return False, f"{GENTLE_GAP}レベル以上格下の相手だけ"
    if m["mp"] < GENTLE_MP:
        return False, "MPが足りない"
    if enemy["hp"] <= 1:
        return False, "相手のHPはもう1"
    return True, ""


def catch_chance(net, enemy, data=None):
    """ネットでつかまえられる確率（%）。ボスは0"""
    if enemy.get("kind") == "boss":
        return 0
    low, high, max_lv = ITEMS[net][1]
    lost = 1 - enemy["hp"] / enemy["hp_max"]  # 減ったHPの割合
    rate = low + (high - low) * lost
    over = enemy["level"] - max_lv
    if over > 0:  # つかまえやすいレベルを10こえるごとに半分
        rate *= 0.5 ** (over / 10)
    if data is not None:
        rate += catch_bonus(data, enemy)
    if enemy.get("kind") == "rare":
        rate *= 0.5
    return max(1, min(95, round(rate)))


def make_caught(enemy):
    """つかまえた敵を、なかまのモンスターにする（能力は野生よりちょっと強く、ポイントは0）"""
    m = {k: enemy[k] for k in ("species", "element", "level", "stage")}
    m["nature"] = enemy.get("nature") or "まじめ"
    m.update({"name": form_name(m["species"], m["stage"], m["nature"]), "kind": "normal", "exp": 0, "points": 0, "pt_v2": True})
    for key in STAT_NAMES:
        m[key] = max(1, round(enemy[key] * CATCH_BOOST))
    m["hp"], m["mp"] = m["hp_max"], m["mp_max"]
    cap_stats(m)
    return m


def do_battle(data, action, arg=None):
    m = active_monster(data)
    enemy = data["battle"]["enemy"]

    if action in ("attack", "skill", "gentle"):
        if action == "gentle":
            ok, why = can_gentle(m, enemy)
            if not ok:
                battle_log(data, f"てかげんは使えない（{why}）。")
                return

            def player_act():
                if not DEMO_MODE:
                    m["mp"] -= GENTLE_MP
                attack(data, m, enemy, "p", 0.5, "てかげん", keep1=True)
        elif action == "skill":
            skill = skills_of(m)[arg]
            if m["mp"] < skill["mp"]:
                battle_log(data, "MPが足りない。")
                return
            if skill["kind"] == "heal" and m["hp"] >= m["hp_max"]:
                battle_log(data, "HPはもう満タンだ。")
                return

            def player_act():
                use_skill(data, m, enemy, skill, "p")
        else:

            def player_act():
                attack(data, m, enemy, "p")

        my_spd, en_spd = buffed(data, m, "p", "spd"), buffed(data, enemy, "e", "spd")
        player_first = my_spd > en_spd or (my_spd == en_spd and random.random() < 0.5)
        order = [player_act, lambda: enemy_action(data)]
        if not player_first:
            order.reverse()
        for act_fn in order:
            if m["hp"] > 0 and enemy["hp"] > 0:
                act_fn()
    elif action == "item":
        if not do_use_item(data, arg):
            return  # 使えなかったときはターンを消費しない
        enemy_action(data)
    elif action == "net":
        if enemy.get("kind") == "boss":
            battle_log(data, "ボスはつかまえられない。")
            return
        if len(data["party"]) >= PARTY_MAX:
            battle_log(data, "ボックスがいっぱいで、つかまえられない。")
            return
        if data["items"].get(arg, 0) <= 0:
            battle_log(data, f"{arg}を持っていない。")
            return
        chance = catch_chance(arg, enemy, data)
        data["items"][arg] -= 1
        if data["items"][arg] <= 0:
            del data["items"][arg]
        battle_log(data, f"{arg}をなげた！（確率 {chance}%）")
        if random.randint(1, 100) <= chance:
            end_battle(data, "catch")
            return
        battle_log(data, f"{enemy['name']}はネットから抜け出した！")
        enemy_action(data)
    elif action == "flee":
        if random.randint(1, 100) <= flee_chance(m, enemy):
            end_battle(data, "flee")
            return
        battle_log(data, "にげられなかった！")
        enemy_action(data)

    if enemy["hp"] <= 0:
        end_battle(data, "win")
    elif m["hp"] <= 0 and not send_next(data):
        end_battle(data, "lose")


def drop_table(data, aid, enemy):
    area = AREAS[aid]
    if enemy["kind"] == "boss":
        return BOSS_DROP
    if enemy["kind"] == "rare":
        return RARE_DROP
    table = dict(area["drop"])
    if area["key_drop"]:
        t, key_item, pct = area["key_drop"]
        if SPECIES[enemy["species"]]["type"] == t and key_item not in data["used_keys"] and data["items"].get(key_item, 0) == 0:
            table["なし"] -= pct
            table[key_item] = pct
    return table


def notice_rewards(data, before):
    for need, _, _ in DEX_REWARDS:
        if before < need <= len(data["dex"]):
            add_log(data, f"◆ ずかんの登録が{need}になった！ なかまタブで報酬を受け取れる")


def end_battle(data, result):
    m = active_monster(data)
    enemy = data["battle"]["enemy"]
    aid = data["battle"]["area"]
    area = AREAS[aid]
    data["last_battle_log"] = data["battle"]["log"]
    dex_before = len(data["dex"])
    data["last_result"] = result
    data["battle"] = None

    if result == "win":
        mult = {"boss": (3, 5), "rare": (2, 3)}.get(enemy["kind"], (1, 1))
        base = max(1, round((3 * enemy["level"] ** 1.5 + 5) * EXP_RATE)) * mult[0]
        amount = max(1, round(base * exp_rate(m["level"], enemy["level"])))
        gold = round(random.randint(*area["gold"]) * mult[1] * GOLD_RATE)
        data["gold"] += gold
        bump(data["kills"], enemy["species"])
        add_log(data, f"{enemy['name']}をたおした！ けいけん +{amount} ／ {gold}G")

        item = roll(drop_table(data, aid, enemy))
        if item == "ポイント+5":
            m["points"] += 5
            add_log(data, f"{enemy['name']}の力を受けとった。ポイント +5")
        elif item != "なし":
            give_item(data, item)
            add_log(data, f"{enemy['name']}は{item}を落としていった。")
        mat = MATERIALS.get(SPECIES[enemy["species"]]["type"])
        if mat and random.random() < MAT_RATE.get(enemy["kind"], 0):
            give_item(data, mat)
            add_log(data, f"{enemy['name']}は{mat}を落としていった。")

        if enemy["kind"] == "boss":
            if enemy["species"] not in data["dex"]:
                data["dex"].append(enemy["species"])
                add_log(data, f"◆ {enemy['name']}をずかんに登録した！")
            data["progress"][str(aid)] = 0
            data["in_area"] = False  # クリアしたらエリアの外に戻る
            data["clear_notice"] = area["name"]
            bump(data["clears"], aid)
            add_log(data, f"◆ {area['name']}をクリアした！（{count(data['clears'], aid)}回目）")
        else:
            bump(data["progress"], aid)
        check_unlocks(data)
        gain_exp(data, m, amount)
        for pm in team_members(data):  # 控えのなかまは半分
            if pm is not m:
                gain_exp(data, pm, max(1, round(base * BENCH_EXP * exp_rate(pm["level"], enemy["level"]))))

    elif result == "catch":
        new = make_caught(enemy)
        data["party"].append(new)
        if new["name"] not in data["dex"]:  # つかまえた姿だけを登録
            data["dex"].append(new["name"])
        bump(data["progress"], aid)  # つかまえても1ステージ進む（けいけん・お金・ドロップはなし）
        add_log(data, f"{new['name']}（Lv.{new['level']}）をつかまえた！ ボックスに入れた（なかま {len(data['party'])}/{PARTY_MAX}）")

    elif result == "lose":
        heal_team(data)
        data["in_area"] = False
        lost = int(data["gold"] * LOSE_GOLD)
        data["gold"] -= lost
        data["progress"][str(aid)] = 0
        add_log(data, f"パーティーは全員たおれた…エリアの外まで逃げ帰り、休んで全回復した（{lost}G 落とした／{area['name']}の進み具合は最初にもどった）")
    else:
        add_log(data, f"{enemy['name']}から逃げきった。")
    if result != "lose":  # 勝ち・つかまえた・にげた：たおれたなかまはHP1で起き上がる
        for pm in team_members(data):
            if pm["hp"] <= 0:
                pm["hp"] = 1
                add_log(data, f"{pm['name']}はなんとか起き上がった（HP 1）")
    notice_rewards(data, dex_before)


# ===== 自動周回 =====
def start_auto(data, laps, item, threshold):
    m = active_monster(data)
    data["auto"] = {
        "running": True, "laps": laps, "area": data["area"], "item": item, "threshold": threshold,
        "start_clears": count(data["clears"], data["area"]), "start_gold": data["gold"],
        "start_level": m["level"], "start_items": dict(data["items"]), "used": 0,
        "start_levels": {str(i): data["party"][i]["level"] for i in data["team"]}, "manual_used": {},
        "wins": 0, "steps": 0, "end": "",
    }
    data["in_area"] = False
    add_log(data, f"▶ {AREAS[data['area']]['name']}で自動周回をはじめた（{laps}周）")


def stop_auto(data, reason):
    a = data["auto"]
    a["running"] = False
    a["end"] = reason
    add_log(data, f"■ 自動周回を終了：{reason}")


def laps_done(data):
    a = data["auto"]
    return count(data["clears"], a["area"]) - a["start_clears"]


def auto_switch_target(data):
    """HPの割合がいちばん多い控え（20%より多いもの）。いなければ None"""
    best, best_rate = None, AUTO_SWITCH
    for i in data["team"]:
        pm = data["party"][i]
        r = pm["hp"] / pm["hp_max"]
        if i != data["active"] and r > best_rate:
            best, best_rate = i, r
    return best


def auto_battle(data):
    """自分は通常攻撃のみ。HPが決めた割合以下なら選んだ回復アイテムを使う"""
    a = data["auto"]
    m = active_monster(data)
    for _ in range(300):
        if not data["battle"]:
            break
        m = active_monster(data)
        item = a["item"]
        if item and data["items"].get(item, 0) > 0 and m["hp"] <= m["hp_max"] * a["threshold"] and m["hp"] < m["hp_max"]:
            do_battle(data, "item", item)
            a["used"] += 1
        elif m["hp"] <= m["hp_max"] * AUTO_SWITCH and (nxt := auto_switch_target(data)) is not None:
            switch_in_battle(data, nxt)
        else:
            do_battle(data, "attack")


def auto_step(data):
    a = data["auto"]
    if data["battle"]:
        auto_battle(data)
    else:
        data["area"] = a["area"]
        if not data.get("in_area"):
            do_enter_area(data)
        data["last_result"] = None
        do_explore(data)
        a["steps"] += 1
        if data["battle"]:
            auto_battle(data)
    if data.get("last_result") == "win":
        a["wins"] += 1
    elif data.get("last_result") == "lose":
        stop_auto(data, "全員たおれたので止めた")
        return
    data["last_result"] = None
    if laps_done(data) >= a["laps"]:
        stop_auto(data, f"{a['laps']}周クリアした")


def auto_summary(data):
    a = data["auto"]
    m = active_monster(data)
    gained = []
    for name in ITEMS:
        diff = data["items"].get(name, 0) - a["start_items"].get(name, 0)
        if name == a["item"]:
            diff += a["used"]
        diff += a.get("manual_used", {}).get(name, 0)  # 周回中に持ち物から使った分
        diff += a.get("sold", {}).get(name, 0)  # 周回中に売った分
        diff -= a.get("bought", {}).get(name, 0)
        if diff > 0:
            gained.append(f"{name}×{diff}")
    lines = [
        f"周回：{laps_done(data)}/{a['laps']}周 ／ 倒した数：{a['wins']}体 ／ 進んだ回数：{a['steps']}回",
        f"獲得：{data['gold'] - a['start_gold'] + a.get('spent', 0) - a.get('earned', 0)}G",
        "レベル：" + " ／ ".join(f"{data['party'][int(i)]['name']} {lv}→{data['party'][int(i)]['level']}"
                               for i, lv in a.get("start_levels", {str(data["active"]): a["start_level"]}).items() if int(i) < len(data["party"])),
        f"拾ったアイテム：{'、'.join(gained) if gained else 'なし'}",
        *([f"買ったアイテム：{'、'.join(f'{k}×{v}' for k, v in a['bought'].items())}"] if a.get("bought") else []),
        *([f"売ったアイテム：{'、'.join(f'{k}×{v}' for k, v in a['sold'].items())}（+{a.get('earned', 0)}G）"] if a.get("sold") else []),
        f"使った回復アイテム：{a['item']}×{a['used']}" if a["item"] else "使った回復アイテム：なし（設定なし）",
    ]
    return "<br>".join(lines)


def on_stop_auto():
    if data.get("auto", {}).get("running"):
        stop_auto(data, "止めるボタンで停止")
        save_data(data)


def on_close_auto():
    data.pop("auto", None)
    save_data(data)


# ===== 見た目 =====
CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
.stApp {background: #f4f5f7;}
.stButton button {width: 100%; border-radius: 4px; border: 1px solid #cfd4db; background: #fff; color: #2f3a4a; font-size: 13px;}
.stButton button:hover {border-color: #3b5b8c; color: #3b5b8c;}
.stButton button:disabled {opacity: 0.35; cursor: not-allowed;}
.stButton button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"] {background: #3b5b8c; color: #fff; border-color: #3b5b8c;}
.header {display: flex; justify-content: space-between; font-size: 13px; letter-spacing: 0.2em; color: #7a8494; border-bottom: 1px solid #dde1e6; padding-bottom: 6px; margin-bottom: 16px;}
.header span {font-size: 11px; letter-spacing: 0; color: #aab1bc; margin-left: 6px;}
.header .gold {font-size: 13px; letter-spacing: 0; color: #2f3a4a;}
.section {font-size: 12px; color: #7a8494; margin: 14px 0 6px;}
.card {background: #fff; border: 1px solid #dde1e6; border-radius: 6px; padding: 14px 18px; margin-bottom: 10px;}
.name {font-size: 18px; font-weight: 600; color: #2f3a4a;}
.lv {font-size: 12px; color: #7a8494; margin-left: 8px;}
.tag {display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 11px; color: #fff; margin-left: 8px; vertical-align: middle;}
.badge {display: inline-block; padding: 1px 8px; border-radius: 3px; font-size: 11px; margin-left: 8px; vertical-align: middle; border: 1px solid #3b5b8c; color: #3b5b8c;}
.sub {font-size: 12px; color: #7a8494; margin: 4px 0 10px;}
.row {display: grid; grid-template-columns: 72px 90px 1fr; align-items: center; gap: 8px; font-size: 13px; margin: 4px 0;}
.row .label {color: #7a8494;}
.row .val {text-align: right; color: #2f3a4a; font-variant-numeric: tabular-nums;}
.bar {background: #eceef1; height: 6px; border-radius: 3px; overflow: hidden;}
.bar div {height: 6px;}
.clear {font-size: 16px; font-weight: 600; color: #3b5b8c; text-align: center; border-color: #3b5b8c;}
.stage {font-size: 15px; font-weight: 600; color: #3b5b8c; margin-top: 6px;}
.skill {font-size: 12px; color: #2f3a4a; margin-top: 6px;}
.skill span {color: #7a8494; margin-left: 6px;}
.skill.locked {color: #aab1bc;}
.log {font-family: Menlo, Consolas, monospace; font-size: 12px; color: #555f6d; line-height: 1.8;}
.note {font-size: 12px; color: #7a8494;}
.points {font-size: 13px; color: #3b5b8c; font-weight: 600;}
.vs {text-align: center; font-size: 11px; color: #aab1bc; letter-spacing: 0.3em; margin: 2px 0 8px;}
.area {font-size: 13px; color: #2f3a4a; padding: 6px 0; border-bottom: 1px solid #eef0f2;}
.area .cond {font-size: 12px; color: #7a8494; margin-left: 12px;}
.area .ok {color: #4f8a6b;}
table.t {border-collapse: collapse; width: 100%; font-size: 12px; background: #fff;}
table.t th, table.t td {border: 1px solid #e3e6ea; padding: 5px 6px; text-align: center;}
table.t th {background: #f0f2f5; color: #5a6474; font-weight: 500;}
/* 右上の読み込み表示をぐるぐるに */
[data-testid="stStatusWidget"] > * {display: none !important;}
[data-testid="stStatusWidget"]::after {
  content: ""; display: inline-block; width: 16px; height: 16px; margin: 8px;
  border: 2px solid #c9cfd8; border-top-color: #2f3a4a; border-radius: 50%;
  animation: ml-spin 0.8s linear infinite;
}
@keyframes ml-spin {to {transform: rotate(360deg);}}
/* ショップのキーパッド（スマホでも3列のまま） */
.st-key-keypad [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 6px;}
.st-key-keypad [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;}
.qty {border: 1px solid #c9cfd8; border-radius: 4px; padding: 8px 12px; font-size: 20px; text-align: right;
  letter-spacing: 1px; color: #2f3a4a; background: #fff; margin-bottom: 6px;}
.qty small {font-size: 11px; color: #8a93a0; float: left; padding-top: 6px; letter-spacing: 0;}
.plus {color: #3b5b8c; font-size: 11px;}
.st-key-arealist {background: #fff; border: 1px solid #dde1e6; border-radius: 6px; padding: 8px 18px; gap: 4px !important;}
.st-key-arealist .stMarkdown, .st-key-arealist [data-testid="stMarkdownContainer"] {margin: 0 !important;}
.st-key-arealist .stButton {margin: 0 0 6px 12px;}
.st-key-arealist .stButton button {width: auto;}
/* 上の「MONSTER LOG・お金」とタブをスクロールしても固定 */
.stElementContainer:has(.header) {position: sticky; top: 3.75rem; z-index: 100; background: #f4f5f7; height: 34px;}
.header {margin-bottom: 0; padding-top: 10px;}
.stTabs [role="tablist"] {position: sticky; top: calc(3.75rem + 34px); z-index: 99; background: #f4f5f7 !important;}
table.dex td {width: 20%; vertical-align: top; line-height: 1.6;}
table.dex .tag {margin-left: 0; margin-right: 4px;}
.dexno {font-size: 10px; color: #aab1bc;}
/* なかまのマス目（ずかんと同じ見た目） */
.st-key-boxgrid [data-testid="stHorizontalBlock"], .st-key-teamgrid [data-testid="stHorizontalBlock"] {gap: 0 !important; flex-wrap: nowrap !important;}
.st-key-boxgrid [data-testid="stColumn"], .st-key-teamgrid [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;}
.st-key-boxgrid, .st-key-teamgrid {gap: 0 !important;}
.st-key-boxgrid .stButton button, .st-key-teamgrid .stButton button {border-radius: 0; min-height: 96px; height: 96px; font-size: 11px; line-height: 1.4; padding: 4px; margin: 0 -1px -1px 0;}
.st-key-boxgrid .stButton button p, .st-key-teamgrid .stButton button p {font-size: 11px; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; word-break: break-all;}
.st-key-boxgrid .stButton button div, .st-key-teamgrid .stButton button div {overflow: visible !important; white-space: normal !important;}
.dexsub {font-size: 11px; color: #8a93a0;}
table.dex .got {color: #1f2733; font-weight: 600;}
table.dex .got .dexsub {color: #1f2733; font-weight: 400;}
table.dex .seen, table.dex .seen .dexsub {color: #b3b9c2;}
table.dex .seen .tag {opacity: 0.45;}
</style>
"""
HP_COLOR, MP_COLOR = "#4f8a6b", "#6b6bb0"


def element_tag(el):
    return f'<span class="tag" style="background:{ELEMENT_COLORS[el]}">{el}</span>'


def stat_row(label, text, ratio, color="#3b5b8c"):
    pct = max(0, min(ratio, 1)) * 100
    return (
        f'<div class="row"><span class="label">{label}</span><span class="val">{text}</span>'
        f'<div class="bar"><div style="width:{pct:.0f}%;background:{color}"></div></div></div>'
    )


def evo_text(m):
    nxt = next_evolution(m)
    if nxt is None:
        return "最終進化"
    if can_evolve(m):
        return f"{form_name(m['species'], m['stage'] + 1, m.get('nature'))}に進化できる"
    return f"Lv.{nxt}で{form_name(m['species'], m['stage'] + 1, m.get('nature'))}に進化"


def monster_card(m):
    el = m["element"]
    html = f'<div class="card"><span class="name">{m["name"]}</span><span class="lv">Lv.{m["level"]}</span>{element_tag(el)}'
    if m.get("nature"):
        html += f'<span class="lv">性格：{m["nature"]}</span>'
    if m.get("equip"):
        html += f'<span class="lv">装備：{m["equip"]}</span>'
    html += f'<div class="sub">{strong_against(el)}に強い ／ {weak_against(el)}に弱い ／ {evo_text(m)}</div>'
    html += stat_row("HP", f'{m["hp"]}/{m["hp_max"]}{plus_text(m, "hp_max")}', m["hp"] / m["hp_max"], HP_COLOR)
    html += stat_row("MP", f'{m["mp"]}/{m["mp_max"]}{plus_text(m, "mp_max")}', m["mp"] / m["mp_max"], MP_COLOR)
    for key in ["atk", "dfn", "spd"]:
        html += stat_row(STAT_NAMES[key], f'{m[key]}{plus_text(m, key)}', m[key] / STAT_SCALE)
    if m["level"] >= MAX_LEVEL:
        html += stat_row("けいけん", "MAX", 1, "#9aa3b0")
    else:
        need = exp_needed(m["level"])
        html += stat_row("けいけん", f'{m["exp"]}/{need}', m["exp"] / need, "#9aa3b0")
    for s in skills_of(m):
        html += f'<div class="skill">技：{s["name"]}<span>{skill_desc(s)}</span></div>'
    if not is_final(m):
        s2 = second_skill_preview(m)
        html += f'<div class="skill locked">技：{s2["name"]}<span>最終進化で覚える（{skill_desc(s2)}）</span></div>'
    html += "</div>"
    return html


def battle_card(m, show_mp=True, buff=0):
    badge = {"boss": '<span class="badge">BOSS</span>', "rare": '<span class="badge">RARE</span>'}.get(m.get("kind"), "")
    html = f'<div class="card"><span class="name">{m["name"]}</span><span class="lv">Lv.{m["level"]}</span>{element_tag(m["element"])}{badge}'
    html += stat_row("HP", f'{m["hp"]}/{m["hp_max"]}', m["hp"] / m["hp_max"], HP_COLOR)
    if show_mp:
        html += stat_row("MP", f'{m["mp"]}/{m["mp_max"]}', m["mp"] / m["mp_max"], MP_COLOR)
    html += (f'<div class="note">こうげき {m["atk"]}{plus_text(m, "atk")} ／ ぼうぎょ {m["dfn"]}{plus_text(m, "dfn")}'
             f' ／ すばやさ {m["spd"]}{plus_text(m, "spd")}</div>')
    if not show_mp:
        html += f'<div class="note">技を使う確率 {round(SKILL_RATE[type_of(m)] * 100)}%</div>'
    if buff > 0 and type_of(m) in BUFFS:
        html += f'<div class="note" style="color:#3b5b8c">能力アップ中：{buff_label(BUFFS[type_of(m)])}（あと{buff}回の攻撃）</div>'
    return html + "</div>"


def team_html(data):
    """パーティーのHP一覧（★＝いま戦うモンスター）"""
    rows = []
    for i in data["team"]:
        pm = data["party"][i]
        mark = "★" if i == data["active"] else "・"
        state = "（たおれている）" if pm["hp"] <= 0 else ""
        rows.append(f'{mark} {pm["name"]} Lv.{pm["level"]} {pm["element"]}　HP {pm["hp"]}/{pm["hp_max"]}　MP {pm["mp"]}/{pm["mp_max"]}{state}')
    return f'<div class="card note"><b>パーティー（{len(data["team"])}/{TEAM_MAX}）</b><br>{"<br>".join(rows)}</div>'


def stage_text(data, aid):
    area = AREAS[aid]
    stage = count(data["progress"], aid)
    if stage == area["stages"] - 1:
        return f"ステージ {area['stages']}/{area['stages']}（ボス）"
    return f"ステージ {stage + 1}/{area['stages']}"


def area_card(data, aid):
    area = AREAS[aid]
    stage = count(data["progress"], aid)
    lo, hi = area["lv"]
    html = f'<div class="card"><span class="name">{area["name"]}</span><span class="lv">推奨Lv.{lo}〜{hi}</span>'
    html += f'<div class="stage">{stage_text(data, aid)}</div>'
    if data.get("in_area") and data.get("lineup"):
        html += f'<div class="sub">今回出るモンスター：{"、".join(data["lineup"])}</div>'
    html += f'<div class="sub">クリア {count(data["clears"], aid)}回'
    if area["rares"]:
        html += " ／ レア出現あり"
    html += "</div>"
    html += stat_row("進み具合", f'{stage}/{area["stages"]}', stage / area["stages"], "#3b5b8c")
    html += "</div>"
    return html


def area_row(data, i):
    """エリア一覧の1エリア分"""
    area = AREAS[i]
    lo, hi = area["lv"]
    mark = "開放済み" if is_unlocked(data, i) else "未開放"
    html = f'<div class="area">{area["name"]}<span class="lv">推奨Lv.{lo}〜{hi} ／ {area["stages"]}ステージ ／ {mark}</span>'
    if not is_unlocked(data, i):
        for c in area["unlock"]:
            text, cur, need = cond_text(data, c)
            ok = cur >= need
            html += f'<div class="cond{" ok" if ok else ""}">{"✓" if ok else "・"} {text}（{min(cur, need)}/{need}）</div>'
    return html + "</div>"


def usable_key(data, i):
    """このエリアの開放に使えるカギ（持っていて、まだ使っていないもの）。なければ None"""
    if is_unlocked(data, i):
        return None
    for c in AREAS[i]["unlock"]:
        if c[0] == "key" and c[1] not in data["used_keys"] and data["items"].get(c[1], 0) > 0:
            return c[1]
    return None


def starter_table():
    html = '<table class="t"><tr><th>名前</th><th>属性</th><th>HP</th><th>こうげき</th><th>ぼうぎょ</th><th>すばやさ</th></tr>'
    for name in STARTERS:
        b = SPECIES[name]
        html += (
            f'<tr><td>{name}</td><td>{b["element"]}</td><td>{b["hp_max"]}</td>'
            f'<td>{b["atk"]}</td><td>{b["dfn"]}</td><td>{b["spd"]}</td></tr>'
        )
    return html + "</table>"


def nature_table():
    html = '<div class="note" style="margin-bottom:6px">伸びやすい能力は1.5倍、伸びにくい能力は0.5倍上がる（2ポイントで HP +9／+3、MP +6／+2、ほか +3／+1）</div>'
    html += '<table class="t"><tr><th>性格</th><th>伸びやすい</th><th>伸びにくい</th></tr>'
    for n, (up, down) in NATURES.items():
        html += f'<tr><td>{n}</td><td>{STAT_NAMES[up] if up else "ー"}</td><td>{STAT_NAMES[down] if down else "ー"}</td></tr>'
    html += '</table>'
    html += '<div class="note" style="margin:12px 0 6px">性格で最終進化が変わるモンスター（変わった姿は進化のとき、その能力がさらに1割上がる）</div>'
    html += '<table class="t"><tr><th>種族</th><th>ふつうの最終進化</th><th>別の最終進化</th><th>性格</th><th>さらに1割</th></tr>'
    for t, (alt, ns, key) in BRANCH.items():
        html += f'<tr><td>{t}</td><td>{EVO[t][-1]}</td><td>{alt}</td><td>{"・".join(ns)}</td><td>{STAT_NAMES[key]}</td></tr>'
    return html + '</table>'


def compat_table():
    html = '<div class="note" style="margin-bottom:6px">火 → 草 → 土 → 雷 → 水 → 火（矢印の先に強い）<br>全属性（一部のボス）：相性なし。どの属性で攻めても、攻められても1.0倍</div>'
    html += '<table class="t"><tr><th>攻撃 ＼ 相手</th>'
    for d in ELEMENTS:
        html += f"<th>{d}</th>"
    html += "</tr>"
    for a in ELEMENTS:
        html += f"<tr><th>{a}</th>"
        for d in ELEMENTS:
            mult = element_multiplier(a, d)
            mark = "◎ 1.5倍" if mult > 1 else ("△ 0.7倍" if mult < 1 else "ー")
            html += f"<td>{mark}</td>"
        html += "</tr>"
    return html + "</table>"


# DEX_ORDER は上（モンスターのところ）で作っている
DEX_COLS = 5


DEX_SORTS = ["番号", "属性", "種族"]
DEX_FILTERS = ["全部", "つかまえた", "出会っただけ", "まだ"]


def dex_table(data, sort="番号", filt="全部"):
    """ずかん：つかまえた（ボスは倒した）ものは黒、出会っただけはグレー、まだは？？？"""
    caught = set(data.get("dex", []))
    seen = set(data.get("seen", [])) | caught
    entries = []
    for no, name in enumerate(DEX_ORDER, 1):
        state = "got" if name in caught else ("seen" if name in seen else "none")
        if filt == "つかまえた" and state != "got" or filt == "出会っただけ" and state != "seen" or filt == "まだ" and state != "none":
            continue
        entries.append((no, name, state))

    def sort_key(e):
        no, name, state = e
        if state == "none" or sort == "番号":  # まだのものは手がかりにならないよう、番号順で最後に
            return (1 if state == "none" and sort != "番号" else 0, "", no)
        sp = SPECIES[FORM_INFO[name][0]]
        if sort == "属性":
            el = sp["element"]
            return (0, str(ELEMENTS.index(el) if el in ELEMENTS else 9), no)
        return (0, f"{GROUP_ORDER.index(GROUP_OF[sp['type']]):02d}", no)

    entries.sort(key=sort_key)
    if not entries:
        return '<div class="note">あてはまるモンスターがいない。</div>'
    html = '<table class="t dex">'
    for i, (no, name, state) in enumerate(entries):
        if i % DEX_COLS == 0:
            html += "<tr>"
        if state != "none":
            sp = SPECIES[FORM_INFO[name][0]]
            kind = GROUP_OF[sp["type"]]
            body = f'<span class="{state}">{name}<br>{element_tag(sp["element"])}<span class="dexsub">{kind}</span></span>'
        else:
            body = '<span class="dexsub">？？？</span>'
        html += f'<td><span class="dexno">No.{no:03d}</span><br>{body}</td>'
        if i % DEX_COLS == DEX_COLS - 1 or i == len(entries) - 1:
            html += "</tr>"
    return html + "</table>"


BOX_SORTS = ["番号", "属性", "種族", "レベル"]


def box_order(data, sort):
    """ボックスの表示順（中の順番は変えない）"""
    idxs = list(range(len(data["party"])))
    P = data["party"]
    if sort == "属性":
        idxs.sort(key=lambda i: (ELEMENTS.index(P[i]["element"]) if P[i]["element"] in ELEMENTS else 9, i))
    elif sort == "種族":
        idxs.sort(key=lambda i: (GROUP_ORDER.index(GROUP_OF[SPECIES[P[i]["species"]]["type"]]), i))
    elif sort == "レベル":
        idxs.sort(key=lambda i: (-P[i]["level"], i))
    return idxs


# ===== 画面 =====
st.set_page_config(page_title="MONSTER LOG" if PUBLIC_MODE else "メモ", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

gold_html = f'<span class="gold">{data["gold"]} G</span>' if data["party"] else ""
st.markdown(f'<div class="header"><div>MONSTER LOG<span>v4.1{" DEMO" if DEMO_MODE else ""}</span></div>{gold_html}</div>', unsafe_allow_html=True)


def act(func, *args):
    func(data, *args)
    save_data(data)
    st.rerun()


def save_box(where):
    """公開版のセーブ：書き出す（ダウンロード）・読み込む（アップロード）"""
    st.download_button(
        "セーブを書き出す", data=json.dumps(data, ensure_ascii=False), file_name="monster_log_save.json",
        mime="application/json", key=f"save_dl_{where}", use_container_width=True,
    )
    up = st.file_uploader("セーブを読み込む（書き出したファイルを選ぶ）", type=["json"], key=f"save_up_{where}")
    if up is not None and st.button("このセーブで遊ぶ", key=f"save_load_{where}", type="primary", use_container_width=True):
        try:
            raw = json.loads(up.getvalue().decode("utf-8"))
            if not isinstance(raw, dict) or not isinstance(raw.get("party"), list):
                raise ValueError
            new = load_data(raw)
        except Exception:
            st.error("このファイルは読み込めない。書き出したセーブファイルを選んでください。")
        else:
            data.clear()
            data.update(new)
            add_log(data, "セーブを読み込んだ。")
            st.rerun()


# --- 最初のモンスター選び ---
if not data["party"]:
    if PUBLIC_MODE:
        with st.expander("続きから遊ぶ（セーブを読み込む）"):
            save_box("start")
    st.markdown('<div class="section">最初のパートナーを選ぶ</div>', unsafe_allow_html=True)
    st.markdown(starter_table(), unsafe_allow_html=True)
    st.markdown('<div class="section">パートナー</div>', unsafe_allow_html=True)
    choice = st.radio("モンスター", STARTERS, horizontal=True, label_visibility="collapsed")
    if st.button(f"{choice}にする", type="primary", key="choose"):
        starter = make_monster(choice)
        starter["nature"] = "まじめ"
        starter["name"] = form_name(choice, starter["stage"], "まじめ")
        data["party"].append(starter)
        data["dex"] = [choice]
        data["seen"] = [choice]
        data["seen_v1"] = True
        data["dex_v2"] = True
        data["dex_starter"] = True
        data["boss_v2"] = True
        data["area_v2"] = True
        add_log(data, f"{choice}がパートナーになった。")
        save_data(data)
        st.rerun()
    st.stop()


def item_box(prefix, idx=None):
    """開閉できる持ち物の枠（prefix はタブごとにボタンを区別するため、idx は使う相手）"""
    with st.expander("持ち物"):
        if idx is not None and not data["battle"]:
            st.markdown(f'<div class="note">使う相手：{data["party"][idx]["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="note">所持金 {data["gold"]} G</div>', unsafe_allow_html=True)
        owned = [n for n in ITEMS if data["items"].get(n, 0) > 0]
        if not owned:
            st.markdown('<div class="note">何も持っていない。探索や戦闘で手に入る。</div>', unsafe_allow_html=True)
        for name in owned:
            c1, c2 = st.columns([3, 2])
            c1.markdown(
                f'<div class="note" style="padding-top:8px">{name} ×{data["items"][name]}　（{item_effect(name)}）</div>',
                unsafe_allow_html=True,
            )
            if ITEMS[name][0] in ("net", "mat", "equip"):
                continue  # ネットは戦闘中の「つかまえる」で使う、ドロップ品は売る・材料
            if ITEMS[name][0] in ("hp", "mp") and ITEMS[name][1] < 9999:
                b1, b2 = c2.columns(2)
                if b1.button("使う", key=f"use_{prefix}_{name}", disabled=data["battle"] is not None):
                    act(do_use_item, name, idx)
                if b2.button("満タン", key=f"full_{prefix}_{name}", disabled=data["battle"] is not None):
                    act(do_use_until_full, name, idx)
            elif c2.button("使う", key=f"use_{prefix}_{name}", disabled=data["battle"] is not None):
                act(do_use_item, name, idx)


m = active_monster(data)
tab_train, tab_explore, tab_shop, tab_party, tab_compat = st.tabs(["育成", "探索", "ショップ", "なかま", "詳細"])

# --- 育成 ---
with tab_train:
    ti = data["active"]
    if len(data["team"]) > 1:
        prev = st.session_state.get("train_last")
        ti = st.radio(
            "育てるモンスター", data["team"], horizontal=True,
            index=data["team"].index(prev) if prev in data["team"] else data["team"].index(data["active"]),
            format_func=lambda i: ("★" if i == data["active"] else "") + f"{data['party'][i]['name']} Lv.{data['party'][i]['level']}"
                                  + (f"（{data['party'][i]['points']}pt）" if data["party"][i]["points"] else ""),
            key=f"train_pick_{'_'.join(map(str, data['team']))}",
        )
        st.session_state["train_last"] = ti
        st.markdown('<div class="note">パーティーの中から育てるモンスターを選ぶ（★＝先頭。ここで選んでも先頭は変わらない）</div>', unsafe_allow_html=True)
    tm = data["party"][ti]
    st.markdown(monster_card(tm), unsafe_allow_html=True)
    if can_evolve(tm):
        nxt_name = form_name(tm["species"], tm["stage"] + 1, tm.get("nature"))
        if st.button(f"進化する（{tm['name']} → {nxt_name}）", type="primary", key="evolve", disabled=data["battle"] is not None):
            act(do_evolve, ti)

    st.markdown('<div class="section">能力ポイント（HPは1ポイントで +3、MPは +2）</div>', unsafe_allow_html=True)
    if tm["points"] > 0:
        st.markdown(f'<div class="points">のこり {tm["points"]} ポイント</div>', unsafe_allow_html=True)
        for key, label in STAT_NAMES.items():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            full = tm[key] >= stat_cap(tm, key)
            c1.markdown(
                f'<div class="note" style="padding-top:8px">{label}　{tm[key]}{plus_text(tm, key)} / {stat_cap(tm, key)}{"（上限）" if full else ""}</div>',
                unsafe_allow_html=True,
            )
            if c2.button("+1", key=f"p1_{key}", disabled=full):
                act(do_allocate, key, 1, ti)
            if c3.button("+5", key=f"p5_{key}", disabled=full):
                act(do_allocate, key, 5, ti)
            if c4.button("+10", key=f"p10_{key}", disabled=full):
                act(do_allocate, key, 10, ti)
    else:
        st.markdown('<div class="note">レベルアップでポイントがもらえる（Lv29まで10・Lv30から15・Lv60から20、HP・MPも全回復）。<br>上限：HP 3000 ／ MP 999 ／ ほかは999</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">装備（1回以上進化したモンスターに1つ）</div>', unsafe_allow_html=True)
    if tm["stage"] < 1:
        st.markdown('<div class="note">進化すると装備を付けられる。</div>', unsafe_allow_html=True)
    else:
        if tm.get("equip"):
            e1, e2 = st.columns([3, 1])
            e1.markdown(f'<div class="note" style="padding-top:8px">いまの装備：{tm["equip"]}（{equip_text(tm["equip"])}）</div>', unsafe_allow_html=True)
            if e2.button("外す", key="unequip", disabled=data["battle"] is not None, use_container_width=True):
                act(do_unequip, ti)
        bag = [n for n in EQUIPS if data["items"].get(n, 0) > 0]
        if bag:
            e3, e4 = st.columns([3, 1])
            eq = e3.selectbox("付ける装備", bag, format_func=lambda n: f"{n}（{equip_text(n)}）", key=f"eq_pick_{len(bag)}", label_visibility="collapsed")
            if e4.button("付ける" if not tm.get("equip") else "付けかえる", key="equip", disabled=data["battle"] is not None, use_container_width=True):
                act(do_equip, eq, ti)
        elif not tm.get("equip"):
            st.markdown('<div class="note">付けられる装備を持っていない。ショップの「装備」で買える。</div>', unsafe_allow_html=True)

    item_box("t", ti)

# --- 探索 ---
auto = data.get("auto")
auto_running = bool(auto and auto["running"])
with tab_explore:
    if auto_running:
        aa = AREAS[auto["area"]]
        st.markdown(f'<div class="section">自動周回中 ／ {aa["name"]} ／ {stage_text(data, auto["area"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card note">{auto_summary(data)}</div>', unsafe_allow_html=True)
        st.markdown(battle_card(m), unsafe_allow_html=True)
        st.markdown(team_html(data), unsafe_allow_html=True)
        st.button("止める", type="primary", key="auto_stop", on_click=on_stop_auto)
        item_box("a")
        if data.get("last_battle_log"):
            st.markdown('<div class="section">直前の戦闘</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card log">{"<br>".join(data["last_battle_log"])}</div>', unsafe_allow_html=True)
    elif data["battle"]:
        enemy = data["battle"]["enemy"]
        baid = data["battle"]["area"]
        st.markdown(f'<div class="section">せんとう ／ {AREAS[baid]["name"]} ／ {stage_text(data, baid)}</div>', unsafe_allow_html=True)
        bf = data["battle"]["buff"]
        st.markdown(battle_card(enemy, show_mp=False, buff=bf["e"]), unsafe_allow_html=True)
        st.markdown('<div class="vs">VS</div>', unsafe_allow_html=True)
        st.markdown(battle_card(m, buff=bf["p"]), unsafe_allow_html=True)
        if len(data["team"]) > 1:
            st.markdown(team_html(data), unsafe_allow_html=True)

        skills = skills_of(m)
        cols = st.columns(1 + len(skills))
        if cols[0].button("こうげき", type="primary", key="b_attack"):
            act(do_battle, "attack")
        for i, s in enumerate(skills):
            if cols[i + 1].button(f"{s['name']}（MP{s['mp']}）", key=f"b_skill{i}", disabled=m["mp"] < s["mp"]):
                act(do_battle, "skill", i)
        if st.button(f"にげる（成功率 {flee_chance(m, enemy)}%）", key="b_flee"):
            act(do_battle, "flee")

        usable = [n for n in ITEMS if data["items"].get(n, 0) > 0 and ITEMS[n][0] in ("hp", "mp")]
        if usable:
            c3, c4 = st.columns([3, 1])
            # 個数が変わったら表示を作り直す（選んでいたアイテムはそのまま）
            prev = st.session_state.get("b_pick_last")
            pick = c3.selectbox(
                "アイテム", usable, index=usable.index(prev) if prev in usable else 0,
                format_func=lambda n: f"{n} ×{data['items'][n]}（{item_effect(n)}）",
                label_visibility="collapsed", key="b_pick_" + "_".join(str(data["items"][n]) for n in usable),
            )
            st.session_state["b_pick_last"] = pick
            if c4.button("使う", key="b_item"):
                act(do_battle, "item", pick)
        else:
            st.markdown('<div class="note">使えるアイテムがない。</div>', unsafe_allow_html=True)

        st.markdown('<div class="section">つかまえる</div>', unsafe_allow_html=True)
        if enemy.get("kind") != "boss":
            gok, gwhy = can_gentle(m, enemy)
            g1, g2 = st.columns([1.4, 3])
            if g1.button(f"てかげん（MP{GENTLE_MP}）", key="b_gentle", disabled=not gok, use_container_width=True):
                act(do_battle, "gentle")
            bonus = catch_bonus(data, enemy)
            g2.markdown(f'<div class="note" style="padding-top:8px">ダメージ半分・HPを必ず1残す（{GENTLE_GAP}レベル以上格下だけ、レア不可）{"　／　使えない：" + gwhy if not gok else ""}'
                        + (f'<br>開放ボーナス：捕獲率 +{bonus}%' if bonus else "") + '</div>', unsafe_allow_html=True)
        nets = [n for n in ITEMS if ITEMS[n][0] == "net" and data["items"].get(n, 0) > 0]
        if enemy.get("kind") == "boss":
            st.markdown('<div class="note">ボスはつかまえられない。</div>', unsafe_allow_html=True)
        elif len(data["party"]) >= PARTY_MAX:
            st.markdown(f'<div class="note">ボックスがいっぱい（{PARTY_MAX}体）。</div>', unsafe_allow_html=True)
        elif not nets:
            st.markdown('<div class="note">ネットを持っていない。ショップで買える。</div>', unsafe_allow_html=True)
        else:
            c5, c6 = st.columns([3, 1])
            prev = st.session_state.get("b_net_last")
            net = c5.selectbox(
                "ネット", nets, index=nets.index(prev) if prev in nets else 0,
                format_func=lambda n: f"{n} ×{data['items'][n]}　確率 {catch_chance(n, enemy, data)}%",
                label_visibility="collapsed",
                key="b_net_" + "_".join(f"{data['items'][n]}-{catch_chance(n, enemy, data)}" for n in nets),
            )
            st.session_state["b_net_last"] = net
            if c6.button("なげる", key="b_catch"):
                act(do_battle, "net", net)
            if enemy.get("kind") == "rare":
                st.markdown('<div class="note">レアモンスターはつかまえにくい（確率半分）。</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="card log">{"<br>".join(data["battle"]["log"])}</div>', unsafe_allow_html=True)
    else:
        unlocked = [i for i in range(len(AREAS)) if is_unlocked(data, i)]
        if data["area"] not in unlocked:
            data["area"] = 0
        pick = st.selectbox(
            "エリア", unlocked, index=unlocked.index(data["area"]),
            format_func=lambda i: f"{AREAS[i]['name']}（推奨Lv.{AREAS[i]['lv'][0]}〜{AREAS[i]['lv'][1]}）　{stage_text(data, i)}",
            label_visibility="collapsed", key="area_pick",
        )
        if pick != data["area"]:
            data["area"] = pick
            data["in_area"] = False
            save_data(data)
        st.markdown(area_card(data, data["area"]), unsafe_allow_html=True)
        st.markdown(battle_card(m), unsafe_allow_html=True)
        st.markdown(team_html(data), unsafe_allow_html=True)
        if len(data["team"]) > 1:
            lead = st.radio(
                "先頭（戦うモンスター）", data["team"], index=data["team"].index(data["active"]), horizontal=True,
                format_func=lambda i: f"{data['party'][i]['name']} Lv.{data['party'][i]['level']}",
                key=f"lead_{'_'.join(map(str, data['team']))}_{data['active']}",
            )
            if lead != data["active"]:
                act(do_switch, lead)
        st.markdown('<div class="note">パーティーは「なかま」タブで3体まで決められる。戦闘中以外ならいつでも先頭を交代できる。</div>', unsafe_allow_html=True)
        rates = " ／ ".join(f"{k} {v}%" for k, v in EXPLORE_EVENTS.items())
        st.markdown(f'<div class="note">モンスターを倒すと1ステージ進む<br>進むと起きること：{rates}</div>', unsafe_allow_html=True)
        if data.get("clear_notice") and not auto_running:
            st.markdown(f'<div class="card clear">{data["clear_notice"]} クリア！</div>', unsafe_allow_html=True)
        if auto and auto.get("end"):
            st.markdown(f'<div class="section">自動周回の結果（{auto["end"]}）</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card note">{auto_summary(data)}</div>', unsafe_allow_html=True)
            st.button("結果を閉じる", key="auto_close", on_click=on_close_auto)
        if data.get("in_area"):
            c1, c2 = st.columns([3, 1])
            if c1.button("進む", type="primary", key="explore", use_container_width=True):
                act(do_explore)
            if c2.button("エリアを出る", key="leave", use_container_width=True):
                act(do_leave_area)
        elif st.button("エリアに入る", type="primary", key="enter"):
            act(do_enter_area)
        with st.expander("自動周回"):
            st.markdown('<div class="note">自分は通常攻撃のみ。全ステージクリアで1周。HPが20%以下になると、HPが多い控えに自動で交代する。全員たおれたら止まる。</div>', unsafe_allow_html=True)
            laps = st.number_input("周回数", min_value=1, max_value=99, value=1, step=1, key="auto_laps")
            hp_items = ["使わない"] + [n for n in ITEMS if ITEMS[n][0] == "hp" and data["items"].get(n, 0) > 0]
            heal = st.selectbox(
                "使う回復アイテム", hp_items,
                format_func=lambda n: n if n == "使わない" else f"{n} ×{data['items'][n]}（{item_effect(n)}）", key="auto_item",
            )
            th = st.radio("回復するタイミング", [30, 50, 70], index=1, horizontal=True, format_func=lambda v: f"HP {v}%以下", key="auto_th")
            if st.button("自動周回をはじめる", type="primary", key="auto_start"):
                act(start_auto, int(laps), None if heal == "使わない" else heal, th / 100)
        item_box("e")
        with st.expander("エリア一覧・開放条件"):
            with st.container(key="arealist"):
                for i in range(len(AREAS)):
                    st.markdown(area_row(data, i), unsafe_allow_html=True)
                    key_item = usable_key(data, i)
                    if key_item and st.button(f"{key_item}を使う", type="primary", key=f"usekey_{i}"):
                        act(do_use_item, key_item)

# --- ショップ ---
def key_press(k):
    q = st.session_state.get("shop_qty", "")
    if k == "消す":
        q = q[:-1]
    elif k == "C":
        q = ""
    elif len(q) < len(str(SHOP_MAX)):
        q = (q + k).lstrip("0")
    st.session_state["shop_qty"] = str(min(int(q), SHOP_MAX)) if q else ""


def keypad(maxn):
    """個数を入れる数字キーパッド。入っている個数を返す"""
    q = st.session_state.get("shop_qty", "")
    if q and int(q) > maxn:
        q = str(maxn) if maxn > 0 else ""
        st.session_state["shop_qty"] = q
    st.markdown(f'<div class="qty"><small>個数（最大{maxn}）</small>{q or "0"}</div>', unsafe_allow_html=True)
    with st.container(key="keypad"):
        for row in (["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["C", "0", "消す"]):
            for col, k in zip(st.columns(3), row):
                col.button(k, key=f"kp_{k}", on_click=key_press, args=(k,), use_container_width=True)
    return int(q) if q else 0


with tab_shop:
    st.markdown(f'<div class="section">ショップ ／ 所持金 {data["gold"]} G</div>', unsafe_allow_html=True)
    mode = st.radio("ショップ", ["買う", "売る", "装備"], horizontal=True, key="shop_mode", label_visibility="collapsed")
    if mode == "装備":
        st.markdown('<div class="note">お金とドロップ品で作る。各装備1つまで。付けられるのは1回以上進化したモンスター（育成タブで付ける）。</div>', unsafe_allow_html=True)
        with st.container(key="equipshop"):
            for name, e in EQUIPS.items():
                ok, why = can_buy_equip(data, name)
                mats = "、".join(f"{m}×{n}（所持{data['items'].get(m, 0)}）" for m, n in e["mats"].items())
                c1, c2 = st.columns([4, 1])
                color = "#2f3a4a" if ok or why in ("お金が足りない", "材料が足りない") else "#9aa3b0"
                c1.markdown(f'<div class="note" style="color:{color}"><b>{name}</b>　{equip_text(name)}<br>{e["gold"]}G ＋ {mats}'
                            + (f'<br>{why}' if why else "") + '</div>', unsafe_allow_html=True)
                if c2.button("買う", key=f"eqbuy_{name}", type="primary", disabled=not ok, use_container_width=True):
                    act(do_buy_equip, name)
    elif mode == "買う":
        lines, open_items = [], []
        for name, (price, aid) in SHOP.items():
            if shop_open(data, aid):
                open_items.append(name)
                lines.append(f'{name}　{price}G　（{item_effect(name)}）　所持 {data["items"].get(name, 0)}')
            else:
                lines.append(f'<span style="color:#9aa3b0">{name}　―　「{AREAS[aid]["name"]}」が開放されると並ぶ</span>')
        st.markdown(f'<div class="card note">{"<br>".join(lines)}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section">買うもの</div>', unsafe_allow_html=True)
        pick = st.radio("買うもの", open_items, key="shop_pick", label_visibility="collapsed",
                        format_func=lambda n: f"{n}（{SHOP[n][0]}G）")
        left, _ = st.columns([1, 1])
        with left:
            qty = keypad(SHOP_MAX)
            total = SHOP[pick][0] * qty
            short = data["gold"] < total
            label = f"{qty}個買う（{total}G）" + ("　お金が足りない" if short and qty else "")
            if st.button(label, type="primary", key="shop_buy", disabled=qty == 0 or short, use_container_width=True):
                st.session_state["shop_qty"] = ""
                act(do_buy, pick, qty)
    else:
        sellable = [n for n in ITEMS if data["items"].get(n, 0) > 0 and sell_price(n)]
        if not sellable:
            st.markdown('<div class="note">売れるものを持っていない。（カギは売れない）</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section">売るもの（カギは売れない）</div>', unsafe_allow_html=True)
            prev = st.session_state.get("sell_last")
            pick = st.radio(
                "売るもの", sellable, index=sellable.index(prev) if prev in sellable else 0, key=f"sell_pick_{len(sellable)}",
                label_visibility="collapsed",
                format_func=lambda n: f"{n} ×{data['items'][n]}　（1個 {sell_price(n)}G）",
            )
            st.session_state["sell_last"] = pick
            left, _ = st.columns([1, 1])
            with left:
                qty = keypad(min(SHOP_MAX, data["items"][pick]))
                total = sell_price(pick) * qty
                if st.button(f"{qty}個売る（+{total}G）", type="primary", key="shop_buy", disabled=qty == 0, use_container_width=True):
                    st.session_state["shop_qty"] = ""
                    act(do_sell, pick, qty)

# キーボードで個数を入れる（数字＝キー、Backspace＝消す、Esc／Delete＝C、Enter＝買う）
# 画面の中だけで動く仕組み。外部との通信はしない。
KEYPAD_JS = """
<script>
const doc = window.parent.document;
if (!doc.getElementById("kp-keyboard")) {
  const sc = doc.createElement("script");
  sc.id = "kp-keyboard";
  sc.textContent = `
    document.addEventListener("keydown", function (e) {
      const pad = document.querySelector(".st-key-keypad");
      if (!pad || pad.getClientRects().length === 0) return;  // ショップを開いていないときは何もしない
      const tag = (document.activeElement && document.activeElement.tagName) || "";
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      let label = null;
      if (/^[0-9]$/.test(e.key)) label = e.key;
      else if (e.key === "Backspace") label = "消す";
      else if (e.key === "Escape" || e.key === "Delete") label = "C";
      let btn = null;
      if (label) {
        btn = Array.from(pad.querySelectorAll("button")).find(b => b.innerText.trim() === label);
      } else if (e.key === "Enter") {
        btn = document.querySelector(".st-key-shop_buy button");
      }
      if (btn && !btn.disabled) { e.preventDefault(); btn.click(); }
    });
  `;
  doc.body.appendChild(sc);
}
// タブ（育成・探索…）をタイトルの行のすぐ下に固定する（Streamlitのバージョンが違っても効くように）
if (!doc.getElementById("ml-sticky")) {
  const sc2 = doc.createElement("script");
  sc2.id = "ml-sticky";
  sc2.textContent = `
    function mlSticky() {
      const head = document.querySelector(".stElementContainer:has(.header)") || document.querySelector(".element-container:has(.header)");
      const list = document.querySelector(".stTabs [role='tablist']");
      if (!head || !list) return;
      // タブの一覧だけを包んでいるいちばん外側の箱を固定する
      let box = list;
      while (box.parentElement && !box.parentElement.classList.contains("stTabs") && !box.parentElement.querySelector("[role='tabpanel']")) {
        box = box.parentElement;
      }
      const top = head.getBoundingClientRect().height + (parseFloat(getComputedStyle(head).top) || 0);
      box.style.position = "sticky";
      box.style.top = top + "px";
      box.style.zIndex = "99";
      box.style.background = "#f4f5f7";
      // 固定のじゃまになる「はみ出し禁止」の設定を外す（スクロールする本体は除く）
      let up = box.parentElement;
      while (up && !up.matches("[data-testid='stMain'], section.main, [data-testid='stAppViewContainer']")) {
        if (getComputedStyle(up).overflow !== "visible") up.style.overflow = "visible";
        up = up.parentElement;
      }
    }
    setInterval(mlSticky, 500);
  `;
  doc.body.appendChild(sc2);
}
</script>
"""
with tab_shop:
    if hasattr(st, "iframe"):  # 新しいStreamlit
        st.iframe(KEYPAD_JS, height=1)
    else:
        components.html(KEYPAD_JS, height=0)
    st.markdown('<div class="note">キーボードの数字でも入力できる（Backspace＝消す、Esc＝C、Enter＝買う・売る）</div>', unsafe_allow_html=True)

# --- なかま ---
def pick_party(i):
    st.session_state["party_pick_last"] = i


def cell_label(i):
    pm = data["party"][i]
    mark = "★" if i == data["active"] else ("◆" if i in data["team"] else "")
    return f"{mark}{pm['name']}  \nLv.{pm['level']}　{pm['element']}  \n{pm.get('nature', '')}"


with tab_party:
    party = data["party"]
    busy = data["battle"] is not None or auto_running
    sel = st.session_state.get("party_pick_last")
    if sel is None or not 0 <= sel < len(party):
        sel = data["active"]

    st.markdown(f'<div class="section">パーティー（{len(data["team"])}/{TEAM_MAX}） ★＝先頭 ◆＝パーティー</div>', unsafe_allow_html=True)
    with st.container(key="teamgrid"):
        cols = st.columns(DEX_COLS)
        for c, i in zip(cols, data["team"]):
            c.button(cell_label(i), key=f"cell_t{i}", on_click=pick_party, args=(i,),
                     type="primary" if i == sel else "secondary", use_container_width=True)

    st.markdown(f'<div class="section">ボックス ／ なかま {len(party)}/{PARTY_MAX}体</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    bsort = c1.selectbox("並び順", BOX_SORTS, key="box_sort")
    order = box_order(data, bsort)
    box = c2.selectbox(
        "ボックス", list(range(BOX_COUNT)), key="box_no",
        format_func=lambda b: f"ボックス{b + 1}（{len(order[b * BOX_SIZE:(b + 1) * BOX_SIZE])}/{BOX_SIZE}）",
    )
    page = order[box * BOX_SIZE:(box + 1) * BOX_SIZE]
    if not page:
        st.markdown('<div class="note">このボックスは空。戦闘中に「つかまえる」でネットを使うと入る。</div>', unsafe_allow_html=True)
    with st.container(key="boxgrid"):
        for r in range(0, len(page), DEX_COLS):
            cols = st.columns(DEX_COLS)
            for c, i in zip(cols, page[r:r + DEX_COLS]):
                c.button(cell_label(i), key=f"cell_b{i}", on_click=pick_party, args=(i,),
                         type="primary" if i == sel else "secondary", use_container_width=True)

    st.markdown('<div class="section">えらんだモンスター</div>', unsafe_allow_html=True)
    st.markdown(monster_card(party[sel]), unsafe_allow_html=True)
    if busy:
        st.markdown('<div class="note">戦闘中・自動周回中はパーティーを変えられない。</div>', unsafe_allow_html=True)
    if sel == data["active"]:
        st.markdown('<div class="note">いまの先頭（戦うモンスター）。</div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2)
        if c1.button("先頭（戦うモンスター）にする", type="primary", key="switch", disabled=busy, use_container_width=True):
            act(do_switch, sel)
        if sel in data["team"]:
            if c2.button("パーティーから外す", key="team_out", disabled=busy, use_container_width=True):
                act(do_team_remove, sel)
        else:
            full = len(data["team"]) >= TEAM_MAX
            if c2.button("パーティーに入れる" + ("（いっぱい）" if full else ""), key="team_in", disabled=busy or full, use_container_width=True):
                act(do_team_add, sel)
        with st.expander("にがす"):
            ok = st.checkbox(f"本当に{party[sel]['name']}（Lv.{party[sel]['level']}）をにがす", key=f"rel_ok_{sel}_{len(party)}")
            if st.button("にがす", key="release", disabled=not ok or busy):
                st.session_state["party_pick_last"] = None
                act(do_release, sel)

    n_got = len(data.get("dex", []))
    ready = [r for r in DEX_REWARDS if r[0] <= n_got and r[0] not in data["dex_claimed"]]
    st.markdown(f'<div class="section">ずかん報酬 ／ 登録 {n_got}/{len(DEX_ORDER)}' + (f'　<b style="color:#3b5b8c">受け取れる報酬 {len(ready)}件</b>' if ready else '') + '</div>', unsafe_allow_html=True)
    with st.expander("報酬リスト", expanded=bool(ready)):
        with st.container(key="rewardlist"):
            for need, items, gold in DEX_REWARDS:
                got = need in data["dex_claimed"]
                c1, c2 = st.columns([4, 1])
                state = "受け取りずみ" if got else ("達成" if n_got >= need else f"あと{need - n_got}")
                color = "#aab1bc" if got else ("#2f3a4a" if n_got >= need else "#7a8494")
                c1.markdown(f'<div class="note" style="color:{color};padding-top:6px"><b>登録{need}</b>（{state}）　{reward_text(items, gold)}</div>', unsafe_allow_html=True)
                if n_got >= need and not got:
                    if c2.button("受け取る", type="primary", key=f"claim_{need}", use_container_width=True):
                        act(do_claim_reward, need)
    n_seen = len(set(data.get("seen", [])) | set(data.get("dex", [])))
    st.markdown(f'<div class="section">ずかん ／ 見つけた {n_seen}/{len(DEX_ORDER)} ／ つかまえた・倒したボス {len(data.get("dex", []))}/{len(DEX_ORDER)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">黒＝つかまえた（ボスは倒した） ／ グレー＝出会っただけ</div>', unsafe_allow_html=True)
    with st.expander("ずかんを見る"):
        d1, d2 = st.columns(2)
        dsort = d1.selectbox("並び順", DEX_SORTS, key="dex_sort")
        dfilt = d2.selectbox("表示", DEX_FILTERS, key="dex_filt")
        st.markdown(dex_table(data, dsort, dfilt), unsafe_allow_html=True)

# --- 相性表 ---
with tab_compat:
    if PUBLIC_MODE:
        st.markdown('<div class="section">セーブ</div>', unsafe_allow_html=True)
        st.markdown('<div class="note">ページを閉じる・読み込み直すとデータが消える。やめる前に「書き出す」で保存し、次は「読み込む」で続きから。</div>', unsafe_allow_html=True)
        save_box("tab")
    st.markdown('<div class="section">属性の相性</div>', unsafe_allow_html=True)
    st.markdown(compat_table(), unsafe_allow_html=True)
    st.markdown('<div class="section">性格（ポイントを振ったときの伸び方）</div>', unsafe_allow_html=True)
    st.markdown(nature_table(), unsafe_allow_html=True)

st.markdown('<div class="section">きろく</div>', unsafe_allow_html=True)
log_html = "<br>".join(data["log"]) if data["log"] else "まだ何もない。"
st.markdown(f'<div class="card log">{log_html}</div>', unsafe_allow_html=True)

with st.sidebar:
    if PUBLIC_MODE:
        st.caption("セーブ")
        st.markdown('<div class="note">ページを閉じる・読み込み直すとデータが消える。やめる前に「書き出す」で保存し、次は「読み込む」で続きから。</div>', unsafe_allow_html=True)
        save_box("side")
    st.caption("設定")
    if st.checkbox("データを消して最初からやり直す"):
        if st.button("本当に消す", key="reset"):
            data.clear()
            data.update(new_data())
            save_data(data)
            st.rerun()

# --- 自動周回：少し待って1回進め、画面を更新する ---
def auto_tick():
    """一定時間ごとに1回進める。画面を最後まで描いてから進めるので、前の画面の部品が残らない"""
    now = time.time()
    if now - st.session_state.get("auto_last", 0) < AUTO_INTERVAL * 0.9:
        return
    st.session_state["auto_last"] = now
    if data.get("auto", {}).get("running"):
        auto_step(data)
        save_data(data)
        st.rerun()


if auto_running:
    try:
        st.fragment(run_every=AUTO_INTERVAL)(auto_tick)()
    except (AttributeError, TypeError):  # 古いStreamlit
        time.sleep(AUTO_INTERVAL)
        if data.get("auto", {}).get("running"):
            auto_step(data)
            save_data(data)
        st.rerun()
