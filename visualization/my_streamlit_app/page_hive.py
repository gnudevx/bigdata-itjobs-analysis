import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

def page_hive():
    st.title("📊 Phân Tích Dữ Liệu IT Jobs (Hive - Local Parquet)")

    options = {
        "🏙️ Top 10 Thành Phố Có Nhiều Việc Làm Nhất": r"D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\output\git_jobs_top10.txt",
        "💼 Top 10 Nhóm Công Việc Có Nhiều Việc Làm Nhất": r"D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\output\top10_jobs_group.txt",
        "🧠 Top 10 Kinh Nghiệm Được Yêu Cầu Nhiều Nhất": r"D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\output\top10_jobs_experience.txt",
        "⚙️ Top 10 Kỹ Năng Được Yêu Cầu Nhiều Nhất": r"D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\output\top10_jobs_skill.txt",
        "💰 Top 10 Công Việc Có Mức Lương Cao Nhất": r"D:\bigdata-itjobs-analysis\hive_scripts\HiveSQL\output\top10_jobs_salary.txt"
    }
    choice = st.selectbox("🔍 Chọn loại thống kê muốn xem:", list(options.keys()))
    local_file = options[choice]
    try:
        df = pd.read_parquet(local_file)
        st.success(f"✅ Đã tải dữ liệu từ: {local_file}")
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file Parquet: {e}")
        return
    st.write("📋 **Các cột có trong file:**", list(df.columns))
    st.dataframe(df, use_container_width=True)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    string_cols = df.select_dtypes(include=["object"]).columns.tolist()

    y_col = next((col for col in ["location", "group", "experience", "skill", "title"] if col in df.columns), None)
    x_col = next((col for col in ["total_jobs", "salary_normalized", "count", "sum_jobs"] if col in df.columns), None)

    if not x_col and numeric_cols:
        x_col = numeric_cols[0]
    if not y_col and string_cols:
        y_col = string_cols[0]

    if not x_col or not y_col:
        st.error("⚠️ Không tìm thấy cột phù hợp để vẽ biểu đồ.")
        return
    if choice.startswith("🏙️"):  # Top thành phố
        chart_type = "bar"
        palette = "crest"
        title = choice
    elif choice.startswith("💼"):  # Top nhóm công việc
        chart_type = "barh"  # cột ngang
        palette = "mako"
        title = choice
    elif choice.startswith("🧠"):  # Top kinh nghiệm
        chart_type = "pie"
        palette = "viridis"
        title = choice
    elif choice.startswith("⚙️"):  # Top kỹ năng
        chart_type = "pie"
        palette = "plasma"
        title = choice
    elif choice.startswith("💰"):  # Top công việc lương cao
        chart_type = "line"
        palette = "tab:blue"
        title = choice
    else:
        chart_type = "bar"
        palette = "crest"
        title = choice
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    df = df.sort_values(by=x_col, ascending=True)

    if chart_type == "bar":
        sns.barplot(data=df, x=x_col, y=y_col, palette=palette, ax=ax)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title)
    elif chart_type == "barh":
        sns.barplot(data=df, x=x_col, y=y_col, palette=palette, ax=ax)
        ax.invert_yaxis()  # đảo thứ tự cho trực quan
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title)
    elif chart_type == "pie":
        plt.pie(
            df[x_col],
            labels=df[y_col],
            autopct='%1.1f%%',
            colors=sns.color_palette(palette, len(df))
        )
        plt.title(title)
    elif chart_type == "line":
        sns.lineplot(data=df, x=x_col, y=y_col, marker="o", ax=ax, color=palette)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(title)

    st.pyplot(fig)
    st.markdown(f"**📊 Tổng số bản ghi:** {len(df)}")
    st.markdown(f"**📌 Cột hiển thị:** `{x_col}` vs `{y_col}`")
