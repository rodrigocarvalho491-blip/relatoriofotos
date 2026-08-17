import streamlit as st
from fpdf import FPDF
from PIL import Image
import io
import os

# 1. Configuração da página e Estilo
st.set_page_config(page_title="Relatório Fotográfico", page_icon="📷", layout="wide")

CUSTOM_CSS = """
<style>
    h1, h2, h3 { color: #004080 !important; font-family: 'Segoe UI', sans-serif; }
    div.stButton > button:first-child {
        background-color: #004080 !important; color: #ffffff !important;
        border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("📷 Relatório Fotográfico & Lista de Equipamentos")
st.divider()

if "equipamentos" not in st.session_state:
    st.session_state.equipamentos = []

# --- SEÇÃO 1: DADOS DO CLIENTE E TIMBRADO ---
st.subheader("1. Identificação do Cliente")
col_c1, col_c2, col_c3 = st.columns([1, 2, 2])

with col_c1:
    cod_cliente = st.text_input("Código do Cliente", placeholder="Ex: 87.653")
with col_c2:
    nome_cliente = st.text_input("Nome / Razão Social", placeholder="Ex: SABOR DA TERRA ALIMENTACAO CORPORATIVA")
with col_c3:
    img_timbrado = st.file_uploader("Papel Timbrado (Opcional)", type=["png", "jpg", "jpeg"])

st.divider()

# --- SEÇÃO 2: EQUIPAMENTOS E CÁLCULO DE VAZÃO ---
st.subheader("2. Equipamentos e Vazão")

col_qtd, col_eq, col_vaz, col_btn = st.columns([1, 2, 2, 1])

with col_qtd:
    qtd_input = st.number_input("Quantidade", min_value=1, value=1, step=1)
with col_eq:
    nome_eq_input = st.text_input("Equipamento", placeholder="Ex: Forno Industrial")
with col_vaz:
    vazao_input = st.text_input("Vazão por Equipamento", placeholder="Ex: 1 ou 1,6")

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("➕ Adicionar"):
        if nome_eq_input.strip() and vazao_input.strip():
            try:
                # Converte e padroniza a vazão digitada
                vazao_clean_str = vazao_input.replace(",", ".").lower().replace("kg/h", "").strip()
                vazao_val = float(vazao_clean_str)
                vazao_formatada_exibicao = f"{vazao_val:.2f}".replace('.', ',').rstrip('0').rstrip(',')

                item_dict = {
                    "qtd": int(qtd_input),
                    "nome": nome_eq_input.strip(),
                    "vazao_unit": vazao_val,
                    "texto": f"{int(qtd_input):02d} - {nome_eq_input.strip()} - {vazao_formatada_exibicao} kg/h"
                }
                st.session_state.equipamentos.append(item_dict)
                st.success("Adicionado!")
            except ValueError:
                st.error("Informe um valor numérico válido para a vazão.")
        else:
            st.warning("Preencha o nome do equipamento e a vazão.")

# Exibição da Lista e Soma Total da Vazão
if st.session_state.equipamentos:
    st.write("**Itens Cadastrados:**")
    total_vazao = 0.0
    
    for idx, item in enumerate(st.session_state.equipamentos):
        # Multiplica a vazão informada pela quantidade do item
        total_vazao += item["qtd"] * item["vazao_unit"]
        
        c_txt, c_del = st.columns([5, 1])
        c_txt.text(item["texto"])
        if c_del.button("❌", key=f"del_{idx}"):
            st.session_state.equipamentos.pop(idx)
            st.rerun()

    vazao_total_str = f"{total_vazao:.2f}".replace('.', ',').rstrip('0').rstrip(',')
    st.markdown(f"**Total vazão: {vazao_total_str} kg/h**")

st.divider()

# --- SEÇÃO 3: UPLOAD DE FOTOS ---
st.subheader("3. Upload de Imagens do Relatório")

def carregar_fotos(label, max_arquivos=None):
    limite_txt = f"(Máximo {max_arquivos})" if max_arquivos else "(Ilimitado)"
    fotos = st.file_uploader(f"{label} {limite_txt}", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=label)
    if max_arquivos and fotos and len(fotos) > max_arquivos:
        st.error(f"⚠️ Limite excedido para {label}. Serão considerados apenas os primeiros {max_arquivos} arquivos.")
        return fotos[:max_arquivos]
    return fotos

col_f1, col_f2 = st.columns(2)
with col_f1:
    fotos_fachada = carregar_fotos("FACHADA", max_arquivos=2)
    fotos_central = carregar_fotos("CENTRAL", max_arquivos=2)
with col_f2:
    fotos_abrigo = carregar_fotos("ABRIGO", max_arquivos=4)
    fotos_equipamentos = carregar_fotos("EQUIPAMENTOS", max_arquivos=None)

st.divider()

# --- SEÇÃO 4: GERADOR DE PDF ---
class RelatorioPDF(FPDF):
    def __init__(self, timbrado_bytes=None, cod_cliente="", nome_cliente=""):
        super().__init__()
        self.timbrado_bytes = timbrado_bytes
        self.cod_cliente = cod_cliente
        self.nome_cliente = nome_cliente

    def header(self):
        if self.timbrado_bytes:
            try:
                img_temp = "temp_timbrado.jpg"
                img = Image.open(io.BytesIO(self.timbrado_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(img_temp)
                self.image(img_temp, x=0, y=0, w=210, h=297)
                if os.path.exists(img_temp):
                    os.remove(img_temp)
            except Exception:
                pass

        self.set_y(15)
        self.set_font("Arial", "B", 15)
        self.cell(0, 8, "RELATÓRIO DE FOTOS", align="C", ln=1)
        
        info_cabecalho = f"{self.cod_cliente} | {self.nome_cliente}".strip(" |")
        if info_cabecalho:
            self.set_font("Arial", "B", 11)
            self.cell(0, 6, info_cabecalho, align="C", ln=1)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def gerar_pdf(equipamentos, dic_fotos, cod_cliente, nome_cliente, timbrado_file):
    timbrado_bytes = timbrado_file.read() if timbrado_file else None
    
    pdf = RelatorioPDF(timbrado_bytes, cod_cliente, nome_cliente)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Inserção da Lista de Equipamentos e Totalizador
    if equipamentos:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "LISTA DE EQUIPAMENTOS E VAZÕES", ln=1)
        pdf.set_font("Arial", "", 10)
        
        total_vazao = 0.0
        for item in equipamentos:
            total_vazao += item["qtd"] * item["vazao_unit"]
            pdf.cell(0, 5, item["texto"], ln=1)
        
        vazao_total_str = f"{total_vazao:.2f}".replace('.', ',').rstrip('0').rstrip(',')
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"Total vazão: {vazao_total_str} kg/h", ln=1)
        pdf.ln(4)

    # Inserção das Fotos organizadas por categoria
    for categoria, arquivos in dic_fotos.items():
        if arquivos:
            for idx, arq in enumerate(arquivos):
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 6, f"{categoria} {idx + 1 if len(arquivos) > 1 else ''}".strip(), ln=1)
                
                try:
                    img = Image.open(arq)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    temp_path = f"temp_{categoria}_{idx}.jpg"
                    img.save(temp_path)
                    
                    pdf.image(temp_path, w=140)
                    pdf.ln(6)
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as e:
                    pdf.cell(0, 6, f"Erro ao processar imagem: {e}", ln=1)

    return pdf.output(dest="S").encode("latin-1", errors="ignore")

if st.button("📄 Gerar Relatório PDF"):
    dicionario_fotos = {
        "FACHADA": fotos_fachada,
        "ABRIGO": fotos_abrigo,
        "CENTRAL": fotos_central,
        "EQUIPAMENTOS": fotos_equipamentos
    }
    
    pdf_out = gerar_pdf(
        st.session_state.equipamentos,
        dicionario_fotos,
        cod_cliente,
        nome_cliente,
        img_timbrado
    )
    
    st.success("✅ Relatório gerado com sucesso!")
    st.download_button(
        label="📥 Baixar Relatório (PDF)",
        data=pdf_out,
        file_name=f"Relatorio_{cod_cliente if cod_cliente else 'Fotos'}.pdf",
        mime="application/pdf"
    )