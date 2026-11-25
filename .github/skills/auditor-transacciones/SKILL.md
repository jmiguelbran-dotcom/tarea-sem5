---
name: auditor-transacciones
description: Audita transacciones financieras inválidas o rechazadas, clasifica su severidad (CRÍTICA, ALTA, MEDIA), diagnostica la causa raíz según las reglas de negocio y genera informes estructurados con propuestas de remediación.
---

# Skill: Auditoría Forense y Remediación de Transacciones

## Propósito
Capacitar al agente de IA para analizar la bandeja de `transacciones_invalidas` generada por el motor de validación, evitando respuestas genéricas y garantizando trazabilidad financiera.

## Reglas de Comportamiento Obligatorias
1. **Nunca descartar registros sin diagnóstico:** Cada transacción marcada con `es_valida = False` debe ser evaluada individualmente.
2. **Clasificación de Severidad Determinista:**
   - **CRÍTICA:** Montos negativos o iguales a cero (`<= 0.00`), o fuente completamente desconocida. Requiere bloqueo inmediato.
   - **ALTA:** Ausencia de identificador único (`ID_FALTANTE`) o moneda no reconocida/no soportada (ej. tokens no autorizados).
   - **MEDIA:** Fechas calendario inexistentes (ej. `2026-02-30`) o estados sin mapeo semántico en `config/reglas_negocio.json`.
3. **Respeto a la Precisión Decimal:** Cualquier monto citado en el informe debe conservar estrictamente dos decimales (`0.00`).
4. **Formato de Salida Estandarizado:** Todo reporte generado bajo esta skill debe seguir la estructura definida en `resources/plantilla_auditoria.md`.