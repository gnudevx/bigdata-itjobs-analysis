import json

input_file = "cleaned_data.json"
output_file = "cleaned_data_line.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)  # đọc toàn bộ mảng JSON

with open(output_file, "w", encoding="utf-8") as f:
    for obj in data:
        json.dump(obj, f, ensure_ascii=False)
        f.write("\n")

print(f"✅ Đã chuyển {len(data)} object thành JSON lines -> {output_file}")
