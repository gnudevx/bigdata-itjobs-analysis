import streamlit as st
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def page_mapreduce():
    st.title("🎯 Phân Tích Dữ Liệu Tuyển Dụng với MapReduce")

    # Các tính năng phân tích
    features = {
        "Những công việc có lương hơn 10 triệu": "Luong",
        "Những Công ty ở Hà Nội hoặc Hồ Chí Minh": "DiaDiem",
        "Những công việc không yêu cầu kinh nghiệm": "KinhNghiem",
        "Những công việc cần ngôn ngữ python": "Skill",
        "Lương trung bình theo từng thành phố": "TinhTrungBinhLuong",
        "Top 10 công việc có mức lương cao nhất": "Top10CV",
        "Những kĩ năng tuyển dụng theo số lượng": "KiNangCanThiet",
        "Top 10 thành phố có nhiều việc làm nhất": "Top10DiaDiem"
    }

    # Tên cột tương ứng cho từng loại dữ liệu
    column_names = {
        "Luong": ["Công việc", "Lương (triệu VND)"],
        "DiaDiem": ["Công ty", "Thành phố"],
        "KinhNghiem": ["Công việc", "Kinh Nghiệm"],
        "Skill": ["Công việc", "Ngôn Ngữ"],
        "TinhTrungBinhLuong": ["Thành phố", "Lương trung bình"],
        "Top10CV": ["Công việc", "Lương"],
        "KiNangCanThiet": ["Kĩ năng", "Số lượng"],
        "Top10DiaDiem": ["Thành phố", "Số lượng"]
    }

    selected_feature = st.selectbox("Chọn tính năng phân tích", list(features.keys()))

    if st.button("Thực thi"):
        job_folder = features[selected_feature]
        map_path = f"/home/hadoopcong/Final_BigData/my_streamlit_app/mapreduce_jobs/{job_folder}/map.py"
        reduce_path = f"/home/hadoopcong/Final_BigData/my_streamlit_app/mapreduce_jobs/{job_folder}/reduce.py"
        input_path = "/user/hadoopcong/final.csv"
        output_path = f"/user/hadoopcong/output/{job_folder}"

        # Xóa output cũ (nếu có)
        subprocess.run(["hadoop", "fs", "-rm", "-r", output_path])

        # Chạy Hadoop Streaming
        result = subprocess.run(
            ["hadoop", "jar", "/home/hadoopcong/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar",
             "-files", f"{map_path},{reduce_path}",
             "-mapper", f"python3 {map_path}",
             "-reducer", f"python3 {reduce_path}",
             "-input", input_path,
             "-output", output_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        st.subheader("📄 Log Thực Thi:")
        st.code(result.stdout + result.stderr)

        if result.returncode != 0:
            st.error(f"❌ Lỗi khi chạy job Hadoop: {result.stderr}")
            return

        try:
            # Đọc kết quả từ HDFS
            hdfs_output = subprocess.check_output(
                ["hadoop", "fs", "-cat", f"{output_path}/part-00000"], text=True
            )

            # Phân tích dữ liệu đầu ra
            data = []
            for line in hdfs_output.splitlines():
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    key, value = parts
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                    data.append((key, value))

            if data:
                columns = column_names.get(job_folder, ["Key", "Value"])
                df = pd.DataFrame(data, columns=columns)

                st.subheader("📋 Dữ liệu chi tiết")
                st.dataframe(df)

                # Vẽ biểu đồ
                st.subheader("📊 Biểu đồ phân tích")
                fig, ax = plt.subplots()

                if job_folder == "TinhTrungBinhLuong":
                    sns.barplot(data=df, x=columns[0], y=columns[1], ax=ax)
                    ax.set_title("Lương trung bình theo thành phố")
                    ax.set_xlabel("Thành phố")
                    ax.set_ylabel("Lương trung bình")

                elif job_folder == "Top10CV":
                    sns.barplot(data=df, x=columns[1], y=columns[0], ax=ax, orient='h')
                    ax.set_title("Top 10 Công Việc Lương Cao Nhất")
                    ax.set_xlabel("Lương (triệu VND)")
                    ax.set_ylabel("Công việc")

                elif job_folder == "KiNangCanThiet":
                    sns.barplot(data=df, x=columns[0], y=columns[1], ax=ax)
                    ax.set_title("Số lượng tuyển dụng theo kỹ năng")
                    ax.set_xlabel("Kỹ năng")
                    ax.set_ylabel("Số lượng")

                elif job_folder == "Top10DiaDiem":
                    sns.barplot(data=df, x=columns[1], y=columns[0], ax=ax, orient='h')
                    ax.set_title("Top 10 Thành Phố Có Nhiều Việc Làm Nhất")
                    ax.set_xlabel("Số lượng việc làm")
                    ax.set_ylabel("Thành phố")

                elif job_folder in ["Luong", "DiaDiem", "KinhNghiem", "Skill"]:
                    sns.scatterplot(data=df, x=columns[0], y=columns[1], ax=ax)
                    ax.set_title(f"Phân tích {selected_feature}")
                    ax.set_xlabel(columns[0])
                    ax.set_ylabel(columns[1])

                st.pyplot(fig)
            else:
                st.warning("⚠️ Không có dữ liệu hiển thị.")
        except subprocess.CalledProcessError:
            st.error("❌ Không thể đọc kết quả từ HDFS!")
