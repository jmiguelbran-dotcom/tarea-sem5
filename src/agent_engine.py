import copy
import json
import os
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.models import TransaccionNormalizada, HallazgoAuditoria
from src.skill_loader import SkillLoader


class AgentePersonalizadoEngine:
    """Orquestador agéntico que adapta su análisis según el perfil y la Skill activa."""

    def __init__(self, perfil_key: str = "auditor_forense"):
        self.loader = SkillLoader()
        self.perfiles = self.loader.cargar_perfiles()
        self.cambiar_perfil(perfil_key)

    def cambiar_perfil(self, perfil_key: str) -> None:
        if perfil_key not in self.perfiles:
            raise ValueError(f"Perfil desconocido: {perfil_key}")
        self.perfil_key = perfil_key
        self.perfil = self.perfiles[perfil_key]
        self.skill = self.loader.cargar_skill(self.perfil["skill_principal"])

    def _clasificar_severidad(self, tx: TransaccionNormalizada) -> str:
        texto_err = " ".join(tx.errores_validacion).lower()
        if "mayor a cero" in texto_err or "fuente" in texto_err or "inválido" in texto_err:
            return "CRÍTICA"
        if "id" in texto_err or "moneda" in texto_err:
            return "ALTA"
        return "MEDIA"

    def _generar_remediacion(self, tx: TransaccionNormalizada) -> tuple[str, Optional[Dict[str, Any]]]:
        sugerido = copy.deepcopy(tx.registro_original)
        acciones = []

        for err in tx.errores_validacion:
            err_low = err.lower()
            if "mayor a cero" in err_low:
                acciones.append("Invertir signo o solicitar confirmación al comercio antes de reprocesar.")
                for k in ("amount_cents", "gross_amount", "monto_transferido", "importe", "efectivo_recibido"):
                    if k in sugerido and isinstance(sugerido[k], (int, float)):
                        sugerido[k] = abs(sugerido[k])
            elif "id de transacción" in err_low:
                acciones.append("Asignar identificador de respaldo basado en timestamp y fuente.")
                for k in ("charge_id", "txn_id", "numero_referencia", "id_autorizacion", "folio_recibo"):
                    if k in sugerido and not sugerido[k]:
                        sugerido[k] = f"AUTO-{tx.fuente[:3]}-99999"
            elif "moneda" in err_low:
                acciones.append("Reemplazar divisa no autorizada por moneda FIAT/Crypto soportada (ej. USD).")
                for k in ("currency_code", "curr", "divisa", "moneda_cobro", "moneda_efectivo"):
                    if k in sugerido:
                        sugerido[k] = "USD"
            elif "estado" in err_low:
                acciones.append("Homologar estado del proveedor a 'pending' para revisión manual.")
                for k in ("charge_status", "payment_status", "estado_operacion", "resultado_pos", "estatus_recibo"):
                    if k in sugerido:
                        sugerido[k] = "pending"
            elif "fecha" in err_low:
                acciones.append("Corregir fecha calendario inválida al último día válido del mes.")
                for k in ("created_at", "payment_date", "fecha_operacion", "timestamp_pos", "fecha_emision"):
                    if k in sugerido:
                        sugerido[k] = "2026-02-28"

        recomendacion = " ".join(acciones) if acciones else "Revisar estructura del payload origen."
        return recomendacion, (sugerido if self.perfil.get("incluir_json_corregido") else None)

    def _consultar_llm_opcional(self, prompt_usuario: str) -> Optional[str]:
        """Si existe OPENAI_API_KEY en el entorno, enriquece el análisis con un LLM real."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {
                        "role": "system",
                        "content": f"Rol: {self.perfil['rol']}. Tono: {self.perfil['tono']}.\n{self.skill['instructions']}",
                    },
                    {"role": "user", "content": prompt_usuario},
                ],
                "temperature": 0.2,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def ejecutar_auditoria(
        self, transacciones: List[TransaccionNormalizada], archivo: str
    ) -> str:
        """Ejecuta el análisis personalizado usando las instrucciones y plantilla de la Skill."""
        invalidas = [t for t in transacciones if not t.es_valida]
        validas = [t for t in transacciones if t.es_valida]

        # Si el perfil usa la skill 'normalizador-financiero', audita el esquema canónico y conciliación
        if self.perfil["skill_principal"] == "normalizador-financiero":
            esquema = json.loads(self.skill["resources"].get("esquema_canonico.json", "{}"))
            pendientes = [t for t in validas if t.estado == "PENDIENTE"]
            ratio_pend = (len(pendientes) / len(validas) * 100) if validas else 0.0
            alerta = (
                f"ALERTA: {ratio_pend:.1f}% de transacciones válidas están PENDIENTES (supera umbral de 30%)."
                if ratio_pend > 30
                else f"OK: Volumen pendiente controlado ({ratio_pend:.1f}%)."
            )
            lineas = [
                "=" * 80,
                f" REPORTE DE CONCILIACIÓN CANÓNICA | {self.perfil['nombre']}",
                f" Skill Aplicada: {self.skill['name']} (Schema v{esquema.get('schema_version', '2.0.0')})",
                "=" * 80,
                f" • Transacciones conformes al esquema : {len(validas)} / {len(transacciones)}",
                f" • Control de liquidez pendiente      : {alerta}",
                f" • Tono del agente                    : {self.perfil['tono']}",
                "=" * 80,
            ]
            return "\n".join(lineas)

        # Flujo para la skill 'auditor-transacciones'
        hallazgos: List[HallazgoAuditoria] = []
        for tx in invalidas:
            sev = self._clasificar_severidad(tx)
            rec, json_fix = self._generar_remediacion(tx)
            hallazgos.append(
                HallazgoAuditoria(
                    id_transaccion=tx.id_transaccion,
                    fuente=tx.fuente,
                    severidad=sev,
                    causas_raiz=tx.errores_validacion,
                    recomendacion=rec,
                    json_sugerido=json_fix,
                )
            )

        bloques = []
        for h in hallazgos:
            bloque = (
                f"[{h.severidad}] ID: {h.id_transaccion} | Fuente: {h.fuente}\n"
                f"  - Diagnóstico : {'; '.join(h.causas_raiz)}\n"
                f"  - Acción      : {h.recomendacion}"
            )
            if h.json_sugerido:
                bloque += f"\n  - Patch JSON  : {json.dumps(h.json_sugerido, ensure_ascii=False)}"
            bloques.append(bloque)

        detalle_txt = "\n\n".join(bloques) if bloques else "Sin hallazgos críticos en el lote."
        riesgo = "ALTO" if any(h.severidad == "CRÍTICA" for h in hallazgos) else ("MEDIO" if hallazgos else "BAJO")

        plantilla = self.skill["resources"].get("plantilla_auditoria.md", "{{DETALLE_HALLAZGOS}}")
        reporte = (
            plantilla.replace("{{NOMBRE_AGENTE}}", self.perfil["nombre"])
            .replace("{{SKILL_NAME}}", self.skill["name"])
            .replace("{{ARCHIVO}}", archivo)
            .replace("{{TOTAL_INVALIDAS}}", str(len(invalidas)))
            .replace("{{RIESGO_GLOBAL}}", riesgo)
            .replace("{{DETALLE_HALLAZGOS}}", detalle_txt)
        )

        # Enriquecimiento opcional si el usuario configuró OPENAI_API_KEY
        sintesis_llm = self._consultar_llm_opcional(
            f"Resume en 2 líneas ejecutivas este reporte de auditoría:\n{reporte}"
        )
        if sintesis_llm:
            reporte += f"\n[SÍNTESIS LLM EXTERNA]: {sintesis_llm}\n"

        return reporte