import os

folder_path = "."  # المجلد الحالي
output_file = "all_codes.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            out.write(f"===== {filename} =====\n")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[لا يمكن قراءة الملف: {e}]")

            out.write("\n\n")
