import csv
from collections import defaultdict

FILE_PATH = "yearly_data.csv"


def read_data():
    with open(FILE_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def to_float(value: str) -> float:
    if value is None:
        return 0.0
    value = value.strip().replace(",", "")
    if value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def aggregate_metrics():
    revenue_by_year = defaultdict(float)
    margin_by_year = defaultdict(float)
    revenue_by_business = defaultdict(float)
    revenue_by_channel = defaultdict(float)
    revenue_by_quarter_year = defaultdict(float)
    cases_by_quarter_year = defaultdict(float)
    negative_margin_rows = 0
    total_rows = 0

    for row in read_data():
        year = int(row["Year"])
        business = row["Business"]
        channel = row["Channel"]
        g_sales = to_float(row["gSales"])
        f_gp = to_float(row["fGP"])
        month_name = row["Month Name"]

        # Rough quarter mapping from month name
        month_to_num = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }
        month_num = month_to_num.get(month_name, 0)
        if month_num:
            quarter = (month_num - 1) // 3 + 1
            revenue_by_quarter_year[(year, quarter)] += g_sales
            cases_by_quarter_year[(year, quarter)] += to_float(row["Cases"])

        revenue_by_year[year] += g_sales
        margin_by_year[year] += f_gp
        revenue_by_business[(year, business)] += g_sales
        revenue_by_channel[(year, channel)] += g_sales

        if f_gp < 0:
            negative_margin_rows += 1
        total_rows += 1

    return {
        "revenue_by_year": dict(revenue_by_year),
        "margin_by_year": dict(margin_by_year),
        "revenue_by_business": dict(revenue_by_business),
        "revenue_by_channel": dict(revenue_by_channel),
        "revenue_by_quarter_year": dict(revenue_by_quarter_year),
        "cases_by_quarter_year": dict(cases_by_quarter_year),
        "negative_margin_share": negative_margin_rows / total_rows if total_rows else 0.0,
    }


def main():
    metrics = aggregate_metrics()

    print("=== Revenue by Year ===")
    for year in sorted(metrics["revenue_by_year"]):
        print(f"{year}: €{metrics['revenue_by_year'][year]:,.0f}")

    print("\n=== Margin by Year ===")
    for year in sorted(metrics["margin_by_year"]):
        print(f"{year}: €{metrics['margin_by_year'][year]:,.0f}")

    print("\n=== Revenue by Business (latest year) ===")
    latest_year = max(metrics["revenue_by_year"])
    for (year, business), value in sorted(
        metrics["revenue_by_business"].items(), key=lambda x: (-x[1], x[0][1])
    ):
        if year == latest_year:
            print(f"{latest_year} - {business}: €{value:,.0f}")

    print("\n=== Revenue by Channel (latest year) ===")
    for (year, channel), value in sorted(
        metrics["revenue_by_channel"].items(), key=lambda x: (-x[1], x[0][1])
    ):
        if year == latest_year:
            print(f"{latest_year} - {channel}: €{value:,.0f}")

    print("\n=== Revenue by Business (trend by year) ===")
    # Build per-year business totals
    per_year_business = defaultdict(lambda: defaultdict(float))
    for (year, business), value in metrics["revenue_by_business"].items():
        per_year_business[business][year] += value
    for business, year_map in per_year_business.items():
        years = sorted(year_map)
        values = [year_map[y] for y in years]
        trend_str = ", ".join(f"{y}: €{v:,.0f}" for y, v in zip(years, values))
        print(f"{business} -> {trend_str}")

    print("\n=== Revenue by Quarter (overall) ===")
    rev_q = metrics["revenue_by_quarter_year"]
    for (year, quarter), value in sorted(rev_q.items()):
        print(f"{year} Q{quarter}: €{value:,.0f}")


    print(
        f"\nShare of rows with negative margin (fGP < 0): "
        f"{metrics['negative_margin_share']:.2%}"
    )


if __name__ == "__main__":
    main()


