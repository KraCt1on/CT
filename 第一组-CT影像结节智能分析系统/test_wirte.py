# test_write.py
import os

# 使用和你的应用完全相同的路径
save_dir = r"D:\CT_Scans"
file_path = os.path.join(save_dir, "hello_world.txt")

try:
    print(f"准备在 '{save_dir}' 文件夹下创建文件...")
    os.makedirs(save_dir, exist_ok=True)
    print("os.makedirs 执行完毕。")

    print(f"准备向 '{file_path}' 写入内容...")
    with open(file_path, "w") as f:
        f.write("This is a test file.")
    print("文件写入成功！")

except Exception as e:
    print(f"！！！发生了错误！！！: {e}")

# 检查文件是否真的存在
if os.path.exists(file_path):
    print("\n验证成功：文件确实存在于磁盘上。")
else:
    print("\n验证失败：文件没有被创建。")
