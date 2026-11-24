import os

def remove_prefix_from_filenames(prefix="489155.com@"):
    """
    去除当前目录下所有文件名开头的指定前缀。
    如果去除前缀后的文件名已存在，则跳过该文件并给出警告。
    """
    current_dir = os.getcwd()  # 获取当前工作目录
    renamed_count = 0
    skipped_count = 0

    for filename in os.listdir(current_dir):
        # 只处理以指定前缀开头的文件（且不是目录）
        if filename.startswith(prefix) and os.path.isfile(filename):
            new_name = filename[len(prefix):]  # 去掉前缀

            # 检查新文件名是否已存在
            if os.path.exists(new_name):
                print(f"⚠️  跳过 '{filename}' → 目标文件 '{new_name}' 已存在")
                skipped_count += 1
                continue

            try:
                os.rename(filename, new_name)
                print(f"✅ 重命名: '{filename}' → '{new_name}'")
                renamed_count += 1
            except Exception as e:
                print(f"❌ 重命名失败: '{filename}'，错误: {e}")
                skipped_count += 1

    print(f"\n完成！重命名 {renamed_count} 个文件，跳过 {skipped_count} 个文件。")

if __name__ == "__main__":
    remove_prefix_from_filenames("489155.com@")
    remove_prefix_from_filenames("hhd800.com@")
    remove_prefix_from_filenames("4k688.com@")