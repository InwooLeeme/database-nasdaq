"""stocks 종가에 코사인 유사도를 적용해 결과를 chart.db 및 그래프로 저장하는 스크립트."""
import os

from db import get_connection
from similarity import (
    BACK_DIR,
    compute_similarities,
    cosine_similarity,
    load_close_prices,
    normalize,
    plot_pattern,
)

START_DATE = "2018-02-01"
END_DATE = "2018-02-20"
GRAPH_PATH = os.path.join(BACK_DIR, "cosine_graph.png")


def save_similarities(conn, sorted_list):
    """상위 유사도 목록을 cosine 테이블에 갱신 저장."""
    conn.execute("CREATE TABLE IF NOT EXISTS cosine (idx int, similarity float)")
    conn.execute("DELETE FROM cosine")
    for idx, sim in sorted_list.items():
        conn.execute(
            "INSERT OR REPLACE INTO cosine (idx, similarity) VALUES (?, ?)",
            (int(idx), sim),
        )
    conn.commit()


def save_graph_image(conn, name, image_path):
    """그래프 PNG를 BLOB으로 images 테이블에 갱신 저장."""
    with open(image_path, "rb") as file:
        binary_image = file.read()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            image BLOB NOT NULL
        )"""
    )
    conn.execute("DELETE FROM images")
    conn.execute(
        "INSERT OR REPLACE INTO images (name, image) VALUES (?, ?)",
        (name, binary_image),
    )
    conn.commit()


def main():
    df = load_close_prices()
    base = normalize(df.loc[START_DATE:END_DATE]["stock_closing_price"])

    sorted_list = compute_similarities(df, base, cosine_similarity).sort_values(
        ascending=False
    ).head(20)

    print(sorted_list.head(10).to_json())
    second_value = sorted_list.index[1]  # 두 번째로 높은 유사도 구간
    print(second_value)

    plot_pattern(base, df, second_value, GRAPH_PATH)

    with get_connection() as conn:
        save_similarities(conn, sorted_list)
        save_graph_image(conn, "cosine_graph", GRAPH_PATH)


if __name__ == "__main__":
    main()
