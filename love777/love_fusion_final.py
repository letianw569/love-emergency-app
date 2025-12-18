import streamlit as st
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import gspread
import time
from datetime import datetime

# ==========================================
# 1. 核心数学模型 (整合自 love7, love8, PDF 原理)
# ==========================================

def generate_confession_times(mode, n=50):
    """模拟表白时刻序列"""
    i_series = np.array(range(1, n + 1))
    if mode == "mo_ceng":      # 磨蹭模式：收敛于1
        return np.array([1 + 1/i for i in i_series])
    elif mode == "sao_dong":   # 骚动模式：从0增加
        return np.array([1 - 1/i for i in i_series])
    else:                      # 随机模式
        return np.sort(np.random.uniform(0, 10, n))

def is_brave(times):
    """判断是否『勇敢』：序列是否收敛"""
    if len(times) < 5: return False
    return np.all(np.abs(np.diff(times[-5:])) < 1e-3)

def success_rate(t, A, t_peak, sigma):
    """高斯成功率模型曲线"""
    return A * np.exp(-((t - t_peak)**2) / (2 * sigma**2))

def stability_analysis(t, A, t_peak, sigma, delta=0.01):
    """稳健性分析 (来自 PPT/PDF 理论)"""
    right = success_rate(t + delta, A, t_peak, sigma)
    left = success_rate(t - delta, A, t_peak, sigma)
    if abs(left - right) < 1e-2:
        return "稳健状态 🌱 (Stable)"
    else:
        return "波动状态 🎁 (Critical/Fate)"

def classify_love_type(I, P, C):
    """斯滕伯格爱情三角分类"""
    th = 7.0
    is_i, is_p, is_c = I >= th, P >= th, C >= th
    if is_i and is_p and is_c: return ("完美之爱", "亲密、激情、承诺高度统一。")
    if is_i and is_p: return ("浪漫之爱", "有亲密与激情，缺乏长期承诺。")
    if is_i and is_c: return ("伴侣之爱", "深厚友谊与承诺，激情稍淡。")
    if is_p and is_c: return ("愚蠢之爱", "基于激情建立的承诺，缺乏理解。")
    if is_i: return ("喜爱", "纯粹的友谊。")
    if is_p: return ("迷恋", "强烈的生理吸引。")
    if is_c: return ("空洞之爱", "只剩下责任与义务。")
    return ("非爱关系", "尚未建立实质情感联系。")

# ==========================================
# 2. 外部功能 (Google Sheets & 可视化)
# ==========================================

def save_to_google_sheets(data):
    """匿名数据保存逻辑"""
    try:
        if "gcp_service_account" in st.secrets:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
            # 这里的名字必须和你 Google Drive 里的表格文件名完全一致
            sh = gc.open("Love_Emergency_Data") 
            wks = sh.get_worksheet(0)
            wks.append_row(list(data.values()))
            return True
    except:
        pass # 本地运行未配置 Secrets 时跳过
    return False

