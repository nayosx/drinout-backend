from models.global_setting import GLOBAL_SETTING_CATEGORIES


GLOBAL_SETTING_CATEGORY_BY_KEY = {
    "express_service_surcharge": "laundry_pricing",
    "delivery_price_per_km": "delivery_pricing",
    "work_session_daily_target_time": "operations_workforce",
}


def infer_global_setting_category(setting_key):
    if not setting_key:
        return "general"

    normalized_key = str(setting_key).strip().lower()
    if normalized_key in GLOBAL_SETTING_CATEGORY_BY_KEY:
        return GLOBAL_SETTING_CATEGORY_BY_KEY[normalized_key]

    if normalized_key.startswith("delivery_") or "delivery" in normalized_key:
        return "delivery_pricing"
    if normalized_key.startswith("work_session_") or normalized_key.startswith("worker_"):
        return "operations_workforce"
    if "discount" in normalized_key:
        return "discounts"
    if "surcharge" in normalized_key or "price" in normalized_key or "pricing" in normalized_key:
        return "laundry_pricing"
    if "billing" in normalized_key or "invoice" in normalized_key or "payment" in normalized_key:
        return "billing"
    if "integration" in normalized_key or "webhook" in normalized_key or "api_key" in normalized_key:
        return "integrations"
    return "general"


def normalize_global_setting_category(category, setting_key=None):
    normalized_category = str(category).strip().lower() if category is not None else ""
    if normalized_category:
        if normalized_category not in GLOBAL_SETTING_CATEGORIES:
            raise ValueError(
                f"Invalid global setting category '{category}'. Allowed values: {', '.join(GLOBAL_SETTING_CATEGORIES)}"
            )
        return normalized_category
    return infer_global_setting_category(setting_key)
