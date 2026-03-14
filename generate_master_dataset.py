import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Aumentar límite de dígitos para manejar Primos de Mersenne gigantescos
sys.set_int_max_str_digits(1000000)

# Rutas Objetivo
REPO_PATH = Path(r"C:\Users\jotam\OneDrive\Desktop\GahenaxAI\Repos_Auditoria\Mersenne-Gahen")
DATA_DIR = REPO_PATH / "artifacts"

def process_mersenne_logs():
    all_data = []
    
    if DATA_DIR.exists():
        for file_path in DATA_DIR.rglob("*.json"):
            if "checkpoint_" in file_path.name:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        row = {
                            'Prime_Exponent_P': data.get('p'),
                            'Lucas_Lehmer_Iterations': data.get('iter'),
                            'Spectral_Hash_PCP': data.get('hash'),
                            'Timestamp_Unix': data.get('timestamp'),
                            'Source_File': file_path.name
                        }
                        
                        ts = data.get('timestamp')
                        if ts:
                            row['Date'] = datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            row['Date'] = None
                            
                        all_data.append(row)
                except Exception as e:
                    print(f"Error procesando {file_path.name}: {e}")
                    
    return pd.DataFrame(all_data)

def generate_enterprise_bundle(df, output_prefix="OEDA_Mersenne_Premium"):
    if df.empty:
        print("No se encontraron logs estructurados para procesar.")
        return
        
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values(by='Date').reset_index(drop=True)
    
    # 1. Generar CSV Crudo (Para Data Scientists / Programmatic)
    csv_path = REPO_PATH / f"{output_prefix}_Raw.csv"
    df.to_csv(csv_path, index=False)
    print(f"[OK] CSV Crudo generado: {csv_path.name}")
    
    # 2. Generar Dashboard Excel (Para Tech Leads / C-Levels)
    excel_path = REPO_PATH / f"{output_prefix}_Dashboard.xlsx"
    
    df_raw = df.copy()
    
    # Resumen Ejecutivo (Agrupación simple para mostrar valor)
    df_summary = pd.DataFrame({
        'Metric': [
            'Total Telemetry Logs Computed',
            'First Recording Date',
            'Last Recording Date',
            'Max Prime Exponent Scanned',
            'Total Lucas-Lehmer Iterations'
        ],
        'Value': [
            len(df),
            df['Date'].min().strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(df['Date'].min()) else 'N/A',
            df['Date'].max().strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(df['Date'].max()) else 'N/A',
            df['Prime_Exponent_P'].max(),
            df['Lucas_Lehmer_Iterations'].sum()
        ]
    })
    
    # Datos de Falsabilidad / Certificación separados
    df_falsifiability = df[['Date', 'Prime_Exponent_P', 'Lucas_Lehmer_Iterations', 'Spectral_Hash_PCP']].dropna(subset=['Prime_Exponent_P'])
    
    # Escribir a Excel con múltiples hojas usando el motor openpyxl
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
            df_falsifiability.to_excel(writer, sheet_name='Certifications (FCD)', index=False)
            df_raw.to_excel(writer, sheet_name='Raw Master Data', index=False)
        print(f"[OK] Dashboard Excel (Múltiples Pestañas) generado: {excel_path.name}")
    except ImportError:
        print("[ERROR] openpyxl no esta instalado. Ejecuta: pip install openpyxl para exportar a XLSX.")
        return

if __name__ == "__main__":
    print(f"Iniciando escaneo de telemetría en: {REPO_PATH.name}...")
    df_master = process_mersenne_logs()
    
    if not df_master.empty:
        print(f"Logrados extraer {len(df_master)} registros de iteración computacional.")
        generate_enterprise_bundle(df_master)
    else:
        print("No se encontraron registros.")
