"""
Consolidation tracking system to monitor progress and enable rollbacks.

This module provides functionality to track the progress of consolidation
operations, monitor success/failure rates, and enable rollback capabilities.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ConsolidationStatus(Enum):
    """Status of a consolidation operation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ConsolidationType(Enum):
    """Type of consolidation operation."""
    FILE_MERGE = "file_merge"
    MODULE_CONSOLIDATION = "module_consolidation"
    SERVICE_CONSOLIDATION = "service_consolidation"
    CONFIG_CONSOLIDATION = "config_consolidation"
    TEST_CONSOLIDATION = "test_consolidation"


@dataclass
class ConsolidationStep:
    """Individual step in a consolidation operation."""
    step_id: str
    name: str
    description: str
    status: ConsolidationStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    files_affected: List[str] = None
    backup_ids: List[str] = None
    
    def __post_init__(self):
        if self.files_affected is None:
            self.files_affected = []
        if self.backup_ids is None:
            self.backup_ids = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConsolidationStep':
        """Create from dictionary."""
        if 'start_time' in data and data['start_time']:
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and data['end_time']:
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['status'] = ConsolidationStatus(data['status'])
        return cls(**data)


@dataclass
class ConsolidationPhase:
    """A phase in the consolidation process."""
    phase_id: str
    name: str
    description: str
    week: int
    consolidation_type: ConsolidationType
    status: ConsolidationStatus
    steps: List[ConsolidationStep]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    files_before: int = 0
    files_after: int = 0
    reduction_percentage: float = 0.0
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['status'] = self.status.value
        data['consolidation_type'] = self.consolidation_type.value
        data['steps'] = [step.to_dict() for step in self.steps]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConsolidationPhase':
        """Create from dictionary."""
        if 'start_time' in data and data['start_time']:
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and data['end_time']:
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['status'] = ConsolidationStatus(data['status'])
        data['consolidation_type'] = ConsolidationType(data['consolidation_type'])
        data['steps'] = [ConsolidationStep.from_dict(step_data) for step_data in data.get('steps', [])]
        return cls(**data)


