import streamlit as st

def render_cost_savings():
    sec2_html = (
        '<div class="glass-card" id="benefits">'
        '<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;">'
        '<div>'
        '<div style="display: flex; align-items: center; gap: 0.8rem;">'
        '<span style="font-size: 2rem;">💰</span>'
        '<h2 style="margin: 0; color: #aed581; font-size: 1.8rem; font-weight: 800;">1. Enterprise Cost Savings & ROI</h2>'
        '</div>'
        '<p style="color: #b0bec5; font-size: 1rem; margin-top: 0.4rem; margin-bottom: 0;">'
        'Groot slashes enterprise AI bills by <b>50-90%</b> (cutting annual spending from <b>$1,000,000 → $100,000-$500,000</b>) across 6 real-world dataset workloads:'
        '</p>'
        '</div>'
        '<div style="background: rgba(156, 204, 101, 0.15); border: 1px solid #9ccc65; padding: 6px 18px; border-radius: 20px; color: #aed581; font-weight: 800; font-size: 1rem;">'
        'Up to 90% Savings'
        '</div>'
        '</div>'
        '<div class="tech-grid">'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🏦</div><div class="tech-step-content"><h4>100 GB Core Banking Audit Dataset</h4><p><b>Before:</b> 100 GB raw regulatory audit logs ($250K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 10 GB targeted audit vectors ($25K/yr)</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📈</div><div class="tech-step-content"><h4>50 GB Wealth & Portfolio Filings Dataset</h4><p><b>Before:</b> 50 GB SEC 10-K & equity reports ($150K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 5 GB equity insight vectors ($15K/yr)</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">⚖️</div><div class="tech-step-content"><h4>80 GB AML & Fraud Compliance Dataset</h4><p><b>Before:</b> 80 GB transaction history logs ($200K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 8 GB risk flag vectors ($20K/yr)</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">💳</div><div class="tech-step-content"><h4>40 GB Commercial Lending Archive Dataset</h4><p><b>Before:</b> 40 GB loan application dossiers ($120K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 4 GB credit risk vectors ($12K/yr)</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📊</div><div class="tech-step-content"><h4>60 GB Institutional Trading Analytics Dataset</h4><p><b>Before:</b> 60 GB market sentiment feeds ($180K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 6 GB alpha signal vectors ($18K/yr)</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🛡️</div><div class="tech-step-content"><h4>30 GB Insurance Claims Archive Dataset</h4><p><b>Before:</b> 30 GB policy & claim dossiers ($100K/yr)<br><b style="color:#9ccc65;">With Groot:</b> 3 GB claim assessment vectors ($10K/yr)</p></div></div>'
        '</div></div>'
    )
    st.markdown(sec2_html, unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
