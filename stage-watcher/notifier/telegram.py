"""Compat: réexporte l'API du package notifier."""

from . import format_job_message, send_batch, send_telegram_message

send_offers = send_batch

__all__ = ["send_batch", "send_offers", "send_telegram_message", "format_job_message"]
