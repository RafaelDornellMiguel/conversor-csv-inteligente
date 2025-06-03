import streamlit as st
import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from io import BytesIO
import os
import re

# ----- Função para sugerir nomes -----
def sugerir_nome(coluna):
    sample = coluna.dropna().astype(str).head(10).tolist()
    joined = " ".join(sample)

    if all(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", v) for v in sample):
        return "CPF"
    elif all(re.fullmatch(r"\(?\d{2}\)?\s?\d{4,5}-\d{4}", v) for v in sample):
        return "Telefone"
    elif all(re.fullmatch(r"\d{2}/\d{2}/\d{4}", v) for v in sample):
        return "Data de Nascimento"
    elif all(re.fullmatch(r"[A-Z][a-z]+(\s[A-Z][a-z]+)*", v) for v in sample):
        return "Nome"
    elif all(re.fullmatch(r"\d+", v) for v in sample):
        if len(sample[0]) >= 6:
            return "Prontuário"
        return "ID"
    elif any("@" in v for v in sample):
        return "Email"
    elif all(re.fullmatch(r"\d+[.,]?\d*", v.replace(",", ".")) for v in sample):
        return "Valor"
    return "Coluna"

# ----- Função para aplicar formatação Excel -----
def format_excel(writer, sheet_name):
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
    for column in worksheet.columns:
        max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column)
        col_letter = get_column_letter(column[0].column)
        worksheet.column_dimensions[col_letter].width = max_length + 2

# ----- Tenta abrir CSV com codificações diferentes -----
def try_read_csv(file):
    encodings = ['utf-8', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            return pd.read_csv(file, encoding=enc)
        except:
            file.seek(0)
    return None

# ----- App principal -----
def main():
    st.set_page_config(page_title="Conversor CSV Inteligente", layout="wide")
    st.title("🧠 Conversor CSV estilo Excel - Renomeia por Conteúdo")

    uploaded_files = st.file_uploader(
        "📁 Selecione arquivos CSV para carregar", 
        type=['csv'], 
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            st.divider()
            st.subheader(f"📄 {file.name}")

            df = try_read_csv(file)
            if df is None:
                st.error("Erro ao ler o arquivo. Codificação não suportada.")
                continue

            st.write("Pré-visualização dos dados:")
            st.dataframe(df.head(50), use_container_width=True)

            with st.expander("🛠️ Transformar dados"):
                # ----- Remover colunas -----
                cols_to_drop = st.multiselect("Remover colunas", df.columns.tolist())
                if cols_to_drop:
                    df.drop(columns=cols_to_drop, inplace=True)

                # ----- Preencher valores vazios -----
                fill_na = st.checkbox("Substituir valores vazios por '-'", value=True)
                if fill_na:
                    df.fillna("-", inplace=True)

                # ----- Renomeia colunas -----
                st.markdown("### ✏️ Renomear colunas com sugestões automáticas")
                new_names = {}
                for col in df.columns:
                    sugestao = sugerir_nome(df[col]) if 'Unnamed' in col or 'Column' in col else col
                    novo_nome = st.text_input(f"'{col}'", value=sugestao)
                    new_names[col] = novo_nome
                df.rename(columns=new_names, inplace=True)

            # ----- Exporta para Excel -----
            output = BytesIO()
            filename = os.path.splitext(file.name)[0] + ".xlsx"

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Dados")
                format_excel(writer, "Dados")

            output.seek(0)
            st.download_button(
                label=f"📥 Baixar {filename}",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
