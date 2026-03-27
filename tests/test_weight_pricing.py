import unittest
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "weight_pricing.py"
module_spec = spec_from_file_location("weight_pricing_under_test", module_path)
weight_pricing_module = module_from_spec(module_spec)
module_spec.loader.exec_module(weight_pricing_module)
WeightPricingEngine = weight_pricing_module.WeightPricingEngine


class FakeTier:
    def __init__(self, tier_id, max_weight_lb, price, sort_order, is_active=True):
        self.id = tier_id
        self.max_weight_lb = Decimal(str(max_weight_lb))
        self.price = Decimal(str(price))
        self.sort_order = sort_order
        self.is_active = is_active


class FakeProfile:
    def __init__(
        self,
        strategy="MAX_REVENUE",
        extra_lb_price="0.90",
        compare_all_tiers=True,
        allow_manual_override=True,
        round_mode="exact",
        auto_upgrade_enabled=False,
        auto_upgrade_margin="0.00",
        force_upgrade_from_lb=None,
    ):
        self.id = 1
        self.name = "Perfil Principal MAX_REVENUE"
        self.is_active = True
        self.strategy = strategy
        self.extra_lb_price = Decimal(str(extra_lb_price))
        self.auto_upgrade_enabled = auto_upgrade_enabled
        self.auto_upgrade_margin = Decimal(str(auto_upgrade_margin))
        self.force_upgrade_from_lb = force_upgrade_from_lb
        self.compare_all_tiers = compare_all_tiers
        self.round_mode = round_mode
        self.allow_manual_override = allow_manual_override
        self.tiers = [
            FakeTier(1, "15.00", "9.99", 1),
            FakeTier(2, "25.00", "14.99", 2),
        ]


class WeightPricingEngineTests(unittest.TestCase):
    def test_max_revenue_prefers_base_plus_extra_for_22_lb(self):
        profile = FakeProfile(strategy="MAX_REVENUE", extra_lb_price="0.90")
        engine = WeightPricingEngine(profile)

        result = engine.quote("22.00")

        self.assertEqual(result["selected_price"], "16.29")
        self.assertEqual(result["recommended_price"], "16.29")
        self.assertEqual(result["selected_option_type"], "BASE_PLUS_EXTRA")
        self.assertEqual(result["highest_valid_price"], "16.29")
        self.assertIn("MAX_REVENUE", result["decision_reason"])
        self.assertIn("ALL_TIERS_BASE_PLUS_EXTRA=16.29", result["decision_reason"])

    def test_max_revenue_prefers_upper_tier_for_20_lb(self):
        profile = FakeProfile(strategy="MAX_REVENUE", extra_lb_price="0.90")
        engine = WeightPricingEngine(profile)

        result = engine.quote("20.00")

        self.assertEqual(result["selected_price"], "14.99")
        self.assertEqual(result["recommended_price"], "14.99")
        self.assertEqual(result["selected_tier_max_weight_lb"], "25.00")
        self.assertEqual(result["highest_valid_price"], "14.99")
        self.assertEqual(result["difference_selected_vs_highest"], "0.00")
        self.assertIn("BEST_TIER_FIT=14.99", result["decision_reason"])

    def test_quote_exposes_manual_override_permission(self):
        profile = FakeProfile(strategy="MAX_REVENUE", allow_manual_override=True)
        engine = WeightPricingEngine(profile)

        result = engine.quote("22.00")

        self.assertTrue(result["allow_manual_override"])
        self.assertGreaterEqual(result["evaluated_options_count"], 2)


if __name__ == "__main__":
    unittest.main()
