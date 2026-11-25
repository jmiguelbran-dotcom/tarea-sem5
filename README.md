# Sistema Agéntico de Normalización y Auditoría de Transacciones Multifuente

**Programa:** AI for Devs Jr. — KODIGO  
**Actividad:** Refactorización y Personalización de un Sistema Agéntico mediante Skills Propias  

---

## 1. Diagnóstico del Proyecto Original (Antes de la Refactorización)
La versión inicial del sistema (`sistema_transacciones.py`) resolvía la normalización de 5 fuentes de pago (*Stripe, PayPal, Transferencia Local, Pago con Tarjeta y Recibo en Efectivo*), pero presentaba **4 problemas críticos de acoplamiento**:

1. **Arquitectura Monolítica:** El modelo de datos, la lógica de extracción, las reglas de validación, el cálculo de métricas y la interfaz de consola convivían en un único archivo de más de 250 líneas.
2. **Mapeos Rígidos (*Hardcoded*):** La identificación de cada pasarela y la extracción de sus llaves nativas estaban cableadas dentro de métodos Python en lugar de residir en configuración externa.
3. **Ausencia de Capa Agéntica:** Ante registros inválidos (montos negativos, fechas inexistentes como `2026-02-30` o divisas no soportadas), el sistema se limitaba a imprimir una lista estática sin diagnóstico de severidad ni propuestas de remediación.
4. **Falta de Personalización:** No existían mecanismos para adaptar el comportamiento, tono o rigor del análisis según el rol operativo del usuario.

---

## 2. Arquitectura Refactorizada (Después)
Se separaron **lógica de negocio**, **configuración**, **perfiles de agente** y **capacidades agénticas (Skills)**:

```text
transacciones-agentic-system/
├── .github/
│   ├── agents/
│   │   └── auditor-financiero.agent.md       # Plantilla de agente para VS Code / Copilot
│   └── skills/
│       ├── auditor-transacciones/            # Skill 1: Diagnóstico forense y remediación
│       │   ├── SKILL.md
│       │   └── resources/plantilla_auditoria.md
│       └── normalizador-financiero/          # Skill 2: Esquema canónico y conciliación FIAT/Crypto
│           ├── SKILL.md
│           └── resources/esquema_canonico.json
├── config/
│   ├── reglas_negocio.json                   # Monedas, estados, fechas y mapeo de las 5 fuentes
│   └── agentes_perfiles.json                 # 3 personalidades/perfiles configurables
├── src/
│   ├── models.py                             # Dataclasses TransaccionNormalizada y HallazgoAuditoria
│   ├── normalizer.py                         # Motor puro dirigido por configuración
│   ├── validator.py                          # Validación estricta con conservación de payload original
│   ├── metrics.py                            # Agregación financiera Decimal (FIAT vs. Crypto)
│   ├── skill_loader.py                       # Lector dinámico de SKILL.md y resources/
│   ├── agent_engine.py                       # Orquestador agéntico híbrido (Offline + API LLM opcional)
│   └── cli.py                                # Interfaz interactiva desacoplada
├── data/
│   ├── transacciones_entrada.json            # Dataset principal (15 registros, 5 fuentes)
│   └── transacciones_caso_borde.json         # Dataset de anomalías y umbrales de liquidez
└── main.py                                   # Punto de entrada