def plot_visuals(I, P, C, A, t_peak, sigma, t_now, love_title):
    """绘图整合"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 左图：雷达图
    labels = ['亲密 (I)', '激情 (P)', '承诺 (C)']
    values = np.array([I, P, C, I])
    angles = np.linspace(0, 2*np.pi, 4)
    ax1 = plt.subplot(121, polar=True)
    ax1.fill(angles, values, color='#ff4b4b', alpha=0.3)
    ax1.plot(angles, values, color='#ff4b4b', marker='o')
    ax1.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax1.set_ylim(0, 10)
    ax1.set_title(f"关系诊断: {love_title}")

    # 右图：成功率曲线
    t_axis = np.linspace(0, max(10, t_peak + 4), 200)
    p_axis = success_rate(t_axis, A, t_peak, sigma)
    ax2 = plt.subplot(122)
    ax2.plot(t_axis, p_axis, label='成功率分布', color='#4A90E2', lw=2)
    ax2.fill_between(t_axis, p_axis, alpha=0.2, color='#4A90E2')
    ax2.axvline(t_now, color='#FF9F43', ls='--', label='预测行动时间')
    ax2.scatter([t_now], [success_rate(t_now, A, t_peak, sigma)], color='#FF9F43', s=100, zorder=5)
    ax2.set_title("表白时机预测")
    ax2.set_xlabel("时间 (周)")
    ax2.legend()
    
    return fig

# ==========================================
# 3. 主程序 (解决 ScriptRunContext 警告的关键)
# ==========================================

def main():
    # --- 必须是第一个 Streamlit 调用 ---
    st.set_page_config(
        page_title="Love Emergency | 恋爱告急·全量版",
        page_icon="💌",
        layout="wide"
    )

    # 字体配置 (解决 Linux/Windows 兼容性)
    try:
        matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        pass

    # UI 标题
    st.title("💌 Love Emergency | 恋爱告急·深度分析系统")
    st.info("本系统结合斯滕伯格爱情理论与高斯分布时机模型。所有输入均将用于匿名分析。")

    # 侧边栏：项目成员 (来自 PDF)
    with st.sidebar:
        st.header("👥 项目团队 (Team 10)")
        st.write("杨桐, 沈烨阳, 王乐天, 王苒伊, 魏子乔")
        st.divider()
        target_type = st.selectbox("🎯 对方性格", ["温婉内敛", "热情开朗", "理性逻辑", "神秘高冷"])
        st.markdown("---")
        st.write("v2.0 Full Fusion Version")

    # 问卷表单 (保留所有输入)
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 行为倾向")
            q1 = st.radio("你的行动倾向：", [1, 2], format_func=lambda x: "稳扎稳打 (推迟)" if x==1 else "主动出击 (提前)")
            q2 = st.radio("计划稳定性：", [1, 2], format_func=lambda x: "计划控 (不改)" if x==1 else "随心派 (反复改)")
        
        with col2:
            st.subheader("🧭 时间锚点")
            t0 = st.number_input("距离理想大事件（如纪念日）还有几周？", 0.1, 20.0, 4.0)
            t0_name = st.text_input("该事件的名称：", "普通周五")

        st.divider()
        st.subheader("💖 关系深度多维度评估 (1-5分)")
        
        # 整合 love7 的 9 道核心题
        ia, pa, ca = st.columns(3)
        with ia:
            st.write("**[亲密感感]**")
            i1 = st.slider("共享秘密与恐惧的程度", 1, 5, 3)
            i2 = st.slider("困难时的支持依赖感", 1, 5, 3)
            i3 = st.slider("相处时的灵魂默契度", 1, 5, 3)
        with pa:
            st.write("**[激情度]**")
            p1 = st.slider("想起对方时的心跳频率", 1, 5, 3)
            p2 = st.slider("制造浪漫惊喜的意愿", 1, 5, 3)
            p3 = st.slider("肢体互动的渴望程度", 1, 5, 3)
        with ca:
            st.write("**[承诺度]**")
            c1 = st.slider("长期未来规划的清晰度", 1, 5, 3)
            c2 = st.slider("矛盾时的坚持意愿", 1, 5, 3)
            c3 = st.slider("视对方为『唯一』的程度", 1, 5, 3)

        submitted = st.form_submit_button("🚀 生成深度分析报告")

    if submitted:
        # 1. 计算标准化分数 (1-10)
        I_score = 1 + (i1+i2+i3 - 3) / 12 * 9
        P_score = 1 + (p1+p2+p3 - 3) / 12 * 9
        C_score = 1 + (c1+c2+c3 - 3) / 12 * 9
        
        # 2. 模型参数推导
        A = 0.5 + (I_score + P_score + C_score) / 30 * 0.45
        sigma = 0.5 + (C_score / 10) * 1.5
        alpha = 1 - ((I_score/10 + C_score/10)/2) * 0.4
        t_peak = t0 * alpha
        
        # 行为模拟
        mode = "mo_ceng" if q1==1 and q2==1 else ("sao_dong" if q1==2 or q2==2 else "random")
        times = generate_confession_times(mode)
        t_now = t_peak + (np.mean(times[-10:]) - 1) * sigma
        
        # 3. 结果分类
        love_title, love_desc = classify_love_type(I_score, P_score, C_score)
        status_text = stability_analysis(t_now, A, t_peak, sigma)
        rate_val = success_rate(t_now, A, t_peak, sigma)

        # 4. 数据匿名存档
        data_to_log = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "I": round(I_score, 2), "P": round(P_score, 2), "C": round(C_score, 2),
            "Type": love_title, "SuccessRate": f"{rate_val*100:.1f}%",
            "Target": target_type, "ActionWeek": round(t_now, 2)
        }
        save_to_google_sheets(data_to_log)

        # 5. UI 展示结果
        st.divider()
        st.header("📊 恋爱告急 · 诊断报告")
        
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("分析类型", love_title)
        r2.metric("当前预测成功率", f"{rate_val*100:.1f}%")
        r3.metric("理论黄金时刻", f"{t_peak:.2f} 周后")
        r4.metric("建议行动时间", f"{t_now:.2f} 周后")

        st.info(f"**综合状态：{status_text}**")
        
        # 绘图展示
        st.pyplot(plot_visuals(I_score, P_score, C_score, A, t_peak, sigma, t_now, love_title))
        
        # 个性化指南 (来自 love8)
        st.subheader("💡 恋爱军师建议")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(f"**针对「{target_type}」：**")
            if "温婉" in target_type: st.write("建议增加相处时长，在柔和的灯光和低分贝环境下表白。")
            else: st.write("建议直球出击，展示你的果敢与自信。")
        with g2:
            st.markdown("**风险预警：**")
            if rate_val < 0.4: st.warning("当前成功率较低，建议继续通过『亲密感』互动增加筹码。")
            else: st.success("条件已基本成熟，真诚是唯一的必杀技。")

if __name__ == "__main__":
    main()