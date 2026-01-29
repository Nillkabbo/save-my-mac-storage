#!/usr/bin/env python3
"""
Advanced analytics module for usage patterns and recommendations.

Copyright (c) 2026 macOS Cleaner contributors
Licensed under the MIT License
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from ..interfaces import SafetyLevel


@dataclass
class UsageEvent:
    """Represents a single usage event"""
    timestamp: datetime
    operation_type: str  # analyze, clean, dry_run
    paths_processed: int
    size_processed: int
    duration_seconds: float
    categories: List[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class SpaceUsageSnapshot:
    """Snapshot of disk space usage at a point in time"""
    timestamp: datetime
    total_disk_space: int
    used_space: int
    free_space: int
    category_breakdown: Dict[str, int]  # category -> size in bytes


@dataclass
class CleaningPattern:
    """Pattern identified from cleaning history"""
    category: str
    frequency_days: float
    avg_size_freed: int
    growth_rate_bytes_per_day: float
    recommended_interval_days: int
    confidence_score: float


@dataclass
class PredictionResult:
    """Result of space prediction"""
    days_until_full: int
    predicted_full_date: datetime
    confidence: float
    assumptions: List[str]


class UsageAnalytics:
    """Advanced analytics for cleaning patterns and recommendations"""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.mac_cleaner_analytics").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Data files
        self.events_file = self.data_dir / "usage_events.json"
        self.snapshots_file = self.data_dir / "space_snapshots.json"
        self.patterns_file = self.data_dir / "patterns.json"
        
        # In-memory data
        self.events: List[UsageEvent] = []
        self.snapshots: List[SpaceUsageSnapshot] = []
        self.patterns: List[CleaningPattern] = []
        
        # Load existing data
        self._load_data()
    
    def record_event(self, event: UsageEvent) -> None:
        """Record a usage event"""
        self.events.append(event)
        self._save_events()
        self.logger.info(f"Recorded {event.operation_type} event: {event.paths_processed} paths, {self._format_bytes(event.size_processed)}")
    
    def record_space_snapshot(self, snapshot: SpaceUsageSnapshot) -> None:
        """Record a disk space snapshot"""
        self.snapshots.append(snapshot)
        self._save_snapshots()
        self.logger.info(f"Recorded space snapshot: {self._format_bytes(snapshot.free_space)} free")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze cleaning patterns and generate insights"""
        if len(self.events) < 2:
            return {"error": "Insufficient data for pattern analysis (need at least 2 events)"}
        
        # Analyze by category
        category_patterns = self._analyze_category_patterns()
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns()
        
        # Analyze efficiency trends
        efficiency_trends = self._analyze_efficiency_trends()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_patterns, temporal_patterns)
        
        # Update stored patterns
        self.patterns = category_patterns
        self._save_patterns()
        
        return {
            "analysis_date": datetime.now().isoformat(),
            "total_events": len(self.events),
            "date_range": {
                "start": min(e.timestamp for e in self.events).isoformat(),
                "end": max(e.timestamp for e in self.events).isoformat()
            },
            "category_patterns": [asdict(p) for p in category_patterns],
            "temporal_patterns": temporal_patterns,
            "efficiency_trends": efficiency_trends,
            "recommendations": recommendations
        }
    
    def predict_space_usage(self, days_ahead: int = 30) -> PredictionResult:
        """Predict when disk will be full based on historical data"""
        if len(self.snapshots) < 2:
            return PredictionResult(
                days_until_full=-1,
                predicted_full_date=datetime.now(),
                confidence=0.0,
                assumptions=["Insufficient data for prediction"]
            )
        
        # Calculate growth rate from recent snapshots
        recent_snapshots = sorted(self.snapshots, key=lambda s: s.timestamp)[-10:]  # Last 10 snapshots
        
        if len(recent_snapshots) < 2:
            return PredictionResult(
                days_until_full=-1,
                predicted_full_date=datetime.now(),
                confidence=0.0,
                assumptions=["Insufficient recent data for prediction"]
            )
        
        # Calculate daily growth rate
        growth_rates = []
        for i in range(1, len(recent_snapshots)):
            days_diff = (recent_snapshots[i].timestamp - recent_snapshots[i-1].timestamp).days
            if days_diff > 0:
                used_diff = recent_snapshots[i].used_space - recent_snapshots[i-1].used_space
                growth_rates.append(used_diff / days_diff)
        
        if not growth_rates:
            return PredictionResult(
                days_until_full=-1,
                predicted_full_date=datetime.now(),
                confidence=0.0,
                assumptions=["No growth detected in recent data"]
            )
        
        avg_growth_rate = statistics.mean(growth_rates)
        
        # Get latest snapshot
        latest_snapshot = max(self.snapshots, key=lambda s: s.timestamp)
        current_free = latest_snapshot.free_space
        
        if avg_growth_rate <= 0:
            # Space is not growing or is shrinking
            return PredictionResult(
                days_until_full=-1,
                predicted_full_date=datetime.now() + timedelta(days=365),  # Far future
                confidence=0.8,
                assumptions=["Disk usage is stable or decreasing"]
            )
        
        # Calculate days until full
        days_until_full = int(current_free / avg_growth_rate)
        predicted_full_date = datetime.now() + timedelta(days=days_until_full)
        
        # Calculate confidence based on data consistency
        confidence = self._calculate_prediction_confidence(growth_rates)
        
        assumptions = [
            f"Average daily growth: {self._format_bytes(avg_growth_rate)}",
            f"Current free space: {self._format_bytes(current_free)}",
            f"Based on {len(recent_snapshots)} recent snapshots"
        ]
        
        return PredictionResult(
            days_until_full=days_until_full,
            predicted_full_date=predicted_full_date,
            confidence=confidence,
            assumptions=assumptions
        )
    
    def suggest_cleanup_schedule(self) -> Dict[str, Any]:
        """Suggest optimal cleaning schedule based on patterns"""
        if not self.patterns:
            # Generate patterns if not available
            self.analyze_patterns()
        
        if not self.patterns:
            return {"error": "No patterns available for schedule recommendation"}
        
        # Group patterns by recommended interval
        schedule_recommendations = {}
        
        for pattern in self.patterns:
            if pattern.confidence_score > 0.5:  # Only use patterns with reasonable confidence
                interval = pattern.recommended_interval_days
                if interval not in schedule_recommendations:
                    schedule_recommendations[interval] = {
                        "categories": [],
                        "expected_space_freed": 0,
                        "confidence": 0
                    }
                
                schedule_recommendations[interval]["categories"].append(pattern.category)
                schedule_recommendations[interval]["expected_space_freed"] += pattern.avg_size_freed
                schedule_recommendations[interval]["confidence"] = max(
                    schedule_recommendations[interval]["confidence"],
                    pattern.confidence_score
                )
        
        # Sort by interval (most frequent first)
        sorted_schedule = dict(sorted(schedule_recommendations.items()))
        
        # Generate overall recommendation
        overall_recommendation = self._generate_overall_schedule(sorted_schedule)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "schedule": sorted_schedule,
            "overall_recommendation": overall_recommendation,
            "next_actions": self._get_next_actions(sorted_schedule)
        }
    
    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]
        
        if not recent_events:
            return {"error": f"No usage data in the last {days} days"}
        
        # Calculate summary statistics
        total_operations = len(recent_events)
        successful_operations = sum(1 for e in recent_events if e.success)
        total_paths_processed = sum(e.paths_processed for e in recent_events)
        total_size_processed = sum(e.size_processed for e in recent_events)
        avg_duration = statistics.mean(e.duration_seconds for e in recent_events)
        
        # Category breakdown
        category_counts = defaultdict(int)
        category_sizes = defaultdict(int)
        
        for event in recent_events:
            for category in event.categories:
                category_counts[category] += 1
                category_sizes[category] += event.size_processed
        
        # Most active day
        day_counts = defaultdict(int)
        for event in recent_events:
            day_counts[event.timestamp.strftime("%A")] += 1
        
        most_active_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        
        return {
            "summary_period": f"Last {days} days",
            "total_operations": total_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "total_paths_processed": total_paths_processed,
            "total_size_processed": total_size_processed,
            "total_size_processed_human": self._format_bytes(total_size_processed),
            "average_duration_seconds": avg_duration,
            "most_active_day": most_active_day,
            "category_breakdown": {
                "operations": dict(category_counts),
                "size_processed": {k: self._format_bytes(v) for k, v in category_sizes.items()}
            },
            "daily_average": {
                "operations": total_operations / days,
                "paths": total_paths_processed / days,
                "size": total_size_processed / days
            }
        }
    
    def _analyze_category_patterns(self) -> List[CleaningPattern]:
        """Analyze patterns for each category"""
        category_events = defaultdict(list)
        
        # Group events by category
        for event in self.events:
            for category in event.categories:
                category_events[category].append(event)
        
        patterns = []
        
        for category, events in category_events.items():
            if len(events) < 2:
                continue
            
            # Calculate frequency
            events_sorted = sorted(events, key=lambda e: e.timestamp)
            intervals = []
            sizes_freed = []
            
            for i in range(1, len(events_sorted)):
                days_diff = (events_sorted[i].timestamp - events_sorted[i-1].timestamp).days
                if days_diff > 0:
                    intervals.append(days_diff)
                sizes_freed.append(events_sorted[i].size_processed)
            
            if not intervals:
                continue
            
            avg_interval = statistics.mean(intervals)
            avg_size_freed = statistics.mean(sizes_freed) if sizes_freed else 0
            
            # Calculate growth rate (simplified)
            growth_rate = 0
            if len(self.snapshots) >= 2:
                # Estimate growth rate for this category
                category_sizes = []
                for snapshot in self.snapshots:
                    category_size = snapshot.category_breakdown.get(category, 0)
                    category_sizes.append((snapshot.timestamp, category_size))
                
                if len(category_sizes) >= 2:
                    category_sizes.sort(key=lambda x: x[0])
                    growth_rates = []
                    for i in range(1, len(category_sizes)):
                        days_diff = (category_sizes[i][0] - category_sizes[i-1][0]).days
                        if days_diff > 0:
                            size_diff = category_sizes[i][1] - category_sizes[i-1][1]
                            growth_rates.append(size_diff / days_diff)
                    
                    if growth_rates:
                        growth_rate = statistics.mean(growth_rates)
            
            # Recommend interval (simplified logic)
            if avg_size_freed > 1024 * 1024 * 1024:  # > 1GB
                recommended_interval = max(1, int(avg_interval * 0.8))  # More frequent
            elif avg_size_freed > 100 * 1024 * 1024:  # > 100MB
                recommended_interval = max(7, int(avg_interval))  # Weekly
            else:
                recommended_interval = max(30, int(avg_interval * 1.2))  # Monthly
            
            # Calculate confidence
            confidence = min(1.0, len(events) / 10)  # More events = higher confidence
            
            patterns.append(CleaningPattern(
                category=category,
                frequency_days=avg_interval,
                avg_size_freed=int(avg_size_freed),
                growth_rate_bytes_per_day=growth_rate,
                recommended_interval_days=recommended_interval,
                confidence_score=confidence
            ))
        
        return patterns
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal usage patterns"""
        # Day of week analysis
        day_counts = defaultdict(list)
        for event in self.events:
            day_name = event.timestamp.strftime("%A")
            day_counts[day_name].append(event.size_processed)
        
        day_stats = {}
        for day, sizes in day_counts.items():
            if sizes:
                day_stats[day] = {
                    "count": len(sizes),
                    "avg_size": statistics.mean(sizes),
                    "total_size": sum(sizes)
                }
        
        # Hour of day analysis
        hour_counts = defaultdict(list)
        for event in self.events:
            hour_counts[event.timestamp.hour].append(event.size_processed)
        
        hour_stats = {}
        for hour, sizes in hour_counts.items():
            if sizes:
                hour_stats[hour] = {
                    "count": len(sizes),
                    "avg_size": statistics.mean(sizes),
                    "total_size": sum(sizes)
                }
        
        # Find peak times
        peak_day = max(day_stats.items(), key=lambda x: x[1]["total_size"]) if day_stats else None
        peak_hour = max(hour_stats.items(), key=lambda x: x[1]["total_size"]) if hour_stats else None
        
        return {
            "day_patterns": day_stats,
            "hour_patterns": hour_stats,
            "peak_day": {"day": peak_day[0], "stats": peak_day[1]} if peak_day else None,
            "peak_hour": {"hour": peak_hour[0], "stats": peak_hour[1]} if peak_hour else None
        }
    
    def _analyze_efficiency_trends(self) -> Dict[str, Any]:
        """Analyze efficiency trends over time"""
        if len(self.events) < 5:
            return {"error": "Insufficient data for trend analysis"}
        
        # Sort events by timestamp
        events_sorted = sorted(self.events, key=lambda e: e.timestamp)
        
        # Calculate moving averages
        window_size = min(10, len(events_sorted) // 2)
        
        size_trend = []
        duration_trend = []
        
        for i in range(window_size, len(events_sorted)):
            window = events_sorted[i-window_size:i]
            avg_size = statistics.mean(e.size_processed for e in window)
            avg_duration = statistics.mean(e.duration_seconds for e in window)
            
            size_trend.append({
                "timestamp": events_sorted[i].timestamp.isoformat(),
                "avg_size": avg_size,
                "avg_size_human": self._format_bytes(avg_size)
            })
            duration_trend.append({
                "timestamp": events_sorted[i].timestamp.isoformat(),
                "avg_duration": avg_duration
            })
        
        # Calculate trend direction
        if len(size_trend) >= 2:
            size_change = size_trend[-1]["avg_size"] - size_trend[0]["avg_size"]
            duration_change = duration_trend[-1]["avg_duration"] - duration_trend[0]["avg_duration"]
            
            size_trend_direction = "increasing" if size_change > 0 else "decreasing" if size_change < 0 else "stable"
            duration_trend_direction = "increasing" if duration_change > 0 else "decreasing" if duration_change < 0 else "stable"
        else:
            size_trend_direction = "unknown"
            duration_trend_direction = "unknown"
        
        return {
            "size_trend": size_trend,
            "duration_trend": duration_trend,
            "trend_direction": {
                "size": size_trend_direction,
                "duration": duration_trend_direction
            }
        }
    
    def _generate_recommendations(self, patterns: List[CleaningPattern], temporal: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []
        
        # Category-based recommendations
        high_growth_categories = [p for p in patterns if p.growth_rate_bytes_per_day > 1024 * 1024]  # > 1MB/day
        if high_growth_categories:
            recommendations.append(
                f"High-growth categories detected: {', '.join(c.category for c in high_growth_categories)}. "
                "Consider more frequent cleaning for these."
            )
        
        # Large space categories
        large_categories = [p for p in patterns if p.avg_size_freed > 1024 * 1024 * 1024]  # > 1GB
        if large_categories:
            recommendations.append(
                f"Categories freeing significant space: {', '.join(c.category for c in large_categories)}. "
                "Prioritize these in cleaning operations."
            )
        
        # Temporal recommendations
        if temporal.get("peak_day"):
            peak_day = temporal["peak_day"]["day"]
            recommendations.append(
                f"Peak usage day is {peak_day}. Consider scheduling cleaning for the following day."
            )
        
        if temporal.get("peak_hour"):
            peak_hour = temporal["peak_hour"]["hour"]
            recommendations.append(
                f"Peak usage hour is {peak_hour}:00. Avoid scheduling cleaning during peak times."
            )
        
        # General recommendations
        if len(patterns) > 0:
            avg_confidence = statistics.mean(p.confidence_score for p in patterns)
            if avg_confidence < 0.5:
                recommendations.append(
                    "Low confidence in patterns detected. More usage data needed for accurate recommendations."
                )
        
        return recommendations
    
    def _generate_overall_schedule(self, schedule: Dict[int, Dict]) -> Dict[str, Any]:
        """Generate overall schedule recommendation"""
        if not schedule:
            return {"recommendation": "No schedule available"}
        
        # Find the most frequent cleaning needed
        min_interval = min(schedule.keys())
        
        # Calculate total expected space freed per week
        weekly_space = 0
        for interval, info in schedule.items():
            weekly_space += (info["expected_space_freed"] * 7) / interval
        
        return {
            "minimum_interval_days": min_interval,
            "recommended_frequency": f"Every {min_interval} days",
            "expected_weekly_space_freed": weekly_space,
            "expected_weekly_space_freed_human": self._format_bytes(int(weekly_space)),
            "confidence": max(info["confidence"] for info in schedule.values())
        }
    
    def _get_next_actions(self, schedule: Dict[int, Dict]) -> List[str]:
        """Get immediate next actions based on schedule"""
        actions = []
        
        if not schedule:
            return ["Run more cleaning operations to establish patterns"]
        
        # Find categories needing immediate attention
        for interval, info in schedule.items():
            if interval <= 7:  # Weekly or more frequent
                actions.append(f"Schedule weekly cleaning for: {', '.join(info['categories'])}")
        
        if not actions:
            actions.append("Current usage patterns are within normal ranges")
        
        return actions
    
    def _calculate_prediction_confidence(self, growth_rates: List[float]) -> float:
        """Calculate confidence score for predictions"""
        if len(growth_rates) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_rate = statistics.mean(growth_rates)
        if mean_rate == 0:
            return 0.0
        
        std_dev = statistics.stdev(growth_rates)
        cv = std_dev / abs(mean_rate)
        
        # Convert to confidence (lower CV = higher confidence)
        confidence = max(0.0, min(1.0, 1.0 - cv))
        
        # Adjust based on number of data points
        data_point_factor = min(1.0, len(growth_rates) / 10)
        
        return confidence * data_point_factor
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes into human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def _load_data(self) -> None:
        """Load data from files"""
        try:
            if self.events_file.exists():
                with open(self.events_file, 'r') as f:
                    events_data = json.load(f)
                    self.events = [
                        UsageEvent(
                            timestamp=datetime.fromisoformat(e["timestamp"]),
                            operation_type=e["operation_type"],
                            paths_processed=e["paths_processed"],
                            size_processed=e["size_processed"],
                            duration_seconds=e["duration_seconds"],
                            categories=e["categories"],
                            success=e["success"],
                            error_message=e.get("error_message")
                        )
                        for e in events_data
                    ]
        except Exception as e:
            self.logger.error(f"Error loading events: {e}")
        
        try:
            if self.snapshots_file.exists():
                with open(self.snapshots_file, 'r') as f:
                    snapshots_data = json.load(f)
                    self.snapshots = [
                        SpaceUsageSnapshot(
                            timestamp=datetime.fromisoformat(s["timestamp"]),
                            total_disk_space=s["total_disk_space"],
                            used_space=s["used_space"],
                            free_space=s["free_space"],
                            category_breakdown=s["category_breakdown"]
                        )
                        for s in snapshots_data
                    ]
        except Exception as e:
            self.logger.error(f"Error loading snapshots: {e}")
        
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.patterns = [
                        CleaningPattern(**p) for p in patterns_data
                    ]
        except Exception as e:
            self.logger.error(f"Error loading patterns: {e}")
    
    def _save_events(self) -> None:
        """Save events to file"""
        try:
            events_data = [asdict(event) for event in self.events]
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving events: {e}")
    
    def _save_snapshots(self) -> None:
        """Save snapshots to file"""
        try:
            snapshots_data = [asdict(snapshot) for snapshot in self.snapshots]
            with open(self.snapshots_file, 'w') as f:
                json.dump(snapshots_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving snapshots: {e}")
    
    def _save_patterns(self) -> None:
        """Save patterns to file"""
        try:
            patterns_data = [asdict(pattern) for pattern in self.patterns]
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving patterns: {e}")
