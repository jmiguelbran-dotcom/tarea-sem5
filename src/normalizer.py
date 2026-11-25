import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple


class NormalizadorMultifuente:
    """Transforma registros heterogéneos al esquema canónico usando configuración externa."""

    def __init__(self, config_path: str = "config/reglas_negocio.json"):
        self.config = self._cargar_config(config_path)

    def _cargar_config(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró la configuración en: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def detectar_fuente(self, registro: Dict[str, Any]) -> str:
        """Identifica la fuente dinámicamente según las reglas en definicion_fuentes."""
        definiciones = self.config.get("definicion_fuentes", {})
        for nombre_fuente, regla in definiciones.items():
            llave_id = regla.get("llave_identificadora", "")
            clave_sis, valor_sis = regla.get("valor_sistema", ["", ""])
            if registro.get(clave_sis) == valor_sis or llave_id in registro:
                return nombre_fuente
        return "FUENTE_DESCONOCIDA"

    def extraer_campos_crudos(self, registro: Dict[str, Any], fuente: str) -> Dict[str, Any]:
        """Extrae valores crudos consultando el diccionario de campos de la fuente."""
        regla = self.config.get("definicion_fuentes", {}).get(fuente)
        if not regla:
            return {}
        campos = regla["campos"]
        return {
            "id": registro.get(campos["id"]),
            "monto": registro.get(campos["monto"]),
            "es_centavos": campos.get("es_centavos", False),
            "moneda": registro.get(campos["moneda"]),
            "estado": registro.get(campos["estado"]),
            "fecha": registro.get(campos["fecha"]),
        }

    def normalizar_monto(self, valor_crudo: Any, es_centavos: bool = False) -> Tuple[Optional[str], Optional[Decimal]]:
        if valor_crudo is None or str(valor_crudo).strip() == "":
            return None, None
        try:
            limpio = re.sub(r"[^\d.-]", "", str(valor_crudo))
            decimal_val = Decimal(limpio)
            if es_centavos:
                decimal_val = decimal_val / Decimal("100")
            redondeado = decimal_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return f"{redondeado:.2f}", redondeado
        except (InvalidOperation, ValueError):
            return None, None

    def normalizar_moneda(self, moneda_cruda: Any) -> Optional[str]:
        if not moneda_cruda:
            return None
        limpia = str(moneda_cruda).strip().lower()
        for codigo, alias_lista in self.config.get("monedas_soportadas", {}).items():
            if limpia == codigo.lower() or limpia in [a.lower() for a in alias_lista]:
                return codigo
        return None

    def normalizar_estado(self, estado_crudo: Any) -> Optional[str]:
        if not estado_crudo:
            return None
        limpio = str(estado_crudo).strip().lower()
        for estado_estandar, sinonimos in self.config.get("mapeo_estados", {}).items():
            if limpio == estado_estandar.lower() or limpio in [s.lower() for s in sinonimos]:
                return estado_estandar
        return None

    def normalizar_fecha(self, fecha_cruda: Any) -> Optional[str]:
        if not fecha_cruda:
            return None
        texto = str(fecha_cruda).strip()
        for fmt in self.config.get("formatos_fecha", []):
            try:
                return datetime.strptime(texto, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None