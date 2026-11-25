from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict, Any


@dataclass
class TransaccionNormalizada:
    """Esquema canónico unificado para todas las fuentes de pago."""
    id_transaccion: str
    fuente: str
    monto: str
    monto_valor: Decimal
    moneda: str
    estado: str
    fecha: str
    es_valida: bool
    errores_validacion: List[str] = field(default_factory=list)
    registro_original: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HallazgoAuditoria:
    """Resultado estructurado producido por el agente tras evaluar un registro inválido."""
    id_transaccion: str
    fuente: str
    severidad: str
    causas_raiz: List[str]
    recomendacion: str
    json_sugerido: Optional[Dict[str, Any]] = None