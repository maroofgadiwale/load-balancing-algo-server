# Program to implement Load Balancer:
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from models import VM
from simulation import run_simulation
from algorithms.round_robin import RoundRobinBalancer
from algorithms.weighted_rr import WeightedRoundRobinBalancer
from algorithms.threshold import ThresholdBalancer
from algorithms.honeybee import HoneyBeeBalancer
from algorithms.aco import ACOBalancer

# PAGE CONFIG
st.set_page_config(
    page_title="LoadSim",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CUSTOM CSS
st.markdown("""
<style>

/* Metric cards */
.metric-card {
    background: #1e2530;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #4a90d9; }
.metric-label {
    font-size: 0.75rem;
    color: #8a9bb0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
    font-weight: 600;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #3b9eff;
}
.metric-unit {
    font-size: 0.72rem;
    color: #4a6d94;
    margin-top: 4px;
}

/* Winner badge */
.winner-badge {
    display: inline-block;
    background: linear-gradient(135deg, #1a4a2e, #145a32);
    border: 1px solid #27ae60;
    color: #2ecc71;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}

/* Section headers */
.section-header {
    font-size: 1.0rem;
    font-weight: 700;
    color: #8ab4d4;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-bottom: 1px solid #2d3748;
    padding-bottom: 10px;
    margin: 32px 0 20px 0;
}

/* Streamlit overrides */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
    font-size: 0.95rem !important;
    width: 100%;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
}
.stDataFrame { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# PLOTLY THEME
ALGO_COLORS = {
    "Round Robin": "#3b9eff",
    "Weighted Round Robin": "#22c55e",
    "Threshold Based": "#f59e0b",
    "Honey Bee Foraging": "#ec4899",
    "Ant Colony Optimization": "#a78bfa",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,24,40,0.8)",
    font=dict(family="Source Sans Pro, sans-serif", color="#c8d8f0"),
    xaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(size=11)),
    legend=dict(bgcolor="rgba(15,24,40,0.9)", bordercolor="#1a2d4a", borderwidth=1),
    margin=dict(l=20, r=20, t=50, b=20),
)


# SIMULATION HELPERS
def build_vms(vm_configs):
    return [VM(vm_id=c[0], mips=c[1], capacity=c[2], weight=c[3]) for c in vm_configs]


@st.cache_data(show_spinner=False)
def run_all(vm_configs, num_tasks, arrival_rate, min_len, max_len, seed,
            threshold_val, abandon_limit, alpha, beta, rho, q):
    algorithms = [
        ("Round Robin", lambda vms: RoundRobinBalancer(vms)),
        ("Weighted Round Robin", lambda vms: WeightedRoundRobinBalancer(vms)),
        ("Threshold Based", lambda vms: ThresholdBalancer(vms, upper_threshold=threshold_val)),
        ("Honey Bee Foraging", lambda vms: HoneyBeeBalancer(vms, abandon_limit=abandon_limit)),
        ("Ant Colony Optimization", lambda vms: ACOBalancer(vms, alpha=alpha, beta=beta, rho=rho, q=q)),
    ]
    results = []
    for _, make_balancer in algorithms:
        vms = build_vms(vm_configs)
        balancer = make_balancer(vms)
        result = run_simulation(
            balancer=balancer, vms=vms,
            num_tasks=num_tasks, avg_arrival_rate=arrival_rate,
            min_task_length=min_len, max_task_length=max_len, seed=seed,
        )
        results.append(result)
    return results


# SIDEBAR
with st.sidebar:
    st.markdown("### ☁️ Set Configuration")
    st.markdown("---")

    st.markdown("**📦 Workload**")
    num_tasks = st.slider("Total Tasks", 100, 2000, 1000, 100)
    arrival_rate = st.slider("Arrival Rate (tasks/s)", 1.0, 50.0, 20.0, 1.0)
    min_task_len = st.slider("Min Task Length (MI)", 50, 500, 200, 50)
    max_task_len = st.slider("Max Task Length (MI)", 500, 5000, 2000, 100)
    seed = st.number_input("Random Seed", value=42, step=1)

    st.markdown("---")
    st.markdown("**🖥️ VM Configuration**")
    num_vms = st.slider("Number of VMs", 2, 8, 5)

    vm_configs = []
    with st.expander("Edit VM Settings", expanded=False):
        default_mips = [1000, 2000, 3000, 1500, 2500, 2000, 1800, 2800]
        default_weights = [1, 2, 3, 2, 2, 2, 1, 3]
        for i in range(num_vms):
            st.markdown(f"**VM-{i + 1}**")
            c1, c2 = st.columns(2)
            mips = c1.number_input(f"MIPS", value=default_mips[i], key=f"mips_{i}", step=100)
            weight = c2.number_input(f"Weight", value=default_weights[i], key=f"weight_{i}", step=1, min_value=1)
            vm_configs.append((i + 1, mips, 8, weight))
    if not vm_configs:
        vm_configs = [(i + 1, [1000, 2000, 3000, 1500, 2500, 2000, 1800, 2800][i],
                       8, [1, 2, 3, 2, 2, 2, 1, 3][i]) for i in range(num_vms)]

    st.markdown("---")
    st.markdown("**⚙️ Algorithm Params**")
    with st.expander("Threshold Based"):
        threshold_val = st.slider("Upper Threshold", 0.5, 1.0, 0.80, 0.05)
    with st.expander("Honey Bee"):
        abandon_limit = st.slider("Abandon Limit", 2, 20, 5)
    with st.expander("ACO"):
        alpha = st.slider("Alpha (pheromone weight)", 0.1, 3.0, 1.0, 0.1)
        beta = st.slider("Beta (heuristic weight)", 0.1, 5.0, 2.0, 0.1)
        rho = st.slider("Rho (evaporation rate)", 0.01, 0.5, 0.1, 0.01)
        q = st.slider("Q (deposit constant)", 10, 500, 100, 10)

    st.markdown("---")
    run_btn = st.button("▶  Run Simulation")

# HERO BANNER
st.markdown("""
<div style="background: linear-gradient(135deg, #0f1f3d 0%, #0a2a5e 50%, #0d1f3c 100%);
            border: 1px solid #1e3a6e; border-radius: 16px;
            padding: 32px 40px; margin-bottom: 28px;">
    <p style="font-size:2rem; font-weight:800; color:#ffffff; margin:0 0 6px 0;">
        ☁️LoadSim: Smart Load Balancer Simulator
    </p>
    <p style="font-size:0.85rem; color:#6b9bd2; margin:0; letter-spacing:0.5px;">
        Performance Comparison using load balancing algorithms
    </p>
</div>
""", unsafe_allow_html=True)

# RUN / LOAD RESULTS
if "results" not in st.session_state or run_btn:
    with st.spinner("⚡ Running simulation..."):
        st.session_state.results = run_all(
            tuple(vm_configs), num_tasks, arrival_rate,
            min_task_len, max_task_len, int(seed),
            threshold_val, abandon_limit, alpha, beta, rho, q
        )

results = st.session_state.results
names = [r.algorithm_name for r in results]
colors = [ALGO_COLORS[n] for n in names]

# Best algorithm
best = min(results, key=lambda r: r.avg_response_time)

# TOP SUMMARY METRICS
st.markdown('<div class="section-header">📊 Simulation Summary</div>', unsafe_allow_html=True)

cols = st.columns(5)
metrics = [
    ("VMs", len(vm_configs), ""),
    ("Tasks", num_tasks, "total"),
    ("Arrival Rate", arrival_rate, "tasks/s"),
    ("Best Algo", best.algorithm_name.split()[0], "winner"),
    ("Best Avg RT", f"{best.avg_response_time:.4f}", "seconds"),
]
for col, (label, value, unit) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-unit">{unit}</div>
        </div>""", unsafe_allow_html=True)

# CHART 1 — Avg Response Time
st.markdown('<div class="section-header">⏱ Response & Processing Time</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    avg_rt = [r.avg_response_time for r in results]
    fig.add_trace(go.Bar(
        x=names, y=avg_rt, marker_color=colors,
        text=[f"{v:.4f}s" for v in avg_rt],
        textposition="outside", textfont=dict(size=11, color="#c8d8f0"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Average Response Time", font=dict(size=14, color="#8ab4d4")),
        yaxis_title="Time (seconds)", showlegend=False,
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure()
    avg_pt = [r.avg_processing_time for r in results]
    fig.add_trace(go.Bar(
        x=names, y=avg_pt, marker_color=colors,
        text=[f"{v:.4f}s" for v in avg_pt],
        textposition="outside", textfont=dict(size=11, color="#c8d8f0"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Average Processing Time", font=dict(size=14, color="#8ab4d4")),
        yaxis_title="Time (seconds)", showlegend=False,
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)

# CHART 2 — Response Time Range (Min/Avg/Max)
fig = go.Figure()
fig.add_trace(go.Bar(name="Min", x=names,
                     y=[r.min_response_time for r in results],
                     marker_color="rgba(59,158,255,0.5)", marker_line_color="#3b9eff", marker_line_width=1))
fig.add_trace(go.Bar(name="Avg", x=names,
                     y=[r.avg_response_time for r in results],
                     marker_color="rgba(59,158,255,0.85)"))
fig.add_trace(go.Bar(name="Max", x=names,
                     y=[r.max_response_time for r in results],
                     marker_color="rgba(59,158,255,0.3)", marker_line_color="#3b9eff", marker_line_width=1))
fig.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="Response Time Range — Min / Avg / Max", font=dict(size=14, color="#8ab4d4")),
    barmode="group", yaxis_title="Time (seconds)", height=380,
)
st.plotly_chart(fig, use_container_width=True)

# CHART 3 — VM Utilization
st.markdown('<div class="section-header">🖥️ VM Utilization</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    avg_util = [r.avg_utilization for r in results]
    fig.add_trace(go.Bar(
        x=names, y=avg_util, marker_color=colors,
        text=[f"{v:.1f}%" for v in avg_util],
        textposition="outside", textfont=dict(size=11, color="#c8d8f0"),
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="#ef4444",
                  annotation_text="80% threshold", annotation_font_color="#ef4444")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Average VM Utilization", font=dict(size=14, color="#8ab4d4")),
        yaxis_title="Utilization (%)", yaxis_range=[0, 115],
        showlegend=False, height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Heatmap
    vm_ids = sorted(results[0].vm_utilizations.keys())
    z_data = [[r.vm_utilizations.get(vm_id, 0) for r in results] for vm_id in vm_ids]
    text_data = [[f"{v:.1f}%" for v in row] for row in z_data]

    fig = go.Figure(go.Heatmap(
        z=z_data,
        x=names,
        y=[f"VM-{v}" for v in vm_ids],
        text=text_data,
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale=[
            [0.0, "#0f1828"],
            [0.3, "#1a3a6e"],
            [0.6, "#c0392b"],
            [1.0, "#8b0000"],
        ],
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#c8d8f0"),
            title=dict(text="Util %", font=dict(color="#8ab4d4")),
        ),
        zmin=0, zmax=100,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="VM Utilization Heatmap (%)", font=dict(size=14, color="#8ab4d4")),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

# CHART 4 — CDF
st.markdown('<div class="section-header">📈 Response Time Distribution (CDF)</div>', unsafe_allow_html=True)

fig = go.Figure()
for r in results:
    rt_sorted = sorted(c.response_time for c in r.cloudlets if c.response_time)
    cdf_y = np.linspace(0, 100, len(rt_sorted))
    fig.add_trace(go.Scatter(
        x=rt_sorted, y=cdf_y,
        name=r.algorithm_name,
        mode="lines",
        line=dict(color=ALGO_COLORS[r.algorithm_name], width=2.5),
    ))
fig.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="Cumulative Distribution — % Tasks Completed by Response Time",
               font=dict(size=14, color="#8ab4d4")),
    xaxis_title="Response Time (seconds)",
    yaxis_title="% of Tasks Completed",
    height=420,
)
st.plotly_chart(fig, use_container_width=True)

# FULL METRICS TABLE
st.markdown('<div class="section-header">📋 Full Metrics Table</div>', unsafe_allow_html=True)

table_data = []
for r in results:
    is_best = r.algorithm_name == best.algorithm_name
    table_data.append({
        "Algorithm": ("🏆 " if is_best else "") + r.algorithm_name,
        "Avg Response (s)": round(r.avg_response_time, 4),
        "Min Response (s)": round(r.min_response_time, 4),
        "Max Response (s)": round(r.max_response_time, 4),
        "Avg Processing (s)": round(r.avg_processing_time, 4),
        "Avg Wait (s)": round(r.avg_wait_time, 4),
        "Avg VM Util (%)": round(r.avg_utilization, 1),
        "Tasks Done": f"{r.completed_tasks}/{r.num_tasks}",
    })

df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# PER-VM BREAKDOWN TABLE
st.markdown('<div class="section-header">🔍 Per-VM Utilization Breakdown</div>', unsafe_allow_html=True)

vm_rows = []
mips_map = {cfg[0]: cfg[1] for cfg in vm_configs}
for vm_id in sorted(results[0].vm_utilizations.keys()):
    row = {"VM": f"VM-{vm_id}", "MIPS": mips_map.get(vm_id, "?")}
    for r in results:
        row[r.algorithm_name[:10]] = f"{r.vm_utilizations.get(vm_id, 0):.1f}%"
    vm_rows.append(row)

st.dataframe(pd.DataFrame(vm_rows), use_container_width=True, hide_index=True)

# DOWNLOAD CSV
st.markdown('<div class="section-header">💾 Export</div>', unsafe_allow_html=True)

csv_rows = []
for r in results:
    csv_rows.append({
        "Algorithm": r.algorithm_name,
        "Avg Response Time": r.avg_response_time,
        "Min Response Time": r.min_response_time,
        "Max Response Time": r.max_response_time,
        "Avg Processing Time": r.avg_processing_time,
        "Avg Wait Time": r.avg_wait_time,
        "Avg VM Utilization": r.avg_utilization,
        "Tasks Completed": r.completed_tasks,
        "Total Tasks": r.num_tasks,
    })

csv_df = pd.DataFrame(csv_rows)
csv_str = csv_df.to_csv(index=False)

st.download_button(
    label="⬇️  Download Results as CSV",
    data=csv_str,
    file_name="lb_simulation_results.csv",
    mime="text/csv",
)

# FOOTER:
st.markdown("""
<div style="text-align:center; margin-top:48px; padding:20px;
            border-top:1px solid #2d3748; color:#4a6a8a;
            font-size:0.78rem; letter-spacing:0.5px;">
    maroofgadiwale
</div>
""", unsafe_allow_html=True)
