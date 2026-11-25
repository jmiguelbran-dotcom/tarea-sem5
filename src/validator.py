from decimal import Decimal
from typing import Dict, Any
from src.models import TransaccionNormalizada
from src.normalizer import NormalizadorMultifuente


class ValidadorTransacciones:
    """Evalúa cada registro y separa los inválidos con trazabilidad de errores."""

    @staticmethod
    def procesar_y_validar(
        registro_crudo: Dict[str, Any], normalizador: NormalizadorMultifuente
    ) -> TransaccionNormalizada:
        errores = []
        fuente = normalizador.detectar_fuente(registro_crudo)

        if fuente == "FUENTE_DESCONOCIDA":
            return TransaccionNormalizada(
                id_transaccion="SIN_ID",
                fuente=fuente,
                monto="0.00",
                monto_valor=Decimal("0.00"),
                moneda="N/A",
                estado="N/A",
                fecha="N/A",
                es_valida=False,
                errores_validacion=["Fuente de transacción no reconocida en configuración"],
                registro_original=registro_crudo,
            )

        crudos = normalizador.extraer_campos_crudos(registro_crudo, fuente)

        id_tx = str(crudos.get("id") or "").strip()
        if not id_tx:
            id_tx = "ID_FALTANTE"
            errores.append("ID de transacción vacío o inexistente")

        monto_str, monto_dec = normalizador.normalizar_monto(
            crudos.get("monto"), crudos.get("es_centavos", False)
        )
        if monto_str is None or monto_dec is None:
            monto_str, monto_dec = "0.00", Decimal("0.00")
            errores.append(f"Formato de monto inválido ({crudos.get('monto')})")
        elif monto_dec <= Decimal("0.00"):
            errores.append(f"El monto debe ser mayor a cero ({monto_str})")

        moneda_norm = normalizador.normalizar_moneda(crudos.get("moneda"))
        if not moneda_norm:
            moneda_norm = f"INVALIDA({crudos.get('moneda')})"
            errores.append(f"Moneda no soportada: '{crudos.get('moneda')}'")

        estado_norm = normalizador.normalizar_estado(crudos.get("estado"))
        if not estado_norm:
            estado_norm = f"INVALIDO({crudos.get('estado')})"
            errores.append(f"Estado no mapeable: '{crudos.get('estado')}'")

        fecha_norm = normalizador.normalizar_fecha(crudos.get("fecha"))
        if not fecha_norm:
            fecha_norm = f"INVALIDA({crudos.get('fecha')})"
            errores.append(f"Fecha inexistente o formato inválido: '{crudos.get('fecha')}'")

        return TransaccionNormalizada(
            id_transaccion=id_tx,
            fuente=fuente,
            monto=monto_str,
            monto_valor=monto_dec,
            moneda=moneda_norm,
            estado=estado_norm,
            fecha=fecha_norm,
            es_valida=len(errores) == 0,
            errores_validacion=errores,
            registro_original=registro_crudo,
        )