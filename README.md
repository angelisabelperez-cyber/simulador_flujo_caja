# 💰 Simulador de Flujo de Caja con Escenarios de Cobranza

Herramienta interactiva construida con Python y Streamlit para analizar la liquidez
de una empresa bajo diferentes políticas de cobranza (30/60/90 días).

---

## 🚀 Cómo ejecutarlo

### 1. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 2. Corre la aplicación

```bash
streamlit run app.py
```

La app se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 🎛️ Qué puedes configurar (panel izquierdo)

| Parámetro | Descripción |
|---|---|
| Venta mensual | Ingreso fijo o con crecimiento estacional |
| Costos variables | % de las ventas (COGS) |
| Gastos fijos | Renta, nómina, servicios, etc. |
| % cobrado a 30d / 60d / 90d | Tu política de cobranza actual |
| Saldo inicial en caja | Disponible al inicio del período |

---

## 📊 Qué analiza la aplicación

- **Flujo neto mensual** — barras verdes/rojas por mes
- **Saldo acumulado** — curva de liquidez durante 12 meses
- **3 escenarios** — Optimista, Base y Pesimista (ajuste automático de cobranza)
- **DSO** — Días promedio de cobro de tu cartera
- **Composición de cobros** — cuánto entra cada mes según la política
- **Alertas de iliquidez** — meses con saldo negativo resaltados en rojo
- **Descarga CSV** — exporta la tabla completa para presentaciones

---

## 📂 Estructura del proyecto

```
simulador_flujo_caja/
├── app.py            ← Aplicación principal
├── requirements.txt  ← Dependencias
└── README.md         ← Este archivo
```

---

## 💡 Próximos pasos para el portafolio

- [ ] Conectar con datos reales vía API de Banxico (INPC para ajuste inflacionario)
- [ ] Agregar exportación a Excel con formato ejecutivo
- [ ] Añadir análisis de sensibilidad (¿qué pasa si ventas caen 20%?)
- [ ] Publicar en Streamlit Community Cloud (gratis) para compartir el link

---

*Proyecto de portafolio — Análisis de Datos Financieros*
