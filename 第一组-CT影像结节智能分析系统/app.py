from pathlib import Path

import streamlit as st
import time
import pandas as pd

import os # <--- 1. 导入 os 库
import json

import dashscope
from http import HTTPStatus

dashscope.api_key = "sk-6fb6cb7d19f948c7b44dd038183bcce6"
# ... (其他 import) ...

# --- 新增：AI 建议生成函数 ---
def get_ai_lifestyle_advice(total, malignant, benign):
    """
    调用 Qwen-Turbo 模型，根据结节分析结果生成生活建议。
    """
    # --- 1. 精心设计的 Prompt ---
    # 这个 Prompt 告诉 AI 它的角色、任务、输入信息，以及最重要的：免责声明。
    prompt = f"""
你是一名专业的健康顾问AI，富有同理心，你的任务是为用户提供一些基于肺结节检查结果的通用性、非医疗处方的生活方式建议。

**重要规则**:
1.  **强调这不是医疗建议**: 在回答的开头，必须明确声明：“以下建议仅供参考，不能替代专业医生的诊断和治疗方案。请务必咨询您的主治医生。”
2.  **不要诊断或预测**: 绝对不要对用户的病情进行诊断、预测或给出任何治疗方案。
3.  **保持积极和鼓励的语气**: 即使有恶性结节，也要以积极、支持性的口吻提供建议。
4.  **建议要具体且可操作**: 提供一些实际可行的生活、饮食和心态调整建议。
5.  **根据数据个性化**: 根据我提供的结节数量，适当调整你的语气和建议重点。


---
**用户的检查结果摘要如下**:
- 检测到的总结节数: {total} 个
- 其中，高度疑似恶性结节数: {malignant} 个
- 其中，判断为良性结节数: {benign} 个
---

请根据以上信息，生成你的健康生活建议。
"""

    # --- 2. 调用 Dashscope API ---
    try:
        response = dashscope.Generation.call(
            model='qwen-turbo',
            prompt=prompt,
            # temperature=0.7 # 可以调整 creativity，默认为 0.85
        )

        if response.status_code == HTTPStatus.OK:
            # 返回 AI 生成的文本内容
            return response.output.text
        else:
            # 如果 API 调用失败，返回错误信息
            return (f"AI 建议服务调用失败: 状态码 {response.status_code}, "
                    f"错误码: {response.code}, 错误信息: {response.message}")

    except Exception as e:
        return f"调用 AI 服务时发生异常: {e}"

from model_evel import NoduleAnalysisApp

# --- 2. 定义目标保存文件夹路径 ---
# 使用 os.path.join 来构建跨平台兼容的路径

# SAVE_DIR = r"D:\PythonProject\test\data-unversioned\data\subset0"
# NODULE_INFO_CACHE_DIR=Path("D:\PythonProject\test\data-unversioned\noduleinfo")
# ADVICE_CACHE_DIR=Path("D:\PythonProject\test\data-unversioned\advice")



# --- 另一种正确的写法 ---
# 使用原始字符串，可以保留反斜杠 \\
SAVE_DIR = r"D:\Pypro\PythonProject\data-unversioned\data\subset0"

BASE_CACHE_DIR = Path("D:\Pypro\PythonProject/data-unversioned/")
NODULE_INFO_CACHE_DIR = BASE_CACHE_DIR / "noduleinfo"
ADVICE_CACHE_DIR = BASE_CACHE_DIR / "advice"  # 这样 "advice" 就不会被错误解析

# 确保目录存在
os.makedirs(NODULE_INFO_CACHE_DIR, exist_ok=True)
os.makedirs(ADVICE_CACHE_DIR, exist_ok=True)
# ...后续逻辑同方案二

# --- 使用 Streamlit 的缓存来实例化模型 ---
# @st.cache_resource 装饰器确保模型只被加载一次，大大提高后续运行速度
@st.cache_resource
def get_analysis_app():
    print("正在创建和缓存 NoduleAnalysisApp 实例...")
    # 注意：这里的初始化参数可能需要根据你的类来调整
    # 如果你的类需要命令行参数，可以传递一个空列表或模拟的参数
    app = NoduleAnalysisApp(sys_argv=[])
    return app



