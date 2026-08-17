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

# Definição de caminhos fixos de arquivos da pasta
LOGO_PATH = "logo.png"
TIMBRADO_PNG = "timbrado.png"
TIMBRADO_JPG = "timbrado.jpg"

def obter_caminho_timbrado():
    if os.path.exists(TIMBRADO_PNG):
        return TIMBRADO_PNG
    elif os.path.exists(TIMBRADO_JPG):
        return TIMBRADO_JPG
    return None

# --- CABEÇALHO DO APP COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.caption("📷 *Adicione 'logo.png' na pasta do projeto*")

with col_titulo:
    st.title("Relatório Fotográfico & Equipamentos")
    st.markdown("Gerador automatizado de relatórios técnicos com layout timbrado.")

st.divider()

if "equipamentos" not in st.session_state:
    st.session_state.equipamentos = []

# --- SEÇÃO 1: DADOS DO CLIENTE ---
st.subheader("1. Identificação do Cliente")
col_c1, col_c2 = st.columns(2)

with col_c1:
    cod_cliente = st.text_input("Código do Cliente", placeholder="Ex: 87.653")
with col_c2:
    nome_cliente = st.text_input("Nome / Razão Social", placeholder="Ex: SABOR DA TERRA ALIMENTACAO CORPORATIVA")

st.divider()

# --- SEÇÃO 2: UPLOAD DE FOTOS ---
st.subheader("2. Upload de Imagens do Relatório")

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

# --- SEÇÃO 3: GERAÇÃO DO RELATÓRIO PDF ---
st.subheader("3. Geração do Relatório")

class RelatorioPDF(FPDF):
    def __init__(self, cod_cliente="", nome_cliente=""):
        super().__init__()
        self.cod_cliente = cod_cliente
        self.nome_cliente = nome_cliente
        self.caminho_timbrado = obter_caminho_timbrado()

    def header(self):
        if self.caminho_timbrado:
            try:
                self.image(self.caminho_timbrado, x=0, y=0, w=210, h=297)
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

def gerar_pdf(equipamentos, dic_fotos, cod_cliente, nome_cliente):
    pdf = RelatorioPDF(cod_cliente, nome_cliente)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    if equipamentos:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "LISTA DE EQUIPAMENTOS E VAZÕES", ln=1)
        pdf.set_font("Arial", "", 10)
        
        total_vazao = 0.0
        for item in equipamentos:
            total_vazao += item["vazao_total_item"]
            pdf.cell(0, 5, item["texto"], ln=1)
        
        vazao_total_str = f"{total_vazao:.2f}".replace('.', ',').rstrip('0').rstrip(',')
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"Total vazão: {vazao_total_str} kg/h", ln=1)
        pdf.ln(4)

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
        nome_cliente
    )
    
    st.success("✅ Relatório gerado com sucesso!")
    st.download_button(
        label="📥 Baixar Relatório (PDF)",
        data=pdf_out,
        file_name=f"Relatorio_{cod_cliente if cod_cliente else 'Fotos'}.pdf",
        mime="application/pdf"
    )

st.divider()

# --- SEÇÃO 4: CADASTRO DE EQUIPAMENTOS (POR FIM) ---
st.subheader("4. Cadastro de Equipamentos")

col_qtd, col_eq, col_vaz, col_btn = st.columns([1, 2, 2, 1])

with col_qtd:
    qtd_input = st.number_input("Quantidade", min_value=1, value=1, step=1, key="eq_qtd")
with col_eq:
    nome_eq_input = st.text_input("Equipamento", placeholder="Ex: Forno Industrial", key="eq_nome")
with col_vaz:
    vazao_input = st.text_input("Vazão Unitária (kg/h)", placeholder="Ex: 1 ou 1,6", key="eq_vazao")

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("➕ Adicionar", key="btn_add_eq"):
        if nome_eq_input.strip() and vazao_input.strip():
            try:
                vazao_clean_str = vazao_input.replace(",", ".").lower().replace("kg/h", "").strip()
                vazao_unit = float(vazao_clean_str)
                qtd = int(qtd_input)
                
                vazao_total_item = vazao_unit * qtd
                vazao_formatada = f"{vazao_total_item:.2f}".replace('.', ',').rstrip('0').rstrip(',')

                item_dict = {
                    "qtd": qtd,
                    "nome": nome_eq_input.strip(),
                    "vazao_unit": vazao_unit,
                    "vazao_total_item": vazao_total_item,
                    "texto": f"{qtd:02d} - {nome_eq_input.strip()} - {vazao_formatada} kg/h"
                }
                st.session_state.equipamentos.append(item_dict)
                st.success("Adicionado!")
            except ValueError:
                st.error("Informe um valor numérico válido para a vazão.")
        else:
            st.warning("Preencha o equipamento e a vazão.")

if st.session_state.equipamentos:
    st.write("**Lista de Equipamentos:**")
    total_vazao = 0.0
    
    for idx, item in enumerate(st.session_state.equipamentos):
        total_vazao += item["vazao_total_item"]
        
        c_txt, c_del = st.columns([5, 1])
        c_txt.text(item["texto"])
        if c_del.button("❌", key=f"del_{idx}"):
            st.session_state.equipamentos.pop(idx)
            st.rerun()

    vazao_total_str = f"{total_vazao:.2f}".replace('.', ',').rstrip('0').rstrip(',')
    st.markdown(f"**Total vazão: {vazao_total_str} kg/h**")
