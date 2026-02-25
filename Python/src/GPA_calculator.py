import pandas as pd

from pathlib import Path

FILE: Path = Path("./grade.csv")
COL_CATEGORY: str = "课程类别"
COL_CREDITS: str = "学分"
COL_GRADE: str = "成绩"
PATTERN: list[str] = [
    "专业必修",
    "专业选修",
    "学院平台课",
    "理学大类",
    "军事理论与军训",
    "思想政治理论必修课",
    "体育类",
    "大类平台课程I",
    "大学外语",
    "社科大类",
    "生命科学大类",
]


def convert_grade(s: str) -> float:
    match s:
        case "A" | "A+":
            return 4.0
        case "A-":
            return 3.7
        case "B+":
            return 3.3
        case "B":
            return 3.0
        case "B-":
            return 2.7
        case "C+":
            return 2.3
        case "C":
            return 2.0
        case "D+":
            return 1.5
        case "D":
            return 1.0
        case "F":
            return 0
        case _:
            return -1


def calculate_gpa(df: pd.DataFrame) -> float:
    
    # 筛选参与计算的课程
    mask: pd.Series[bool] = df[COL_CATEGORY].isin(PATTERN)
    df_calc: pd.DataFrame = df[mask].copy()
    df_calc["绩点"] = df_calc[COL_GRADE].apply(convert_grade)
    df_calc = df_calc[df_calc["绩点"] != -1]
    total_credits = df_calc[COL_CREDITS].sum()
    if total_credits == 0:
        return 0.0
    weighted_gpa = (df_calc["绩点"] * df_calc[COL_CREDITS]).sum() / total_credits
    return weighted_gpa


def main() -> None:
    with open(FILE) as f:
        df: pd.DataFrame = pd.read_csv(f)
    gpa = calculate_gpa(df)
    print(f"GPA: {gpa:.2f}")


if __name__ == "__main__":
    main()