def save_uploaded_files(mhd_file, raw_file):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        mhd_save_path = os.path.join(SAVE_DIR, mhd_file.name)
        raw_save_path = os.path.join(SAVE_DIR, raw_file.name)
        with open(mhd_save_path, "wb") as f:
            f.write(mhd_file.getvalue())
        with open(raw_save_path, "wb") as f:
            f.write(raw_file.getvalue())
        return True, mhd_file.name.replace('.mhd', '')
    except Exception as e:
        st.error(f"保存文件时出错: {e}")
        return False, None


def save_nodule_analysis_results(series_uid, total, malignant, benign, nodule_details_list):
    """
    将结节分析结果保存为 JSON 文件。

    Args:
        series_uid (str): 唯一的序列 ID，用作文件名。
        total (int): 总结节数。
        malignant (int): 恶性结节数。
        benign (int): 良性结节数。
        nodule_details_list (list): 包含结节详细信息的字典列表。
    """
    # 1. 将所有数据打包到一个字典中
    data_to_save = {
        "total_nodules": total,
        "malignant_nodules": malignant,
        "benign_nodules": benign,
        "nodules_details": nodule_details_list
    }

    # 2. 定义文件路径
    file_path = NODULE_INFO_CACHE_DIR / f"{series_uid}.json"

    # 3. 写入 JSON 文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"结节分析结果成功保存到: {file_path}")
        return True
    except Exception as e:
        st.error(f"保存结节结果时出错: {e}")
        print(f"保存结节结果时出错: {e}")
        return False


def save_ai_advice(series_uid, ai_advice):
    """
    将 AI 生成的生活建议保存为 JSON 文件。

    Args:
        series_uid (str): 唯一的序列 ID，用作文件名。
        ai_advice (str): AI 生成的建议文本。
    """
    # 1. 将建议打包到字典
    data_to_save = {
        "ai_advice": ai_advice
    }

    # 2. 定义文件路径
    file_path = ADVICE_CACHE_DIR / f"{series_uid}.json"

    # 3. 写入 JSON 文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"AI 建议成功保存到: {file_path}")
        return True
    except Exception as e:
        st.error(f"保存 AI 建议时出错: {e}")
        print(f"保存 AI 建议时出错: {e}")
        return False


def load_cached_nodule_analysis(series_uid):
    """从缓存加载结节分析结果。"""
    file_path = NODULE_INFO_CACHE_DIR / f"{series_uid}.json"
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 检查文件是否为空
                if f.tell() == f.seek(0, 2) and f.tell() == 0:
                    print(f"警告：缓存文件 {file_path} 是空的。将忽略此缓存。")
                    return None

                # 文件非空，移回文件开头并加载
                f.seek(0)
                return json.load(f)
        except json.JSONDecodeError:
            # 如果文件内容不是有效的 JSON，捕获错误
            st.warning(f"缓存文件 {file_path} 已损坏，将重新进行分析。")
            print(f"警告：缓存文件 {file_path} 已损坏，无法解析。")
            return None  # 返回 None，让主逻辑知道需要重新分析
    return None

def load_cached_ai_advice(series_uid):
    """从缓存加载 AI 建议。"""
    file_path = ADVICE_CACHE_DIR / f"{series_uid}.json"
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if f.tell() == f.seek(0, 2) and f.tell() == 0:
                    print(f"警告：AI 建议缓存文件 {file_path} 是空的。")
                    return None

                f.seek(0)
                data = json.load(f)
                return data.get("ai_advice")
        except json.JSONDecodeError:
            st.warning(f"AI 建议缓存文件 {file_path} 已损坏，将重新生成。")
            print(f"警告：AI 建议缓存文件 {file_path} 已损坏，无法解析。")
            return None
    return None



st.set_page_config(page_title="智能结节分析", page_icon="🩺", layout="wide")

