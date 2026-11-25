import json
import os
from typing import Dict, Any


class SkillLoader:
    """Lee y parsea las Agent Skills (.github/skills/) y los perfiles personalizados."""

    def __init__(
        self,
        skills_dir: str = ".github/skills",
        perfiles_path: str = "config/agentes_perfiles.json",
    ):
        self.skills_dir = skills_dir
        self.perfiles_path = perfiles_path

    def cargar_perfiles(self) -> Dict[str, Any]:
        if not os.path.exists(self.perfiles_path):
            raise FileNotFoundError(f"No se encontró {self.perfiles_path}")
        with open(self.perfiles_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def cargar_skill(self, skill_name: str) -> Dict[str, str]:
        """Carga el contenido de SKILL.md y cualquier recurso asociado en resources/."""
        ruta_skill = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if not os.path.exists(ruta_skill):
            raise FileNotFoundError(f"Skill no encontrada: {ruta_skill}")

        with open(ruta_skill, "r", encoding="utf-8") as f:
            contenido_md = f.read()

        recursos: Dict[str, str] = {}
        ruta_recursos = os.path.join(self.skills_dir, skill_name, "resources")
        if os.path.isdir(ruta_recursos):
            for archivo in os.listdir(ruta_recursos):
                ruta_archivo = os.path.join(ruta_recursos, archivo)
                if os.path.isfile(ruta_archivo):
                    with open(ruta_archivo, "r", encoding="utf-8") as rf:
                        recursos[archivo] = rf.read()

        return {
            "name": skill_name,
            "instructions": contenido_md,
            "resources": recursos,
        }