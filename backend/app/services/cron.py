"""
Cron job services for scheduled tasks (daily digest, notifications, etc.)
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

from ..repositories.interfaces import Repository
from ..infra.wechat_client import WeChatClient
from ..infra.config import settings

logger = logging.getLogger(__name__)


class CronService:
    """Service for scheduled cron jobs"""

    def __init__(self, repo: Repository, wechat_client: Optional[WeChatClient] = None):
        self.repo = repo
        self.wechat_client = wechat_client

    def daily_digest(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Send daily digest notifications to users.

        Sends two types of messages:
        1. Review reminders for users with due vocab
        2. Streak reminders for users who haven't studied today

        Args:
            dry_run: If True, only log what would be sent without actually sending

        Returns:
            Dict with counts of messages sent
        """
        logger.info("Starting daily digest", extra={"dry_run": dry_run})

        stats = {
            "review_reminders": 0,
            "streak_reminders": 0,
            "errors": 0
        }

        try:
            # 1. Send review reminders
            review_count = self._send_review_reminders(dry_run)
            stats["review_reminders"] = review_count

            # 2. Send streak reminders
            streak_count = self._send_streak_reminders(dry_run)
            stats["streak_reminders"] = streak_count

        except Exception as e:
            logger.error("Daily digest failed", extra={"error": str(e)}, exc_info=True)
            stats["errors"] += 1

        logger.info("Daily digest completed", extra=stats)
        return stats

    def _send_review_reminders(self, dry_run: bool) -> int:
        """Send review reminders to users with due vocab."""
        logger.info("Sending review reminders")

        now = datetime.now(timezone.utc).isoformat()
        sent_count = 0

        try:
            # Query all users with due vocab
            # Group by user_id to get unique users
            users_with_due_vocab = self._get_users_with_due_vocab(now)

            for user_data in users_with_due_vocab:
                user_id = user_data.get("user_id")
                due_count = user_data.get("due_count", 0)

                if not user_id or due_count == 0:
                    continue

                # Get user info for openid
                user = self.repo.query("users", {"id": user_id}, limit=1, offset=0)[0]
                if not user or len(user) == 0:
                    continue

                openid = user[0].get("openid")
                if not openid:
                    continue

                # Send notification
                if not dry_run and self.wechat_client:
                    try:
                        self.wechat_client.send_template_message(
                            openid=openid,
                            template_id=self._get_review_template_id(),
                            data={
                                "thing1": {"value": "词汇复习提醒"},
                                "number2": {"value": str(due_count)},
                                "thing3": {"value": "点击查看今日待复习词汇"}
                            },
                            page="pages/vocab/vocab"
                        )
                        sent_count += 1
                    except Exception as e:
                        logger.warning(
                            "Failed to send review reminder",
                            extra={"user_id": user_id, "error": str(e)}
                        )
                else:
                    logger.info(
                        "Would send review reminder",
                        extra={"user_id": user_id, "due_count": due_count, "dry_run": dry_run}
                    )
                    sent_count += 1

        except Exception as e:
            logger.error("Review reminders failed", extra={"error": str(e)}, exc_info=True)

        logger.info("Review reminders completed", extra={"sent": sent_count})
        return sent_count

    def _send_streak_reminders(self, dry_run: bool) -> int:
        """Send streak reminders to users who haven't studied today."""
        logger.info("Sending streak reminders")

        sent_count = 0
        today = datetime.now(timezone.utc).date().isoformat()

        try:
            # Get all active users
            all_users, total = self.repo.query("users", {}, limit=1000, offset=0)

            for user in all_users:
                user_id = user.get("id")
                openid = user.get("openid")

                if not user_id or not openid:
                    continue

                # Check if user studied today
                studied_today = self._has_studied_today(user_id, today)

                if not studied_today:
                    # Get current streak
                    streak = self._get_user_streak(user_id)

                    if streak >= 3:  # Only remind users with streak >= 3
                        # Send notification
                        if not dry_run and self.wechat_client:
                            try:
                                self.wechat_client.send_template_message(
                                    openid=openid,
                                    template_id=self._get_streak_template_id(),
                                    data={
                                        "thing1": {"value": "学习打卡提醒"},
                                        "number2": {"value": str(streak)},
                                        "thing3": {"value": "继续保持连续学习记录"}
                                    },
                                    page="pages/plan/plan"
                                )
                                sent_count += 1
                            except Exception as e:
                                logger.warning(
                                    "Failed to send streak reminder",
                                    extra={"user_id": user_id, "error": str(e)}
                                )
                        else:
                            logger.info(
                                "Would send streak reminder",
                                extra={"user_id": user_id, "streak": streak, "dry_run": dry_run}
                            )
                            sent_count += 1

        except Exception as e:
            logger.error("Streak reminders failed", extra={"error": str(e)}, exc_info=True)

        logger.info("Streak reminders completed", extra={"sent": sent_count})
        return sent_count

    def _get_users_with_due_vocab(self, before_time: str) -> List[Dict]:
        """Get list of users with due vocab, grouped by user."""
        try:
            # Query vocab items that are due
            vocab_items, _ = self.repo.query(
                "vocab",
                {"next_review_at": {"$lte": before_time}},
                limit=10000,
                offset=0
            )

            # Group by user_id and count
            user_due_counts = {}
            for item in vocab_items:
                user_id = item.get("user_id")
                if user_id:
                    user_due_counts[user_id] = user_due_counts.get(user_id, 0) + 1

            # Convert to list format
            return [
                {"user_id": user_id, "due_count": count}
                for user_id, count in user_due_counts.items()
            ]

        except Exception as e:
            logger.error("Failed to get users with due vocab", extra={"error": str(e)})
            return []

    def _has_studied_today(self, user_id: str, today: str) -> bool:
        """Check if user has studied today."""
        try:
            # Check progress records for today
            progress_items, total = self.repo.query(
                "progress",
                {
                    "user_id": user_id,
                    "ts": {"$gte": f"{today}T00:00:00Z"}
                },
                limit=1,
                offset=0
            )
            return total > 0

        except Exception as e:
            logger.warning("Failed to check study status", extra={"user_id": user_id, "error": str(e)})
            return False

    def _get_user_streak(self, user_id: str) -> int:
        """Get user's current streak."""
        try:
            # Get plan stats
            plan_items, total = self.repo.query(
                "plans",
                {"user_id": user_id},
                limit=1,
                offset=0
            )

            if plan_items and len(plan_items) > 0:
                return plan_items[0].get("streak", 0)

            return 0

        except Exception as e:
            logger.warning("Failed to get user streak", extra={"user_id": user_id, "error": str(e)})
            return 0

    def _get_review_template_id(self) -> str:
        """Get template ID for review reminders."""
        # TODO: Replace with actual template ID from WeChat MP platform
        return os.getenv("WECHAT_TEMPLATE_REVIEW", "TEMPLATE_ID_REVIEW")

    def _get_streak_template_id(self) -> str:
        """Get template ID for streak reminders."""
        # TODO: Replace with actual template ID from WeChat MP platform
        return os.getenv("WECHAT_TEMPLATE_STREAK", "TEMPLATE_ID_STREAK")
