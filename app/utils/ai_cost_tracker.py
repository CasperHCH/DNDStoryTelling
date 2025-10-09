"""
AI Service Cost Tracking and Usage Monitoring.
Prevents unexpected API charges and tracks usage across all AI services.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from app.utils.monitoring import performance_metrics, alert_manager

logger = logging.getLogger(__name__)


class AIService(Enum):
    """Supported AI services."""
    OPENAI_GPT = "openai_gpt"
    OPENAI_WHISPER = "openai_whisper"
    OPENAI_EMBEDDINGS = "openai_embeddings"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    GOOGLE_GEMINI = "google_gemini"
    AZURE_OPENAI = "azure_openai"
    LOCAL_WHISPER = "local_whisper"
    HUGGINGFACE = "huggingface"


class UsageType(Enum):
    """Types of usage tracking."""
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    AUDIO_MINUTES = "audio_minutes"
    EMBEDDING_DIMENSIONS = "embedding_dimensions"
    API_REQUESTS = "api_requests"
    PROCESSING_TIME = "processing_time"


@dataclass
class CostRate:
    """Cost rate configuration for AI services."""
    service: AIService
    usage_type: UsageType
    cost_per_unit: Decimal
    unit_name: str
    model_name: Optional[str] = None

    def calculate_cost(self, usage_amount: float) -> Decimal:
        """Calculate cost for given usage amount."""
        return (Decimal(str(usage_amount)) * self.cost_per_unit).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )


@dataclass
class UsageRecord:
    """Individual usage record."""
    timestamp: datetime
    service: AIService
    usage_type: UsageType
    amount: float
    cost: Decimal
    model_name: Optional[str]
    operation_id: Optional[str]
    user_id: Optional[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['cost'] = float(self.cost)
        result['service'] = self.service.value
        result['usage_type'] = self.usage_type.value
        return result


@dataclass
class UsageQuota:
    """Usage quota configuration."""
    service: Optional[AIService]
    usage_type: Optional[UsageType]
    period_hours: int
    max_usage: float
    max_cost: Decimal
    alert_threshold_percent: int = 80

    def get_quota_id(self) -> str:
        """Generate unique quota identifier."""
        service_part = self.service.value if self.service else "all"
        usage_part = self.usage_type.value if self.usage_type else "all"
        return f"{service_part}_{usage_part}_{self.period_hours}h"


class AIUsageTracker:
    """Tracks AI service usage and costs."""

    def __init__(self, usage_file: str = "ai_usage.json"):
        self.usage_file = Path(usage_file)
        self.usage_records: List[UsageRecord] = []
        self.cost_rates: Dict[str, CostRate] = {}
        self.usage_quotas: Dict[str, UsageQuota] = {}

        # Load existing data
        self._load_usage_data()
        self._initialize_cost_rates()
        self._initialize_default_quotas()

    def _load_usage_data(self):
        """Load usage data from file."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)

                self.usage_records = []
                for record_data in data.get('usage_records', []):
                    record_data['timestamp'] = datetime.fromisoformat(record_data['timestamp'])
                    record_data['service'] = AIService(record_data['service'])
                    record_data['usage_type'] = UsageType(record_data['usage_type'])
                    record_data['cost'] = Decimal(str(record_data['cost']))
                    self.usage_records.append(UsageRecord(**record_data))

                logger.info(f"Loaded {len(self.usage_records)} usage records")

            except Exception as e:
                logger.error(f"Failed to load usage data: {e}")

    def _save_usage_data(self):
        """Save usage data to file."""
        try:
            data = {
                'usage_records': [record.to_dict() for record in self.usage_records],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")

    def _initialize_cost_rates(self):
        """Initialize current cost rates for AI services."""

        # OpenAI GPT-4 rates (as of 2024)
        self.cost_rates.update({
            'openai_gpt4_input': CostRate(
                service=AIService.OPENAI_GPT,
                usage_type=UsageType.INPUT_TOKENS,
                cost_per_unit=Decimal('0.00003'),  # $0.03 per 1K tokens
                unit_name='tokens',
                model_name='gpt-4'
            ),
            'openai_gpt4_output': CostRate(
                service=AIService.OPENAI_GPT,
                usage_type=UsageType.OUTPUT_TOKENS,
                cost_per_unit=Decimal('0.00006'),  # $0.06 per 1K tokens
                unit_name='tokens',
                model_name='gpt-4'
            ),
            'openai_gpt35_input': CostRate(
                service=AIService.OPENAI_GPT,
                usage_type=UsageType.INPUT_TOKENS,
                cost_per_unit=Decimal('0.0000015'),  # $0.0015 per 1K tokens
                unit_name='tokens',
                model_name='gpt-3.5-turbo'
            ),
            'openai_gpt35_output': CostRate(
                service=AIService.OPENAI_GPT,
                usage_type=UsageType.OUTPUT_TOKENS,
                cost_per_unit=Decimal('0.000002'),  # $0.002 per 1K tokens
                unit_name='tokens',
                model_name='gpt-3.5-turbo'
            ),
            'openai_whisper': CostRate(
                service=AIService.OPENAI_WHISPER,
                usage_type=UsageType.AUDIO_MINUTES,
                cost_per_unit=Decimal('0.006'),  # $0.006 per minute
                unit_name='minutes',
                model_name='whisper-1'
            ),
            'openai_embeddings': CostRate(
                service=AIService.OPENAI_EMBEDDINGS,
                usage_type=UsageType.INPUT_TOKENS,
                cost_per_unit=Decimal('0.0000001'),  # $0.0001 per 1K tokens
                unit_name='tokens',
                model_name='text-embedding-ada-002'
            )
        })

        # Anthropic Claude rates
        self.cost_rates.update({
            'claude_input': CostRate(
                service=AIService.ANTHROPIC_CLAUDE,
                usage_type=UsageType.INPUT_TOKENS,
                cost_per_unit=Decimal('0.000008'),  # $8 per 1M tokens
                unit_name='tokens',
                model_name='claude-3-sonnet'
            ),
            'claude_output': CostRate(
                service=AIService.ANTHROPIC_CLAUDE,
                usage_type=UsageType.OUTPUT_TOKENS,
                cost_per_unit=Decimal('0.000024'),  # $24 per 1M tokens
                unit_name='tokens',
                model_name='claude-3-sonnet'
            )
        })

        # Local/free services (zero cost)
        self.cost_rates.update({
            'local_whisper': CostRate(
                service=AIService.LOCAL_WHISPER,
                usage_type=UsageType.AUDIO_MINUTES,
                cost_per_unit=Decimal('0'),
                unit_name='minutes'
            ),
            'huggingface_free': CostRate(
                service=AIService.HUGGINGFACE,
                usage_type=UsageType.API_REQUESTS,
                cost_per_unit=Decimal('0'),
                unit_name='requests'
            )
        })

        logger.info(f"Initialized {len(self.cost_rates)} cost rates")

    def _initialize_default_quotas(self):
        """Initialize default usage quotas."""

        # Daily quotas
        self.usage_quotas.update({
            'openai_daily_cost': UsageQuota(
                service=AIService.OPENAI_GPT,
                usage_type=None,
                period_hours=24,
                max_usage=float('inf'),
                max_cost=Decimal('50.00'),  # $50/day limit
                alert_threshold_percent=80
            ),
            'whisper_daily_minutes': UsageQuota(
                service=AIService.OPENAI_WHISPER,
                usage_type=UsageType.AUDIO_MINUTES,
                period_hours=24,
                max_usage=1000,  # 1000 minutes/day
                max_cost=Decimal('6.00'),
                alert_threshold_percent=85
            ),
            'total_daily_cost': UsageQuota(
                service=None,
                usage_type=None,
                period_hours=24,
                max_usage=float('inf'),
                max_cost=Decimal('100.00'),  # $100/day total
                alert_threshold_percent=75
            )
        })

        # Hourly quotas for burst protection
        self.usage_quotas.update({
            'openai_hourly_tokens': UsageQuota(
                service=AIService.OPENAI_GPT,
                usage_type=UsageType.INPUT_TOKENS,
                period_hours=1,
                max_usage=100000,  # 100K tokens/hour
                max_cost=Decimal('10.00'),
                alert_threshold_percent=90
            ),
            'whisper_hourly_minutes': UsageQuota(
                service=AIService.OPENAI_WHISPER,
                usage_type=UsageType.AUDIO_MINUTES,
                period_hours=1,
                max_usage=60,  # 60 minutes/hour
                max_cost=Decimal('0.36'),
                alert_threshold_percent=90
            )
        })

        logger.info(f"Initialized {len(self.usage_quotas)} usage quotas")

    async def record_usage(self,
                          service: AIService,
                          usage_type: UsageType,
                          amount: float,
                          model_name: Optional[str] = None,
                          operation_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          metadata: Dict[str, Any] = None) -> Decimal:
        """Record AI service usage and calculate cost."""

        # Find appropriate cost rate
        cost_rate = self._get_cost_rate(service, usage_type, model_name)
        if not cost_rate:
            logger.warning(f"No cost rate found for {service.value} {usage_type.value}")
            cost = Decimal('0')
        else:
            cost = cost_rate.calculate_cost(amount)

        # Create usage record
        usage_record = UsageRecord(
            timestamp=datetime.now(),
            service=service,
            usage_type=usage_type,
            amount=amount,
            cost=cost,
            model_name=model_name,
            operation_id=operation_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        # Add to records
        self.usage_records.append(usage_record)

        # Check quotas
        await self._check_quotas(usage_record)

        # Save data periodically
        if len(self.usage_records) % 10 == 0:  # Save every 10 records
            self._save_usage_data()

        # Record metrics
        performance_metrics.record_function_call(f"ai_usage_{service.value}", amount)
        performance_metrics.record_function_call(f"ai_cost_{service.value}", float(cost))

        logger.debug(f"Recorded usage: {service.value} {usage_type.value} {amount} units, cost ${cost}")

        return cost

    def _get_cost_rate(self, service: AIService, usage_type: UsageType, model_name: Optional[str]) -> Optional[CostRate]:
        """Find appropriate cost rate for service/usage type combination."""

        # Try to find exact match with model name
        if model_name:
            for rate_key, rate in self.cost_rates.items():
                if (rate.service == service and
                    rate.usage_type == usage_type and
                    rate.model_name == model_name):
                    return rate

        # Fallback to service/usage type match
        for rate_key, rate in self.cost_rates.items():
            if rate.service == service and rate.usage_type == usage_type:
                return rate

        return None

    async def _check_quotas(self, usage_record: UsageRecord):
        """Check if usage exceeds any quotas."""

        for quota_id, quota in self.usage_quotas.items():
            # Calculate usage in quota period
            period_start = datetime.now() - timedelta(hours=quota.period_hours)

            # Filter records for this quota period
            relevant_records = [
                record for record in self.usage_records
                if record.timestamp >= period_start and self._matches_quota(record, quota)
            ]

            # Calculate totals
            total_usage = sum(record.amount for record in relevant_records)
            total_cost = sum(record.cost for record in relevant_records)

            # Check usage quota
            if total_usage > quota.max_usage:
                await alert_manager.trigger_alert(
                    "usage_quota_exceeded",
                    "error",
                    f"Usage quota exceeded for {quota_id}: {total_usage:.2f} > {quota.max_usage}",
                    {
                        'quota_id': quota_id,
                        'current_usage': total_usage,
                        'max_usage': quota.max_usage,
                        'period_hours': quota.period_hours
                    }
                )

            # Check cost quota
            if total_cost > quota.max_cost:
                await alert_manager.trigger_alert(
                    "cost_quota_exceeded",
                    "error",
                    f"Cost quota exceeded for {quota_id}: ${total_cost:.4f} > ${quota.max_cost}",
                    {
                        'quota_id': quota_id,
                        'current_cost': float(total_cost),
                        'max_cost': float(quota.max_cost),
                        'period_hours': quota.period_hours
                    }
                )

            # Check alert thresholds
            usage_percent = (total_usage / quota.max_usage) * 100 if quota.max_usage != float('inf') else 0
            cost_percent = (total_cost / quota.max_cost) * 100

            max_percent = max(usage_percent, cost_percent)

            if max_percent >= quota.alert_threshold_percent:
                await alert_manager.trigger_alert(
                    "quota_alert_threshold",
                    "warning",
                    f"Quota threshold reached for {quota_id}: {max_percent:.1f}%",
                    {
                        'quota_id': quota_id,
                        'usage_percent': usage_percent,
                        'cost_percent': cost_percent,
                        'threshold_percent': quota.alert_threshold_percent
                    }
                )

    def _matches_quota(self, record: UsageRecord, quota: UsageQuota) -> bool:
        """Check if usage record matches quota criteria."""

        # Service filter
        if quota.service and record.service != quota.service:
            return False

        # Usage type filter
        if quota.usage_type and record.usage_type != quota.usage_type:
            return False

        return True

    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for specified period."""

        period_start = datetime.now() - timedelta(hours=hours)
        recent_records = [
            record for record in self.usage_records
            if record.timestamp >= period_start
        ]

        # Group by service
        service_usage = {}
        for record in recent_records:
            service_key = record.service.value
            if service_key not in service_usage:
                service_usage[service_key] = {
                    'total_cost': Decimal('0'),
                    'usage_by_type': {},
                    'request_count': 0
                }

            service_usage[service_key]['total_cost'] += record.cost
            service_usage[service_key]['request_count'] += 1

            usage_type_key = record.usage_type.value
            if usage_type_key not in service_usage[service_key]['usage_by_type']:
                service_usage[service_key]['usage_by_type'][usage_type_key] = 0
            service_usage[service_key]['usage_by_type'][usage_type_key] += record.amount

        # Convert Decimal to float for JSON serialization
        for service_data in service_usage.values():
            service_data['total_cost'] = float(service_data['total_cost'])

        total_cost = sum(record.cost for record in recent_records)
        total_requests = len(recent_records)

        return {
            'period_hours': hours,
            'total_cost': float(total_cost),
            'total_requests': total_requests,
            'service_breakdown': service_usage,
            'record_count': len(recent_records),
            'period_start': period_start.isoformat(),
            'period_end': datetime.now().isoformat()
        }

    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status for all quotas."""

        quota_status = {}

        for quota_id, quota in self.usage_quotas.items():
            period_start = datetime.now() - timedelta(hours=quota.period_hours)

            # Filter records for this quota
            relevant_records = [
                record for record in self.usage_records
                if record.timestamp >= period_start and self._matches_quota(record, quota)
            ]

            # Calculate current usage
            current_usage = sum(record.amount for record in relevant_records)
            current_cost = sum(record.cost for record in relevant_records)

            # Calculate percentages
            usage_percent = (current_usage / quota.max_usage) * 100 if quota.max_usage != float('inf') else 0
            cost_percent = (current_cost / quota.max_cost) * 100

            quota_status[quota_id] = {
                'current_usage': current_usage,
                'max_usage': quota.max_usage,
                'usage_percent': usage_percent,
                'current_cost': float(current_cost),
                'max_cost': float(quota.max_cost),
                'cost_percent': cost_percent,
                'period_hours': quota.period_hours,
                'alert_threshold': quota.alert_threshold_percent,
                'status': 'ok' if max(usage_percent, cost_percent) < quota.alert_threshold_percent else 'warning'
            }

        return quota_status

    async def estimate_cost(self,
                          service: AIService,
                          usage_type: UsageType,
                          estimated_amount: float,
                          model_name: Optional[str] = None) -> Tuple[Decimal, bool]:
        """Estimate cost for planned usage and check if it would exceed quotas."""

        # Calculate estimated cost
        cost_rate = self._get_cost_rate(service, usage_type, model_name)
        if not cost_rate:
            return Decimal('0'), True

        estimated_cost = cost_rate.calculate_cost(estimated_amount)

        # Check if this would exceed any quotas
        would_exceed = False

        for quota in self.usage_quotas.values():
            if not self._service_matches_quota(service, usage_type, quota):
                continue

            period_start = datetime.now() - timedelta(hours=quota.period_hours)
            relevant_records = [
                record for record in self.usage_records
                if record.timestamp >= period_start and self._matches_quota(record, quota)
            ]

            current_usage = sum(record.amount for record in relevant_records)
            current_cost = sum(record.cost for record in relevant_records)

            # Check if estimated usage would exceed quotas
            if (current_usage + estimated_amount > quota.max_usage or
                current_cost + estimated_cost > quota.max_cost):
                would_exceed = True
                break

        return estimated_cost, not would_exceed

    def _service_matches_quota(self, service: AIService, usage_type: UsageType, quota: UsageQuota) -> bool:
        """Check if service/usage type matches quota."""

        if quota.service and quota.service != service:
            return False

        if quota.usage_type and quota.usage_type != usage_type:
            return False

        return True

    def add_custom_quota(self, quota: UsageQuota) -> str:
        """Add a custom usage quota."""

        quota_id = quota.get_quota_id()
        self.usage_quotas[quota_id] = quota

        logger.info(f"Added custom quota: {quota_id}")
        return quota_id

    def export_usage_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export usage data for analysis or billing."""

        filtered_records = self.usage_records

        if start_date:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_date]

        if end_date:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_date]

        return [record.to_dict() for record in filtered_records]

    def cleanup_old_records(self, days_to_keep: int = 90):
        """Clean up old usage records to prevent unlimited growth."""

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        old_count = len(self.usage_records)
        self.usage_records = [
            record for record in self.usage_records
            if record.timestamp >= cutoff_date
        ]

        removed_count = old_count - len(self.usage_records)

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old usage records")
            self._save_usage_data()


# Global usage tracker instance
usage_tracker = AIUsageTracker()