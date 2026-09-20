"""
Scenario and Persona manager for loading, querying, and filtering practice scenarios and AI personas.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple

from src.scenarios.scenario_models import (
    Scenario,
    Persona,
    PRACTICE_MODES,
    DIFFICULTY_LEVELS,
)

logger = logging.getLogger(__name__)


class ScenarioManager:
    """
    Manages loading and querying of practice scenarios and AI personas.
    
    Attributes:
        data_path: Path to the JSON file or directory containing scenario definitions.
        personas_path: Path to the JSON file or directory containing persona definitions.
        _scenarios: Internal cached list of loaded Scenario objects.
        _personas: Internal cached dictionary of loaded Persona objects keyed by ID.
    """

    DEFAULT_DATA_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "data"
        / "scenarios"
        / "scenarios.json"
    )

    DEFAULT_PERSONAS_PATH = (
        Path(__file__).resolve().parent.parent.parent
        / "data"
        / "personas"
        / "personas.json"
    )

    def __init__(
        self,
        data_path: Optional[Union[str, Path]] = None,
        personas_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Initialize ScenarioManager with optional custom data and persona paths.
        
        Args:
            data_path: Optional path to scenario data file or directory.
            personas_path: Optional path to persona data file or directory.
        """
        self.data_path = Path(data_path) if data_path else self.DEFAULT_DATA_PATH
        self.personas_path = (
            Path(personas_path) if personas_path else self.DEFAULT_PERSONAS_PATH
        )
        self._scenarios: List[Scenario] = []
        self._personas: Dict[str, Persona] = {}
        self.reload()

    def reload(self) -> None:
        """Load or reload scenarios and personas from configured data paths."""
        self._personas = self._load_personas()
        self._scenarios = self._load_scenarios()

    # --------------------------------------------------------------------------
    # Persona Loading & Queries
    # --------------------------------------------------------------------------

    def _load_personas(self) -> Dict[str, Persona]:
        """
        Internal loader that parses JSON persona data safely.
        
        Returns:
            Dictionary mapping persona ID to Persona objects.
        """
        if not self.personas_path.exists():
            logger.warning("Persona data path does not exist: %s", self.personas_path)
            return {}

        personas: Dict[str, Persona] = {}
        try:
            if self.personas_path.is_dir():
                for json_file in sorted(self.personas_path.glob("*.json")):
                    personas.update(self._load_personas_from_file(json_file))
            else:
                personas = self._load_personas_from_file(self.personas_path)
        except Exception as e:
            logger.error("Failed to load personas from %s: %s", self.personas_path, e)
        return personas

    def _load_personas_from_file(self, file_path: Path) -> Dict[str, Persona]:
        """Load persona objects from a single JSON file."""
        loaded: Dict[str, Persona] = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(
                    "Expected a JSON list of personas in %s, got %s", file_path, type(data)
                )
                return {}

            for item in data:
                if isinstance(item, dict):
                    try:
                        persona = Persona.from_dict(item)
                        loaded[persona.id] = persona
                    except Exception as err:
                        logger.warning("Skipping invalid persona item: %s (%s)", item, err)
        except json.JSONDecodeError as err:
            logger.error("Invalid JSON format in personas file %s: %s", file_path, err)
        except Exception as err:
            logger.error("Unexpected error reading personas file %s: %s", file_path, err)
        return loaded

    def get_all_personas(self) -> List[Persona]:
        """
        Retrieve all loaded personas.
        
        Returns:
            List of all Persona instances.
        """
        return list(self._personas.values())

    def get_persona_by_id(self, persona_id: str) -> Optional[Persona]:
        """
        Retrieve a specific persona by its unique identifier.
        
        Args:
            persona_id: Unique persona ID string (e.g., 'persona_hr_friendly').
            
        Returns:
            The matching Persona instance, or None if not found.
        """
        if not persona_id or not isinstance(persona_id, str):
            return None
        return self._personas.get(persona_id.strip())

    def get_personas_by_mode(self, mode: str) -> List[Persona]:
        """
        Retrieve personas suitable for a given practice mode.
        
        Args:
            mode: The practice mode name (e.g., 'HR Interview').
            
        Returns:
            List of matching Persona instances.
        """
        if not mode or not isinstance(mode, str):
            return []
        normalized_mode = mode.strip().lower()
        return [
            p
            for p in self._personas.values()
            if any(m.strip().lower() == normalized_mode for m in p.supported_modes)
        ]

    # --------------------------------------------------------------------------
    # Scenario Loading & Queries
    # --------------------------------------------------------------------------

    def _load_scenarios(self) -> List[Scenario]:
        """
        Internal loader that parses JSON scenario data safely.
        
        Returns:
            List of validated Scenario objects.
        """
        if not self.data_path.exists():
            logger.warning("Scenario data path does not exist: %s", self.data_path)
            return []

        try:
            if self.data_path.is_dir():
                scenarios: List[Scenario] = []
                for json_file in sorted(self.data_path.glob("*.json")):
                    scenarios.extend(self._load_scenarios_from_file(json_file))
                return scenarios
            else:
                return self._load_scenarios_from_file(self.data_path)
        except Exception as e:
            logger.error("Failed to load scenarios from %s: %s", self.data_path, e)
            return []

    def _load_scenarios_from_file(self, file_path: Path) -> List[Scenario]:
        """Load scenario objects from a single JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(
                    "Expected a JSON list in %s, got %s", file_path, type(data)
                )
                return []

            scenarios: List[Scenario] = []
            for item in data:
                if isinstance(item, dict):
                    try:
                        scenarios.append(Scenario.from_dict(item))
                    except Exception as err:
                        logger.warning("Skipping invalid scenario item: %s (%s)", item, err)
            return scenarios
        except json.JSONDecodeError as err:
            logger.error("Invalid JSON format in %s: %s", file_path, err)
            return []
        except Exception as err:
            logger.error("Unexpected error reading %s: %s", file_path, err)
            return []

    def get_all_scenarios(self) -> List[Scenario]:
        """
        Retrieve all loaded practice scenarios.
        
        Returns:
            List of all Scenario instances.
        """
        return list(self._scenarios)

    def get_scenarios_by_mode(self, mode: str) -> List[Scenario]:
        """
        Retrieve scenarios filtered by practice mode.
        
        Args:
            mode: The practice mode name (e.g., 'HR Interview').
            
        Returns:
            List of matching Scenario instances, or an empty list if none found.
        """
        if not mode or not isinstance(mode, str):
            return []
        normalized_mode = mode.strip().lower()
        return [s for s in self._scenarios if s.mode.strip().lower() == normalized_mode]

    def get_scenarios_by_difficulty(self, difficulty: str) -> List[Scenario]:
        """
        Retrieve scenarios filtered by difficulty level.
        
        Args:
            difficulty: Target difficulty (e.g., 'Beginner').
            
        Returns:
            List of matching Scenario instances.
        """
        if not difficulty or not isinstance(difficulty, str):
            return []
        normalized_diff = difficulty.strip().lower()
        return [
            s
            for s in self._scenarios
            if s.difficulty.strip().lower() == normalized_diff
        ]

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """
        Retrieve a specific scenario by its unique identifier.
        
        Args:
            scenario_id: Unique scenario ID string (e.g. 'hr_intro_01').
            
        Returns:
            The matching Scenario instance, or None if not found.
        """
        if not scenario_id or not isinstance(scenario_id, str):
            return None
        scenario_id_cleaned = scenario_id.strip()
        for scenario in self._scenarios:
            if scenario.id == scenario_id_cleaned:
                return scenario
        return None

    def get_persona_for_scenario(self, scenario_id: str) -> Optional[Persona]:
        """
        Retrieve the Persona associated with a specific scenario.
        
        Args:
            scenario_id: Unique identifier for the scenario.
            
        Returns:
            The associated Persona instance, or None if scenario or persona not found.
        """
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario or not scenario.persona_id:
            return None
        return self.get_persona_by_id(scenario.persona_id)

    def get_scenarios_with_personas(self) -> List[Dict[str, Any]]:
        """
        Retrieve all scenarios paired with their resolved Persona data.
        
        Returns:
            List of dictionaries containing 'scenario' and 'persona' keys.
        """
        results: List[Dict[str, Any]] = []
        for scenario in self._scenarios:
            persona = self.get_persona_by_id(scenario.persona_id) if scenario.persona_id else None
            results.append({
                "scenario": scenario,
                "persona": persona,
            })
        return results

    def get_modes(self) -> List[str]:
        """Get the supported practice modes."""
        return list(PRACTICE_MODES)

    def get_difficulties(self) -> List[str]:
        """Get the supported difficulty levels."""
        return list(DIFFICULTY_LEVELS)
