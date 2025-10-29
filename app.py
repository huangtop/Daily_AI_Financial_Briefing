import streamlit as st
import requests

st.set_page_config(
    page_title="AI Financial Briefing",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Financial Briefing")
st.markdown("每日 AI 財經簡報 - 自動生成雙語金融新聞摘要")

# GitHub raw URLs
GITHUB_REPO = "huangtop/Daily_AI_Financial_Briefing"
HTML_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/Daily%20AI%20Financial%20Briefing.html"
PNG_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/source_distribution.png"

# Display pre-generated briefing from GitHub
try:
    # Fetch HTML content
    html_response = requests.get(HTML_URL, timeout=10)
    if html_response.status_code == 200:
        html_content = html_response.text
        st.success("✅ 今日簡報已載入")

        # Display the briefing using HTML
        st.components.v1.html(html_content, height=800, scrolling=True)

        # Display chart
        try:
            png_response = requests.get(PNG_URL, timeout=10)
            if png_response.status_code == 200:
                st.markdown("---")
                st.subheader("📊 新聞來源分佈")
                st.image(png_response.content, caption="新聞來源統計圖表")
            else:
                st.warning("圖表載入失敗")
        except Exception as e:
            st.warning(f"圖表載入錯誤: {e}")

    else:
        st.error(f"❌ 載入簡報失敗: HTTP {html_response.status_code}")
        st.info("💡 請檢查GitHub repo是否已更新，或聯繫管理員")

except Exception as e:
    st.error(f"❌ 網路錯誤: {e}")
    st.info("💡 請檢查網路連線，或稍後再試")