# 2. 侧边栏 (Sidebar) 用于放置说明和关于信息
with st.sidebar:
    st.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
    st.title("关于应用")
    st.info(
        "这是一个基于深度学习的CT影像肺结节智能分析系统。"
        "上传您的.mhd和.raw文件，系统将自动检测结节并评估其恶性风险。"
    )
    st.header("使用说明")
    st.markdown("""
    1.  点击“浏览文件”按钮分别上传对应的`.mhd`和`.raw`文件。
    2.  确保两个文件都已经成功上传（文件名会显示出来）。
    3.  点击“开始分析”按钮。
    4.  在右侧查看分析结果摘要和详细报告。
    """)

# 3. 主页面标题
st.title("🩺 CT 影像结节智能分析系统")
st.markdown("---")

# 4. 使用容器和分栏来组织上传区域
with st.container(border=True):
    st.subheader("📤 文件上传区域")
    col1, col2 = st.columns(2)
    with col1:
        mhd_file = st.file_uploader("上传 .mhd 文件", type=['mhd'], help="这是包含元数据头文件")
    with col2:
        raw_file = st.file_uploader("上传 .raw 文件", type=['raw'], help="这是包含原始像素数据的文件")

# 5. 分析按钮和处理逻辑
if st.button("🚀 开始分析", type="primary", use_container_width=True):
    if mhd_file is not None and raw_file is not None:

        # --- 新增：从文件名中提取主干部分 (不含扩展名) ---
        mhd_stem = Path(mhd_file.name).stem
        raw_stem = Path(raw_file.name).stem

        if mhd_stem==raw_stem:
            # 文件名校验通过，继续执行你的原始逻辑
            st.success(f"文件名校验通过！开始处理 Series UID: {mhd_stem}")

            with st.spinner('正在保存文件...'):
                save_success, series_uid = save_uploaded_files(mhd_file, raw_file)

            # --- 核心修改 1: 在所有逻辑开始前，先创建好结果区域的占位符 ---
            results_placeholder = st.empty()

            if save_success:
                st.success(f"文件保存成功！开始进行模型分析 UID: {series_uid}")

                cached_results = load_cached_nodule_analysis(series_uid)
                cached_advice = load_cached_ai_advice(series_uid)

                if cached_results and cached_advice:
                    # --- 如果缓存存在，直接从缓存加载 ---
                    st.info("检测到已存在的分析结果，正在从缓存加载...")
                    # --- 核心修改 2: 直接使用缓存数据填充占位符，而不是只存session_state ---
                    with results_placeholder.container():
                        st.header("📊 分析报告")
                        with st.container(border=True):
                            st.subheader(f"病例 UID: {series_uid}")
                            col1, col2, col3 = st.columns(3)
                            col1.metric("总结节数", f"{cached_results['total_nodules']} 个")
                            col2.metric("高度疑似恶性", f"{cached_results['malignant_nodules']} 个",
                                        delta=f"{cached_results['malignant_nodules']} 个风险", delta_color="inverse")
                            col3.metric("判断为良性", f"{cached_results['benign_nodules']} 个", delta_color="normal")

                            st.markdown("---")

                            with st.container(border=True):
                                st.subheader("💡 AI 健康生活建议")
                                st.markdown(cached_advice)

                            st.markdown("---")
                            st.subheader("📄 结节详情列表")
                            df = pd.DataFrame(cached_results['nodules_details'])
                            st.dataframe(
                                df.style.highlight_max(axis=0, subset=['恶性概率'], color='lightcoral').highlight_min(
                                    axis=0, subset=['恶性概率'], color='lightgreen'),
                                use_container_width=True
                            )



                    st.session_state['analysis_results'] = {
                        "series_uid": series_uid,
                        "total_nodules": cached_results["total_nodules"],
                        "malignant_nodules": cached_results["malignant_nodules"],
                        "benign_nodules": cached_results["benign_nodules"],
                        "nodules_details": cached_results["nodules_details"],
                        "ai_advice": cached_advice
                    }
                    st.success('🎉 从缓存加载完成！')
                    st.balloons()
                else:
                    st.info("未找到缓存，开始执行新的分析流程...")

                    # --- 核心修改 3: 同样先用一个外框填充占位符，内部再创建子占位符 ---
                    with results_placeholder.container():
                        st.header("📊 分析报告")
                        model_output_placeholder = st.empty()
                        ai_output_placeholder = st.empty()


                    with st.spinner('🔬 模型正在紧张分析中，这可能需要一些时间...'):
                        # --- 2. 获取缓存的 app 实例并运行分析 ---
                        nodule_app = get_analysis_app()
                        classifications_list = nodule_app.main(series_uid)

                        # --- 新增：将元组列表转换为带有明确键名的字典列表 ---
                        nodule_details_list = []
                        for i, (prob, prob_mal, center_xyz, center_irc) in enumerate(classifications_list):
                            # 我们只筛选出概率大于0.5的结节进行展示
                            if prob > 0.5:
                                nodule_details_list.append({
                                    "ID": i + 1,
                                    "结节概率": f"{prob:.3f}",
                                    "恶性概率": prob_mal,  # 注意这里保留原始浮点数用于高亮
                                    "中心坐标 (xyz)": str(center_xyz),
                                    "诊断": "高度疑似恶性" if prob_mal > 0.7 else (
                                        "疑似恶性" if prob_mal > 0.5 else "良性")
                                })
                        # ----------------------------------------------------

                        # --- 3. 调用 getter 方法获取结果 ---
                        total = nodule_app.get_total_nodules()
                        malignant = nodule_app.get_malignant_nodules()
                        benign = nodule_app.get_benign_nodules()

                    # 模型分析完成，立刻填充模型结果的占位符
                    with model_output_placeholder.container(border=True):
                        st.subheader(f"病例 UID: {series_uid}")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("总结节数", f"{total} 个")
                        col2.metric("高度疑似恶性", f"{malignant} 个", delta=f"{malignant} 个风险",
                                    delta_color="inverse")
                        col3.metric("判断为良性", f"{benign} 个", delta_color="normal")
                        st.markdown("---")
                        st.subheader("📄 结节详情列表")
                        if nodule_details_list:
                            df = pd.DataFrame(nodule_details_list)
                            st.dataframe(
                                df.style.highlight_max(axis=0, subset=['恶性概率'],
                                                       color='lightcoral').highlight_min(axis=0,
                                                                                         subset=['恶性概率'],
                                                                                         color='lightgreen'),
                                use_container_width=True
                            )
                        else:
                            st.success("未在影像中发现明显结节。")



                    st.info("定量分析完成，正在请求 AI 生成生活建议...")
                    with st.spinner('🧠 AI 正在思考中，请稍候...'):
                        # --- 新增：调用 AI 建议函数 ---
                        ai_advice = get_ai_lifestyle_advice(total, malignant, benign)
                        # -----------------------------
                    # AI分析完成，立刻填充AI建议的占位符
                    with ai_output_placeholder.container(border=True):
                        st.subheader("💡 AI 健康生活建议")
                        st.markdown(ai_advice)
                    # --- 新增：将新结果保存到缓存文件 ---
                    save_nodule_analysis_results(series_uid, total, malignant, benign, nodule_details_list)
                    save_ai_advice(series_uid, ai_advice)
                    # ------------------------------------

                    st.session_state['analysis_results'] = {
                        "series_uid": series_uid,
                        "total_nodules": total,
                        "malignant_nodules": malignant,
                        "benign_nodules": benign,
                        "nodules_details": nodule_details_list,
                        "ai_advice": ai_advice  # 将 AI 建议也存起来
                    }
                    st.success('🎉 所有分析均已完成！')
                    st.balloons()
        else:
            # 如果文件名不匹配，显示清晰的错误信息
            st.error(f"文件名不匹配！请确保 .mhd 和 .raw 文件的主文件名相同。")
            st.error(f"检测到 MHD 文件名: `{mhd_file.name}` (UID: `{mhd_stem}`)")
            st.error(f"检测到 RAW 文件名: `{raw_file.name}` (UID: `{raw_stem}`)")
    else:
        st.error('⚠️ 请确保 .mhd 和 .raw 文件都已上传！')

# 6. 结果展示区域
if 'analysis_results' not in st.session_state:
    st.markdown("---")
    st.header("📊 分析报告")
    st.info("上传文件并点击开始分析后，结果将显示在这里。")
