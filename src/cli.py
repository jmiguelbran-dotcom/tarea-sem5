import json
from typing import List
from src.models import TransaccionNormalizada
from src.normalizer import NormalizadorMultifuente
from src.validator import ValidadorTransacciones
from src.metrics import GeneradorMetricas
from src.agent_engine import AgentePersonalizadoEngine


class InterfazCLI:
    """Capa de presentación interactiva en consola."""

    def __init__(self):
        self.normalizador = NormalizadorMultifuente("config/reglas_negocio.json")
        self.agente = AgentePersonalizadoEngine("auditor_forense")
        self.transacciones: List[TransaccionNormalizada] = []
        self.archivo_actual = ""

    def cargar_archivo(self, ruta: str) -> bool:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, list):
                print("\n[ERROR] El archivo JSON debe contener una lista de transacciones.")
                return False
            self.transacciones = [
                ValidadorTransacciones.procesar_y_validar(item, self.normalizador)
                for item in datos
            ]
            self.archivo_actual = ruta
            print(f"\n[OK] {len(self.transacciones)} registros cargados desde '{ruta}'.")
            return True
        except FileNotFoundError:
            print(f"\n[ERROR] Archivo no encontrado: '{ruta}'.")
        except json.JSONDecodeError:
            print(f"\n[ERROR] Formato JSON inválido en '{ruta}'.")
        return False

    def imprimir_tabla(self, lista: List[TransaccionNormalizada], titulo: str) -> None:
        print("\n" + "=" * 95)
        print(f" {titulo} ({len(lista)} registros)")
        print("=" * 95)
        if not lista:
            print(" No hay registros que coincidan con el criterio.")
            print("=" * 95)
            return
        print(f"{'ID TX':<15} | {'FUENTE':<20} | {'MONTO':>10} | {'MONEDA':<8} | {'ESTADO':<12} | {'FECHA':<10} | {'VÁLIDA'}")
        print("-" * 95)
        for t in lista:
            val_str = "SÍ" if t.es_valida else "NO"
            print(f"{t.id_transaccion:<15} | {t.fuente:<20} | {t.monto:>10} | {t.moneda:<8} | {t.estado:<12} | {t.fecha:<10} | {val_str}")
        print("=" * 95)

    def mostrar_metricas(self) -> None:
        m = GeneradorMetricas.calcular(self.transacciones)
        print("\n" + "=" * 62)
        print("       CONSOLIDADO DE MÉTRICAS FINANCIERAS (FIAT / CRYPTO)")
        print("=" * 62)
        print(f" Archivo analizado         : {self.archivo_actual}")
        print(f" Total procesadas          : {m['total_procesadas']}")
        print(f"  ├── Transacciones Válidas   : {m['total_validas']}")
        print(f"  └── Transacciones Inválidas : {m['total_invalidas']}")
        print("-" * 62)
        print(" CONTEO POR ESTADO:")
        for est, cant in m["conteo_estados"].items():
            print(f"  - {est:<12} : {cant}")
        print("-" * 62)
        print(" TOTALES DIVISAS FIAT:")
        for mon, total in m["totales_fiat"].items():
            print(f"  - {mon:<6} : {total}")
        print("-" * 62)
        print(" TOTALES CRIPTOMONEDAS:")
        for mon, total in m["totales_crypto"].items():
            print(f"  - {mon:<6} : {total}")
        print("=" * 62)

    def seleccionar_agente(self) -> None:
        print("\n--- SELECCIÓN DE AGENTE PERSONALIZADO ---")
        claves = list(self.agente.perfiles.keys())
        for idx, k in enumerate(claves, start=1):
            p = self.agente.perfiles[k]
            marca = " [ACTIVO]" if k == self.agente.perfil_key else ""
            print(f"{idx}. {p['nombre']} -> Skill: {p['skill_principal']}{marca}")
        eleccion = input(f"Seleccione perfil (1-{len(claves)}): ").strip()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(claves):
            self.agente.cambiar_perfil(claves[int(eleccion) - 1])
            print(f"\n[OK] Perfil cambiado a: {self.agente.perfil['nombre']}")
        else:
            print("[AVISO] Selección no válida.")

    def menu_filtros(self) -> None:
        validas = [t for t in self.transacciones if t.es_valida]
        print("\n--- FILTRAR TRANSACCIONES VÁLIDAS ---")
        print("1. Por Estado (COMPLETADO / PENDIENTE / FALLIDO)")
        print("2. Por Moneda (USD, EUR, BTC, ETH, SOL, MXN, SVC)")
        print("3. Por Fuente (STRIPE, PAYPAL, TRANSFERENCIA_LOCAL, PAGO_TARJETA, RECIBO_EFECTIVO)")
        sub = input("Opción (1-3): ").strip()
        if sub == "1":
            val = input("Estado: ").strip().upper()
            self.imprimir_tabla([t for t in validas if t.estado == val], f"ESTADO: {val}")
        elif sub == "2":
            val = input("Moneda: ").strip().upper()
            self.imprimir_tabla([t for t in validas if t.moneda == val], f"MONEDA: {val}")
        elif sub == "3":
            val = input("Fuente: ").strip().upper()
            self.imprimir_tabla([t for t in validas if t.fuente == val], f"FUENTE: {val}")

    def ejecutar(self) -> None:
        print("=" * 75)
        print(" SISTEMA AGÉNTICO DE NORMALIZACIÓN Y AUDITORÍA DE TRANSACCIONES")
        print(" KODIGO - Refactorización y Personalización mediante Agent Skills")
        print("=" * 75)

        ruta = input("Ruta del archivo JSON [Enter para 'data/transacciones_entrada.json']: ").strip()
        if not ruta:
            ruta = "data/transacciones_entrada.json"
        if not self.cargar_archivo(ruta):
            return

        while True:
            print(f"\n[Agente Activo: {self.agente.perfil['nombre']} | Skill: {self.agente.skill['name']}]")
            print("1. Ver transacciones VÁLIDAS normalizadas")
            print("2. Filtrar transacciones (Estado, Moneda o Fuente)")
            print("3. Ver resumen de métricas financieras (FIAT vs. Crypto)")
            print("4. Ejecutar Auditoría / Conciliación con el Agente Personalizado")
            print("5. Cambiar perfil de Agente Personalizado (y su Skill asociada)")
            print("6. Cargar otro archivo JSON de entrada")
            print("7. Salir")
            op = input("Seleccione una opción (1-7): ").strip()

            if op == "1":
                self.imprimir_tabla([t for t in self.transacciones if t.es_valida], "TRANSACCIONES VÁLIDAS")
            elif op == "2":
                self.menu_filtros()
            elif op == "3":
                self.mostrar_metricas()
            elif op == "4":
                print("\n" + self.agente.ejecutar_auditoria(self.transacciones, self.archivo_actual))
            elif op == "5":
                self.seleccionar_agente()
            elif op == "6":
                nueva = input("Ruta del nuevo archivo JSON: ").strip()
                self.cargar_archivo(nueva)
            elif op == "7":
                print("\n[INFO] Sesión finalizada.")
                break
            else:
                print("\n[AVISO] Opción inválida.")