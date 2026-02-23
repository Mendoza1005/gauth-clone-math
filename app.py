import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
# try to use the new `google-genai` package, but fall back to the
# legacy one if it isn't available or doesn't expose the required API.  Both
# packages currently offer `configure()` and `GenerativeModel` so the rest of
# the application can be written once.
try:
    import google.genai as genai
    # if the imported module doesn't have the expected methods, pretend it
    # failed so we can fall back to the older package.
    if not hasattr(genai, "configure") or not hasattr(genai, "GenerativeModel"):
        raise ImportError("google.genai missing expected API")
except ImportError:
    import google.generativeai as genai
    st.warning("Usando paquete obsoleto google.generativeai; se recomienda seguir usando este por ahora")


# 1. Configuración de Estilo
st.set_page_config(page_title="Gauth-Lite", page_icon="🎓", layout="wide")

# --- NUEVA SECCIÓN: CONTACTO EN EL SIDEBAR ---
with st.sidebar:
    st.header("👤 Desarrollador")
    st.markdown("""
    **Creado por: Torres Mendoza Christian Miguel**
    
    Estudiante de ingenieria en desarrollo de software, apasionado por los videjuegos y la tecnología, con experiencia en desarrollo web y aplicaciones de inteligencia artificial.
    
    [![GitHub](https://img.shields.io/badge/GitHub-Profile-black?style=flat&logo=github)](https://github.com/)
    [![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com/)
    """)
    st.divider()
    
    st.header("⚙️ Configuración")
    modo = st.radio("Tipo de Integral:", ["Indefinida", "Definida (Área)"])
    st.divider()
    st.info("💡 Tip: Usa `x**2` para x² y `exp(x)` para eˣ.")

# --- TÍTULO PRINCIPAL ---
st.title("🎓 Gauth-Lite: Inteligencia Matemática")
st.subheader("Solucionador de integrales profesional con IA")

# 2. Entrada de Usuario
expr_input = st.text_input("Introduce la función f(x):", "x**2")

if modo == "Definida (Área)":
    col1, col2 = st.columns(2)
    a_val = col1.number_input("Límite a", value=0.0)
    b_val = col2.number_input("Límite b", value=2.0)
    # si el usuario invirtió los límites, cámbialos silenciosamente para no
    # romper la lógica de la gráfica y el cálculo.
    if a_val > b_val:
        a_val, b_val = b_val, a_val
else:
    a_val, b_val = -2.0, 2.0

# 3. Procesamiento Principal
if expr_input:
    try:
        x = sp.symbols('x')
        f = sp.sympify(expr_input)
        integral_indef = sp.integrate(f, x)
        # preparar resultado de la integral definida si corresponde
        if modo == "Definida (Área)":
            resultado_def = sp.integrate(f, (x, a_val, b_val))

        tab1, tab2, tab3 = st.tabs(["📊 Gráfica", "📝 Paso a Paso (IA)", "🧪 Verificación"])

        with tab1:
            st.success("### Resultado")
            if modo == "Indefinida":
                st.latex(f"\\int ({sp.latex(f)}) \\, dx = {sp.latex(integral_indef)} + C")
            else:
                st.latex(f"\\int_{{{a_val}}}^{{{b_val}}} ({sp.latex(f)}) \\, dx = {sp.latex(resultado_def.evalf(4))}")
            
            # Gráfica dinámica
            f_num = sp.lambdify(x, f, 'numpy')
            x_vals = np.linspace(a_val - 5, b_val + 5, 400)
            y_vals = f_num(x_vals)
            
            fig, ax = plt.subplots(figsize=(8, 4))
            if modo == "Definida (Área)":
                x_fill = np.linspace(a_val, b_val, 100)
                ax.fill_between(x_fill, f_num(x_fill), color='skyblue', alpha=0.5, label="Área")
            
            ax.plot(x_vals, y_vals, color='#1E88E5', lw=2, label="f(x)")
            ax.axhline(0, color='black', lw=1)
            ax.axvline(0, color='black', lw=1)
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with tab2:
            st.info("### Explicación con IA")
            api_key = st.secrets.get("GEMINI_API_KEY")
            
            if not api_key:
                api_key = st.text_input("🔑 Pega tu API Key para activar la IA:", type="password")

            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    chosen_model = 'gemini-1.5-flash'
                    try:
                        models_info = genai.list_models()
                        # NOTE: we no longer dump the entire response to the UI; it
                        # was only useful during early testing and cluttered the
                        # interface for normal users.  Keep the variable in case
                        # we want to inspect it programmatically later.
                        # try to pick a working model automatically
                        candidates = []
                        if isinstance(models_info, dict):
                            candidates = models_info.get('models', [])
                        elif isinstance(models_info, list):
                            candidates = models_info
                        # normalize to name strings
                        names = []
                        for entry in candidates:
                            if isinstance(entry, dict):
                                names.append(entry.get('name'))
                            else:
                                names.append(entry)
                        # attempt to instantiate each
                        for nm in names:
                            if not nm:
                                continue
                            try:
                                genai.GenerativeModel(nm)
                                chosen_model = nm
                                break
                            except Exception:
                                continue
                        # let user choose explicitly if there are multiple
                        if names:
                            # ensure selected model is in names
                            default_index = names.index(chosen_model) if chosen_model in names else 0
                            chosen_model = st.selectbox("Elige un modelo IA:", names, index=default_index)
                        st.write(f"Using model: {chosen_model}")
                    except Exception as e:
                        st.write(f"Could not list models: {e}")
                    model = genai.GenerativeModel(chosen_model)
                    
                    with st.spinner("🤖 La IA está redactando la explicación..."):
                        if modo == "Indefinida":
                            prompt = (f"Explica paso a paso la integral indefinida de f(x) = {expr_input}. "
                                      f"El resultado es {sp.latex(integral_indef)}. Sé muy didáctico.")
                            resultado_para_descarga = integral_indef
                        else:
                            # modo definida
                            prompt = (f"Explica paso a paso la integral definida de f(x) = {expr_input} "
                                      f"desde {a_val} hasta {b_val}. "
                                      f"El resultado es {sp.latex(resultado_def.evalf(4))}. Sé muy didáctico.")
                            resultado_para_descarga = resultado_def.evalf(4)

                        response = model.generate_content(prompt)
                        explicacion = response.text
                        st.markdown(explicacion)
                        
                        # --- BOTÓN DE DESCARGA ---
                        st.download_button(
                            label="📥 Descargar Solución",
                            data=f"RESULTADO: {resultado_para_descarga}\n\nEXPLICACIÓN:\n{explicacion}",
                            file_name="solucion_matematica.txt",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Error de IA: {e}")

        with tab3:
            st.write("### Verificación Matemática")
            derivada = sp.diff(integral_indef, x)
            st.latex(f"\\frac{{d}}{{dx}} ({sp.latex(integral_indef)}) = {sp.latex(derivada)}")
            if sp.simplify(derivada - f) == 0:
                st.success("✅ ¡Verificación exitosa!")

    except Exception as e:
        st.error(f"Error en la expresión: {e}")