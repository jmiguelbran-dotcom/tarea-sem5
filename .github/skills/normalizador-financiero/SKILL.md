---
name: normalizador-financiero
description: Verifica que las transacciones normalizadas cumplan estrictamente el esquema canónico financiero (precisión Decimal 0.00, fechas ISO YYYY-MM-DD, separación entre divisas FIAT y Criptomonedas) y audita la conciliación de totales.
---

# Skill: Control de Esquema Canónico y Conciliación Financiera

## Propósito
Asegurar que la transformación de datos heterogéneos (Stripe, PayPal, Transferencia Local, Tarjeta y Efectivo) respete invariantes contables y valide el cumplimiento contra `resources/esquema_canonico.json`.

## Reglas de Comportamiento Obligatorias
1. **Separación FIAT vs. Crypto:** Al presentar conciliaciones o métricas, el agente debe distinguir explícitamente entre divisas fiduciarias (`USD`, `EUR`, `GBP`, `JPY`, `MXN`, `SVC`) y criptoactivos (`BTC`, `ETH`, `SOL`, `USDC`), jamás sumando monedas distintas entre sí.
2. **Validación de Contrato:** Toda transacción válida debe cumplir al 100 % las restricciones de `resources/esquema_canonico.json`.
3. **Detección de Anomalías de Precisión:** Alertar si se detectan desviaciones de redondeo o transacciones en estado `PENDIENTE` que representen más del 30 % del volumen válido.