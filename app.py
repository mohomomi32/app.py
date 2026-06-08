import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Professional Geotechnical Suite", layout="wide")

st.title("📊 Professional Particle Size Distribution Suite")
st.write("Aapki di hui custom sieve range (25.0mm to 0.075mm) par mabni automated calculations.")

# --- Main Screen Input Fields ---
st.subheader("1. Project & Sample Identification (Manual Input)")
col_meta1, col_meta2, col_meta3 = st.columns(3)

with col_meta1:
    project_name = st.text_input("Project Name:", "Site Investigation Project")
with col_meta2:
    bh_number = st.text_input("Borehole Number (BH):", "BH-02")
with col_meta3:
    sample_depth = st.text_input("Sample Depth:", "1.5m - 3.0m")

st.markdown("---")

# --- Helper Function for Log Interpolation ---
def get_diameter(pct_target, sizes, passing):
    sizes_rev = np.array(sizes[::-1])
    passing_rev = np.array(passing[::-1])
    
    if pct_target > max(passing_rev) or pct_target < min(passing_rev):
        return None
        
    log_sizes = np.log10(sizes_rev)
    log_d = np.interp(pct_target, passing_rev, log_sizes)
    return 10**log_d

# --- Sieve Data Input ---
st.subheader("2. Sieve Analysis Data Input")
col_input1, col_input2, col_input3 = st.columns([2, 2, 1])

with col_input1:
    # Aapki di hui exact sieve range ko default bana diya hai
    custom_sieves = "25.0, 19.0, 9.5, 4.75, 2.00, 0.85, 0.425, 0.25, 0.15, 0.075"
    sieve_input = st.text_area("Sieve Sizes (mm):", custom_sieves, height=70)
with col_input2:
    # Unhi 10 sieves ke mutabiq realistic default weights set kiye hain
    default_retained = "0, 15, 35, 55, 70, 90, 110, 85, 60, 45"
    retained_input = st.text_area("Weight Retained (g):", default_retained, height=70)
with col_input3:
    pan_weight = st.number_input("Pan Weight (g):", min_value=0.0, value=25.0)

