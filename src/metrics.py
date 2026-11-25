import json
import os
from decimal import Decimal
from typing import List, Dict, Any
from src.models import TransaccionNormalizada


class GeneradorMetricas:
    """Agrega estadísticas operativas y financieras separando divisas FIAT y Crypto."""

    @staticmethod
    def _cargar_clasificacion_divisas() -> Dict[str, List[str]]:
        ruta = ".github/skills/normalizador-financiero/resources/esquema_canonico.json"
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("clasificacion_divisas", {})
        return {"FIAT": ["USD", "EUR", "GBP", "JPY", "MXN", "SVC"], "CRYPTO": ["BTC", "ETH", "SOL", "USDC"]}

    @classmethod
    def calcular(cls, transacciones: List[TransaccionNormalizada]) -> Dict[str, Any]:
        validas = [t for t in transacciones if t.es_valida]
        invalidas = [t for t in transacciones if not t.es_valida]
        clasificacion = cls._cargar_clasificacion_divisas()

        conteo_estados: Dict[str, int] = {"COMPLETADO": 0, "PENDIENTE": 0, "FALLIDO": 0}
        totales_fiat: Dict[str, Decimal] = {}
        totales_crypto: Dict[str, Decimal] = {}
        conteo_fuentes: Dict[str, int] = {}

        for tx in validas:
            conteo_estados[tx.estado] = conteo_estados.get(tx.estado, 0) + 1
            conteo_fuentes[tx.fuente] = conteo_fuentes.get(tx.fuente, 0) + 1
            if tx.moneda in clasificacion.get("CRYPTO", []):
                totales_crypto[tx.moneda] = totales_crypto.get(tx.moneda, Decimal("0.00")) + tx.monto_valor
            else:
                totales_fiat[tx.moneda] = totales_fiat.get(tx.moneda, Decimal("0.00")) + tx.monto_valor

        return {
            "total_procesadas": len(transacciones),
            "total_validas": len(validas),
            "total_invalidas": len(invalidas),
            "conteo_estados": conteo_estados,
            "conteo_fuentes": conteo_fuentes,
            "totales_fiat": {k: f"{v:.2f}" for k, v in totales_fiat.items()},
            "totales_crypto": {k: f"{v:.2f}" for k, v in totales_crypto.items()},
        }