"""stocks 종가에 피어슨 유사도를 적용해 유사 패턴 그래프를 저장하는 스크립트."""
import os

from similarity import (
    BACK_DIR,
    compute_similarities,
    load_close_prices,
    normalize,
    pearson_similarity,
    plot_pattern,
)

START_DATE = "2021-09-01"
END_DATE = "2021-09-20"
GRAPH_PATH = os.path.join(BACK_DIR, "pearson_graph.png")


def main():
    df = load_close_prices()
    base = normalize(df.loc[START_DATE:END_DATE]["stock_closing_price"])

    sorted_list = compute_similarities(df, base, pearson_similarity).sort_values(
        ascending=False
    ).head(20)

    second_value = sorted_list.index[1]  # 두 번째로 높은 유사도 구간
    print(second_value)

    plot_pattern(base, df, second_value, GRAPH_PATH)


if __name__ == "__main__":
    main()
