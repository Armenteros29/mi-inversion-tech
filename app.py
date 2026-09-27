import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="Inversor Tech", page_icon="📈", layout="wide")

PORTFOLIO_FILE = "portfolio_data.json"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return []

def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f)

st.sidebar.title("Configuración")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Necesaria para el análisis con IA. Consíguela en Google AI Studio.")
st.sidebar.markdown("[Obtener API Key gratuita](https://aistudio.google.com/app/apikey)")

menu = st.sidebar.radio("Navegación", ["Analizador con IA", "Mi Portfolio"])

if menu == "Analizador con IA":
    st.title("🧠 Analizador de Empresas Tech")
    ticker = st.text_input("Introduce el Ticker de la empresa (Ej. MSFT, AAPL, NVDA):").upper()
    
    if st.button("Analizar") and ticker:
        with st.spinner("Recopilando datos financieros..."):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if False:
                    st.error("No se ha encontrado la empresa. Revisa el Ticker.")
                else:
                    name = info.get('shortName', ticker)
                    price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    per = info.get('trailingPE', 'N/A')
                    fwd_per = info.get('forwardPE', 'N/A')
                    revenue_growth = info.get('revenueGrowth', 'N/A')
                    margins = info.get('profitMargins', 'N/A')
                    debt_eq = info.get('debtToEquity', 'N/A')
                    
                    st.subheader(f"📊 Datos de {name}")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Precio Actual", f"${price}")
                    col2.metric("PER (Valoración)", f"{round(per, 2) if isinstance(per, float) else per}")
                    col3.metric("Crecimiento Ingresos", f"{round(revenue_growth*100, 2)}%" if isinstance(revenue_growth, float) else revenue_growth)
                    col4.metric("Margen de Beneficio", f"{round(margins*100, 2)}%" if isinstance(margins, float) else margins)
                    
                    if api_key:
                        with st.spinner("🤖 La IA está evaluando los datos..."):
                            import requests
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
                            prompt = f"""
                            Eres un analista financiero experto en tecnología. 
                            Analiza estos datos de {name} ({ticker}):
                            - Precio: {price}
                            - PER histórico: {per}
                            - Crecimiento de ingresos: {revenue_growth}
                            - Deuda vs Capital: {debt_eq}
                            - Márgenes de beneficio: {margins}
                            
                            1. Dame una puntuación del 1 al 10 sobre si es buena inversión ahora mismo (ponla grande al principio).
                            2. Redacta un consejo de 3-4 párrafos explicando tus razones de manera sencilla para alguien que invierte y lee desde su móvil. Usa viñetas para lo bueno y lo malo.
                            """
                            
                            data = {
                                "contents": [{"parts":[{"text": prompt}]}]
                            }
                            
                            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=data)
                            
                            if response.status_code == 200:
                                result = response.json()
                                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No se pudo generar el consejo.')
                                st.success("Análisis completado")
                                st.markdown(text)
                            else:
                                st.error(f"Error de la API de IA: {response.status_code} - {response.text}")
                    else:
                        st.warning("⚠️ Introduce tu clave API de Gemini en la barra lateral para generar el consejo experto con IA.")
            except Exception as e:
                st.error(f"Error al conectar con la base de datos financiera: {e}")

elif menu == "Mi Portfolio":
    st.title("💼 Mi Portfolio")
    portfolio = load_portfolio()
    
    with st.expander("➕ Añadir nueva inversión"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_ticker = st.text_input("Ticker (Ej. AMD)").upper()
        with col2:
            shares = st.number_input("Número de acciones", min_value=0.01, step=0.01)
        with col3:
            buy_price = st.number_input("Precio de compra ($)", min_value=0.01, step=0.01)
            
        if st.button("Añadir a portfolio"):
            if new_ticker and shares > 0 and buy_price > 0:
                portfolio.append({"ticker": new_ticker, "shares": shares, "buy_price": buy_price})
                save_portfolio(portfolio)
                st.success("¡Añadido!")
                st.rerun()

    if portfolio:
        st.subheader("Estado Actual")
        total_invested = 0
        total_current = 0
        
        display_data = []
        with st.spinner("Actualizando precios de mercado..."):
            for item in portfolio:
                ticker = item["ticker"]
                try:
                    # Intentar obtener precio actual
                    current_price = yf.Ticker(ticker).info.get('currentPrice', item["buy_price"])
                except:
                    current_price = item["buy_price"]
                    
                invested = item["shares"] * item["buy_price"]
                current_value = item["shares"] * current_price
                profit = current_value - invested
                profit_pct = (profit / invested) * 100 if invested > 0 else 0
                
                total_invested += invested
                total_current += current_value
                
                display_data.append({
                    "Empresa": ticker,
                    "Acciones": item["shares"],
                    "Invertido": round(invested, 2),
                    "Valor Actual": round(current_value, 2),
                    "Beneficio ($)": round(profit, 2),
                    "Rendimiento (%)": round(profit_pct, 2)
                })
        
        # Resumen general superior
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invertido", f"${round(total_invested, 2)}")
        
        # Calcular rentabilidad total
        rent_total_pct = round(((total_current-total_invested)/total_invested)*100, 2) if total_invested else 0
        col2.metric("Valor Actual", f"${round(total_current, 2)}", f"{rent_total_pct}%")
        col3.metric("Beneficio Total", f"${round(total_current - total_invested, 2)}")
        
        # Tabla
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Gráfico visual
        st.subheader("Distribución de tus Inversiones")
        fig = px.pie(df, values='Valor Actual', names='Empresa', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("Limpiar Portfolio"):
            save_portfolio([])
            st.rerun()
    else:
        st.info("Tu portfolio está vacío. Añade empresas para empezar a trackear tu dinero.")