class ConsolidationTracker:
    """System for tracking consolidation progress and enabling rollbacks."""
    
    def __init__(self, tracking_file: str = "data/consolidation_backups/consolidation_tracking.json"):
        """
        Initialize consolidation tracker.
        
        Args:
            tracking_file: Path to tracking data file
        """
        self.tracking_file = Path(tracking_file)
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Consolidation phases
        self.phases: Dict[str, ConsolidationPhase] = {}
        
        # Overall progress tracking
        self.project_start_time: Optional[datetime] = None
        self.project_end_time: Optional[datetime] = None
        self.total_files_before: int = 0
        self.total_files_after: int = 0
        
        # Load existing tracking data
        self._load_tracking_data()
    
    def _load_tracking_data(self) -> None:
        """Load tracking data from file."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load phases
                    self.phases = {
                        phase_id: ConsolidationPhase.from_dict(phase_data)
                        for phase_id, phase_data in data.get('phases', {}).items()
                    }
                    
                    # Load project-level data
                    if 'project_start_time' in data and data['project_start_time']:
                        self.project_start_time = datetime.fromisoformat(data['project_start_time'])
                    if 'project_end_time' in data and data['project_end_time']:
                        self.project_end_time = datetime.fromisoformat(data['project_end_time'])
                    
                    self.total_files_before = data.get('total_files_before', 0)
                    self.total_files_after = data.get('total_files_after', 0)
                
                logger.info(f"Loaded tracking data for {len(self.phases)} phases")
            except Exception as e:
                logger.error(f"Failed to load tracking data: {e}")
                self.phases = {}
    
    def _save_tracking_data(self) -> None:
        """Save tracking data to file."""
        try:
            data = {
                'phases': {
                    phase_id: phase.to_dict()
                    for phase_id, phase in self.phases.items()
                },
                'project_start_time': self.project_start_time.isoformat() if self.project_start_time else None,
                'project_end_time': self.project_end_time.isoformat() if self.project_end_time else None,
                'total_files_before': self.total_files_before,
                'total_files_after': self.total_files_after
            }
            
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved tracking data")
        except Exception as e:
            logger.error(f"Failed to save tracking data: {e}")
    
    def initialize_project(self, total_files_before: int) -> None:
        """
        Initialize project-level tracking.
        
        Args:
            total_files_before: Total number of files before consolidation
        """
        self.project_start_time = datetime.now()
        self.total_files_before = total_files_before
        self._save_tracking_data()
        
        logger.info(f"Initialized consolidation project with {total_files_before} files")
    
    def create_phase(
        self,
        name: str,
        description: str,
        week: int,
        consolidation_type: ConsolidationType
    ) -> str:
        """
        Create a new consolidation phase.
        
        Args:
            name: Phase name
            description: Phase description
            week: Week number in the consolidation plan
            consolidation_type: Type of consolidation
            
        Returns:
            Phase ID
        """
        phase_id = str(uuid.uuid4())
        
        phase = ConsolidationPhase(
            phase_id=phase_id,
            name=name,
            description=description,
            week=week,
            consolidation_type=consolidation_type,
            status=ConsolidationStatus.NOT_STARTED,
            steps=[]
        )
        
        self.phases[phase_id] = phase
        self._save_tracking_data()
        
        logger.info(f"Created consolidation phase: {name} (ID: {phase_id})")
        return phase_id
    
    def add_step_to_phase(
        self,
        phase_id: str,
        name: str,
        description: str,
        files_affected: Optional[List[str]] = None
    ) -> str:
        """
        Add a step to a consolidation phase.
        
        Args:
            phase_id: ID of the phase
            name: Step name
            description: Step description
            files_affected: List of files affected by this step
            
        Returns:
            Step ID
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase not found: {phase_id}")
        
        step_id = str(uuid.uuid4())
        
        step = ConsolidationStep(
            step_id=step_id,
            name=name,
            description=description,
            status=ConsolidationStatus.NOT_STARTED,
            files_affected=files_affected or []
        )
        
        self.phases[phase_id].steps.append(step)
        self._save_tracking_data()
        
        logger.info(f"Added step to phase {phase_id}: {name} (ID: {step_id})")
        return step_id
    
    def start_phase(self, phase_id: str) -> None:
        """
        Start a consolidation phase.
        
        Args:
            phase_id: ID of the phase to start
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase not found: {phase_id}")
        
        phase = self.phases[phase_id]
        phase.status = ConsolidationStatus.IN_PROGRESS
        phase.start_time = datetime.now()
        
        self._save_tracking_data()
        logger.info(f"Started phase: {phase.name}")
    
    def complete_phase(
        self,
        phase_id: str,
        files_before: int,
        files_after: int
    ) -> None:
        """
        Complete a consolidation phase.
        
        Args:
            phase_id: ID of the phase to complete
            files_before: Number of files before consolidation
            files_after: Number of files after consolidation
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase not found: {phase_id}")
        
        phase = self.phases[phase_id]
        phase.status = ConsolidationStatus.COMPLETED
        phase.end_time = datetime.now()
        phase.files_before = files_before
        phase.files_after = files_after
        
        if files_before > 0:
            phase.reduction_percentage = ((files_before - files_after) / files_before) * 100
        
        self._save_tracking_data()
        logger.info(f"Completed phase: {phase.name} ({files_before} -> {files_after} files, {phase.reduction_percentage:.1f}% reduction)")
    
    def fail_phase(self, phase_id: str, error_message: str) -> None:
        """
        Mark a phase as failed.
        
        Args:
            phase_id: ID of the phase that failed
            error_message: Error message describing the failure
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase not found: {phase_id}")
        
        phase = self.phases[phase_id]
        phase.status = ConsolidationStatus.FAILED
        phase.end_time = datetime.now()
        
        # Mark current step as failed if any
        for step in phase.steps:
            if step.status == ConsolidationStatus.IN_PROGRESS:
                step.status = ConsolidationStatus.FAILED
                step.error_message = error_message
                step.end_time = datetime.now()
        
        self._save_tracking_data()
        logger.error(f"Phase failed: {phase.name} - {error_message}")
    
    def start_step(self, phase_id: str, step_id: str) -> None:
        """
        Start a consolidation step.
        
        Args:
            phase_id: ID of the phase
            step_id: ID of the step to start
        """
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase not found: {phase_id}")
        
        step = next((s for s in phase.steps if s.step_id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")
        
        step.status = ConsolidationStatus.IN_PROGRESS
        step.start_time = datetime.now()
        
        self._save_tracking_data()
        logger.info(f"Started step: {step.name}")
    
    def complete_step(
        self,
        phase_id: str,
        step_id: str,
        backup_ids: Optional[List[str]] = None
    ) -> None:
        """
        Complete a consolidation step.
        
        Args:
            phase_id: ID of the phase
            step_id: ID of the step to complete
            backup_ids: List of backup IDs created during this step
        """
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase not found: {phase_id}")
        
        step = next((s for s in phase.steps if s.step_id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")
        
        step.status = ConsolidationStatus.COMPLETED
        step.end_time = datetime.now()
        if backup_ids:
            step.backup_ids.extend(backup_ids)
        
        self._save_tracking_data()
        logger.info(f"Completed step: {step.name}")
    
    def fail_step(
        self,
        phase_id: str,
        step_id: str,
        error_message: str
    ) -> None:
        """
        Mark a step as failed.
        
        Args:
            phase_id: ID of the phase
            step_id: ID of the step that failed
            error_message: Error message describing the failure
        """
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase not found: {phase_id}")
        
        step = next((s for s in phase.steps if s.step_id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")
        
        step.status = ConsolidationStatus.FAILED
        step.end_time = datetime.now()
        step.error_message = error_message
        
        self._save_tracking_data()
        logger.error(f"Step failed: {step.name} - {error_message}")
    
    def rollback_phase(self, phase_id: str) -> List[str]:
        """
        Rollback a consolidation phase.
        
        Args:
            phase_id: ID of the phase to rollback
            
        Returns:
            List of backup IDs that need to be restored
        """
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase not found: {phase_id}")
        
        # Collect all backup IDs from completed steps
        backup_ids = []
        for step in phase.steps:
            if step.status == ConsolidationStatus.COMPLETED:
                backup_ids.extend(step.backup_ids)
                step.status = ConsolidationStatus.ROLLED_BACK
        
        phase.status = ConsolidationStatus.ROLLED_BACK
        phase.end_time = datetime.now()
        
        self._save_tracking_data()
        logger.info(f"Rolled back phase: {phase.name} ({len(backup_ids)} backups to restore)")
        
        return backup_ids
    
    def get_phase_progress(self, phase_id: str) -> Dict:
        """
        Get progress information for a phase.
        
        Args:
            phase_id: ID of the phase
            
        Returns:
            Progress information dictionary
        """
        phase = self.phases.get(phase_id)
        if not phase:
            raise ValueError(f"Phase not found: {phase_id}")
        
        total_steps = len(phase.steps)
        completed_steps = sum(1 for step in phase.steps if step.status == ConsolidationStatus.COMPLETED)
        failed_steps = sum(1 for step in phase.steps if step.status == ConsolidationStatus.FAILED)
        in_progress_steps = sum(1 for step in phase.steps if step.status == ConsolidationStatus.IN_PROGRESS)
        
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        duration = None
        if phase.start_time:
            end_time = phase.end_time or datetime.now()
            duration = (end_time - phase.start_time).total_seconds()
        
        return {
            "phase_id": phase_id,
            "name": phase.name,
            "status": phase.status.value,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "in_progress_steps": in_progress_steps,
            "progress_percentage": progress_percentage,
            "duration_seconds": duration,
            "files_before": phase.files_before,
            "files_after": phase.files_after,
            "reduction_percentage": phase.reduction_percentage
        }
    
    def get_overall_progress(self) -> Dict:
        """
        Get overall consolidation progress.
        
        Returns:
            Overall progress information dictionary
        """
        total_phases = len(self.phases)
        completed_phases = sum(1 for phase in self.phases.values() if phase.status == ConsolidationStatus.COMPLETED)
        failed_phases = sum(1 for phase in self.phases.values() if phase.status == ConsolidationStatus.FAILED)
        in_progress_phases = sum(1 for phase in self.phases.values() if phase.status == ConsolidationStatus.IN_PROGRESS)
        
        progress_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        
        # Calculate total file reduction
        total_files_reduced = 0
        total_files_before_phases = 0
        total_files_after_phases = 0
        
        for phase in self.phases.values():
            if phase.status == ConsolidationStatus.COMPLETED:
                total_files_before_phases += phase.files_before
                total_files_after_phases += phase.files_after
                total_files_reduced += (phase.files_before - phase.files_after)
        
        overall_reduction_percentage = 0
        if self.total_files_before > 0:
            current_files = self.total_files_before - total_files_reduced
            overall_reduction_percentage = ((self.total_files_before - current_files) / self.total_files_before) * 100
        
        duration = None
        if self.project_start_time:
            end_time = self.project_end_time or datetime.now()
            duration = (end_time - self.project_start_time).total_seconds()
        
        return {
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": failed_phases,
            "in_progress_phases": in_progress_phases,
            "progress_percentage": progress_percentage,
            "duration_seconds": duration,
            "total_files_before": self.total_files_before,
            "current_files": self.total_files_before - total_files_reduced,
            "files_reduced": total_files_reduced,
            "overall_reduction_percentage": overall_reduction_percentage,
            "target_reduction_percentage": 50.0
        }
    
    def generate_progress_report(self) -> Dict:
        """
        Generate a comprehensive progress report.
        
        Returns:
            Detailed progress report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_progress": self.get_overall_progress(),
            "phases": []
        }
        
        # Add phase details
        for phase_id, phase in self.phases.items():
            phase_progress = self.get_phase_progress(phase_id)
            
            # Add step details
            phase_progress["steps"] = []
            for step in phase.steps:
                step_info = {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "files_affected_count": len(step.files_affected),
                    "backup_count": len(step.backup_ids),
                    "error_message": step.error_message
                }
                
                if step.start_time and step.end_time:
                    step_info["duration_seconds"] = (step.end_time - step.start_time).total_seconds()
                
                phase_progress["steps"].append(step_info)
            
            report["phases"].append(phase_progress)
        
        return report
    
    def list_phases(self) -> List[ConsolidationPhase]:
        """
        List all consolidation phases.
        
        Returns:
            List of consolidation phases
        """
        return list(self.phases.values())
    
    def get_phase(self, phase_id: str) -> Optional[ConsolidationPhase]:
        """
        Get a specific consolidation phase.
        
        Args:
            phase_id: ID of the phase
            
        Returns:
            Consolidation phase if found, None otherwise
        """
        return self.phases.get(phase_id)
    
    def finalize_project(self, total_files_after: int) -> None:
        """
        Finalize the consolidation project.
        
        Args:
            total_files_after: Total number of files after consolidation
        """
        self.project_end_time = datetime.now()
        self.total_files_after = total_files_after
        self._save_tracking_data()
        
        reduction_percentage = ((self.total_files_before - total_files_after) / self.total_files_before) * 100
        
        logger.info(f"Finalized consolidation project: {self.total_files_before} -> {total_files_after} files ({reduction_percentage:.1f}% reduction)")