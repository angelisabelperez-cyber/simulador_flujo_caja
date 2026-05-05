import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Simulador de Flujo de Caja",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-label { font-size: 12px; color: #64748b; margin: 0; }
    .metric-value { font-size: 24px; font-weight: 600; margin: 4px 0 0; }
    .positive { color: #059669; }
    .negative { color: #dc2626; }
    .neutral  { color: #2563eb; }
    .section-title {
        font-size: 15px; font-weight: 600;
        color: #1e293b; margin: 1.5rem 0 0.75rem;
        padding-bottom: 6px;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 16px; border-radius: 6px; }
    div[data-testid="stSidebarContent"] { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def fmt_mxn(val):
    return f"${val:,.0f}"

def color_class(val):
    if val > 0:   return "positive"
    if val < 0:   return "negative"
    return "neutral"


def build_cashflow(ventas_mensuales, costo_pct, gastos_fijos,
                   p30, p60, p90, saldo_inicial, meses=12):
    """
    Calcula flujo de caja mensual.
    p30/p60/p90 = fracción de ventas cobrada a 30/60/90 días.
    El resto se asume incobrable.
    """
    rows = []
    saldo = saldo_inicial

    for m in range(1, meses + 1):
        # Ingresos cobrados este mes
        cobro_30 = ventas_mensuales[m - 1] * p30          # ventas del mes actual
        cobro_60 = ventas_mensuales[m - 2] * p60 if m >= 2 else 0
        cobro_90 = ventas_mensuales[m - 3] * p90 if m >= 3 else 0
        total_cobrado = cobro_30 + cobro_60 + cobro_90

        # Egresos
        costos_variables = ventas_mensuales[m - 1] * costo_pct
        total_egreso = costos_variables + gastos_fijos

        flujo_neto = total_cobrado - total_egreso
        saldo += flujo_neto

        rows.append({
            "Mes": m,
            "Ventas": ventas_mensuales[m - 1],
            "Cobro 30d": cobro_30,
            "Cobro 60d": cobro_60,
            "Cobro 90d": cobro_90,
            "Total cobrado": total_cobrado,
            "Costos variables": costos_variables,
            "Gastos fijos": gastos_fijos,
            "Total egresos": total_egreso,
            "Flujo neto": flujo_neto,
            "Saldo acumulado": saldo,
        })

    return pd.DataFrame(rows)


# ── sidebar: parámetros ──────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/1f4b0.svg",
             width=36)
    st.title("Parámetros")

    st.markdown('<p class="section-title">Ventas mensuales (MXN)</p>',
                unsafe_allow_html=True)

    modo_ventas = st.radio("Tipo de ingreso", ["Ingreso fijo mensual",
                                                "Ingreso con variación estacional"],
                           label_visibility="collapsed")

    if modo_ventas == "Ingreso fijo mensual":
        venta_base = st.number_input("Venta mensual fija ($)", min_value=1000,
                                     max_value=10_000_000, value=500_000, step=10_000,
                                     format="%d")
        ventas = [venta_base] * 14   # 14 = 12 meses + 2 buffer para cobros anteriores
    else:
        venta_base = st.number_input("Venta base mensual ($)", min_value=1000,
                                     max_value=10_000_000, value=500_000, step=10_000,
                                     format="%d")
        crecimiento = st.slider("Crecimiento mensual (%)", -10, 30, 5) / 100
        ventas = [int(venta_base * (1 + crecimiento) ** i) for i in range(14)]

    st.markdown('<p class="section-title">Costos y gastos</p>',
                unsafe_allow_html=True)
    costo_variable_pct = st.slider("Costos variables (% de ventas)", 0, 80, 40) / 100
    gastos_fijos = st.number_input("Gastos fijos mensuales ($)", min_value=0,
                                   max_value=5_000_000, value=80_000, step=5_000,
                                   format="%d")

    st.markdown('<p class="section-title">Política de cobranza</p>',
                unsafe_allow_html=True)
    st.caption("Las fracciones deben sumar ≤ 100%. El resto es incobrable.")

    p30 = st.slider("% cobrado a 30 días", 0, 100, 40) / 100
    max_p60 = int((1 - p30) * 100)
    p60 = st.slider("% cobrado a 60 días", 0, max_p60,
                    min(35, max_p60)) / 100
    max_p90 = int((1 - p30 - p60) * 100)
    p90 = st.slider("% cobrado a 90 días", 0, max_p90,
                    min(20, max_p90)) / 100

    incobrable = round((1 - p30 - p60 - p90) * 100, 1)
    if incobrable > 0:
        st.warning(f"⚠️ {incobrable}% de ventas sin cobrar (incobrable)")
    else:
        st.success("✅ 100% de ventas contempladas")

    st.markdown('<p class="section-title">Saldo inicial</p>',
                unsafe_allow_html=True)
    saldo_inicial = st.number_input("Saldo en caja ($)", min_value=0,
                                    max_value=50_000_000, value=200_000, step=10_000,
                                    format="%d")

    nombres_mes = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ── cálculo de escenarios ─────────────────────────────────────────────────────

escenarios = {
    "Optimista":  (min(p30 + 0.10, 1.0),
                   max(p60 - 0.05, 0.0),
                   max(p90 - 0.05, 0.0)),
    "Base":       (p30, p60, p90),
    "Pesimista":  (max(p30 - 0.10, 0.0),
                   min(p60 + 0.05, 1.0 - max(p30 - 0.10, 0)),
                   min(p90 + 0.05, 1.0 - max(p30 - 0.10, 0) -
                       min(p60 + 0.05, 1.0 - max(p30 - 0.10, 0)))),
}

dfs = {}
for nombre, (e30, e60, e90) in escenarios.items():
    dfs[nombre] = build_cashflow(ventas, costo_variable_pct, gastos_fijos,
                                 e30, e60, e90, saldo_inicial)

df_base = dfs["Base"]


# ── cabecera ──────────────────────────────────────────────────────────────────

st.title("💰 Simulador de Flujo de Caja")
st.caption("Análisis de liquidez con escenarios de cobranza a 30 / 60 / 90 días")

# KPIs resumen
col1, col2, col3, col4 = st.columns(4)
saldo_final = df_base["Saldo acumulado"].iloc[-1]
flujo_total = df_base["Flujo neto"].sum()
meses_negativos = (df_base["Saldo acumulado"] < 0).sum()
dso = (df_base["Total cobrado"].sum() /
       df_base["Ventas"].sum() * 30
       * (p30 * 1 + p60 * 2 + p90 * 3)
       ) if df_base["Ventas"].sum() > 0 else 0

for col, label, valor, css in [
    (col1, "Saldo final (Mes 12)", fmt_mxn(saldo_final), color_class(saldo_final)),
    (col2, "Flujo neto acumulado",  fmt_mxn(flujo_total), color_class(flujo_total)),
    (col3, "Meses con saldo negativo", f"{meses_negativos} / 12",
     "negative" if meses_negativos > 0 else "positive"),
    (col4, "DSO estimado (días)", f"{p30*30 + p60*60 + p90*90:.0f} días", "neutral"),
]:
    col.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">{label}</p>
            <p class="metric-value {css}">{valor}</p>
        </div>""", unsafe_allow_html=True)


# ── tabs principales ──────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Flujo de caja",
    "🎯 Comparativo de escenarios",
    "📊 Análisis de cobranza",
    "📋 Tabla detallada"
])


# TAB 1 — Flujo de caja base
with tab1:
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Flujo neto mensual (Escenario Base)",
                        "Saldo acumulado mensual"),
        vertical_spacing=0.18,
        row_heights=[0.45, 0.55]
    )

    colors_bar = ["#059669" if v >= 0 else "#dc2626"
                  for v in df_base["Flujo neto"]]

    fig.add_trace(go.Bar(
        x=nombres_mes,
        y=df_base["Flujo neto"],
        marker_color=colors_bar,
        name="Flujo neto",
        hovertemplate="<b>%{x}</b><br>Flujo neto: $%{y:,.0f}<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=nombres_mes,
        y=df_base["Saldo acumulado"],
        mode="lines+markers",
        line=dict(color="#2563eb", width=2.5),
        marker=dict(size=7, color=[
            "#dc2626" if v < 0 else "#2563eb"
            for v in df_base["Saldo acumulado"]
        ]),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.08)",
        name="Saldo acumulado",
        hovertemplate="<b>%{x}</b><br>Saldo: $%{y:,.0f}<extra></extra>"
    ), row=2, col=1)

    # Línea de alerta en 0
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8",
                  line_width=1, row=2, col=1)

    fig.update_layout(height=520, showlegend=False,
                      plot_bgcolor="white", paper_bgcolor="white",
                      margin=dict(l=0, r=0, t=40, b=0))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9")
    fig.update_xaxes(gridcolor="#f1f5f9")

    st.plotly_chart(fig, use_container_width=True)

    if meses_negativos > 0:
        meses_riesgo = df_base[df_base["Saldo acumulado"] < 0]["Mes"].tolist()
        nombres_riesgo = [nombres_mes[m - 1] for m in meses_riesgo]
        st.error(f"🚨 **Riesgo de iliquidez** en: {', '.join(nombres_riesgo)}. "
                 f"Considera ajustar tu política de cobranza o aumentar el saldo inicial.")
    else:
        st.success("✅ El negocio mantiene saldo positivo los 12 meses con los parámetros actuales.")


# TAB 2 — Comparativo de escenarios
with tab2:
    fig2 = go.Figure()

    colores_esc = {"Optimista": "#059669", "Base": "#2563eb", "Pesimista": "#dc2626"}
    dash_esc   = {"Optimista": "solid", "Base": "solid", "Pesimista": "dash"}

    for nombre, df_esc in dfs.items():
        fig2.add_trace(go.Scatter(
            x=nombres_mes,
            y=df_esc["Saldo acumulado"],
            name=nombre,
            mode="lines+markers",
            line=dict(color=colores_esc[nombre], width=2.5,
                      dash=dash_esc[nombre]),
            marker=dict(size=6),
            hovertemplate=f"<b>{nombre}</b><br>%{{x}}: $%{{y:,.0f}}<extra></extra>"
        ))

    fig2.add_hline(y=0, line_dash="dot", line_color="#94a3b8", line_width=1)
    fig2.update_layout(
        title="Saldo acumulado por escenario",
        height=400,
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9"),
        xaxis=dict(gridcolor="#f1f5f9"),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Tabla resumen escenarios
    st.markdown("**Resumen por escenario**")
    resumen = []
    for nombre, (e30, e60, e90) in escenarios.items():
        df_e = dfs[nombre]
        resumen.append({
            "Escenario": nombre,
            "Cobro 30d": f"{e30*100:.0f}%",
            "Cobro 60d": f"{e60*100:.0f}%",
            "Cobro 90d": f"{e90*100:.0f}%",
            "Saldo final": fmt_mxn(df_e["Saldo acumulado"].iloc[-1]),
            "Meses negativos": int((df_e["Saldo acumulado"] < 0).sum()),
            "Flujo acumulado": fmt_mxn(df_e["Flujo neto"].sum()),
        })
    st.dataframe(pd.DataFrame(resumen).set_index("Escenario"),
                 use_container_width=True)


# TAB 3 — Análisis de cobranza
with tab3:
    col_a, col_b = st.columns(2)

    with col_a:
        # Dona: distribución de cobranza
        labels = ["30 días", "60 días", "90 días", "Incobrable"]
        values = [p30 * 100, p60 * 100, p90 * 100, incobrable]
        colores_dona = ["#059669", "#2563eb", "#f59e0b", "#dc2626"]

        fig_dona = go.Figure(go.Pie(
            labels=labels, values=values,
            hole=0.55,
            marker_colors=colores_dona,
            textinfo="label+percent",
            hovertemplate="%{label}: %{value:.1f}%<extra></extra>"
        ))
        fig_dona.update_layout(
            title="Distribución de política de cobranza",
            height=320, showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_dona, use_container_width=True)

    with col_b:
        # Barras apiladas: composición de cobros por mes
        fig_stack = go.Figure()
        for col_name, color, label in [
            ("Cobro 30d", "#059669", "Cobro 30d"),
            ("Cobro 60d", "#2563eb", "Cobro 60d"),
            ("Cobro 90d", "#f59e0b", "Cobro 90d"),
        ]:
            fig_stack.add_trace(go.Bar(
                x=nombres_mes,
                y=df_base[col_name],
                name=label,
                marker_color=color,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: $%{{y:,.0f}}<extra></extra>"
            ))

        fig_stack.update_layout(
            barmode="stack",
            title="Composición de cobros mensuales",
            height=320,
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9"),
            xaxis=dict(gridcolor="#f1f5f9"),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    # Diagnóstico de cobranza
    st.markdown("**Diagnóstico de tu política de cobranza**")
    dso_val = p30 * 30 + p60 * 60 + p90 * 90
    eficiencia = (p30 + p60 + p90) * 100

    c1, c2, c3 = st.columns(3)
    for col, label, valor, css in [
        (c1, "DSO (días promedio de cobro)",
         f"{dso_val:.0f} días", "positive" if dso_val <= 45 else
                                "neutral"  if dso_val <= 65 else "negative"),
        (c2, "Eficiencia de cobranza",
         f"{eficiencia:.0f}%", "positive" if eficiencia >= 90 else
                               "neutral"  if eficiencia >= 75 else "negative"),
        (c3, "Ventas incobrables",
         f"{incobrable:.1f}%", "positive" if incobrable == 0 else
                               "neutral"  if incobrable <= 5 else "negative"),
    ]:
        col.markdown(f"""
            <div class="metric-card">
                <p class="metric-label">{label}</p>
                <p class="metric-value {css}">{valor}</p>
            </div>""", unsafe_allow_html=True)


# TAB 4 — Tabla detallada
with tab4:
    st.markdown("**Detalle mensual — Escenario Base**")

    df_tabla = df_base.copy()
    df_tabla["Mes"] = nombres_mes
    df_tabla = df_tabla.set_index("Mes")

    cols_mxn = ["Ventas", "Cobro 30d", "Cobro 60d", "Cobro 90d",
                "Total cobrado", "Costos variables", "Gastos fijos",
                "Total egresos", "Flujo neto", "Saldo acumulado"]

    df_fmt = df_tabla[cols_mxn].map(lambda x: f"${x:,.0f}")

    def highlight_row(row):
        original = df_base[df_base.index == df_tabla.index.get_loc(row.name) + 1 - 1]
        if "Flujo neto" in row.index:
            idx = df_tabla.index.get_loc(row.name)
            saldo = df_base.iloc[idx]["Saldo acumulado"]
            flujo = df_base.iloc[idx]["Flujo neto"]
            styles = [""] * len(row)
            col_names = list(row.index)
            if "Saldo acumulado" in col_names:
                i = col_names.index("Saldo acumulado")
                styles[i] = "color: #dc2626; font-weight: 600" if saldo < 0 else "color: #059669; font-weight: 600"
            if "Flujo neto" in col_names:
                i = col_names.index("Flujo neto")
                styles[i] = "color: #dc2626" if flujo < 0 else "color: #059669"
            return styles
        return [""] * len(row)

    st.dataframe(df_fmt.style.apply(highlight_row, axis=1),
                 use_container_width=True, height=480)

    # Botón de descarga
    csv = df_base.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar tabla en CSV",
        data=csv,
        file_name="flujo_de_caja_simulacion.csv",
        mime="text/csv"
    )

st.divider()
st.caption("Simulador de Flujo de Caja · Análisis de cobranza a 30/60/90 días · "
           "Datos ingresados manualmente — no se almacena ninguna información.")