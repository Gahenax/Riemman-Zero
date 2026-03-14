from prometheus_client import start_http_server, Gauge, Counter
import time
import json
import os

# ============================================================================
# OEDA Observability: Prometheus Exporter para OUROBOROS LAB
# ============================================================================

# Definición de Métricas SLA/SLI estilo Cloud-Native
OUROBOROS_EXPERIMENTS_RUN = Counter('oeda_ouroboros_experiments_total', 'Total de experimentos Ouroboros ejecutados')
OUROBOROS_FAILURES = Counter('oeda_ouroboros_failures_total', 'Fallos críticos en la convergencia del ciclo Ouroboros')
OUROBOROS_CURRENT_VARIANCE = Gauge('oeda_ouroboros_current_variance', 'Varianza espectral medida en la última pasada')

def monitor_ouroboros_report(report_path="ouroboros_report.json"):
    """
    Lee periódicamente el JSON de salida de Ouroboros y actualiza
    las métricas de Prometheus en memoria. (Modelo Pull de Prometheus)
    """
    global_last_modified = 0
    print(f"[*] Iniciando Exporter de Observabilidad de OEDA en puerto 8000...")
    start_http_server(8000)
    
    while True:
        try:
            if os.path.exists(report_path):
                mtime = os.path.getmtime(report_path)
                if mtime > global_last_modified:
                    # El reporte fue actualizado por el autopiloto!
                    global_last_modified = mtime
                    with open(report_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Extraer telemetría
                    OUROBOROS_EXPERIMENTS_RUN.inc()
                    
                    status = data.get("global_verdict", "UNKNOWN")
                    if status != "GREEN":
                        OUROBOROS_FAILURES.inc()
                        
                    # Digamos que hay un campo de varianza (mockupeado o real)
                    metrics = data.get("metrics", {})
                    variance = metrics.get("spectral_variance", 0.0)
                    OUROBOROS_CURRENT_VARIANCE.set(variance)
                    
                    print(f"[+] Grafana/Prometheus Actualizado -> Veredicto: {status} | Varianza: {variance}")
                    
        except Exception as e:
            print(f"[!] Error leyendo telemetría: {e}")
            
        # Prometheus hace scraping cada 15s (ver observacion en workflow), 
        # actualizamos la variable de estado cada 5s
        time.sleep(5)

if __name__ == "__main__":
    # Integración con `/observability-monitoring-stack`
    # Esto levantará `http://localhost:8000/metrics` para que Grafana lo lea en tiempo real
    monitor_ouroboros_report()
