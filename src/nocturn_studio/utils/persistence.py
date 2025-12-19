import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..model.mapping import Mapping, MappingTarget, TargetType, MappingMode

class PersistenceManager:
    def __init__(self, app_name: str = "NocturnStudio"):
        self.app_dir = Path.home() / "Library" / "Application Support" / app_name
        self.presets_dir = self.app_dir / "presets"
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def save_preset(self, name: str, mappings: Dict[str, Mapping]):
        path = self.presets_dir / f"{name}.json"
        
        # Convert objects to dict
        data = {}
        for control_id, m in mappings.items():
            data[control_id] = {
                "target": {
                    "type": m.target.type.name,
                    "channel": m.target.channel,
                    "identifier": m.target.identifier
                },
                "mode": m.mode.name,
                "min_val": m.min_val,
                "max_val": m.max_val
            }
            
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"[Persistence] Preset saved: {path}")

    def load_preset(self, name: str) -> Optional[Dict[str, Mapping]]:
        path = self.presets_dir / f"{name}.json"
        if not path.exists():
            return None
            
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            mappings = {}
            for control_id, m_data in data.items():
                target_data = m_data["target"]
                target = MappingTarget(
                    type=TargetType[target_data["type"]],
                    channel=target_data["channel"],
                    identifier=target_data["identifier"]
                )
                mapping = Mapping(
                    source_id=control_id,
                    target=target,
                    mode=MappingMode[m_data["mode"]],
                    min_val=m_data["min_val"],
                    max_val=m_data["max_val"]
                )
                mappings[control_id] = mapping
            return mappings
        except Exception as e:
            print(f"[Persistence] Error loading preset {name}: {e}")
            return None