try:
    sieves = [float(x.strip()) for x in sieve_input.split(",")]
    retained = [float(x.strip()) for x in retained_input.split(",")]
    
    if len(sieves) != len(retained):
        st.error(f"Error: Sieve sizes ({len(sieves)}) aur Weight Retained ({len(retained)}) ki tadad barabar honi chahiye!")
    else:
        # Calculations
        total_weight = sum(retained) + pan_weight
        cum_retained = np.cumsum(retained)
        cum_retained_pct = (cum_retained / total_weight) * 100
        passing_pct = 100 - cum_retained_pct
        
        # DataFrame
        df = pd.DataFrame({
            "Sieve Size (mm)": sieves,
            "Weight Retained (g)": retained,
            "Cumulative Retained (g)": cum_retained,
            "Cumulative % Retained": cum_retained_pct,
            "% Passing (Finer)": passing_pct
        })
        
        st.markdown("---")
        
        # Layout splitting for Results and Graph
        col_res, col_graph = st.columns([1, 2])
        
        with col_res:
            st.subheader("📋 Executed Summary")
            st.markdown(f"**Project:** {project_name}")
            st.markdown(f"**Borehole:** {bh_number}")
            st.markdown(f"**Depth:** {sample_depth}")
            st.markdown(f"**Total Sample Weight:** {total_weight:.2f} g")
            
            # --- D-Values Calculation ---
            d60 = get_diameter(60.0, sieves, passing_pct)
            d30 = get_diameter(30.0, sieves, passing_pct)
            d10 = get_diameter(10.0, sieves, passing_pct)
            
            cu, cc, classification = None, None, "N/A"
            
            if d10 and d30 and d60:
                cu = d60 / d10
                cc = (d30**2) / (d60 * d10)
                
                p200 = np.interp(0.075, sieves[::-1], passing_pct[::-1])
                p4 = np.interp(4.75, sieves[::-1], passing_pct[::-1])
                
                if p200 < 50: 
                    coarse_fraction = 100 - p200
                    gravel_fraction = 100 - p4
                    sand_fraction = coarse_fraction - gravel_fraction
                    
                    if gravel_fraction > sand_fraction:
                        classification = "Well-Graded GRAVEL (GW)" if (cu >= 4 and 1 <= cc <= 3) else "Poorly-Graded GRAVEL (GP)"
                    else:
                        classification = "Well-Graded SAND (SW)" if (cu >= 6 and 1 <= cc <= 3) else "Poorly-Graded SAND (SP)"
                else:
                    classification = "Fine-Grained Soil"
            
            # Displaying Metrics
            st.subheader("⚙️ Index Properties")
            st.write(f"**$D_{{60}}$:** {f'{d60:.3f} mm' if d60 else 'Out of range'}")
            st.write(f"**$D_{{30}}$:** {f'{d30:.3f} mm' if d30 else 'Out of range'}")
            st.write(f"**$D_{{10}}$:** {f'{d10:.3f} mm' if d10 else 'Out of range'}")
            st.write(f"**Uniformity Coefficient ($C_u$):** {f'{cu:.2f}' if cu else 'N/A'}")
            st.write(f"**Coefficient of Curvature ($C_c$):** {f'{cc:.2f}' if cc else 'N/A'}")
            st.success(f"**USCS Code:** {classification}")
            
            st.subheader("📊 Calculation Table")
            st.dataframe(df.style.format("{:.2f}"), height=280)

        with col_graph:
            st.subheader("📈 Particle Size Distribution Curve")
            
            # Plot Styling for Consultancy Level Reports
            plt.rcParams['font.family'] = 'serif'
            fig, ax = plt.subplots(figsize=(10, 6.5))
            
            # Plotting main curve
            ax.plot(sieves, passing_pct, marker='s', markersize=6, linestyle='-', color='#1f77b4', linewidth=2, label='Grain Size Distribution')
            
            ax.set_xscale('log')
            ax.set_xlabel('Particle Size (mm)', fontsize=11, fontweight='bold', labelpad=10)
            ax.set_ylabel('Percent Finer / Passing (%)', fontsize=11, fontweight='bold', labelpad=10)
            ax.set_title('PARTICLE SIZE DISTRIBUTION CURVE', fontsize=13, fontweight='bold', pad=15)
            
            # Grid lines
            ax.grid(True, which="major", color="#555555", linestyle="-", alpha=0.6)
            ax.grid(True, which="minor", color="#999999", linestyle=":", alpha=0.4)
            
            # Professional X-limits to completely cover your 25mm down to 0.075mm range beautifully
            ax.set_xlim(100.0, 0.01) 
            ax.set_ylim(0, 100)
            
            # Interpolated D-Lines overlay
            colors = {'D60': '#d62728', 'D30': '#2ca02c', 'D10': '#9467bd'}
            if d60:
                ax.axvline(x=d60, color=colors['D60'], linestyle='--', alpha=0.7)
                ax.axhline(y=60, color=colors['D60'], linestyle='--', alpha=0.5)
            if d30:
                ax.axvline(x=d30, color=colors['D30'], linestyle='--', alpha=0.7)
                ax.axhline(y=30, color=colors['D30'], linestyle='--', alpha=0.5)
            if d10:
                ax.axvline(x=d10, color=colors['D10'], linestyle='--', alpha=0.7)
                ax.axhline(y=10, color=colors['D10'], linestyle='--', alpha=0.5)

            # Inside Graph Text Box (Legend & Metadata)
            textstr = '\n'.join((
                r'$\mathbf{Project\ Information:}$',
                f'Project: {project_name}',
                f'Borehole No: {bh_number}',
                f'Depth: {sample_depth}',
                r'------------------------------------',
                r'$\mathbf{Geotechnical\ Properties:}$',
                r'$D_{60} = %.3f\ mm$' % (d60, ) if d60 else r'$D_{60} = N/A$',
                r'$D_{30} = %.3f\ mm$' % (d30, ) if d30 else r'$D_{30} = N/A$',
                r'$D_{10} = %.3f\ mm$' % (d10, ) if d10 else r'$D_{10} = N/A$',
                r'$C_u = %.2f$' % (cu, ) if cu else r'$C_u = N/A$',
                r'$C_c = %.2f$' % (cc, ) if cc else r'$C_c = N/A$',
                f'Classification: {classification}'
            ))
            
            props = dict(boxstyle='round', facecolor='#f9f9f9', alpha=0.9, edgecolor='#cccccc')
            ax.text(0.03, 0.03, textstr, transform=ax.transAxes, fontsize=9.5, verticalalignment='bottom', bbox=props)
            
            # Secondary top axis for Soil Component Boundaries
            ax2 = ax.twiny()
            ax2.set_xscale('log')
            ax2.set_xlim(100.0, 0.01)
            ax2.set_xticks([75, 4.75, 2.0, 0.425, 0.075])
            ax2.set_xticklabels(['Cobbles', 'Gravel', 'C. Sand', 'M. Sand', 'Fines'], fontsize=8, rotation=30)
            ax2.tick_params(axis='x', colors='#555555')

            st.pyplot(fig)
            
            # --- PDF Export Preparation ---
            buf = BytesIO()
            fig.savefig(buf, format="pdf", bbox_inches='tight', dpi=300) 
            buf.seek(0)
            
            safe_bh = bh_number.replace(" ", "_")
            safe_depth = sample_depth.replace(" ", "_").replace("-", "_")
            file_label = f"Sieve_Report_{safe_bh}_{safe_depth}.pdf"
            
            st.download_button(
                label=f"📥 Download PDF Report ({bh_number} @ {sample_depth})",
                data=buf,
                file_name=file_label,
                mime="application/pdf"
            )

except ValueError:
    st.error("Inputs check karein! numbers ko comma (,) se hi alag kiya jaye.")